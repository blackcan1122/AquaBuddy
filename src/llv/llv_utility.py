import struct
from typing import Union, overload

def _as_bytes(
    data: Union[str, bytes, bytearray, memoryview, int, float],
    *,
    encoding: str = "utf-8",
    byteorder: str = "big",
    signed: bool = False,
    length: int | None = None,
    fp_size: int = 8,          # 4 = 32-bit float, 8 = 64-bit double
) -> bytes:
    """
    Convert `data` to its raw byte representation.

    Text  → encoded bytes
    Bytes → unchanged
    Int   → int.to_bytes(length or minimal, byteorder, signed)
    Float → IEEE-754 via struct.pack()
    """
    if isinstance(data, str):
        return data.encode(encoding)

    if isinstance(data, (bytes, bytearray, memoryview)):
        return bytes(data)

    if isinstance(data, int):
        if length is None:                  # minimal width that fits the value
            bits = data.bit_length() + (1 if signed else 0)
            length = max(1, (bits + 7) // 8)
        return data.to_bytes(length, byteorder, signed=signed)

    if isinstance(data, float):
        if fp_size not in (4, 8):
            raise ValueError("fp_size must be 4 or 8 bytes")
        fmt = ("<" if byteorder == "little" else ">") + ("f" if fp_size == 4 else "d")
        return struct.pack(fmt, data)

    raise TypeError(f"Unsupported type: {type(data).__name__}")


def dec_to_bin(n, width=None):
    if n < 0:
        raise ValueError("n must be non-negative")
    s = format(n, "b")          # same as bin(n)[2:]
    if width:
        s = s.zfill(width)
    return s

def bin_to_decimal(bin_num: int) -> int:
    bin_str = str(bin_num)
    bin_str = bin_str.strip().lower().lstrip("0b")
    if not bin_str or any(ch not in "01" for ch in bin_str):
        raise ValueError("Input must be a non-empty binary string containing only 0 or 1.")

    decimal_value = 0
    power = 0

    for bit in reversed(bin_str):
        decimal_value += int(bit) * (2 ** power)
        power += 1

    return decimal_value

def dec_to_hex(n, width=None):
    if n < 0:
        raise ValueError("n must be non-negative")
    s = format(n, "X")
    if width:
        s = s.zfill(width)
    return s

def hex_to_dec(hex_str):
    hex_str = hex_str.strip().upper().lstrip("0X")
    hex_digits = "0123456789ABCDEF"

    decimal_value = 0
    power = 0
    for digit in reversed(hex_str):
        if digit not in hex_digits:
            raise ValueError(f"Illegal hex digit: {digit!r}")

        value = hex_digits.index(digit)
        decimal_value += value * (16 ** power)
        power += 1

    return int(decimal_value)

BYTES_PER_LINE = 16

def bit_is_set(hex_value, bit_index : int):
    if isinstance(hex_value, str):
        hex_value = int(hex_value, 0)          # handles '0x5A' or '5A'
    if bit_index < 0:
        raise ValueError("bit_index must be >= 0")
    return (hex_value >> bit_index) & 1 == 1

def dump_hex(buffer, offset):
    hex_values = buffer.hex()
    byte_str = []
    for i in range(0, len(str(hex_values)), 2):
        byte_str.append(str(hex_values)[i:i+2])
    print(f"{offset}: {byte_str}")
    return

def dump_line(addr: int,
              chunk: bytes,
              bytes_per_line: int,
              group_size: int = 8) -> str:
    """Return one formatted hex-dump line."""

    addr_str = f"{addr:08X}"

    # 1)  build the groups -------------------------------------------------
    groups = [
        " ".join(f"{b:02X}" for b in chunk[i:i + group_size])
        for i in range(0, len(chunk), group_size)
    ]
    hex_bytes = "  ".join(groups)          # double space between groups

    # 2)  pad so the ASCII column always starts at the same x-pos ----------
    groups_per_line = (bytes_per_line + group_size - 1) // group_size
    hex_width = (
        bytes_per_line * 3 - 1             # "XX " per byte (minus last space)
        + (groups_per_line - 1) * 2        # the extra gaps we just inserted
    )
    hex_bytes = f"{hex_bytes:<{hex_width}}"

    # 3)  ASCII column -----------------------------------------------------
    ascii_ = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
    ascii_+="\n"
    returnstring = f"{addr_str}: {hex_bytes} {ascii_}"
    return (returnstring, ascii_)



def dump_buffer(buf: bytes | bytearray | memoryview, base: int = 0) -> None:
    """Hex-dump an in-memory buffer using your helpers."""
    for off in range(0, len(buf), BYTES_PER_LINE):
        dump_line(base + off, buf[off:off + BYTES_PER_LINE], BYTES_PER_LINE)

if __name__ == "__main__":
    print("Decimal 13 in Binary: ")
    print(dec_to_bin(13))
    print("=========================")
    print("")
    print("Decimal 90 in Hex: ")
    print(dec_to_hex(90))
    print("=========================")
    print("")
    print("Hex 0x5A in Decimal: ")
    print(hex_to_dec("5A"))
    print("=========================")
    print("")
    print("Binary 101001 in Decimal: ")
    print(bin_to_decimal(101001))
    print("=========================")
    print("")
    print("Is Sixth Bit set in 0x5A: ")
    print(bit_is_set("0x5A", 6))
    print("=========================")
    print("")
    print("Hex Dump of  'Hello World' with Offset 0x0100: ")
    dump_hex(_as_bytes("Hello World"), "0100")