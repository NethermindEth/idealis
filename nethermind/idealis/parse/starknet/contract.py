from typing import Any

from nethermind.idealis.types.starknet.contracts import StarknetClass
from nethermind.idealis.types.starknet.core import TransactionResponse


def parse_starknet_class(
    declare_tx: TransactionResponse,
    class_json: dict[str, Any],
    class_name: str | None = None,
) -> StarknetClass:
    if declare_tx.class_hash is None:
        raise ValueError(
            f"Starknet Tx 0x{declare_tx.transaction_hash.hex()} is not valid Declare Tx"
        )

    return StarknetClass(
        name=class_name,
        abi_json=class_json.get("abi", []),
        class_hash=declare_tx.class_hash,
        class_version=class_json["contract_class_version"],
        declaration_block=declare_tx.block_number,
        declaration_transaction=declare_tx.transaction_hash,
    )
