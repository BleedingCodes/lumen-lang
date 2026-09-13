from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from .bytecode import Op
from .compiler import FunctionProto


class VMError(RuntimeError):
    pass


@dataclass(slots=True)
class Cell:
    value: object


@dataclass(slots=True)
class Closure:
    proto: FunctionProto
    upvalues: list[Cell]

    def __repr__(self) -> str:
        return f"<fn {self.proto.name}>"


@dataclass(slots=True)
class Native:
    name: str
    arity: int | None
    function: Callable[..., object]

    def __repr__(self) -> str:
        return f"<native {self.name}>"


@dataclass(slots=True)
class Frame:
    closure: Closure
    ip: int
    slots: int


class VM:
    def __init__(self, *, trace: bool = False) -> None:
        self.trace = trace
        self.stack: list[object] = []
        self.frames: list[Frame] = []
        self.globals: dict[str, object] = {}
        self.open_upvalues: dict[int, Cell] = {}

        self.globals.update(
            {
                "print": Native("print", None, self._native_print),
                "clock": Native("clock", 0, lambda: time.time()),
                "len": Native("len", 1, len),
                "type": Native("type", 1, self._native_type),
                "range": Native("range", None, lambda *args: list(range(*args))),
            }
        )

    def run(self, proto: FunctionProto) -> object:
        script = Closure(proto, [])
        self.stack.append(script)
        self._call(script, 0)

        while self.frames:
            frame = self.frames[-1]
            instruction = frame.closure.proto.chunk.code[frame.ip]
            frame.ip += 1

            if self.trace:
                print(
                    f"{frame.ip - 1:04d} {instruction.op.name:<18} "
                    f"{instruction.operand!r} stack={self.stack!r}"
                )

            op = instruction.op
            operand = instruction.operand

            if op is Op.CONSTANT:
                self.stack.append(frame.closure.proto.chunk.constants[operand])
            elif op is Op.NULL:
                self.stack.append(None)
            elif op is Op.TRUE:
                self.stack.append(True)
            elif op is Op.FALSE:
                self.stack.append(False)
            elif op is Op.POP:
                self.stack.pop()

            elif op is Op.GET_LOCAL:
                value = self.stack[frame.slots + operand]
                self.stack.append(value.value if isinstance(value, Cell) else value)
            elif op is Op.SET_LOCAL:
                index = frame.slots + operand
                current = self.stack[index]
                if isinstance(current, Cell):
                    current.value = self.stack[-1]
                else:
                    self.stack[index] = self.stack[-1]
            elif op is Op.GET_GLOBAL:
                name = frame.closure.proto.chunk.constants[operand]
                if name not in self.globals:
                    raise VMError(f"Undefined variable {name!r}.")
                self.stack.append(self.globals[name])
            elif op is Op.DEFINE_GLOBAL:
                name = frame.closure.proto.chunk.constants[operand]
                self.globals[name] = self.stack.pop()
            elif op is Op.SET_GLOBAL:
                name = frame.closure.proto.chunk.constants[operand]
                if name not in self.globals:
                    raise VMError(f"Undefined variable {name!r}.")
                self.globals[name] = self.stack[-1]
            elif op is Op.GET_UPVALUE:
                self.stack.append(frame.closure.upvalues[operand].value)
            elif op is Op.SET_UPVALUE:
                frame.closure.upvalues[operand].value = self.stack[-1]

            elif op is Op.EQUAL:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a == b)
            elif op is Op.GREATER:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a > b)
            elif op is Op.LESS:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a < b)
            elif op is Op.ADD:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a + b)
            elif op is Op.SUBTRACT:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a - b)
            elif op is Op.MULTIPLY:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a * b)
            elif op is Op.DIVIDE:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a / b)
            elif op is Op.MODULO:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a % b)
            elif op is Op.NOT:
                self.stack.append(not self._truthy(self.stack.pop()))
            elif op is Op.NEGATE:
                self.stack.append(-self.stack.pop())

            elif op is Op.JUMP:
                frame.ip = operand
            elif op is Op.JUMP_IF_FALSE:
                if not self._truthy(self.stack[-1]):
                    frame.ip = operand
            elif op is Op.LOOP:
                frame.ip = operand

            elif op is Op.CALL:
                self._call_value(self.stack[-operand - 1], operand)
            elif op is Op.CLOSURE:
                child_proto = frame.closure.proto.chunk.constants[operand]
                upvalues = []
                for is_local, index in child_proto.upvalue_specs:
                    if is_local:
                        absolute = frame.slots + index
                        cell = self.open_upvalues.get(absolute)
                        if cell is None:
                            current = self.stack[absolute]
                            cell = current if isinstance(current, Cell) else Cell(current)
                            self.stack[absolute] = cell
                            self.open_upvalues[absolute] = cell
                        upvalues.append(cell)
                    else:
                        upvalues.append(frame.closure.upvalues[index])
                self.stack.append(Closure(child_proto, upvalues))
            elif op is Op.CLOSE_UPVALUE:
                absolute = len(self.stack) - 1
                self.open_upvalues.pop(absolute, None)
                self.stack.pop()
            elif op is Op.RETURN:
                result = self.stack.pop()
                finished = self.frames.pop()

                self._close_upvalues(finished.slots)
                del self.stack[finished.slots:]

                if not self.frames:
                    return result

                self.stack.append(result)

            elif op is Op.BUILD_LIST:
                items = self.stack[-operand:] if operand else []
                if operand:
                    del self.stack[-operand:]
                self.stack.append(list(items))
            elif op is Op.BUILD_DICT:
                result = {}
                for _ in range(operand):
                    value = self.stack.pop()
                    key = self.stack.pop()
                    result[key] = value
                self.stack.append(result)
            elif op is Op.INDEX:
                index = self.stack.pop()
                collection = self.stack.pop()
                self.stack.append(collection[index])
            else:
                raise VMError(f"Unknown opcode {op!r}.")

        return None

    def _call_value(self, callee: object, arg_count: int) -> None:
        if isinstance(callee, Closure):
            self._call(callee, arg_count)
            return

        if isinstance(callee, Native):
            if callee.arity is not None and callee.arity != arg_count:
                raise VMError(
                    f"{callee.name} expected {callee.arity} argument(s), "
                    f"got {arg_count}."
                )
            args = self.stack[-arg_count:] if arg_count else []
            result = callee.function(*args)
            del self.stack[-arg_count - 1:]
            self.stack.append(result)
            return

        raise VMError(f"Object is not callable: {callee!r}")

    def _call(self, closure: Closure, arg_count: int) -> None:
        if arg_count != closure.proto.arity:
            raise VMError(
                f"{closure.proto.name} expected {closure.proto.arity} "
                f"argument(s), got {arg_count}."
            )

        self.frames.append(
            Frame(
                closure=closure,
                ip=0,
                slots=len(self.stack) - arg_count - 1,
            )
        )

    def _close_upvalues(self, from_index: int) -> None:
        for index in list(self.open_upvalues):
            if index >= from_index:
                self.open_upvalues.pop(index, None)

    @staticmethod
    def _truthy(value: object) -> bool:
        return value is not None and value is not False

    @staticmethod
    def _native_type(value: object) -> str:
        """Return Lumen type name for a runtime value."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, dict):
            return "dict"
        if isinstance(value, (Closure, Native)):
            return "function"
        return type(value).__name__

    @staticmethod
    def _lumen_repr(value: object) -> str:
        """Convert a runtime value to its Lumen string representation."""
        if value is True:
            return "true"
        if value is False:
            return "false"
        if value is None:
            return "null"
        # Integers that are whole floats: 2.0 -> 2
        if isinstance(value, float) and value == int(value):
            return str(int(value))
        return str(value)

    @staticmethod
    def _native_print(*values: object) -> None:
        print(*[VM._lumen_repr(v) for v in values])
        return None
