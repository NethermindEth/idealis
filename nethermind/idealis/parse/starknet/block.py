from typing import Any

from nethermind.idealis.parse.starknet.transaction import parse_transaction_with_receipt
from nethermind.idealis.types.starknet.core import Block, Event, Transaction
from nethermind.idealis.types.starknet.enums import BlockDataAvailabilityMode
from nethermind.idealis.types.starknet.rollup import OutgoingMessage
from nethermind.idealis.utils import hex_to_int, to_bytes


def parse_block(response_json: dict[str, Any]) -> Block:
    return Block(
        block_number=response_json["block_number"],
        block_hash=to_bytes(response_json["block_hash"], pad=32),
        parent_hash=to_bytes(response_json["parent_hash"], pad=32),
        state_root=to_bytes(response_json["new_root"], pad=32),
        sequencer_address=to_bytes(response_json["sequencer_address"], pad=32),
        timestamp=response_json["timestamp"],
        l1_gas_price_fri=hex_to_int(response_json["l1_gas_price"]["price_in_fri"]),
        l1_gas_price_wei=hex_to_int(response_json["l1_gas_price"]["price_in_wei"]),
        l1_data_gas_price_fri=hex_to_int(response_json["l1_data_gas_price"]["price_in_fri"]),
        l1_data_gas_price_wei=hex_to_int(response_json["l1_data_gas_price"]["price_in_wei"]),
        l1_da_mode=BlockDataAvailabilityMode(response_json.get("l1_da_mode", "CALLDATA")),
        starknet_version=response_json["starknet_version"],
        transaction_count=len(response_json["transactions"]),
        total_fee=0,
    )


def parse_block_with_tx_receipts(
    response_json: dict[str, Any]
) -> tuple[Block, list[Transaction], list[Event], list[OutgoingMessage]]:
    block_response = parse_block(response_json)

    transactions, all_events, all_messages = [], [], []
    for tx_idx, tx in enumerate(response_json["transactions"]):
        tx_response, events, messages = parse_transaction_with_receipt(
            tx, block_response.block_number, tx_idx, block_response.timestamp
        )

        transactions.append(tx_response)
        all_events.extend(events)
        all_messages.extend(messages)

    block_response.total_fee = sum(tx.actual_fee for tx in transactions)

    return block_response, transactions, all_events, all_messages
