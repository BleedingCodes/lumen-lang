from __future__ import annotations

from .ast_nodes import (
    Assign,
    Binary,
    BlockStmt,
    Call,
    DictLiteral,
    ExpressionStmt,
    FunctionStmt,
    IfStmt,
    Index,
    LetStmt,
    ListLiteral,
    Literal,
    Logical,
    ReturnStmt,
    Unary,
    Variable,
    WhileStmt,
)
from .token import Token, TokenType


class ParseError(SyntaxError):
    pass


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def parse(self):
        statements = []
        while not self._at_end():
            statements.append(self._declaration())
        return statements

    def _declaration(self):
        if self._match(TokenType.LET):
            return self._let_declaration()
        if self._match(TokenType.FN):
            return self._function_declaration()
        return self._statement()

    def _let_declaration(self):
        name = self._consume(TokenType.IDENTIFIER, "Expected variable name.")
        self._consume(TokenType.EQUAL, "Expected '=' after variable name.")
        initializer = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after declaration.")
        return LetStmt(name.lexeme, initializer)

    def _function_declaration(self):
        name = self._consume(TokenType.IDENTIFIER, "Expected function name.")
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after function name.")
        params: list[str] = []

        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                params.append(
                    self._consume(
                        TokenType.IDENTIFIER,
                        "Expected parameter name.",
                    ).lexeme
                )
                if not self._match(TokenType.COMMA):
                    break

        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters.")
        self._consume(TokenType.LEFT_BRACE, "Expected '{' before function body.")
        body = self._block()
        return FunctionStmt(name.lexeme, params, body)

    def _statement(self):
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.LEFT_BRACE):
            return BlockStmt(self._block())

        expression = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression.")
        return ExpressionStmt(expression)

    def _if_statement(self):
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'if'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after condition.")
        then_branch = self._statement()
        else_branch = self._statement() if self._match(TokenType.ELSE) else None
        return IfStmt(condition, then_branch, else_branch)

    def _while_statement(self):
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'while'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after condition.")
        return WhileStmt(condition, self._statement())

    def _return_statement(self):
        value = None if self._check(TokenType.SEMICOLON) else self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after return value.")
        return ReturnStmt(value)

    def _block(self):
        statements = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._at_end():
            statements.append(self._declaration())
        self._consume(TokenType.RIGHT_BRACE, "Expected '}' after block.")
        return statements

    def _expression(self):
        return self._assignment()

    def _assignment(self):
        expression = self._or()

        if self._match(TokenType.EQUAL):
            value = self._assignment()
            if isinstance(expression, Variable):
                return Assign(expression.name, value)
            raise self._error(self._previous(), "Invalid assignment target.")

        return expression

    def _or(self):
        expression = self._and()
        while self._match(TokenType.OR):
            expression = Logical(expression, "||", self._and())
        return expression

    def _and(self):
        expression = self._equality()
        while self._match(TokenType.AND):
            expression = Logical(expression, "&&", self._equality())
        return expression

    def _equality(self):
        expression = self._comparison()
        while self._match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self._previous().lexeme
            expression = Binary(expression, operator, self._comparison())
        return expression

    def _comparison(self):
        expression = self._term()
        while self._match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            operator = self._previous().lexeme
            expression = Binary(expression, operator, self._term())
        return expression

    def _term(self):
        expression = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous().lexeme
            expression = Binary(expression, operator, self._factor())
        return expression

    def _factor(self):
        expression = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            operator = self._previous().lexeme
            expression = Binary(expression, operator, self._unary())
        return expression

    def _unary(self):
        if self._match(TokenType.BANG, TokenType.MINUS):
            return Unary(self._previous().lexeme, self._unary())
        return self._call()

    def _call(self):
        expression = self._primary()

        while True:
            if self._match(TokenType.LEFT_PAREN):
                arguments = []
                if not self._check(TokenType.RIGHT_PAREN):
                    while True:
                        arguments.append(self._expression())
                        if not self._match(TokenType.COMMA):
                            break
                self._consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments.")
                expression = Call(expression, arguments)
            elif self._match(TokenType.LEFT_BRACKET):
                index = self._expression()
                self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after index.")
                expression = Index(expression, index)
            else:
                break

        return expression

    def _primary(self):
        if self._match(TokenType.FALSE):
            return Literal(False)
        if self._match(TokenType.TRUE):
            return Literal(True)
        if self._match(TokenType.NULL):
            return Literal(None)
        if self._match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self._previous().literal)
        if self._match(TokenType.IDENTIFIER):
            return Variable(self._previous().lexeme)
        if self._match(TokenType.LEFT_PAREN):
            expression = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after expression.")
            return expression
        if self._match(TokenType.LEFT_BRACKET):
            items = []
            if not self._check(TokenType.RIGHT_BRACKET):
                while True:
                    items.append(self._expression())
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after list.")
            return ListLiteral(items)
        if self._match(TokenType.LEFT_BRACE):
            items = []
            if not self._check(TokenType.RIGHT_BRACE):
                while True:
                    key = self._expression()
                    self._consume(TokenType.COLON, "Expected ':' in dictionary.")
                    value = self._expression()
                    items.append((key, value))
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RIGHT_BRACE, "Expected '}' after dictionary.")
            return DictLiteral(items)

        raise self._error(self._peek(), "Expected expression.")

    def _match(self, *types: TokenType) -> bool:
        if any(self._check(type_) for type_ in types):
            self._advance()
            return True
        return False

    def _consume(self, type_: TokenType, message: str) -> Token:
        if self._check(type_):
            return self._advance()
        raise self._error(self._peek(), message)

    def _check(self, type_: TokenType) -> bool:
        return self._peek().type is type_

    def _advance(self) -> Token:
        if not self._at_end():
            self.current += 1
        return self._previous()

    def _at_end(self) -> bool:
        return self._peek().type is TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _error(self, token: Token, message: str) -> ParseError:
        return ParseError(
            f"[line {token.line}, column {token.column}] {message}"
        )
