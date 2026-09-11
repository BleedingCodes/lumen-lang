from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Expr:
    pass


class Stmt:
    pass


@dataclass(slots=True)
class Literal(Expr):
    value: object


@dataclass(slots=True)
class Variable(Expr):
    name: str


@dataclass(slots=True)
class Assign(Expr):
    name: str
    value: Expr


@dataclass(slots=True)
class Unary(Expr):
    operator: str
    right: Expr


@dataclass(slots=True)
class Binary(Expr):
    left: Expr
    operator: str
    right: Expr


@dataclass(slots=True)
class Logical(Expr):
    left: Expr
    operator: str
    right: Expr


@dataclass(slots=True)
class Call(Expr):
    callee: Expr
    arguments: list[Expr]


@dataclass(slots=True)
class ListLiteral(Expr):
    items: list[Expr]


@dataclass(slots=True)
class DictLiteral(Expr):
    items: list[tuple[Expr, Expr]]


@dataclass(slots=True)
class Index(Expr):
    collection: Expr
    index: Expr


@dataclass(slots=True)
class ExpressionStmt(Stmt):
    expression: Expr


@dataclass(slots=True)
class LetStmt(Stmt):
    name: str
    initializer: Expr


@dataclass(slots=True)
class BlockStmt(Stmt):
    statements: list[Stmt]


@dataclass(slots=True)
class IfStmt(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt | None


@dataclass(slots=True)
class WhileStmt(Stmt):
    condition: Expr
    body: Stmt


@dataclass(slots=True)
class FunctionStmt(Stmt):
    name: str
    params: list[str]
    body: list[Stmt]


@dataclass(slots=True)
class ReturnStmt(Stmt):
    value: Expr | None
