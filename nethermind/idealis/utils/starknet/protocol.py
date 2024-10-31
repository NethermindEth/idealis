from nethermind.idealis.utils import to_bytes

STARKNET_ID_MAINNET_NAMING_CONTRACT = to_bytes("0x06ac597f8116f886fa1c97a23fa4e08299975ecaf6b598873ca6792b9bbfb678")
STARKNET_ID_MAINNET_VERIFIER_CONTRACT = to_bytes("0x07d14dfd8ee95b41fce179170d88ba1f0d5a512e13aeb232f19cfeec0a88f8bf")
STARKNET_ID_MAINNET_IDENTITY_CONTRACT = to_bytes("0x05dbdedc203e92749e2e746e2d40a768d966bd243df04a6b712e222bc040a9af")

STARKNET_ID_BASIC_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789-"
STARKNET_ID_BIG_ALPHABET = "这来"


def _extract_stars(domain_name: str) -> tuple[str, int]:
    k = 0
    while domain_name.endswith(STARKNET_ID_BIG_ALPHABET[-1]):
        domain_name = domain_name[:-1]
        k += 1
    return domain_name, k

def decode_subdomain(domains: list[int]) -> str:
    return f"{'.'.join(decode_starknet_id_domain(d) for d in domains)}.stark"


def encode_subdomain(subdomain: str) -> list[int]:
    if subdomain.endswith('.stark'):
        subdomain = subdomain[:-6]

    return [encode_starknet_id_domain(d) for d in subdomain.split('.')]


def decode_starknet_id_domain(encoded_domain_id: int) -> str:
    """
    Decodes Base 38 encoded starknet ID domain into a human-readable domain name.
    """
    decoded = ""
    while encoded_domain_id != 0:
        code = encoded_domain_id % (len(STARKNET_ID_BASIC_ALPHABET) + 1)
        encoded_domain_id = encoded_domain_id // (len(STARKNET_ID_BASIC_ALPHABET) + 1)
        if code == len(STARKNET_ID_BASIC_ALPHABET):
            next_encoded_domain_id = encoded_domain_id // (len(STARKNET_ID_BIG_ALPHABET) + 1)
            if next_encoded_domain_id == 0:
                code2 = encoded_domain_id % (len(STARKNET_ID_BIG_ALPHABET) + 1)
                encoded_domain_id = next_encoded_domain_id
                decoded += STARKNET_ID_BASIC_ALPHABET[0] if code2 == 0 else STARKNET_ID_BIG_ALPHABET[code2 - 1]
            else:
                decoded += STARKNET_ID_BIG_ALPHABET[encoded_domain_id % len(STARKNET_ID_BIG_ALPHABET)]
                encoded_domain_id = encoded_domain_id // len(STARKNET_ID_BIG_ALPHABET)
        else:
            decoded += STARKNET_ID_BASIC_ALPHABET[code]

    decoded, k = _extract_stars(decoded)
    if k:
        decoded += (
            (
                (STARKNET_ID_BIG_ALPHABET[-1] * (k // 2 - 1))
                + STARKNET_ID_BIG_ALPHABET[0]
                + STARKNET_ID_BASIC_ALPHABET[1]
            )
            if k % 2 == 0
            else STARKNET_ID_BIG_ALPHABET[-1] * (k // 2 + 1)
        )

    return decoded


def encode_starknet_id_domain(domain_name: str) -> int:
    """Encode domain name into base 38 encoded starknet ID domain."""
    mul = 1
    output = 0
    if domain_name.endswith(".stark"):
        domain_name = domain_name[:-6]

    if domain_name.endswith(STARKNET_ID_BIG_ALPHABET[0] + STARKNET_ID_BASIC_ALPHABET[1]):
        domain_name, k = _extract_stars(domain_name[:-2])
        domain_name += STARKNET_ID_BIG_ALPHABET[-1] * (2 * (k + 1))
    else:
        domain_name, k = _extract_stars(domain_name)
        if k:
            domain_name += STARKNET_ID_BIG_ALPHABET[-1] * (1 + 2 * (k - 1))

    domain_name_size = len(domain_name)

    for i in range(domain_name_size):
        c = domain_name[i]

        # if c is a 'a' at the end of the word
        if i == domain_name_size - 1 and c == STARKNET_ID_BASIC_ALPHABET[0]:
            output += len(STARKNET_ID_BASIC_ALPHABET) * mul

        elif c in STARKNET_ID_BASIC_ALPHABET:
            output += mul * STARKNET_ID_BASIC_ALPHABET.index(c)
            mul *= len(STARKNET_ID_BASIC_ALPHABET) + 1

        elif c in STARKNET_ID_BIG_ALPHABET:
            # adding escape char
            output += len(STARKNET_ID_BASIC_ALPHABET) * mul
            mul *= len(STARKNET_ID_BASIC_ALPHABET) + 1

            # adding char from big alphabet

            # otherwise (includes last char)
            output += mul * (STARKNET_ID_BIG_ALPHABET.index(c) + int(i == domain_name_size - 1))
            mul *= len(STARKNET_ID_BIG_ALPHABET)

        else:
            raise RuntimeError("input string contains unsupported characters")

    return output
