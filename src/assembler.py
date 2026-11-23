"""Assembler for educational VM, variant 26 (stages 1 and 2)."""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


OPCODES = {
    "LOAD_CONST": 4,
    "LOAD_MEM": 15,
    "STORE_MEM": 0,
    "GE": 13,
}
COMMAND_BYTES = 5
MAX_CONSTANT = (1 << 10) - 1
MAX_ADDRESS = (1 << 29) - 1


@dataclass(frozen=True)
class Instruction:
    """Intermediate representation of one VM instruction."""

    name: str
    a: int
    b: int | None = None


PATTERNS = (
    ("LOAD_CONST", re.compile(r"ACC\s*=\s*(\d+)\Z")),
    ("LOAD_MEM", re.compile(r"ACC\s*=\s*MEM\s*\[\s*ACC\s*\]\Z")),
    ("STORE_MEM", re.compile(r"MEM\s*\[\s*(\d+)\s*\]\s*=\s*ACC\Z")),
    ("GE", re.compile(
        r"MEM\s*\[\s*(\d+)\s*\]\s*=\s*"
        r"MEM\s*\[\s*\1\s*\]\s*>=\s*ACC\Z"
    )),
)


def parse_line(text: str, line_number: int) -> Instruction | None:
    """Parse one algebraic statement into opcode fields A and B."""
    statement = text.split("#", maxsplit=1)[0].strip()
    if not statement:
        return None
    for name, pattern in PATTERNS:
        match = pattern.fullmatch(statement)
        if match is None:
            continue
        operand = int(match.group(1)) if match.groups() else None
        limit = MAX_CONSTANT if name == "LOAD_CONST" else MAX_ADDRESS
        if operand is not None and operand > limit:
            raise ValueError(
                f"Line {line_number}: B out of range (0..{limit})"
            )
        return Instruction(name, OPCODES[name], operand)
    raise ValueError(f"Line {line_number}: invalid statement: {statement}")


def parse_program(source: str) -> list[Instruction]:
    """Translate textual instructions to intermediate representation."""
    result = []
    for number, line in enumerate(source.splitlines(), start=1):
        instruction = parse_line(line, number)
        if instruction is not None:
            result.append(instruction)
    return result


def print_fields(program: list[Instruction]) -> None:
    """Show instructions in field/value format required by stage 1."""
    for index, instruction in enumerate(program, start=1):
        fields = f"A={instruction.a}"
        if instruction.b is not None:
            fields += f", B={instruction.b}"
        print(f"{index}. {instruction.name}: {fields}")


def encode_instruction(instruction: Instruction) -> bytes:
    """Encode field A and optional field B into five little-endian bytes."""
    if instruction.name not in OPCODES:
        raise ValueError(f"Unknown instruction: {instruction.name}")
    if instruction.a != OPCODES[instruction.name]:
        raise ValueError("Opcode A does not match instruction name")
    if instruction.b is None:
        if instruction.name != "LOAD_MEM":
            raise ValueError("Missing operand B")
        value = instruction.a
    else:
        if instruction.name == "LOAD_MEM":
            raise ValueError("LOAD_MEM must not have operand B")
        limit = (
            MAX_CONSTANT
            if instruction.name == "LOAD_CONST"
            else MAX_ADDRESS
        )
        if not 0 <= instruction.b <= limit:
            raise ValueError("Operand B out of range")
        value = instruction.a | (instruction.b << 4)
    return value.to_bytes(COMMAND_BYTES, byteorder="little")


def assemble(program: list[Instruction]) -> bytes:
    """Convert intermediate representation into binary machine code."""
    return b"".join(encode_instruction(item) for item in program)


def print_bytes(data: bytes) -> None:
    """Print one hexadecimal byte sequence per machine instruction."""
    for offset in range(0, len(data), COMMAND_BYTES):
        chunk = data[offset:offset + COMMAND_BYTES]
        print(", ".join(f"0x{byte:02X}" for byte in chunk))


def make_parser() -> argparse.ArgumentParser:
    """Configure command-line arguments."""
    parser = argparse.ArgumentParser(description="VM assembler, variant 26")
    parser.add_argument("source", type=Path, help="Source program file")
    parser.add_argument("output", type=Path, help="Output binary file")
    parser.add_argument(
        "--test", action="store_true", help="Show fields and bytes"
    )
    return parser


def main() -> None:
    """Run the assembler CLI."""
    args = make_parser().parse_args()
    try:
        program = parse_program(args.source.read_text(encoding="utf-8"))
        if args.test:
            print_fields(program)
        data = assemble(program)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
        print(f"Assembled instructions: {len(program)}")
        if args.test:
            print_bytes(data)
    except (ValueError, OSError) as error:
        raise SystemExit(f"Error: {error}") from error


if __name__ == "__main__":
    main()
