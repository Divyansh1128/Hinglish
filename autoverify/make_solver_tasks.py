#!/usr/bin/env python3
"""Write shuffled blind claude_tasks.jsonl and gpt_tasks.jsonl files."""

import argparse
import json
import random
from pathlib import Path

if __package__:
    from ._common import DEFAULT_SEED, FORMS, SOLVERS, load_families
else:
    from _common import DEFAULT_SEED, FORMS, SOLVERS, load_families


def make_solver_tasks(families_path, out_dir, seed=DEFAULT_SEED):
    families = load_families(families_path)
    # Explicit whitelist: never copy the family or rendering dictionaries.
    tasks = [dict(family_id=family["family_id"],
                  rendering_id=family["forms"][form]["rendering_id"],
                  form=form, text=family["forms"][form]["text"])
             for family in families for form in FORMS]
    destination = Path(out_dir)
    paths = {solver: destination / f"{solver}_tasks.jsonl" for solver in SOLVERS}
    if Path(families_path).resolve() in {path.resolve() for path in paths.values()}:
        raise ValueError("output would overwrite the families input")
    destination.mkdir(parents=True, exist_ok=True)
    for solver, path in paths.items():
        shuffled = list(tasks)
        random.Random(f"{seed}:{solver}").shuffle(shuffled)
        path.write_text("".join(json.dumps(task, ensure_ascii=False, allow_nan=False) + "\n"
                                for task in shuffled), encoding="utf-8")
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("families", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args(argv)
    try:
        paths = make_solver_tasks(args.families, args.out_dir, args.seed)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    for solver, path in paths.items():
        print(f"{solver}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
