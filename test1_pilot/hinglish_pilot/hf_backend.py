"""Lazy GPU dependencies: model-free tools never import CUDA packages."""
import copy
import time
from .data import digest, require
from .engine import default_config, environment, read, utc, validate_config

PINS = {'transformers': '4.51.3', 'bitsandbytes': '0.50.2', 'accelerate': '1.6.0',
        'huggingface-hub': '0.30.2', 'tokenizers': '0.21.1', 'safetensors': '0.5.3'}


def resolve_config(config, existing_run=None):
    config = copy.deepcopy(config)
    if existing_run is not None and (existing_run / 'experiment_config.json').exists():
        saved = read(existing_run / 'experiment_config.json')
        for key in ('model_revision', 'tokenizer_revision'):
            if config[key] is None:
                config[key] = saved[key]
    if config['model_revision'] is None:
        from huggingface_hub import HfApi
        config['model_revision'] = HfApi().model_info(config['model_id'], revision='main').sha
    if config['tokenizer_revision'] is None:
        config['tokenizer_revision'] = config['model_revision']
    validate_config(config)
    return config


class HFBackend:
    def __init__(self, config):
        validate_config(config)
        import torch
        from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, GenerationConfig
        from torch.nn.attention import SDPBackend, sdpa_kernel
        require(torch.cuda.is_available(), 'GPU required: Colab Runtime > Change runtime type > T4 GPU')
        require(all(environment()['packages'][k] == v for k, v in PINS.items()), 'Pinned dependency mismatch: fresh runtime, run installation, then restart if imports are stale')
        require(torch.cuda.device_count() == 1, 'Test 1 expects one visible CUDA GPU')
        torch.cuda.set_device(0)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.use_deterministic_algorithms(True)
        self.torch, self.sdpa_kernel, self.SDPBackend = torch, sdpa_kernel, SDPBackend
        self.config = copy.deepcopy(config)
        self.tokenizer = AutoTokenizer.from_pretrained(config['model_id'], revision=config['tokenizer_revision'], trust_remote_code=False)
        model_config = AutoConfig.from_pretrained(config['model_id'], revision=config['model_revision'], trust_remote_code=False)
        require(model_config.model_type == 'qwen3', 'Unexpected model architecture')
        self.native_context = min(32768, model_config.max_position_embeddings)
        require(config['context_limit'] <= self.native_context, 'Requested context exceeds native bound')
        start = time.monotonic()
        torch.cuda.reset_peak_memory_stats()
        quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                                   bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
        self.model = AutoModelForCausalLM.from_pretrained(config['model_id'], revision=config['model_revision'],
            trust_remote_code=False, torch_dtype=torch.float16, quantization_config=quant,
            device_map={'': 0}, attn_implementation='sdpa', low_cpu_mem_usage=True)
        self.model.eval()
        for parameter in self.model.parameters():
            parameter.requires_grad_(False)
        require(getattr(self.model, 'is_loaded_in_4bit', False), '4-bit loading not active')
        require(all(str(x) in ('0', 'cuda:0') for x in self.model.hf_device_map.values()), 'CPU/disk offload forbidden for this recipe')
        torch.cuda.synchronize()
        self.GenerationConfig = GenerationConfig
        prop = torch.cuda.get_device_properties(0)
        # Only stable execution facts participate in resume identity; load timing is separate.
        self.metadata = {'backend': 'huggingface', 'model_revision': config['model_revision'],
            'tokenizer_revision': config['tokenizer_revision'], 'hardware': prop.name,
            'gpu_total_bytes': prop.total_memory, 'capability': list(torch.cuda.get_device_capability()),
            'torch_cuda': torch.version.cuda, 'quantization': self.model.config.quantization_config.to_dict(),
            'attention': 'sdpa with math kernel only', 'compute_dtype': 'float16',
            'chat_template_sha256': digest(self.tokenizer.chat_template),
            'gpu_verified': True, 'verification_scope': 'model loaded; pilot success not yet established'}
        self.load_report = {'loaded_at': utc(), 'load_seconds': time.monotonic() - start,
                            'memory': self.memory(), 'model_memory_bytes': self.model.get_memory_footprint()}

    def memory(self):
        torch = self.torch
        free, total = torch.cuda.mem_get_info()
        return {'peak_allocated_bytes': torch.cuda.max_memory_allocated(),
                'peak_reserved_bytes': torch.cuda.max_memory_reserved(),
                'device_free_at_end_bytes': free, 'device_total_bytes': total,
                'measurement_scope': 'PyTorch peaks on device 0 since per-attempt reset; device free is endpoint only, not minimum throughout'}

    def prepare(self, text, config):
        require(config == self.config, 'Backend config changed after loading')
        require(not any(marker and marker in text for marker in self.tokenizer.all_special_tokens), 'Literal special token in question')
        messages = [{'role': 'system', 'content': config['instruction']}, {'role': 'user', 'content': text}]
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        # Template already adds control tokens; do not duplicate BOS/EOS.
        token_ids = self.tokenizer(prompt, add_special_tokens=False, truncation=False)['input_ids']
        require(len(token_ids) + config['max_new_tokens'] <= min(config['context_limit'], self.native_context),
                f'Overlength prompt ({len(token_ids)} tokens); change data/config with a new version, never truncate')
        return {'rendered_prompt': prompt, 'input_tokens': len(token_ids), 'token_count_kind': 'actual tokenizer'}

    def generate(self, prepared, config, seed):
        import random
        import numpy as np
        torch = self.torch
        require(config == self.config, 'Backend config changed')
        random.seed(seed)
        np.random.seed(seed % 2**32)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        inputs = self.tokenizer(prepared['rendered_prompt'], add_special_tokens=False,
                                return_tensors='pt', truncation=False).to('cuda:0')
        require(inputs['input_ids'].shape[1] == prepared['input_tokens'], 'Tokenization changed')
        eos = self.model.generation_config.eos_token_id
        eos_ids = eos if isinstance(eos, list) else [eos]
        require(all(isinstance(x, int) for x in eos_ids), 'Missing EOS policy')
        pad = self.tokenizer.pad_token_id
        if pad is None:
            pad = eos_ids[0]  # Explicit padding choice for one unpadded example.
        policy = self.GenerationConfig(max_new_tokens=config['max_new_tokens'], do_sample=False,
            num_beams=1, use_cache=True, eos_token_id=eos, pad_token_id=pad,
            repetition_penalty=1.0, temperature=1.0, top_p=1.0, top_k=50)
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        start = time.monotonic()
        with torch.inference_mode(), self.sdpa_kernel(self.SDPBackend.MATH):
            generated = self.model.generate(**inputs, generation_config=policy)
        torch.cuda.synchronize()
        elapsed = time.monotonic() - start
        ids = generated[0, inputs['input_ids'].shape[1]:].tolist()
        ended = bool(ids and ids[-1] in eos_ids)
        truncated = not ended and len(ids) >= config['max_new_tokens']
        return {'raw_response': self.tokenizer.decode(ids, skip_special_tokens=True),
                'raw_response_with_special_tokens': self.tokenizer.decode(ids, skip_special_tokens=False),
                'output_tokens': len(ids), 'latency_seconds': elapsed, 'truncated': truncated,
                'finish_reason': 'eos' if ended else ('length' if truncated else 'unknown'),
                'generation_settings': policy.to_dict(), 'memory': self.memory()}
