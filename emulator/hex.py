import re

VALID_HEX = re.compile(r"^([0-9a-fA-F]|\s)*$")

def hexdumps(b: bytes):
    return " ".join(f"{x:02x}" for x in b)

def hexparse(hex: str):
    if not VALID_HEX.match(hex):
        raise Exception("Invalid pattern")

    # remove whitespace
    hex = re.sub(r"\s", "", hex)

    if len(hex) % 2 != 0:
        raise Exception("Invalid length")

    # split into groups of two characters
    hex_chars = (hex[i:i+2] for i in range(0, len(hex), 2))

    # convert each group to a byte
    return bytes(int(h, 16) for h in hex_chars)
