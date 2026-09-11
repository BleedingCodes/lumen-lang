from __future__ import annotations

from dataclasses import dataclass

from . import ast_nodes as ast
from .bytecode import Chunk, Op


class CompileError(SyntaxError):
    pass


@dataclass(slots=True)
class FunctionProto:
    name: str
    arity: int
    chunk: Chunk
    upvalue_specs: list[tuple[bool, int]]


@dataclass(slots=True)
class Local:
    name: str
    depth: int
    captured: bool = False


class Compiler:
    def __init__(
        self,
        *,
        name: str = "<script>",
        enclosing: "Compiler | None" = None,
        function_arity: int = 0,
    ) -> None:
        self.name = name
        self.enclosing = enclosing
        self.function_arity = function_arity
        self.chunk = Chunk()
        self.scope_depth = 0
        self.locals: list[Local] = [Local("", 0)]
        self.upvalues: list[tuple[bool, int]] = []

    def compile(self, statements: list[ast.Stmt]) -> FunctionProto:
        for statement in statements:
            self._stmt(statement)

        self.chunk.emit(Op.NULL)
        self.chunk.emit(Op.RETURN)

        return FunctionProto(
            self.name,
            self.function_arity,
            self.chunk,
            self.upvalues,
        )

    def _stmt(self, statement: ast.Stmt) -> None:
        if isinstance(statement, ast.ExpressionStmt):
            self._expr(statement.expression)
            self.chunk.emit(Op.POP)

        elif isinstance(statement, ast.LetStmt):
            if self.scope_depth == 0:
                self._expr(statement.initializer)
                index = self.chunk.add_constant(statement.name)
                self.chunk.emit(Op.DEFINE_GLOBAL, index)
            else:
                self._declare_local(statement.name)
                self._expr(statement.initializer)

        elif isinstance(statement, ast.BlockStmt):
            self._begin_scope()
            for child in statement.statements:
                self._stmt(child)
            self._end_scope()

        elif isinstance(statement, ast.IfStmt):
            self._expr(statement.condition)
            false_jump = self.chunk.emit(Op.JUMP_IF_FALSE, None)
            self.chunk.emit(Op.POP)
            self._stmt(statement.then_branch)
            end_jump = self.chunk.emit(Op.JUMP, None)
            self.chunk.patch(false_jump, len(self.chunk.code))
            self.chunk.emit(Op.POP)
            if statement.else_branch is not None:
                self._stmt(statement.else_branch)
            self.chunk.patch(end_jump, len(self.chunk.code))

        elif isinstance(statement, ast.WhileStmt):
            loop_start = len(self.chunk.code)
            self._expr(statement.condition)
            exit_jump = self.chunk.emit(Op.JUMP_IF_FALSE, None)
            self.chunk.emit(Op.POP)
            self._stmt(statement.body)
            self.chunk.emit(Op.LOOP, loop_start)
            self.chunk.patch(exit_jump, len(self.chunk.code))
            self.chunk.emit(Op.POP)

        elif isinstance(statement, ast.FunctionStmt):
            if self.scope_depth > 0:
                self._declare_local(statement.name)

            function_compiler = Compiler(
                name=statement.name,
                enclosing=self,
                function_arity=len(statement.params),
            )
            function_compiler.scope_depth = 1
            for parameter in statement.params:
                function_compiler.locals.append(
                    Local(parameter, function_compiler.scope_depth)
                )

            proto = function_compiler.compile(statement.body)
            constant = self.chunk.add_constant(proto)
            self.chunk.emit(Op.CLOSURE, constant)

            if self.scope_depth == 0:
                name_index = self.chunk.add_constant(statement.name)
                self.chunk.emit(Op.DEFINE_GLOBAL, name_index)

        elif isinstance(statement, ast.ReturnStmt):
            if self.enclosing is None:
                raise CompileError("Cannot return from top-level code.")
            if statement.value is None:
                self.chunk.emit(Op.NULL)
            else:
                self._expr(statement.value)
            self.chunk.emit(Op.RETURN)

        else:
            raise CompileError(f"Unsupported statement: {statement!r}")

    def _expr(self, expression: ast.Expr) -> None:
        if isinstance(expression, ast.Literal):
            if expression.value is None:
                self.chunk.emit(Op.NULL)
            elif expression.value is True:
                self.chunk.emit(Op.TRUE)
            elif expression.value is False:
                self.chunk.emit(Op.FALSE)
            else:
                self.chunk.emit(
                    Op.CONSTANT,
                    self.chunk.add_constant(expression.value),
                )

        elif isinstance(expression, ast.Variable):
            self._named_variable(expression.name, assign=False)

        elif isinstance(expression, ast.Assign):
            self._expr(expression.value)
            self._named_variable(expression.name, assign=True)

        elif isinstance(expression, ast.Unary):
            self._expr(expression.right)
            self.chunk.emit(
                Op.NEGATE if expression.operator == "-" else Op.NOT
            )

        elif isinstance(expression, ast.Binary):
            self._expr(expression.left)
            self._expr(expression.right)
            mapping = {
                "==": Op.EQUAL,
                "!=": Op.EQUAL,
                ">": Op.GREATER,
                "<": Op.LESS,
                ">=": Op.LESS,
                "<=": Op.GREATER,
                "+": Op.ADD,
                "-": Op.SUBTRACT,
                "*": Op.MULTIPLY,
                "/": Op.DIVIDE,
                "%": Op.MODULO,
            }
            self.chunk.emit(mapping[expression.operator])
            if expression.operator in {"!=", ">=", "<="}:
                self.chunk.emit(Op.NOT)

        elif isinstance(expression, ast.Logical):
            self._expr(expression.left)
            if expression.operator == "||":
                end_jump = self.chunk.emit(Op.JUMP_IF_FALSE, None)
                skip_jump = self.chunk.emit(Op.JUMP, None)
                self.chunk.patch(end_jump, len(self.chunk.code))
                self.chunk.emit(Op.POP)
                self._expr(expression.right)
                self.chunk.patch(skip_jump, len(self.chunk.code))
            else:
                end_jump = self.chunk.emit(Op.JUMP_IF_FALSE, None)
                self.chunk.emit(Op.POP)
                self._expr(expression.right)
                self.chunk.patch(end_jump, len(self.chunk.code))

        elif isinstance(expression, ast.Call):
            self._expr(expression.callee)
            for argument in expression.arguments:
                self._expr(argument)
            self.chunk.emit(Op.CALL, len(expression.arguments))

        elif isinstance(expression, ast.ListLiteral):
            for item in expression.items:
                self._expr(item)
            self.chunk.emit(Op.BUILD_LIST, len(expression.items))

        elif isinstance(expression, ast.DictLiteral):
            for key, value in expression.items:
                self._expr(key)
                self._expr(value)
            self.chunk.emit(Op.BUILD_DICT, len(expression.items))

        elif isinstance(expression, ast.Index):
            self._expr(expression.collection)
            self._expr(expression.index)
            self.chunk.emit(Op.INDEX)

        else:
            raise CompileError(f"Unsupported expression: {expression!r}")

    def _named_variable(self, name: str, *, assign: bool) -> None:
        local = self._resolve_local(name)
        if local is not None:
            self.chunk.emit(Op.SET_LOCAL if assign else Op.GET_LOCAL, local)
            return

        upvalue = self._resolve_upvalue(name)
        if upvalue is not None:
            self.chunk.emit(Op.SET_UPVALUE if assign else Op.GET_UPVALUE, upvalue)
            return

        constant = self.chunk.add_constant(name)
        self.chunk.emit(Op.SET_GLOBAL if assign else Op.GET_GLOBAL, constant)

    def _resolve_local(self, name: str) -> int | None:
        for index in range(len(self.locals) - 1, -1, -1):
            if self.locals[index].name == name:
                return index
        return None

    def _resolve_upvalue(self, name: str) -> int | None:
        if self.enclosing is None:
            return None

        local = self.enclosing._resolve_local(name)
        if local is not None:
            self.enclosing.locals[local].captured = True
            return self._add_upvalue(True, local)

        upvalue = self.enclosing._resolve_upvalue(name)
        if upvalue is not None:
            return self._add_upvalue(False, upvalue)

        return None

    def _add_upvalue(self, is_local: bool, index: int) -> int:
        spec = (is_local, index)
        if spec in self.upvalues:
            return self.upvalues.index(spec)
        self.upvalues.append(spec)
        return len(self.upvalues) - 1

    def _declare_local(self, name: str) -> None:
        self.locals.append(Local(name, self.scope_depth))

    def _begin_scope(self) -> None:
        self.scope_depth += 1

    def _end_scope(self) -> None:
        self.scope_depth -= 1
        while self.locals and self.locals[-1].depth > self.scope_depth:
            local = self.locals.pop()
            self.chunk.emit(
                Op.CLOSE_UPVALUE if local.captured else Op.POP
            )
