import pytest

from nethermind.idealis.parse.starknet.event import filter_transfers
from nethermind.idealis.types.starknet import Event
from nethermind.idealis.utils import to_bytes

ADDR_0 = b"\x00" * 32
ADDR_1 = to_bytes("0x0000abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdef")
ADDR_2 = to_bytes("0x0000012345678901234567890123456789012345678901234567890123456789")
ADDR_3 = to_bytes("0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef")

ID_0_HEX = "0x0000000000000000000000000000000000000000000000000000000000000000"
ID_1_HEX = "0x0000000000000000001111111110000000000000111111111111111100000000"
ID_0 = to_bytes("0x00")
ID_1 = to_bytes("0x1111111110000000000000111111111111111100000000")

ADDR_0_HEX, ADDR_1_HEX = "0x" + ADDR_0.hex(), "0x" + ADDR_1.hex()
ADDR_2_HEX, ADDR_3_HEX = "0x" + ADDR_2.hex(), "0x" + ADDR_3.hex()


EVENT_DEFAULTS = {
    "block_number": 0,
    "transaction_index": 0,
    "event_index": 0,
    "contract_address": ADDR_0,
    "class_hash": None,
    "data": [],
    # Keys shouldnt matter since the transfer parsing ignores them & only looks at decoded_params
    "keys": [to_bytes("0099cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9")],
}


# Distinct event signatures from events with 'Transfer' signature
# ------------------------------------------------------------
# SELECT
#     DISTINCT
#         ARRAY(SELECT jsonb_object_keys(decoded_data)) as event_params
# FROM core.events WHERE event_name = 'Transfer';
# ------------------------------------------------------------
# {to,_from,tokenId}                            -- (ERC721) done
# {to,from,amountOrId}                          -- ignore
# {to,ext,token,amount}                         -- ignore
# {id,amount,caller,sender,receiver}            -- ignore
# {to,from,value,counter}                       -- (ERC20) done
# {to,from,token_id}                            -- (ERC721) done
# {to,from_,tokenId}                            -- (ERC721) done
# {_to,_from,_tokenId}                          -- (ERC721) done
# {value,sender,recipient}                      -- (ERC20) done
# {to,from,asset,amount}                        -- (ERC20) done
# {to,from,value}                               -- (ERC20) done
# {to,from_,value}                              -- (ERC20) done
# {amount,to_address,from_address}              -- (ERC20) done
# {to,from,amount}                              -- (ERC20) done
# {id,to,amount,exp_time}                       -- ignore
# {to,from,tick,value}                          -- (ERC20) done


@pytest.mark.parametrize(
    ["params", "expected_from", "expected_to", "expected_value"],
    [
        # fmt: off
        ({"from": ADDR_1_HEX, "to": ADDR_2_HEX, "value": 1000}, ADDR_1, ADDR_2, 1000),
        ({"from_": ADDR_1_HEX, "to": ADDR_2_HEX, "value": 1000}, ADDR_1, ADDR_2, 1000),
        ({"amount": 1000, "from": ADDR_1_HEX, "to": ADDR_2_HEX}, ADDR_1, ADDR_2, 1000),
        ({"to": ADDR_2_HEX, "from": ADDR_1_HEX, "tick": 120, "value": 1000}, ADDR_1, ADDR_2, 1000),
        ({"to_address": ADDR_1_HEX, "from_address": ADDR_3_HEX, "amount": 525}, ADDR_3, ADDR_1, 525),
        ({"to": ADDR_2_HEX, "from": ADDR_3_HEX, "amount": 1200, "asset": 0xabcd}, ADDR_3, ADDR_2, 1200),
        ({"value": 321, "sender": ADDR_0_HEX, "recipient": ADDR_1_HEX}, ADDR_0, ADDR_1, 321),
        ({"to": ADDR_0_HEX, "from": ADDR_1_HEX, "value": 4321, "counter": 100}, ADDR_1, ADDR_0, 4321),
        # fmt: on
    ],
    ids=[
        "standard_value",
        "underscored_from",
        "standard_amount",
        "tick_case",
        "from_address_to_address",
        "asset_case",
        "sender_recipient",
        "counter",
    ],
)
def test_parse_erc20_events(params, expected_from, expected_to, expected_value):
    transfer, erc_721 = filter_transfers(
        [
            Event(
                decoded_params=params,
                **EVENT_DEFAULTS,
            )
        ]
    )

    assert len(transfer) == 1
    assert len(erc_721) == 0

    assert transfer[0].from_address == expected_from
    assert transfer[0].to_address == expected_to
    assert transfer[0].value == expected_value


@pytest.mark.parametrize(
    ["params", "expected_from", "expected_to", "expected_id"],
    [
        # fmt: off
        ({"to": ADDR_3_HEX, "from": ADDR_1_HEX, "token_id": ID_0_HEX}, ADDR_1, ADDR_3, ID_0),
        ({"to": ADDR_3_HEX, "from": ADDR_0_HEX, "token_id": 255}, ADDR_0, ADDR_3, to_bytes('0xff')),
        ({"to": ADDR_3_HEX, "from_": ADDR_1_HEX, "tokenId": ID_1_HEX}, ADDR_1, ADDR_3, ID_1),
        ({"_to": ADDR_2_HEX, "_from": ADDR_3_HEX, "_tokenId": ID_0_HEX}, ADDR_3, ADDR_2, ID_0),
        ({"to": ADDR_2_HEX,"_from": ADDR_0_HEX,"tokenId": ID_1_HEX}, ADDR_0, ADDR_2, ID_1),
        ({'from_': '0x00', 'to': ADDR_2_HEX, 'tokenId': 0}, ADDR_0, ADDR_2, to_bytes('0x00')),
        ({'from_': '0x00', 'to': ADDR_2_HEX, 'tokenId': '0x00'}, ADDR_0, ADDR_2, to_bytes('0x00')),
        # fmt: on
    ],
    ids=[
        "standard_hex",
        "standard_integer",
        "underscored_from",
        "underscore_prefixed",
        "prefixed_from",
        "zero_token_id",
        "zero_token_id_hex",
    ],
)
def test_parse_erc_721_events(params, expected_from, expected_to, expected_id):
    erc_20, transfer = filter_transfers(
        [
            Event(
                decoded_params=params,
                **EVENT_DEFAULTS,
            )
        ]
    )

    assert len(erc_20) == 0
    assert len(transfer) == 1

    assert transfer[0].from_address == expected_from
    assert transfer[0].to_address == expected_to
    assert transfer[0].token_id == expected_id
