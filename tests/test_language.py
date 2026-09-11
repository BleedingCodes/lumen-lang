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


if __name__ == "__main__":
    unittest.main()
