def to_hex(hex_encode_str: bytes | str, pad: int | None = None) -> str:
    """
    Convert a bytestring to a hex string.
    :param hex_encode_str:
    :param pad:
    :return:
    """

    if isinstance(hex_encode_str, bytes):
        hex_encode_str = f"0x{hex_encode_str.hex()}"

    if pad:
        hex_encode_str = zero_pad_hexstr(hex_encode_str, byte_length=pad)

    return hex_encode_str


def to_bytes(hexstr: str, pad: int | None = None) -> bytes:
    """
    Convert a hex string to a bytestring.  If hexstring is '0x' prefixed, the prefix is removed.

    :param hexstr:  Hex string to convert.
    :param pad: Zero-Pad Hexstring before converting to bytes (default: False).
    :return:
    """
    if pad:
        hexstr = zero_pad_hexstr(hexstr, pad)

    if hexstr.startswith("0x"):
        hexstr = hexstr[2:]

    if len(hexstr) % 2 != 0:
        hexstr = "0" + hexstr

    return bytes.fromhex(hexstr)


def strip_leading_zeroes(byte_list: list[bytes]) -> list[bytes]:
    """
    Strips leading zeroes from a list of bytes

    :param byte_list:
    :return:
    """
    return [b.lstrip(b"\x00") for b in byte_list]


def hex_to_int(hexstr: str) -> int:
    """
    Convert a hex string to an integer.
    :param hexstr:
    :return:
    """
    if isinstance(hexstr, int):
        return hexstr
    return int(hexstr, 16)


def zero_pad_hexstr(hex_str: str, byte_length: int = 32) -> str:
    """
    Zero pad a hex string to a certain length.
    :param hex_str:
    :param byte_length:
    :return:
    """
    hex_str = hex_str[2:] if hex_str.startswith("0x") else hex_str
    hex_str = hex_str.rjust(byte_length * 2, "0")
    return f"0x{hex_str}"
