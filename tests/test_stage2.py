"""Tests for five-byte instruction encoding and command line interface."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.assembler import assemble, encode_instruction, parse_program


EXPECTED = bytes.fromhex(
    "F4 0B 00 00 00 "
    "0F 00 00 00 00 "
    "70 16 00 00 00 "
    "CD 07 00 00 00"
)
ROOT = Path(__file__).resolve().parents[1]


class TestMachineCode(unittest.TestCase):
    """Verify all reference sequences from the task specification."""

    def test_each_reference_instruction(self):
        source = (ROOT / "examples/reference.asm").read_text(encoding="utf-8")
        program = parse_program(source)
        for index, instruction in enumerate(program):
            with self.subTest(name=instruction.name):
                start = index * 5
                self.assertEqual(
                    encode_instruction(instruction), EXPECTED[start:start + 5]
                )

    def test_complete_reference_program(self):
        source = (ROOT / "examples/reference.asm").read_text(encoding="utf-8")
        self.assertEqual(assemble(parse_program(source)), EXPECTED)

    def test_cli_creates_binary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "program.bin"
            command = [
                sys.executable, "-m", "src.assembler",
                "examples/reference.asm", str(output), "--test",
            ]
            result = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True,
                check=True,
            )
            self.assertEqual(output.read_bytes(), EXPECTED)
            self.assertIn("Assembled instructions: 4", result.stdout)
            self.assertIn("A=4, B=191", result.stdout)
            self.assertIn("0xF4, 0x0B, 0x00, 0x00, 0x00", result.stdout)


if __name__ == "__main__":
    unittest.main()
