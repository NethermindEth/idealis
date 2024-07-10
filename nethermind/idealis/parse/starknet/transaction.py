from dataclasses import dataclass
from typing import Any

from nethermind.idealis.types.starknet.core import (
    Event,
    Transaction,
    TransactionResponse,
)
from nethermind.idealis.types.starknet.enums import (
    StarknetFeeUnit,
    StarknetTxType,
    TransactionStatus,
)
from nethermind.idealis.utils import hex_to_int, to_bytes
from nethermind.starknet_abi.utils import starknet_keccak


def parse_transaction(
    tx_data: dict[str, Any],
    block_number: int,
    tx_index: int,
    block_timestamp: int,
):
    tx_type = StarknetTxType(tx_data["type"])
    tx_version = hex_to_int(tx_data["version"])

    class_hash = to_bytes(tx_data["class_hash"], pad=32) if "class_hash" in tx_data else None
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

    return TransactionResponse(
        transaction_hash=to_bytes(tx_data["transaction_hash"], pad=32),
        block_number=block_number,
        transaction_index=tx_index,
        type=tx_type,
        nonce=hex_to_int(tx_data.get("nonce", "0x0")),
        timestamp=block_timestamp,
        version=tx_version,
        signature=[to_bytes(sig, pad=32) for sig in tx_data.get("signature", [])],
        # Optional Tx Fields
        contract_address=contract_address,
        entry_point_selector=selector,
        calldata=[to_bytes(data) for data in tx_data.get("calldata", [])],
        constructor_calldata=[to_bytes(data) for data in tx_data.get("constructor_calldata", [])],
        class_hash=class_hash,
        compiled_class_hash=compiled_class_hash,
        contract_address_salt=contract_address_salt,
        contract_class=contract_class,
        # V3 Transaction Fields
        account_deployment_data=[to_bytes(account_data) for account_data in tx_data.get("account_deployment_data", [])],
        tip=tx_data.get("tip", 0),
        resource_bounds=tx_data.get("resource_bounds", {}),
        paymaster_data=[to_bytes(paymaster_data) for paymaster_data in tx_data.get("paymaster_data", [])],
        fee_data_availability_mode=0,  # Not in Use -- Convert to Enum Eventually
        nonce_data_availability_mode=0,  # Not in Use -- Convert to Enum Eventually
        # Legacy Transaction Fields
        max_fee=hex_to_int(tx_data.get("max_fee", "0x0")),
        fee_unit=StarknetFeeUnit.wei,
        actual_fee=0,
        status=TransactionStatus.not_received,
        execution_resources={},
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
    tx_response: dict[str, Any], block_number: int, tx_index: int, block_timestamp: int
) -> tuple[TransactionResponse, list[Event]]:
    tx_data = tx_response["transaction"]
    tx_receipt = tx_response["receipt"]

    parsed_transaction = parse_transaction(tx_data, block_number, tx_index, block_timestamp)

    actual_fee = tx_receipt.get("actual_fee", {})

    parsed_transaction.fee_unit = StarknetFeeUnit(actual_fee.get("unit", "WEI"))
    parsed_transaction.actual_fee = hex_to_int(actual_fee.get("amount", "0x0"))
    parsed_transaction.status = tx_status_from_receipt(
        tx_receipt.get("execution_status"), tx_receipt.get("finality_status")
    )
    parsed_transaction.execution_resources = tx_receipt.get("execution_resources", {})

    events = [
        Event(
            block_number=block_number,
            tx_index=tx_index,
            event_index=event_index,
            class_hash=b"",  # Event class hashes are unknown to tx receipts.  Use contract mapping
            contract_address=to_bytes(event_dict["from_address"], pad=32),
            keys=[to_bytes(k, pad=32) for k in event_dict["keys"]],
            data=[to_bytes(d) for d in event_dict["data"]],
        )
        for event_index, event_dict in enumerate(tx_receipt.get("events", []))
    ]

    return parsed_transaction, events


@dataclass
class FilteredTransactions:
    invoke_transactions: list[TransactionResponse]
    declare_transactions: list[TransactionResponse]
    deploy_transactions: list[TransactionResponse]
    deploy_account_transactions: list[TransactionResponse]
    l1_handler_transactions: list[TransactionResponse]


# TODO: Fix this dumpster fire
def filter_transactions_by_type(
    transactions: list[TransactionResponse],
) -> FilteredTransactions:
    invoke = []
    declare = []
    deploy = []
    deploy_account = []
    l1_handler = []

    for tx in transactions:
        match tx.type:
            case StarknetTxType.invoke:
                invoke.append(tx)
            case StarknetTxType.declare:
                declare.append(tx)
            case StarknetTxType.deploy:
                deploy.append(tx)
            case StarknetTxType.deploy_account:
                deploy_account.append(tx)
            case StarknetTxType.l1_handler:
                l1_handler.append(tx)

    return FilteredTransactions(
        invoke_transactions=invoke,
        declare_transactions=declare,
        deploy_transactions=deploy,
        deploy_account_transactions=deploy_account,
        l1_handler_transactions=l1_handler,
    )


def parse_transaction_responses(
    transactions: list[TransactionResponse],
) -> list[Transaction]:
    """
    Parses transaction_response into a Transaction, adding user operations and resource consumption from traces,
    and returns a list of DecodedTransactions.

    :param transactions:
    :return:
    """

    decoded_txns = []

    for tx in transactions:
        decoded_txns.append(
            Transaction(
                transaction_hash=tx.transaction_hash,
                block_number=tx.block_number,
                transaction_index=tx.transaction_index,
                type=tx.type,
                nonce=tx.nonce,
                signature=tx.signature,
                version=tx.version,
                timestamp=tx.timestamp,
                status=tx.status,
                max_fee=tx.max_fee,
                actual_fee=tx.actual_fee,
                fee_unit=tx.fee_unit,
                execution_resources=tx.execution_resources,
                gas_used=0,
                tip=0,
                resource_bounds={},
                paymaster_data=[],
                account_deployment_data=[],
                contract_address=tx.contract_address,
                selector=tx.entry_point_selector,
                calldata=(tx.calldata if tx.type == StarknetTxType.invoke else tx.constructor_calldata),
                class_hash=tx.class_hash,
                user_operations=[],
                revert_error=None,
            )
        )

    return decoded_txns
