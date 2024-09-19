import pytest

from nethermind.idealis.parse.starknet.event import filter_transfers
from nethermind.idealis.types.starknet import Event
from nethermind.idealis.utils import to_bytes

ADDR_0 = b"\x00" * 32
ADDR_1 = to_bytes("0x0000abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdef")
ADDR_2 = to_bytes("0x0000012345678901234567890123456789012345678901234567890123456789")
ADDR_3 = to_bytes("0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef")

EVENT_DEFAULTS = {
    "block_number": 0,
    "transaction_index": 0,
    "event_index": 0,
    "contract_address": ADDR_0,
    "class_hash": None,
    "data": [],
    "keys": [to_bytes("0099cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9")],
}

# Distinct event signatures from events with 'Transfer' signature
# ------------------------------------------------------------
# SELECT
#     DISTINCT
#         ARRAY(SELECT jsonb_object_keys(decoded_data)) as event_params,
#         array_length(keys, 1) as indexed_params
# FROM core.events WHERE event_name = 'Transfer';
# ------------------------------------------------------------


@pytest.mark.parametrize(
    "params,expected_from,expected_to,expected_value",
    [
        ({"from": ADDR_1, "to": ADDR_2, "value": 1000}, ADDR_1, ADDR_2, 1000),
        ({"from_": ADDR_1, "to": ADDR_2, "value": 1000}, ADDR_1, ADDR_2, 1000),
        ({"amount": 1000, "from": ADDR_1, "to": ADDR_2}, ADDR_1, ADDR_2, 1000),
    ],
    ids=["standard_case_0", "standard_case_1", "standard_case_2"],
)
def test_parse_erc20_events(params, expected_from, expected_to, expected_value):
    transfer, _ = filter_transfers(
        [
            Event(
                decoded_params=params,
                **EVENT_DEFAULTS,
            )
        ]
    )

    assert transfer[0].from_address == expected_from
    assert transfer[0].to_address == expected_to
    assert transfer[0].value == expected_value
