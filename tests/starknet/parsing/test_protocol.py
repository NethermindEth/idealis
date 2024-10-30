from nethermind.idealis.utils.starknet import (
    decode_starknet_id_domain,
    encode_starknet_id_domain,
)


def test_starknet_id_domain_encoding():
    assert encode_starknet_id_domain("nethermind") == 553122413236441
    assert encode_starknet_id_domain("nethermind.stark") == 553122413236441


def test_starknet_id_domain_decoding():
    assert decode_starknet_id_domain(553122413236441) == "nethermind"


def test_parse_starknet_id_updates():
    pass


def test_parse_starknet_id_state():
    pass


def test_parse_v0_braavos_subdomain():
    pass
