"""Standard-library end-to-end DEMO; no downloads or GPU dependencies."""
import argparse
from pathlib import Path
from hinglish_pilot.engine import FakeBackend, default_config, read, run
from hinglish_pilot.report import analyze, export

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path(__file__).parent/'local_demo'/'demo-v2')
    args = parser.parse_args()
    root = Path(__file__).parent
    config = default_config()
    config['model_revision'] = config['tokenizer_revision'] = '0'*40
    run(args.output, read(root/'fixtures/demo_dataset.json'), read(root/'fixtures/demo_splits.json'), config, FakeBackend())
    metrics, _ = analyze(args.output)
    print(metrics['label'], metrics['status'])
    print(export(args.output))
