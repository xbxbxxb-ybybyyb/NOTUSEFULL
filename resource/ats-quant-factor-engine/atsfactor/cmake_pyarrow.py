#!/usr/bin/env python3

import argparse
import pyarrow as pa


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--get-include', action='store_true')
    parser.add_argument('--get-libraries', action='store_true')
    parser.add_argument('--get-library-dirs', action='store_true')

    args = parser.parse_args()

    if args.get_include:
        print(pa.get_include())

    if args.get_libraries:
        print(';'.join(pa.get_libraries()))

    if args.get_library_dirs:
        print(';'.join(pa.get_library_dirs()))
