from nethermind.idealis.parse.starknet.transaction import (
    parse_incoming_messages,
    parse_transaction_with_receipt,
)
from nethermind.idealis.utils import to_bytes


def test_parse_incoming_message():
    tx_and_receipt_json = {
        "transaction": {
            "transaction_hash": "0x7746b17062141a32b57c328ef875797a8ea89aab99e3660e81199e1f5694f02",
            "type": "L1_HANDLER",
            "version": "0x0",
            "nonce": "0x195e03",
            "contract_address": "0x73314940630fd6dcda0d772d4c972c4e0a9946bef9dabf4ef84eda8ef542b82",
            "calldata": [
                "0xae0ee0a63a2ce6baeeffe56e7714fb4efe48d419",
                "0x455448",
                "0x569d327288d8354f16813afb01bba0e60c1301f9",
                "0x17846b313cb69e95fc2e41b7be3d046edc40a33844c23fdd67c576abc706f0b",
                "0x4563918244f400000",
                "0x0",
            ],
            "entry_point_selector": "0x1b64b1b3b690b43b9b514fb81377518f4039cd3e4f4914d8a6bdf01d679fb19",
        },
        "receipt": {
            "type": "L1_HANDLER",
            "transaction_hash": "0x7746b17062141a32b57c328ef875797a8ea89aab99e3660e81199e1f5694f02",
            "actual_fee": {"amount": "0x0", "unit": "WEI"},
            "execution_status": "SUCCEEDED",
            "finality_status": "ACCEPTED_ON_L2",
            "messages_sent": [],
            "events": [
                {
                    "from_address": "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
                    "keys": ["0x99cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9"],
                    "data": [
                        "0x0",
                        "0x17846b313cb69e95fc2e41b7be3d046edc40a33844c23fdd67c576abc706f0b",
                        "0x4563918244f400000",
                        "0x0",
                    ],
                },
                {
                    "from_address": "0x73314940630fd6dcda0d772d4c972c4e0a9946bef9dabf4ef84eda8ef542b82",
                    "keys": [
                        "0x374396cb322ab5ffd35ddb8627514609289d22c07d039ead5327782f61bb833",
                        "0x455448",
                        "0x17846b313cb69e95fc2e41b7be3d046edc40a33844c23fdd67c576abc706f0b",
                    ],
                    "data": ["0x4563918244f400000", "0x0"],
                },
            ],
            "execution_resources": {
                "steps": 4893,
                "pedersen_builtin_applications": 19,
                "range_check_builtin_applications": 156,
                "poseidon_builtin_applications": 3,
                "data_availability": {"l1_gas": 0, "l1_data_gas": 128},
            },
            "message_hash": "0xc73588b8819b265d2a58556a181c0607e05a5be20c99657bc097e61c1509d0ac",
        },
    }

    transaction_response, _, _ = parse_transaction_with_receipt(
        tx_and_receipt_json, block_number=790105, block_timestamp=1728576433, transaction_index=15
    )

    incoming_messages = parse_incoming_messages([transaction_response])

    assert len(incoming_messages) == 1

    assert incoming_messages[0].message_hash == to_bytes(
        "0xc73588b8819b265d2a58556a181c0607e05a5be20c99657bc097e61c1509d0ac", pad=32
    )
    assert incoming_messages[0].starknet_block_number == 790105
    assert incoming_messages[0].starknet_transaction_index == 15
    assert incoming_messages[0].to_starknet_address == to_bytes(
        "0x73314940630fd6dcda0d772d4c972c4e0a9946bef9dabf4ef84eda8ef542b82", pad=32
    )
    assert len(incoming_messages[0].calldata) == 6


def test_parse_outgoing_message():
    tx_and_receipt_json = {
        "transaction": {
            "transaction_hash": "0x1b011d7326040ddfe5eb6284f11ac1bedea184494f7d6b4d7bcbbbec2f737e0",
            "type": "INVOKE",
            "version": "0x1",
            "nonce": "0x7",
            "max_fee": "0x8c48a407fa1f2",
            "sender_address": "0x3cf29e63d19a19ac92aa5dd7a64c2b1f522aa4320cb223126a65c9d8f3a82b",
            "signature": [
                "0x6ca4c052f41dc79482a5c89787f39dba160ddd39217cde0d22084c2b66b9d56",
                "0x65a56ce4f53de7f78f6c5cc73de262422c067615022f935f456f2bb7cdda1a5",
            ],
            "calldata": [
                "0x1",
                "0x74761a8d48ce002963002becc6d9c3dd8a2a05b1075d55e5967f42296f16bd0",
                "0xe48e45e0642d5f170bb832c637926f4c85b77d555848b693304600c4275f26",
                "0x0",
                "0x3",
                "0x3",
                "0x8b694da611dbd24a06f616f256560170d162e35f",
                "0x19f0a0",
                "0x0",
            ],
        },
        "receipt": {
            "type": "INVOKE",
            "transaction_hash": "0x1b011d7326040ddfe5eb6284f11ac1bedea184494f7d6b4d7bcbbbec2f737e0",
            "actual_fee": {"amount": "0x2e33235694930", "unit": "WEI"},
            "execution_status": "SUCCEEDED",
            "finality_status": "ACCEPTED_ON_L1",
            "messages_sent": [
                {
                    "from_address": "0x74761a8d48ce002963002becc6d9c3dd8a2a05b1075d55e5967f42296f16bd0",
                    "to_address": "0xbb3400f107804dfb482565ff1ec8d8ae66747605",
                    "payload": ["0x0", "0x8b694da611dbd24a06f616f256560170d162e35f", "0x19f0a0", "0x0"],
                }
            ],
            "events": [
                {
                    "from_address": "0x68f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
                    "keys": ["0x99cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9"],
                    "data": [
                        "0x3cf29e63d19a19ac92aa5dd7a64c2b1f522aa4320cb223126a65c9d8f3a82b",
                        "0x0",
                        "0x19f0a0",
                        "0x0",
                    ],
                },
                {
                    "from_address": "0x74761a8d48ce002963002becc6d9c3dd8a2a05b1075d55e5967f42296f16bd0",
                    "keys": ["0x194fc63c49b0f07c8e7a78476844837255213824bd6cb81e0ccfb949921aad1"],
                    "data": [
                        "0x8b694da611dbd24a06f616f256560170d162e35f",
                        "0x19f0a0",
                        "0x0",
                        "0x3cf29e63d19a19ac92aa5dd7a64c2b1f522aa4320cb223126a65c9d8f3a82b",
                    ],
                },
                {
                    "from_address": "0x3cf29e63d19a19ac92aa5dd7a64c2b1f522aa4320cb223126a65c9d8f3a82b",
                    "keys": ["0x5ad857f66a5b55f1301ff1ed7e098ac6d4433148f0b72ebc4a2945ab85ad53"],
                    "data": ["0x1b011d7326040ddfe5eb6284f11ac1bedea184494f7d6b4d7bcbbbec2f737e0", "0x0"],
                },
                {
                    "from_address": "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
                    "keys": ["0x99cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9"],
                    "data": [
                        "0x3cf29e63d19a19ac92aa5dd7a64c2b1f522aa4320cb223126a65c9d8f3a82b",
                        "0x1176a1bd84444c89232ec27754698e5d2e7e1a7f1539f12027f28b23ec9f3d8",
                        "0x2e33235694930",
                        "0x0",
                    ],
                },
            ],
            "execution_resources": {
                "steps": 13347,
                "pedersen_builtin_applications": 20,
                "range_check_builtin_applications": 308,
                "ecdsa_builtin_applications": 1,
                "data_availability": {"l1_gas": 0, "l1_data_gas": 0},
            },
        },
    }

    transaction_response, _, messages = parse_transaction_with_receipt(
        tx_and_receipt_json, block_number=29446, block_timestamp=1680264970, transaction_index=234
    )

    assert len(messages) == 1

    assert messages[0].message_index == 0
    assert messages[0].starknet_transaction_hash == to_bytes(
        "0x1b011d7326040ddfe5eb6284f11ac1bedea184494f7d6b4d7bcbbbec2f737e0", pad=32
    )
    assert messages[0].starknet_transaction_index == 234

    assert len(messages[0].payload) == 4
    assert messages[0].payload[0] == b"\x00"
    assert messages[0].payload[1] == to_bytes("0x8b694da611dbd24a06f616f256560170d162e35f")
