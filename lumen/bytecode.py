from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, auto


class Op(IntEnum):
    CONSTANT = auto()
    NULL = auto()
    TRUE = auto()
    FALSE = auto()
    POP = auto()

    GET_LOCAL = auto()
    SET_LOCAL = auto()
    GET_GLOBAL = auto()
    DEFINE_GLOBAL = auto()
    SET_GLOBAL = auto()
    GET_UPVALUE = auto()
    SET_UPVALUE = auto()

    EQUAL = auto()
    GREATER = auto()
    LESS = auto()
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    NOT = auto()
    NEGATE = auto()

    JUMP = auto()
    JUMP_IF_FALSE = auto()
    LOOP = auto()

    CALL = auto()
    CLOSURE = auto()
    CLOSE_UPVALUE = auto()
    RETURN = auto()

    BUILD_LIST = auto()
    BUILD_DICT = auto()
    INDEX = auto()


@dataclass(slots=True)
class Instruction:
    op: Op
    operand: object = None


@dataclass(slots=True)
class Chunk:
    code: list[Instruction] = field(default_factory=list)
    constants: list[object] = field(default_factory=list)

    def add_constant(self, value: object) -> int:
        self.constants.append(value)
        return len(self.constants) - 1

    def emit(self, op: Op, operand: object = None) -> int:
        self.code.append(Instruction(op, operand))
        return len(self.code) - 1

    def patch(self, index: int, operand: object) -> None:
        self.code[index].operand = operand


def disassemble(chunk: Chunk, name: str = "<script>") -> str:
    lines = [f"== {name} =="]

    for offset, instruction in enumerate(chunk.code):
        operand = "" if instruction.operand is None else f" {instruction.operand!r}"
        lines.append(f"{offset:04d} {instruction.op.name:<18}{operand}")

    if chunk.constants:
        lines.append("-- constants --")
        for index, value in enumerate(chunk.constants):
            lines.append(f"{index:04d} {value!r}")

    return "\n".join(lines)
