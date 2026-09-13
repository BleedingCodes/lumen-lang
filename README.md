# lumen-lang

A small but complete programming language implemented in Python. Lumen has its
own syntax, compiles to bytecode, and runs on a stack-based virtual machine —
all written from scratch in pure Python with no dependencies.

Built as a systems programming showcase: lexer, Pratt parser, AST, bytecode
compiler, and VM are all written by hand. No parser generators, no external
libraries, no shortcuts.

---

## What It Is

Built with AI assistance as a learning exercise in language implementation.
Lumen is a dynamically typed, expression-oriented language with:

- **Lexer** — hand-written scanner with line/column tracking and clean error reporting
- **Pratt parser** — top-down operator precedence parsing, the same technique used in production language implementations
- **AST** — typed node hierarchy covering all language constructs
- **Bytecode compiler** — tree-walk compiler that emits a compact instruction set
- **Stack-based VM** — executes bytecode with a call stack, upvalue capture, and native function dispatch
- **Closures** — first-class functions with lexical scoping and upvalue capture
- **Recursion** — full support, verified with fibonacci and factorial examples
- **Collections** — lists and dictionaries with index access
- **Bytecode disassembler** — inspect compiled output for any program
- **Interactive REPL** — evaluate expressions and statements live
- **Native builtins** — `print`, `len`, `type`, `clock`, and more

---

## Language Features

```lumen
// Variables
let x = 10;
let name = "Lumen";

// Arithmetic and comparison
print(2 + 3 * 4);       // 14
print(10 > 5);          // true

// Conditionals
if (x > 5) {
    print("big");
} else {
    print("small");
}

// While loop
let i = 0;
let total = 0;
while (i < 5) {
    total = total + i;
    i = i + 1;
}
print(total);           // 10

// Functions
fn greet(name) {
    return "Hello, " + name;
}
print(greet("world"));  // Hello, world

// Recursion
fn fib(n) {
    if (n < 2) { return n; }
    return fib(n - 1) + fib(n - 2);
}
print(fib(10));         // 55

// Closures
fn make_counter(start) {
    let value = start;
    fn next() {
        value = value + 1;
        return value;
    }
    return next;
}
let counter = make_counter(10);
print(counter());       // 11
print(counter());       // 12

// Lists
let primes = [2, 3, 5, 7, 11];
print(primes[2]);       // 5

// Dictionaries
let person = {"name": "Ada", "field": "computing"};
print(person["name"]);  // Ada
```

---

## Requirements

- Python 3.11+
- No external dependencies — standard library only

---

## Installation

```bash
git clone https://github.com/BleedingCodes/lumen-lang.git
cd lumen-lang
```

No install required. Run directly with `python -m lumen`.

Optional — install as a package for the `lumen` CLI command:

```bash
pip install -e .
```

---

## Usage

**Run a file:**
```bash
python -m lumen examples/demo.lm
```

**Inspect bytecode:**
```bash
python -m lumen --disassemble examples/demo.lm
```

**Interactive REPL:**
```bash
python -m lumen
```

**After `pip install -e .`:**
```bash
lumen examples/demo.lm
lumen --disassemble examples/demo.lm
lumen
```

---

## Bytecode Disassembly

Lumen can print the compiled bytecode for any program. Example output for a
counter closure:

```
== <script> ==
0000 CLOSURE            0  <fn make_counter>
0001 DEFINE_GLOBAL      1
...

== make_counter ==
0000 GET_LOCAL          1
0001 CLOSURE            0  <fn next>
0002 GET_LOCAL          3
0003 RETURN
...

== next ==
0000 GET_UPVALUE        0
0001 CONSTANT           0
0002 ADD
0003 SET_UPVALUE        0
0004 POP
0005 GET_UPVALUE        0
0006 RETURN
...
```

Useful for understanding how the compiler lowers language constructs to
instructions and how the VM's call stack and upvalue mechanism work.

---

## Project Structure

```
lumen-lang/
├── lumen/
│   ├── token.py        # Token types and Token dataclass
│   ├── lexer.py        # Hand-written scanner
│   ├── ast_nodes.py    # AST node definitions
│   ├── parser.py       # Pratt parser
│   ├── bytecode.py     # Instruction set (Op enum) and Chunk
│   ├── compiler.py     # AST → bytecode compiler
│   ├── vm.py           # Stack-based virtual machine
│   ├── runtime.py      # Top-level execute() entry point
│   ├── cli.py          # Command-line interface and REPL
│   └── __main__.py     # python -m lumen entry point
├── examples/
│   └── demo.lm         # Fibonacci, closures, lists, dictionaries
├── tests/
│   └── test_language.py
├── pyproject.toml
└── README.md
```

**Pipeline:**

```
Source text
    ↓ Lexer
Token stream
    ↓ Pratt Parser
AST
    ↓ Compiler
Bytecode (Chunk)
    ↓ VM
Output
```

---

## Running Tests

```bash
python -m unittest discover -s tests -v
```

Tests cover arithmetic, recursion, closures, collections, and while loops —
all verified against exact output from the VM.

---

## Why Pratt Parsing

A Pratt parser (top-down operator precedence) handles operator associativity
and precedence cleanly without grammar rules for every precedence level. Each
token type carries its own binding power and parse functions. It's the same
technique used in production implementations including V8 (JavaScript) and
rustc (Rust) — compact, readable, and easy to extend with new operators.

---

## Built by MainbyteLabs

Python tooling for electronics labs, hardware shops, and Linux-based tech teams.

[MainbyteLabs](https://github.com/MR-MainbyteLabs) ·
[LinkedIn](https://linkedin.com/in/michael-rivera-c0ding) ·
mr.mainbytelabs@gmail.com

---

## License

MIT License

Copyright (c) 2026 Michael Rivera

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
