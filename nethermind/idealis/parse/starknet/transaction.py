from dataclasses import dataclass
from typing import Any

from nethermind.idealis.types.starknet.core import Event, Transaction
from nethermind.idealis.types.starknet.enums import (
    StarknetFeeUnit,
    StarknetTxType,
    TransactionStatus,
)
from nethermind.idealis.types.starknet.rollup import IncomingMessage, OutgoingMessage
from nethermind.idealis.utils import hex_to_int, to_bytes
from nethermind.starknet_abi.utils import starknet_keccak


def parse_transaction(
    tx_data: dict[str, Any],
    block_number: int,
    transaction_index: int,
    block_timestamp: int,
) -> Transaction:
    tx_type = StarknetTxType(tx_data["type"])
    tx_version = hex_to_int(tx_data["version"])

    class_hash = to_bytes(tx_data["class_hash"], pad=32) if "class_hash" in tx_data else None

    # compiled_class_hash=compiled_class_hash,
    # contract_address_salt=contract_address_salt,
    # contract_class=contract_class,

    compiled_class_hash = to_bytes(tx_data["compiled_class_hash"], pad=32) if "compiled_class_hash" in tx_data else None
    contract_address_salt = (
        to_bytes(tx_data["contract_address_salt"], pad=32) if "contract_address_salt" in tx_data else None
    )
    contract_class = to_bytes(tx_data["contract_class"], pad=32) if "contract_class" in tx_data else None

    if "contract_address" in tx_data:
        contract_address = to_bytes(tx_data["contract_address"], pad=32)
    elif "sender_address" in tx_data:
        contract_address = to_bytes(tx_data["sender_address"], pad=32)
    else:
        contract_address = None

    selector = (
        to_bytes(tx_data["entry_point_selector"], pad=32)
        if "entry_point_selector" in tx_data
        else starknet_keccak(b"__execute__")
    )

    if "calldata" in tx_data:
        calldata = [to_bytes(data) for data in tx_data.get("calldata", [])]
    elif "constructor_calldata" in tx_data:
        calldata = [to_bytes(data) for data in tx_data.get("constructor_calldata", [])]
    else:
        calldata = []

    return Transaction(
        transaction_hash=to_bytes(tx_data["transaction_hash"], pad=32),
        block_number=block_number,
        transaction_index=transaction_index,
        type=tx_type,
        nonce=hex_to_int(tx_data.get("nonce", "0x0")),
        timestamp=block_timestamp,
        version=tx_version,
        signature=[to_bytes(sig, pad=32) for sig in tx_data.get("signature", [])],
        # Optional Tx Fields
        contract_address=contract_address,
        selector=selector,
        calldata=calldata,
        class_hash=class_hash,
        # V3 Transaction Fields
        account_deployment_data=[to_bytes(account_data) for account_data in tx_data.get("account_deployment_data", [])],
        tip=tx_data.get("tip", 0),
        resource_bounds=tx_data.get("resource_bounds", {}),
        paymaster_data=[to_bytes(paymaster_data) for paymaster_data in tx_data.get("paymaster_data", [])],
        # Receipt Transaction Fields
        max_fee=hex_to_int(tx_data.get("max_fee", "0x0")),
        fee_unit=StarknetFeeUnit.wei,
        actual_fee=0,
        status=TransactionStatus.not_received,
        execution_resources={},
        message_hash=None,
        gas_used=None,
        user_operations=[],
        revert_error=None,
    )


def tx_status_from_receipt(execution_status: str | None, finality_status: str | None) -> TransactionStatus:
    match execution_status, finality_status:
        case None, "NOT_RECEIVED":
            return TransactionStatus.not_received
        case None, "RECEIVED":
            return TransactionStatus.received
        case "REJECTED", "RECEIVED":
            return TransactionStatus.rejected
        case "REVERTED", "RECEIVED":
            return TransactionStatus.reverted
        case "SUCCEEDED", "ACCEPTED_ON_L2":
            return TransactionStatus.accepted_on_l2
        case "SUCCEEDED", "ACCEPTED_ON_L1":
            return TransactionStatus.accepted_on_l1

    return TransactionStatus.not_received


def parse_transaction_with_receipt(
    tx_response: dict[str, Any],
    block_number: int,
    transaction_index: int,
    block_timestamp: int,
) -> tuple[Transaction, list[Event], list[OutgoingMessage],]:
    tx_data = tx_response["transaction"]
    tx_receipt = tx_response["receipt"]

    parsed_transaction = parse_transaction(tx_data, block_number, transaction_index, block_timestamp)

    actual_fee = tx_receipt.get("actual_fee", {})

    parsed_transaction.fee_unit = StarknetFeeUnit(actual_fee.get("unit", "WEI"))
    parsed_transaction.actual_fee = hex_to_int(actual_fee.get("amount", "0x0"))
    parsed_transaction.status = tx_status_from_receipt(
        tx_receipt.get("execution_status"), tx_receipt.get("finality_status")
    )
    parsed_transaction.execution_resources = tx_receipt.get("execution_resources", {})

    msg_hash = tx_receipt.get("message_hash")
    parsed_transaction.message_hash = to_bytes(msg_hash, pad=32) if msg_hash else None

    if parsed_transaction.contract_address is None:
        receipt_addr = tx_receipt.get("contract_address")
        parsed_transaction.contract_address = to_bytes(receipt_addr, pad=32) if receipt_addr else None

    events = [
        Event(
            block_number=block_number,
            transaction_index=transaction_index,
            event_index=event_index,
            class_hash=b"",  # Event class hashes are unknown to tx receipts.  Use contract mapping
            contract_address=to_bytes(event_dict["from_address"], pad=32),
            keys=[to_bytes(k, pad=32) for k in event_dict["keys"]],
            data=[to_bytes(d) for d in event_dict["data"]],
        )
        for event_index, event_dict in enumerate(tx_receipt.get("events", []))
    ]

    messages = [
        OutgoingMessage(
            starknet_block_number=parsed_transaction.block_number,
            starknet_transaction_index=parsed_transaction.transaction_index,
            starknet_transaction_hash=parsed_transaction.transaction_hash,
            message_index=message_index,
            from_starknet_address=to_bytes(message_data["from_address"], pad=32),
            to_ethereum_address=to_bytes(message_data["to_address"], pad=20),
            payload=[to_bytes(p) for p in message_data.get("payload", [])],
        )
        for message_index, message_data in enumerate(tx_receipt.get("messages_sent", []))
    ]

    return parsed_transaction, events, messages


@dataclass
class FilteredTransactions:
    invoke_transactions: list[Transaction]
    declare_transactions: list[Transaction]
    deploy_transactions: list[Transaction]
    deploy_account_transactions: list[Transaction]
    l1_handler_transactions: list[Transaction]


# TODO: Fix this dumpster fire
def filter_transactions_by_type(
    transactions: list[Transaction],
) -> FilteredTransactions:
    return FilteredTransactions(
        invoke_transactions=[tx for tx in transactions if tx.type == StarknetTxType.invoke],
        declare_transactions=[tx for tx in transactions if tx.type == StarknetTxType.declare],
        deploy_transactions=[tx for tx in transactions if tx.type == StarknetTxType.deploy],
        deploy_account_transactions=[tx for tx in transactions if tx.type == StarknetTxType.deploy_account],
        l1_handler_transactions=[tx for tx in transactions if tx.type == StarknetTxType.l1_handler],
    )


def parse_incoming_messages(l1_handler_transactions: list[Transaction]) -> list[IncomingMessage]:
    incoming_messages = []

    for tx in l1_handler_transactions:
        if tx.type != StarknetTxType.l1_handler:
            continue

        assert tx.message_hash is not None, "L1 Handler txns must have message_hash in receipt"

        incoming_messages.append(
            IncomingMessage(
                starknet_block_number=tx.block_number,
                starknet_transaction_index=tx.transaction_index,
                starknet_transaction_hash=tx.transaction_hash,
                message_hash=tx.message_hash,
                to_starknet_address=tx.contract_address,
                calldata=tx.calldata,
                selector=tx.selector,
            )
        )

    return incoming_messages
