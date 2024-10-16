from nethermind.idealis.parse.starknet.contract import parse_starknet_class
from nethermind.idealis.types.starknet.core import (
    StarknetFeeUnit,
    Transaction,
    TransactionStatus,
)
from nethermind.idealis.types.starknet.enums import StarknetTxType
from nethermind.idealis.utils import to_bytes
from tests.utils import load_rpc_response

default_tx_fields = {
    "timestamp": 0,
    "selector": b"",
    "status": TransactionStatus.accepted_on_l1,
    "actual_fee": 0,
    "fee_unit": StarknetFeeUnit.wei,
    "execution_resources": {},
    "nonce": 0,
    "signature": [b"", b""],
    "version": "0.13.1",
    "max_fee": 100,
    "account_deployment_data": [b""],
    "tip": 0,
    "resource_bounds": {},
    "paymaster_data": [],
    "calldata": [b""],
    "contract_address": b"",
    "message_hash": None,
    "gas_used": None,
    "user_operations": None,
    "revert_error": None,
}


def test_parse_class_response():
    starknet_class = load_rpc_response("starknet", "get_class_0x5ff.json")
    declare_tx = Transaction(
        class_hash=to_bytes("0x05ffbcfeb50d200a0677c48a129a11245a3fc519d1d98d76882d1c9a1b19c6ed"),
        type=StarknetTxType.declare,
        transaction_hash=to_bytes("0x66d8a952d966c9d8b5deeab61fd70f872b153c4721a1bfffad0fca8cfa4b719"),
        transaction_index=117,
        block_number=505959,
        **default_tx_fields
    )

    parsed_class = parse_starknet_class(declare_tx, starknet_class["result"])
    assert parsed_class.class_hash == to_bytes("0x05ffbcfeb50d200a0677c48a129a11245a3fc519d1d98d76882d1c9a1b19c6ed")
    assert parsed_class.declaration_transaction == to_bytes(
        "0x66d8a952d966c9d8b5deeab61fd70f872b153c4721a1bfffad0fca8cfa4b719"
    )
    assert parsed_class.declaration_block == 505959
