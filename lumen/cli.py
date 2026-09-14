from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .bytecode import disassemble
from .runtime import compile_source
from .vm import VM


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lumen",
        description="Lumen bytecode language.",
    )
    parser.add_argument("file", nargs="?", type=Path)
    parser.add_argument("--disassemble", action="store_true")
    parser.add_argument("--trace", action="store_true")
    return parser


def run_file(path: Path, *, disasm: bool, trace: bool) -> int:
    source = path.read_text(encoding="utf-8")
    proto = compile_source(source)

    if disasm:
        print(disassemble(proto.chunk, str(path)))

    VM(trace=trace).run(proto)
    return 0


def repl(*, trace: bool) -> int:
    print("Lumen 0.1.1 — Ctrl-D to exit")
    vm = VM(trace=trace)

    while True:
        try:
            source = input("lumen> ")
        except EOFError:
            print()
            return 0

        if not source.strip():
            continue

        if not source.rstrip().endswith(";") and not source.rstrip().endswith("}"):
            source += ";"

        try:
            vm.run(compile_source(source))
        except Exception as error:
            print(f"error: {error}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.file:
            return run_file(
                args.file,
                disasm=args.disassemble,
                trace=args.trace,
            )
        return repl(trace=args.trace)
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
