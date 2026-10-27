"""POST-HOC EXPLORATORY tokenization / length analysis (A1/A2 of
research/claude_deep_research/mechanisms_tokenization_2026-10-15.md).

EXPLORATORY: written after all Pilot-B and original-cohort outputs were seen.
Not pre-registered as run here; descriptive only; no causal claims.

Question: do question length and Qwen3 tokenization explain the Romanized-Hindi (R)
accuracy deficit?

Usage (from anywhere; needs only the `tokenizers` package):
    python -I analysis/tokenization/analyze.py --tokenizer /path/to/tokenizer.json
The tokenizer must be Qwen/Qwen3-4B tokenizer.json at revision
1cfa9a7208912126459214e8b04321603b3df60c (sha256 checked below).
Writes analysis/tokenization/results.json. Deterministic (no randomness).
"""
import argparse, csv, hashlib, json, math, os, re, statistics as st
from itertools import combinations

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'analysis', 'tokenization', 'results.json')
QWEN_REPO, QWEN_REV = 'Qwen/Qwen3-4B', '1cfa9a7208912126459214e8b04321603b3df60c'
QWEN_SHA = 'aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4'
COHORTS = {
    'pilot_b': ('pilot_b/pilot_b_families.v2.json', 'results/pilot_b'),
    'pilot_original': ('pilot_original/cohort_dataset.json', 'results/pilot_original'),
}
MODELS = ['qwen3-4b', 'qwen3-8b', 'llama-3.2-3b']
FORMS = 'ERC'

# Lexicon: research/operation_vocabulary_2026-10-15.md section 2 (entry + listed spellings/inflections).
LEXICON = {
    'jod': 'jod jodna jodo jor', 'ghata': 'ghata ghatao ghatana ghataana ghataayi ghataai ghataaya ghataya ghati ghatti',
    'guna': 'guna gunaa gunan', 'bhaag': 'bhaag bhag', 'bhinn': 'bhinn bhin bhinna', 'anupat': 'anupat anupaat',
    'pratishat': 'pratishat pratishaat pratisat', 'kam': 'kam kum', 'zyada': 'zyada zyaada jyada jyaada',
    'bacha': 'bacha bachaa bache bachi bachta bachti bachte', 'kul': 'kul kull', 'yog': 'yog yoga',
    'varg': 'varg varga', 'har': 'har', 'hissa': 'hissa hisa hissaa hisse', 'baraabar': 'baraabar barabar baraabr',
    'baant': 'baant bant baantna baanto baanta baanti baante baantte', 'vaapas': 'vaapas wapas waapas vapas',
    'kaat': 'kaat kat kaata kata kaatna kaatne', 'nikaal': 'nikaal nikal nikaali nikali nikaalna',
    'milkar': 'milkar|mil kar', 'prati': 'prati', 'baaki': 'baaki baki',
    'bada/chhota': 'bada badi bade bara chhota chhoti chhote chota choti chote',
    'ek jaisi': 'ek jaisi|ek jaisa|ek jaise',
}
SINGLE, MULTI = {}, {}
for entry, forms in LEXICON.items():  # '|' separates variants when some variants are multi-word
    for v in (forms.split('|') if '|' in forms else forms.split()):
        if ' ' in v:
            MULTI[tuple(v.split())] = entry
        else:
            SINGLE[v] = entry


def med(x):
    return st.median(x) if x else None


def q(x, p):
    """Linear-interpolated quantile."""
    x = sorted(x); k = (len(x) - 1) * p; f = math.floor(k)
    return x[f] + (x[min(f + 1, len(x) - 1)] - x[f]) * (k - f)


def summ(x):
    return {'n': len(x), 'median': med(x), 'q25': q(x, .25), 'q75': q(x, .75), 'mean': round(st.mean(x), 3),
            'min': min(x), 'max': max(x)} if x else {'n': 0}


def analyse_text(tok, text):
    enc = tok.encode(text, add_special_tokens=False)
    words = [(m.start(), m.end()) for m in re.finditer(r'\S+', text)]
    per_word = [0] * len(words)
    for a, b in enc.offsets:  # assign each token to the word containing its last non-space char (or next word)
        c = b - 1
        while c < len(text) and text[c].isspace():
            c += 1
        for i, (s, e) in enumerate(words):
            if s <= c < e or c < s:
                per_word[i] += 1; break
    cores = []  # alphabetic core of each word, for lexicon matching
    for s, e in words:
        m = re.search(r'[A-Za-z]+', text[s:e])
        cores.append((m.group().lower(), s + m.start(), s + m.end()) if m else (None, s, e))
    def pieces(s, e):
        return sum(1 for a, b in enc.offsets if a < e and b > s)
    ops, used = [], set()
    for i in range(len(cores) - 1):
        key = (cores[i][0], cores[i + 1][0])
        if key in MULTI:
            ops.append({'entry': MULTI[key], 'surface': ' '.join(key), 'pieces': pieces(cores[i][1], cores[i + 1][2])})
            used |= {i, i + 1}
    for i, (w, s, e) in enumerate(cores):
        if i not in used and w in SINGLE:
            ops.append({'entry': SINGLE[w], 'surface': w, 'pieces': pieces(s, e)})
    alpha = [pieces(s, e) for w, s, e in cores if w]
    return {'tokens': len(enc.ids), 'words': len(words), 'tpw': len(enc.ids) / len(words),
            'alpha_word_pieces': alpha, 'ops': ops}


def load_families(path):
    d = json.load(open(os.path.join(ROOT, path), encoding='utf-8'))
    fams = d['families'] if isinstance(d, dict) else d
    return [f for f in fams if f.get('status') == 'ACCEPT']


def load_rows(cohort_dir, model):
    rows = list(csv.DictReader(open(os.path.join(ROOT, cohort_dir, model, 'per_rendering.csv'), encoding='utf-8-sig')))
    return {(r['family_id'], r['form']): r for r in rows}


def exact_perm_mean_diff(vals, flags):
    """Exact two-sided permutation test for the difference in group means (integer values),
    by counting k-subsets via dynamic programming over subset sums."""
    n, k = len(vals), sum(flags)
    if k == 0 or k == n:
        return None
    tot = sum(vals); obs = sum(v for v, f in zip(vals, flags) if f)
    dev = abs(obs * n - k * tot)
    dp = [dict() for _ in range(k + 1)]; dp[0][0] = 1
    for v in vals:
        for j in range(k, 0, -1):
            for s, c in dp[j - 1].items():
                dp[j][s + v] = dp[j].get(s + v, 0) + c
    allc = sum(dp[k].values())
    ext = sum(c for s, c in dp[k].items() if abs(s * n - k * tot) >= dev)
    return ext / allc


def logistic(x, y, iters=50):
    """One-predictor logistic regression by Newton-Raphson; returns None if not well-defined."""
    if len(set(y)) < 2 or min(sum(y), len(y) - sum(y)) < 5:
        return {'status': 'not_fitted', 'reason': 'fewer than 5 events in a class'}
    xs = sorted(zip(x, y))
    if max(a for a, b in xs if b == 0) < min(a for a, b in xs if b == 1) or \
       max(a for a, b in xs if b == 1) < min(a for a, b in xs if b == 0):
        return {'status': 'not_fitted', 'reason': 'complete separation'}
    b0 = b1 = 0.0
    for _ in range(iters):
        g0 = g1 = h00 = h01 = h11 = 0.0
        for xi, yi in zip(x, y):
            p = 1 / (1 + math.exp(-(b0 + b1 * xi))); w = p * (1 - p)
            g0 += yi - p; g1 += (yi - p) * xi; h00 += w; h01 += w * xi; h11 += w * xi * xi
        det = h00 * h11 - h01 ** 2
        b0 += (h11 * g0 - h01 * g1) / det; b1 += (h00 * g1 - h01 * g0) / det
    se1 = math.sqrt(h00 / det)
    return {'status': 'fitted', 'outcome': 'R correct (among E-correct families)', 'predictor': 'R-E question tokens',
            'n': len(y), 'events_R_wrong': len(y) - sum(y), 'beta_per_token': round(b1, 4), 'se': round(se1, 4),
            'OR_per_10_tokens': round(math.exp(10 * b1), 3),
            'OR_per_10_tokens_wald95': [round(math.exp(10 * (b1 - 1.96 * se1)), 3), round(math.exp(10 * (b1 + 1.96 * se1)), 3)],
            'wald_p': round(math.erfc(abs(b1 / se1) / math.sqrt(2)), 4)}


def terciles(fids, val):
    """Rank-based terciles (ties broken by family_id; deterministic)."""
    order = sorted(fids, key=lambda f: (val[f], f)); n = len(order)
    return [order[: round(n / 3)], order[round(n / 3): round(2 * n / 3)], order[round(2 * n / 3):]]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--tokenizer', required=True); a = ap.parse_args()
    from tokenizers import Tokenizer
    import tokenizers
    sha = hashlib.sha256(open(a.tokenizer, 'rb').read()).hexdigest()
    assert sha == QWEN_SHA, f'tokenizer.json sha256 mismatch: {sha}'
    tok = Tokenizer.from_file(a.tokenizer)
    res = {'label': 'POST-HOC EXPLORATORY (outputs already seen; descriptive; no causal claims)',
           'tokenizer': {'repo': QWEN_REPO, 'revision': QWEN_REV, 'file': 'tokenizer.json', 'sha256': sha,
                         'tokenizers_version': tokenizers.__version__, 'add_special_tokens': False},
           'lexicon_source': 'research/operation_vocabulary_2026-10-15.md section 2 (whole-word, case-insensitive; entry + listed variants)',
           'scoring': 'strict scorer v1.0.0 `correct` column of per_rendering.csv', 'cohorts': {}}
    for cname, (dpath, rdir) in COHORTS.items():
        fams = load_families(dpath)
        T = {(f['family_id'], fm): analyse_text(tok, f['forms'][fm]['text']) for f in fams for fm in FORMS}
        fids = [f['family_id'] for f in fams]
        c = {'n_families': len(fids), 'A1': {}, 'A2': {}}
        # ---- A1: model-free tokenization per form
        for fm in FORMS:
            alpha = [p for fid in fids for p in T[(fid, fm)]['alpha_word_pieces']]
            c['A1'][fm] = {'question_tokens': summ([T[(fid, fm)]['tokens'] for fid in fids]),
                           'whitespace_words': summ([T[(fid, fm)]['words'] for fid in fids]),
                           'tokens_per_word': summ([round(T[(fid, fm)]['tpw'], 4) for fid in fids]),
                           'pct_alpha_words_ge3_pieces': round(100 * sum(p >= 3 for p in alpha) / len(alpha), 1),
                           'mean_pieces_per_alpha_word': round(st.mean(alpha), 3)}
        for x in 'RC':
            d = [T[(fid, x)]['tokens'] - T[(fid, 'E')]['tokens'] for fid in fids]
            r = [T[(fid, x)]['tokens'] / T[(fid, 'E')]['tokens'] for fid in fids]
            dt = [T[(fid, x)]['tpw'] - T[(fid, 'E')]['tpw'] for fid in fids]
            c['A1'][f'{x}-E_paired'] = {'token_diff': summ(d), 'token_ratio': summ([round(v, 4) for v in r]),
                                        'tokens_per_word_diff': summ([round(v, 4) for v in dt]),
                                        'families_longer': sum(v > 0 for v in d), 'families_equal': sum(v == 0 for v in d)}
        c['A1']['per_family'] = {fid: {fm: {'tokens': T[(fid, fm)]['tokens'], 'words': T[(fid, fm)]['words'],
                                            'ops': [o['surface'] + ':' + str(o['pieces']) for o in T[(fid, fm)]['ops']]}
                                       for fm in FORMS} for fid in fids}
        opw = {}
        for fm in FORMS:
            occ = [o for fid in fids for o in T[(fid, fm)]['ops']]
            by = {}
            for o in occ:
                by.setdefault(o['entry'], []).append(o['pieces'])
            opw[fm] = {'occurrences': len(occ), 'families_with_any': sum(bool(T[(fid, fm)]['ops']) for fid in fids),
                       'pieces': summ([o['pieces'] for o in occ]),
                       'pct_ge3_pieces': round(100 * sum(o['pieces'] >= 3 for o in occ) / len(occ), 1) if occ else None,
                       'by_entry': {e: {'n': len(v), 'median_pieces': med(v), 'max': max(v)} for e, v in sorted(by.items())}}
        c['A1']['operation_words'] = opw
        # ---- A2: length vs correctness, per model
        for m in MODELS:
            rows = load_rows(rdir, m)
            ok = {(fid, fm): rows[(fid, fm)]['correct'] == 'True' for fid in fids for fm in FORMS}
            rid = {(f['family_id'], fm): f['forms'][fm]['rendering_id'] for f in fams for fm in FORMS}
            assert all(rows[k]['rendering_id'] == rid[k] for k in rid), 'rendering_id mismatch'
            itok = {(fid, fm): int(rows[(fid, fm)]['input_tokens']) for fid in fids for fm in FORMS}
            otok = {(fid, fm): int(rows[(fid, fm)]['output_tokens']) for fid in fids for fm in FORMS}
            Rtok = {fid: T[(fid, 'R')]['tokens'] for fid in fids}
            dRE = {fid: T[(fid, 'R')]['tokens'] - T[(fid, 'E')]['tokens'] for fid in fids}
            mm = {'accuracy': {fm: round(100 * sum(ok[(f, fm)] for f in fids) / len(fids), 1) for fm in FORMS},
                  'output_tokens': {fm: summ([otok[(f, fm)] for f in fids]) for fm in FORMS},
                  'stored_input_tokens_whole_prompt': {fm: summ([itok[(f, fm)] for f in fids]) for fm in FORMS},
                  'stored_input_R-E': summ([itok[(f, 'R')] - itok[(f, 'E')] for f in fids]),
                  'stored_input_C-E': summ([itok[(f, 'C')] - itok[(f, 'E')] for f in fids])}
            if m.startswith('qwen'):  # template is constant, so stored whole-prompt diffs should equal question-only diffs
                mm['check_stored_diff_equals_question_diff'] = {x: sum((itok[(f, x)] - itok[(f, 'E')]) == (T[(f, x)]['tokens'] - T[(f, 'E')]['tokens']) for f in fids) for x in 'RC'}
            tl = []
            for i, grp in enumerate(terciles(fids, Rtok)):
                tl.append({'tercile': i + 1, 'n': len(grp), 'R_tokens_range': [Rtok[grp[0]], Rtok[grp[-1]]],
                           'R_correct': sum(ok[(f, 'R')] for f in grp),
                           'R_acc_pct': round(100 * sum(ok[(f, 'R')] for f in grp) / len(grp), 1),
                           'E_acc_pct': round(100 * sum(ok[(f, 'E')] for f in grp) / len(grp), 1)})
            mm['a_R_accuracy_by_R_question_token_tercile_qwen_tokenizer'] = tl
            disc = [f for f in fids if ok[(f, 'E')] and not ok[(f, 'R')]]
            both = [f for f in fids if ok[(f, 'E')] and ok[(f, 'R')]]
            ewrong = [f for f in fids if not ok[(f, 'E')]]
            mm['b_E_correct_R_wrong_vs_both_correct'] = {
                'E_correct_R_wrong': {'n': len(disc), 'families': disc, 'R-E_tokens': summ([dRE[f] for f in disc]),
                                      'R_tokens': summ([Rtok[f] for f in disc]),
                                      'R-E_ratio_median': med([T[(f, 'R')]['tokens'] / T[(f, 'E')]['tokens'] for f in disc])},
                'both_correct': {'n': len(both), 'R-E_tokens': summ([dRE[f] for f in both]),
                                 'R_tokens': summ([Rtok[f] for f in both]),
                                 'R-E_ratio_median': med([T[(f, 'R')]['tokens'] / T[(f, 'E')]['tokens'] for f in both])},
                'E_wrong_excluded': len(ewrong)}
            ec = disc + both
            flags = [f in disc for f in ec]
            mm['c_family_level'] = {
                'exact_permutation_p_two_sided_mean_R-E_tokens': (lambda p: None if p is None else round(p, 4))(
                    exact_perm_mean_diff([dRE[f] for f in ec], flags)),
                'exact_permutation_p_two_sided_mean_R_tokens': (lambda p: None if p is None else round(p, 4))(
                    exact_perm_mean_diff([Rtok[f] for f in ec], flags)),
                'logistic_R_correct_on_R-E_tokens': logistic([dRE[f] for f in ec], [0 if fl else 1 for fl in flags]),
                'note': 'Among E-correct families only. Post hoc; small n; tokens are Qwen3 counts for all models.'}
            if not m.startswith('qwen'):  # own-tokenizer proxy: stored whole-prompt counts (template constant across forms)
                sd = {f: itok[(f, 'R')] - itok[(f, 'E')] for f in fids}
                mm['c_family_level']['own_tokenizer_stored_R-E'] = {
                    'E_correct_R_wrong': summ([sd[f] for f in disc]), 'both_correct': summ([sd[f] for f in both]),
                    'exact_permutation_p_two_sided_mean': (lambda p: None if p is None else round(p, 4))(
                        exact_perm_mean_diff([sd[f] for f in ec], flags)),
                    'logistic': dict(logistic([sd[f] for f in ec], [0 if fl else 1 for fl in flags]),
                                     predictor='R-E stored whole-prompt input_tokens (Llama tokenizer)')}
            c['A2'][m] = mm
        res['cohorts'][cname] = c
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
