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
    def div_two(number) -> list[int,int]:
        result = number / 2
        intnum = int (result)
        remain = number % 2
        return [intnum, remain]
    
    def ReverseOrder(bin_num : int) -> int:
        reversed = str(bin_num)[::-1]
        return int(reversed)
    
    num = n
    binary = 0
    while num != 0:
        myvalue = div_two(num)
        num = myvalue[0]
        binary = binary * 10 + myvalue[1]
    return binary

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

    hex_values = {
    10: "A",
    11: "B",
    12: "C",
    13: "D",
    14: "E",
    15: "F",
    }

    def generate_numbers(number):
        result = number / 16
        intnum = int (result)
        remain = number % 16
        return [intnum, remain]
    
    def number_to_hex(n):
        if n > 9:
            return hex_values[n]
        return str(n)
    
    def to_hex(pair : list[int,int]):
        first = number_to_hex(pair[0])
        second = number_to_hex(pair[1])
        return first + second
    
    return to_hex(generate_numbers(n))

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


def bit_is_set(hex_value, bit_index : int):
    value_str = str(dec_to_bin(hex_to_dec(hex_value)))
    assert len(value_str) > bit_index -1

    if value_str[bit_index - 1] != "0":
        return True
    return False

def dump_hex(buffer, offset):
    return


if __name__ == "__main__":
    print(dec_to_bin(13))
    print(dec_to_hex(90))
    print(hex_to_dec("5A"))
    print(bin_to_decimal(101001))
    print(bit_is_set("0x5A", 6))

    print("=====================")
    buf = _as_bytes(-5, length=4,byteorder="big", signed=True)
    print(buf.hex())
    '''
    Debug Values
    '''
    b = b"Hello World"
    hex_list = [format(byte, "02x") for byte in b]
    print(hex_list)