from nethermind.idealis.utils import to_bytes


def pprint_hash(format_hash: str | bytes) -> str:
    """Formatting & Printing helper for printing hashes.  Prints the first & last 4 digits of hash hex"""
    if isinstance(format_hash, str):
        format_hash = to_bytes(format_hash)

    return f"0x{format_hash[:4].hex()}...{format_hash[-4:].hex()}"
