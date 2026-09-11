from __future__ import annotations

from .bytecode import disassemble
from .compiler import Compiler
from .lexer import Lexer
from .parser import Parser
from .vm import VM


def compile_source(source: str):
    tokens = Lexer(source).scan_tokens()
    statements = Parser(tokens).parse()
    return Compiler().compile(statements)


def execute(
    source: str,
    *,
    vm: VM | None = None,
    trace: bool = False,
):
    machine = vm or VM(trace=trace)
    proto = compile_source(source)
    return machine.run(proto)


def disassemble_source(source: str) -> str:
    proto = compile_source(source)
    return disassemble(proto.chunk, proto.name)
