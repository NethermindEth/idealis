from typing import Any

from nethermind.idealis.types.ethereum import Block, Event, Transaction
from nethermind.idealis.utils import hex_to_int, to_bytes


def parse_get_block_response(response_json: dict[str, Any]) -> tuple[Block, list[Transaction]]:
    output_transactions = []

    block_number = hex_to_int(response_json["number"])
    block_timestamp = hex_to_int(response_json["timestamp"])

    for transaction in response_json["transactions"]:
        if isinstance(transaction, str):  # Transaction hash instead of full transaction dict
            continue

        output_transactions.append(
            Transaction(
                block_number=block_number,
                transaction_hash=to_bytes(transaction["hash"], pad=32),
                transaction_index=hex_to_int(transaction["transactionIndex"]),
                timestamp=block_timestamp,
                nonce=hex_to_int(transaction["nonce"]),
                type=hex_to_int(transaction["type"]),
                value=hex_to_int(transaction["value"]),
                gas_price=None,
                gas_supplied=hex_to_int(transaction["gas"]),
                gas_used=None,
                max_priority_fee=hex_to_int(transaction.get("maxPriorityFeePerGas", "0x0")),
                max_fee=hex_to_int(transaction.get("maxFeePerGas", "0x0")),
                to_address=to_bytes(transaction["to"], pad=20) if transaction["to"] else None,
                from_address=to_bytes(transaction["from"], pad=20),
                input=to_bytes(transaction["input"]),
                decoded_input=None,
                function_name=None,
            )
        )

    parsed_block = Block(
        block_number=block_number,
        block_hash=to_bytes(response_json["hash"], pad=32),
        timestamp=block_timestamp,
        base_fee_per_gas=hex_to_int(response_json["baseFeePerGas"]) if "baseFeePerGas" in response_json else None,
        miner=to_bytes(response_json["miner"], pad=20),
        difficulty=hex_to_int(response_json["difficulty"]),
        extra_data=to_bytes(response_json["extraData"]),
        gas_limit=hex_to_int(response_json["gasLimit"]),
        gas_used=hex_to_int(response_json["gasUsed"]),
        nonce=to_bytes(response_json["nonce"]),
        parent_hash=to_bytes(response_json["parentHash"], pad=32),
        size=hex_to_int(response_json["size"]),
        state_root=to_bytes(response_json["stateRoot"], pad=32),
        total_difficulty=hex_to_int(response_json["totalDifficulty"]),
    )

    return parsed_block, output_transactions


def parse_get_logs_response(response_json: list[dict[str, Any]]) -> list[Event]:
    return [
        Event(
            block_number=hex_to_int(log["blockNumber"]),
            transaction_index=hex_to_int(log["transactionIndex"]),
            event_index=hex_to_int(log["logIndex"]),
            contract_address=to_bytes(log["address"], pad=20),
            data=to_bytes(log["data"]),
            topics=[to_bytes(topic) for topic in log["topics"]],
            event_name=None,
            decoded_params=None,
        )
        for log in response_json
        if not log["removed"]
    ]
