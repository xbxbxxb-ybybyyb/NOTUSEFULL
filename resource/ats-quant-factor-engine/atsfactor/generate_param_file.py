#!/usr/bin/env python3

import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re
import csv
import json


@dataclass
class FactorData:
    is_nonfactor: bool
    type_name: str
    filepath: Path
    content: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    def __post_init__(self):
        with open(self.filepath, 'r') as fin:
            self.content = fin.read()

        get_factor_pattern = r"get_factor<(.*)>\(\)"
        deps = re.findall(get_factor_pattern, self.content)
        self.dependencies = [dep.strip() for dep in deps]

    def to_dict(self):
        d = {
            'type': self.type_name,
        }

        if len(self.dependencies) > 0:
            d['dependencies'] = self.dependencies

        return d


def scan_include(include_dir: Path) -> Dict[str, FactorData]:
    FACTOR_DIRS = ['custom', 'nonfactor']
    FACTOR_NAMESPACE = 'huatai/atsquant/factor'
    factor_data_map = {}

    for factor_dir in FACTOR_DIRS:
        factor_dir = include_dir / FACTOR_NAMESPACE / factor_dir
        for child in factor_dir.iterdir():
            if not child.name.endswith((".h", ".hpp")):
                continue

            factor_data_map[child.stem] = FactorData(
                is_nonfactor=factor_dir.name == 'nonfactor',
                type_name=child.stem,
                filepath=child,
            )

    return factor_data_map


def generate_params(ctx, data: Dict[str, FactorData]):
    param_factors = []
    with open(ctx.input, 'r') as fin:
        reader = csv.reader(fin)
        for row in reader:
            param_factors.append(row[0])

    factors = []

    # factors in csv
    for param_factor in param_factors:
        item = data.get(param_factor)
        if item is None:
            raise RuntimeError(
                'Factor type "{}" not found'.format(param_factor))
        factors.append(item.to_dict())

    # extra factors in dependencies
    i = 0
    while i < len(param_factors):
        param_factor = param_factors[i]
        for dependency in data[param_factor].dependencies:
            if not (dependency in param_factors):
                factors.append(data[dependency].to_dict())
                param_factors.append(dependency)
        i += 1

    with open(ctx.output, 'w') as fout:
        print(json.dumps({
            'factors': factors
        }, indent=2), file=fout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=Path, default='/dev/stdin')
    parser.add_argument('-o', '--output', type=Path, default='/dev/stdout')
    parser.add_argument('--include-dir', type=Path,
                        default=Path(__file__).resolve().parent / "include")
    args = parser.parse_args()
    data = scan_include(args.include_dir)
    generate_params(args, data)


if __name__ == '__main__':
    main()
