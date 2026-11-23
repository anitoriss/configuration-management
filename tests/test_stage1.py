"""Tests for translation to intermediate representation."""

import subprocess
import sys
import unittest
from pathlib import Path

from src.assembler import Instruction, parse_program


SAMPLE = """\
ACC = 191
ACC = MEM[ACC]
MEM[359] = ACC
MEM[124] = MEM[124] >= ACC
"""


class TestIntermediateRepresentation(unittest.TestCase):
    """Validate four specified commands and invalid inputs."""

    def test_reference_fields(self):
        self.assertEqual(parse_program(SAMPLE), [
            Instruction("LOAD_CONST", 4, 191),
            Instruction("LOAD_MEM", 15),
            Instruction("STORE_MEM", 0, 359),
            Instruction("GE", 13, 124),
        ])

    def test_empty_lines_and_comments(self):
        self.assertEqual(parse_program("# comment\n\nACC = 1 # note"), [
            Instruction("LOAD_CONST", 4, 1),
        ])

    def test_reject_constant_overflow(self):
        with self.assertRaisesRegex(ValueError, "out of range"):
            parse_program("ACC = 1024")

    def test_reject_address_overflow(self):
        with self.assertRaisesRegex(ValueError, "out of range"):
            parse_program("MEM[536870912] = ACC")

    def test_stage1_cli_prints_intermediate_representation(self):
        """First commit must be runnable without stage 2 functions."""
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [
                sys.executable, "-m", "src.assembler",
                "examples/reference.asm", "build/reference.bin", "--test",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertRegex(
            result.stdout, r"(?:Parsed|Assembled) instructions: 4"
        )
        self.assertIn("LOAD_CONST: A=4, B=191", result.stdout)
        self.assertIn("LOAD_MEM: A=15", result.stdout)
        self.assertIn("GE: A=13, B=124", result.stdout)

    def test_reject_different_ge_addresses(self):
        with self.assertRaisesRegex(ValueError, "Line 1"):
            parse_program("MEM[1] = MEM[2] >= ACC")


if __name__ == "__main__":
    unittest.main()
