from __future__ import annotations

from .token import KEYWORDS, Token, TokenType


class LexError(SyntaxError):
    pass


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.start_column = 1
        self.tokens: list[Token] = []

    def scan_tokens(self) -> list[Token]:
        while not self._at_end():
            self.start = self.current
            self.start_column = self.column
            self._scan_token()

        self.tokens.append(
            Token(TokenType.EOF, "", None, self.line, self.column)
        )
        return self.tokens

    def _scan_token(self) -> None:
        char = self._advance()

        singles = {
            "(": TokenType.LEFT_PAREN,
            ")": TokenType.RIGHT_PAREN,
            "{": TokenType.LEFT_BRACE,
            "}": TokenType.RIGHT_BRACE,
            "[": TokenType.LEFT_BRACKET,
            "]": TokenType.RIGHT_BRACKET,
            ",": TokenType.COMMA,
            ".": TokenType.DOT,
            ";": TokenType.SEMICOLON,
            ":": TokenType.COLON,
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "%": TokenType.PERCENT,
        }

        if char in singles:
            self._add(singles[char])
        elif char == "!":
            self._add(TokenType.BANG_EQUAL if self._match("=") else TokenType.BANG)
        elif char == "=":
            self._add(TokenType.EQUAL_EQUAL if self._match("=") else TokenType.EQUAL)
        elif char == "<":
            self._add(TokenType.LESS_EQUAL if self._match("=") else TokenType.LESS)
        elif char == ">":
            self._add(TokenType.GREATER_EQUAL if self._match("=") else TokenType.GREATER)
        elif char == "&":
            if self._match("&"):
                self._add(TokenType.AND)
            else:
                self._error("Expected '&' after '&'.")
        elif char == "|":
            if self._match("|"):
                self._add(TokenType.OR)
            else:
                self._error("Expected '|' after '|'.")
        elif char == "/":
            if self._match("/"):
                while self._peek() != "\n" and not self._at_end():
                    self._advance()
            else:
                self._add(TokenType.SLASH)
        elif char in {" ", "\r", "\t"}:
            return
        elif char == "\n":
            self.line += 1
            self.column = 1
        elif char == '"':
            self._string()
        elif char.isdigit():
            self._number()
        elif char.isalpha() or char == "_":
            self._identifier()
        else:
            self._error(f"Unexpected character {char!r}.")

    def _string(self) -> None:
        chars: list[str] = []

        while not self._at_end():
            char = self._advance()

            if char == '"':
                self._add(TokenType.STRING, "".join(chars))
                return

            if char == "\\":
                if self._at_end():
                    break
                escape = self._advance()
                escapes = {
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    '"': '"',
                    "\\": "\\",
                }
                if escape not in escapes:
                    self._error(f"Unknown escape sequence '\\\\{escape}'.")
                chars.append(escapes[escape])
            else:
                if char == "\n":
                    self.line += 1
                    self.column = 1
                chars.append(char)

        self._error("Unterminated string.")

    def _number(self) -> None:
        while self._peek().isdigit():
            self._advance()

        if self._peek() == "." and self._peek_next().isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()

        text = self.source[self.start:self.current]
        value = float(text) if "." in text else int(text)
        self._add(TokenType.NUMBER, value)

    def _identifier(self) -> None:
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        text = self.source[self.start:self.current]
        self._add(KEYWORDS.get(text, TokenType.IDENTIFIER))

    def _add(self, type_: TokenType, literal: object = None) -> None:
        text = self.source[self.start:self.current]
        self.tokens.append(
            Token(type_, text, literal, self.line, self.start_column)
        )

    def _match(self, expected: str) -> bool:
        if self._at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def _peek(self) -> str:
        return "\0" if self._at_end() else self.source[self.current]

    def _peek_next(self) -> str:
        return "\0" if self.current + 1 >= len(self.source) else self.source[self.current + 1]

    def _advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        self.column += 1
        return char

    def _at_end(self) -> bool:
        return self.current >= len(self.source)

    def _error(self, message: str) -> None:
        raise LexError(f"[line {self.line}, column {self.start_column}] {message}")
