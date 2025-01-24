import logging

from aiohttp import ClientSession

from nethermind.idealis.parse.starknet.abi import (
    is_class_account,
    is_class_erc20_token,
    is_class_erc721_token,
    is_class_proxy,
)
from nethermind.idealis.rpc.starknet.core import get_class_abis
from nethermind.idealis.types.starknet.contracts import (
    ClassDeclaration,
    ContractDeployment,
)
from nethermind.idealis.types.starknet.core import Transaction
from nethermind.idealis.types.starknet.enums import StarknetTxType
from nethermind.starknet_abi.dispatch import DecodingDispatcher, StarknetAbi
from nethermind.starknet_abi.exceptions import InvalidCalldataError, TypeDecodeError
from nethermind.starknet_abi.utils import starknet_keccak

CONSTRUCTOR_SIGNATURE = starknet_keccak(b"constructor")

root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("rpc").getChild("starknet")


async def get_class_declarations(
    declare_transactions: list[Transaction],
    deploy_transactions: list[Transaction],
    json_rpc: str,
    client_session: ClientSession,
    known_classes: set[bytes] | None = None,
) -> list[ClassDeclaration]:
    """
    Parse Transactions into ClassDeclaration details.

    Deploy transactions are passed since deploy transactions were able to declare classes.  This was removed in
    later versions, and deploy_account transactions cannot do this, and all classes are defined using declare
    transactions

    This unfortunately has a synchronous constraint within the block range.  It has to order transactions within
    each block  to track which deploy is the first tx to show up with a class hash.
    This can be paralellized across blocks however, ie

        asyncio.gather(get_class_declarations(...) for from_blk, to_blk in ((0, 100), (100, 200)))

    :param declare_transactions: Declare transactions
    :param deploy_transactions: v0 Deploy transactions that are able to declare classes
    :param json_rpc: JSON RPC endpoint to query for classes @ block number
    :param client_session: Aiohttp Client Session for sending RPC requests
    :param known_classes: Cache of classes that we know are already deployed, and don't need to query chain to check
    """

    class_declarations = []

    if known_classes is None:
        known_classes = set()

    ordered_txns = sorted(
        deploy_transactions + declare_transactions,
        key=lambda t: (t.block_number, t.transaction_index),
    )

    for tx in ordered_txns:
        if tx.class_hash is None:
            logger.error(f"Cannot Parse Transaction into ClassDeclaration: {tx}")
            continue

        # If deploy transaction, and we know class hash already exists, can skip
        # If declare transaction and class already exists, skip
        if tx.class_hash in known_classes:
            continue

        if tx.type == StarknetTxType.deploy:
            prev_class = await get_class_abis(
                class_hashes=[tx.class_hash],
                rpc_url=json_rpc,
                aiohttp_session=client_session,
                block_number=tx.block_number - 1,
            )
            class_exists_before = False if prev_class[0] is None else True
        else:
            class_exists_before = False

        known_classes.add(tx.class_hash)
        # If the class is known before or not, we still know it now and dont need to re-query the RPC

        if class_exists_before:  # Skip when Deploy txn didnt create class
            continue

        get_classes_response = await get_class_abis(
            class_hashes=[tx.class_hash], rpc_url=json_rpc, aiohttp_session=client_session, block_number=tx.block_number
        )

        if get_classes_response[0] is None:
            class_declarations.append(
                ClassDeclaration(
                    class_hash=tx.class_hash,
                    declaration_block=tx.block_number,
                    declaration_timestamp=tx.timestamp,
                    declare_transaction_hash=tx.transaction_hash,
                    proxy_kind=None,
                    is_account=None,
                    is_erc20=None,
                    is_erc721=None,
                )
            )

        else:
            declare_class_abi = StarknetAbi.from_json(
                abi_json=get_classes_response[0],
                class_hash=tx.class_hash,
                abi_name="",
            )

            class_declarations.append(
                ClassDeclaration(
                    class_hash=tx.class_hash,
                    declaration_block=tx.block_number,
                    declaration_timestamp=tx.timestamp,
                    declare_transaction_hash=tx.transaction_hash,
                    proxy_kind=is_class_proxy(declare_class_abi),
                    is_account=is_class_account(declare_class_abi),
                    is_erc20=is_class_erc20_token(declare_class_abi),
                    is_erc721=is_class_erc721_token(declare_class_abi),
                )
            )

    return class_declarations


def get_contract_deployments(
    deploy_account_transactions: list[Transaction],
    deploy_transactions: list[Transaction],
    decoding_dispatcher: DecodingDispatcher,
) -> list[ContractDeployment]:
    """
    Parse Transactions into ContractDeployment dataclasses.  Handles all versions of starknet transactions.

    In early starknet, deploy tx was used, and is handled.  deploy_account transactions are also handled and
    parsed into shared schema
    """

    contract_deployments = []

    for transaction in deploy_account_transactions + deploy_transactions:
        if transaction.contract_address is None or transaction.class_hash is None:
            logger.error(f"Cannot Parse transaction response into ContractDeployment: {transaction}")
            continue

        try:
            decoded = decoding_dispatcher.decode_function(
                calldata=[int.from_bytes(b) for b in transaction.calldata],
                result=[],
                function_selector=CONSTRUCTOR_SIGNATURE,
                class_hash=transaction.class_hash,
            )
        except (InvalidCalldataError, KeyError, TypeDecodeError) as e:
            logger.error(
                f"Decode Error while Parsing Contract Deployment for Transaction "
                f"0x{transaction.transaction_hash.hex()}: {e}"
            )
            decoded = None

        contract_deployments.append(
            ContractDeployment(
                contract_address=transaction.contract_address,
                initial_class_hash=transaction.class_hash,
                deploy_transaction_hash=transaction.transaction_hash,
                deploy_block=transaction.block_number,
                deploy_timestamp=transaction.timestamp,
                constructor_args=decoded.inputs if decoded else None,
            )
        )

    return contract_deployments
