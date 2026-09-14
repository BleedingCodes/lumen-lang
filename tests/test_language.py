import io
import unittest
from contextlib import redirect_stdout

from lumen.runtime import execute


class LanguageTests(unittest.TestCase):
    def run_program(self, source: str) -> str:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            execute(source)
        return buffer.getvalue().strip()

    def test_arithmetic(self):
        output = self.run_program("print(2 + 3 * 4);")
        self.assertEqual(output, "14")

    def test_recursion(self):
        output = self.run_program(
            """
            fn fact(n) {
                if (n < 2) { return 1; }
                return n * fact(n - 1);
            }
            print(fact(6));
            """
        )
        self.assertEqual(output, "720")

    def test_closure(self):
        output = self.run_program(
            """
            fn make_counter(start) {
                let value = start;
                fn next() {
                    value = value + 1;
                    return value;
                }
                return next;
            }

            let counter = make_counter(10);
            print(counter());
            print(counter());
            """
        )
        self.assertEqual(output, "11\n12")

    def test_collections(self):
        output = self.run_program(
            """
            let xs = [10, 20, 30];
            let info = {"name": "Lumen"};
            print(xs[1], info["name"]);
            """
        )
        self.assertEqual(output, "20 Lumen")

    def test_while(self):
        output = self.run_program(
            """
            let i = 0;
            let total = 0;
            while (i < 5) {
                total = total + i;
                i = i + 1;
            }
            print(total);
            """
        )
        self.assertEqual(output, "10")


    def test_boolean_display(self):
        """Booleans must print as 'true'/'false', not Python 'True'/'False'."""
        self.assertEqual(self.run_program("print(true);"), "true")
        self.assertEqual(self.run_program("print(false);"), "false")
        self.assertEqual(self.run_program("print(10 > 5);"), "true")
        self.assertEqual(self.run_program("print(1 == 2);"), "false")

    def test_null_display(self):
        """null must print as 'null', not Python 'None'."""
        self.assertEqual(self.run_program("print(null);"), "null")

    def test_integer_division_display(self):
        """Whole-number float results should display without decimal point."""
        self.assertEqual(self.run_program("print(4 / 2);"), "2")
        self.assertEqual(self.run_program("print(6 / 3);"), "2")
        # Non-whole results keep the decimal
        self.assertEqual(self.run_program("print(1 / 2);"), "0.5")

    def test_type_builtin(self):
        """type() must return Lumen type names."""
        self.assertEqual(self.run_program("print(type(null));"), "null")
        self.assertEqual(self.run_program("print(type(true));"), "bool")
        self.assertEqual(self.run_program("print(type(1));"), "int")
        self.assertEqual(self.run_program("print(type(1.5));"), "float")
        self.assertEqual(self.run_program('print(type("x"));'), "string")
        self.assertEqual(self.run_program("print(type([1, 2]));"), "list")

    def test_local_shadowing(self):
        """let x = x + n inside a function should see the outer x, not itself."""
        output = self.run_program(
            """
            let x = 10;
            fn f() {
                let x = x + 1;
                print(x);
            }
            f();
            """
        )
        self.assertEqual(output, "11")

    def test_disassembler_recurses(self):
        """Disassembler output must include nested function bytecode."""
        from lumen.runtime import disassemble_source
        output = disassemble_source("fn f(n) { return n * 2; }")
        self.assertIn("== f ==", output)

    def test_logical_short_circuit(self):
        """Short-circuit operators must not evaluate the right side unnecessarily."""
        # OR: right side must not run when left is truthy
        output = self.run_program(
            """
            let called = false;
            fn side() { called = true; return true; }
            let r = true || side();
            print(called);
            """
        )
        self.assertEqual(output, "false")

        # AND: right side must not run when left is falsy
        output = self.run_program(
            """
            let called = false;
            fn side() { called = true; return true; }
            let r = false && side();
            print(called);
            """
        )
        self.assertEqual(output, "false")


    # --- Tests for patched bugs (v0.1.1) ---

    def test_dict_duplicate_key_last_wins(self):
        """Duplicate dict keys must resolve to the last value (standard semantics)."""
        output = self.run_program('let d = {"a": 1, "b": 2, "a": 3}; print(d["a"]);')
        self.assertEqual(output, "3")

    def test_division_by_zero_raises_vm_error(self):
        """Division by zero must raise VMError, not a bare Python ZeroDivisionError."""
        from lumen.vm import VMError
        with self.assertRaises(VMError):
            self.run_program("print(1 / 0);")

    def test_modulo_by_zero_raises_vm_error(self):
        """Modulo by zero must raise VMError, not a bare Python ZeroDivisionError."""
        from lumen.vm import VMError
        with self.assertRaises(VMError):
            self.run_program("print(5 % 0);")

    def test_type_error_arithmetic_raises_vm_error(self):
        """Type mismatch in arithmetic must raise VMError, not a bare Python TypeError."""
        from lumen.vm import VMError
        with self.assertRaises(VMError):
            self.run_program('print(1 + "a");')

    def test_index_out_of_bounds_raises_vm_error(self):
        """Out-of-bounds list access must raise VMError, not a bare Python IndexError."""
        from lumen.vm import VMError
        with self.assertRaises(VMError):
            self.run_program("let xs = [1, 2, 3]; print(xs[10]);")

    def test_dict_missing_key_raises_vm_error(self):
        """Missing dict key must raise VMError, not a bare Python KeyError."""
        from lumen.vm import VMError
        with self.assertRaises(VMError):
            self.run_program('let d = {"a": 1}; print(d["b"]);')

    def test_print_list_with_booleans_and_null(self):
        """List contents must print with Lumen spellings, not Python True/False/None."""
        output = self.run_program("print([true, false, null]);")
        self.assertEqual(output, "[true, false, null]")

    def test_print_dict_with_boolean_value(self):
        """Dict values must print with Lumen spellings.
        String keys print without surrounding quotes — consistent with how
        print("hello") outputs hello, not "hello".
        """
        output = self.run_program('print({"k": true});')
        self.assertEqual(output, "{k: true}")

    def test_unknown_escape_raises_lex_error(self):
        """An unknown escape sequence must raise LexError, not silently pass through."""
        from lumen.lexer import LexError
        with self.assertRaises(LexError):
            self.run_program(r'print("a\zb");')


if __name__ == "__main__":
    unittest.main()
