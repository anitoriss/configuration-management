#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 -m src.assembler examples/reference.asm build/reference.bin --test
python3 -m unittest discover -s tests -v
