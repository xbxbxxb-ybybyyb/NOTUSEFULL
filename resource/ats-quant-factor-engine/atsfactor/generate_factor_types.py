#!/usr/bin/env python3

import argparse
from pathlib import Path
from jinja2 import Template


def build_context(include_dir: str, input_dir: list) -> dict:
    types = []
    nonfactors = []
    for i in input_dir:
        path = Path(i)
        for child in path.iterdir():
            if not child.name.endswith((".h", ".hpp")):
                continue

            types.append({
                "path": child.relative_to(include_dir),
                "type": child.stem
            })

            if path.name == 'nonfactor':
                nonfactors.append(child.stem)

    return {
        "factors": types,
        "nonfactors": nonfactors
    }


def search_template(include_dir: str) -> list:
    include_path = Path(include_dir)
    template_list = []
    for t in include_path.rglob('*.j2'):
        template_list.append(t)

    return template_list


def render_template(path: Path, ctx: dict):
    content = None
    with open(path, "r") as fi:
        content = fi.read()

    out = path.parent / path.stem
    rendered = Template(content).render(ctx)
    with open(out, "w") as fo:
        print("// Auto-generated file, do not edit it.", file=fo)
        print(rendered, file=fo)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', action='append')
    parser.add_argument('--include-dir')
    args = parser.parse_args()

    ctx = build_context(args.include_dir, args.input_dir)
    for t in search_template(args.include_dir):
        render_template(t, ctx)
