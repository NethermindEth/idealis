import logging
from bisect import bisect_right

import requests
from aiohttp import ClientSession
from starknet_abi.abi_types import StarknetCoreType
from starknet_abi.dispatch import DecodingDispatcher
from starknet_abi.utils import starknet_keccak

from nethermind.idealis.rpc.starknet.core import (
    _starknet_block_id,
    sync_get_current_block,
)
from nethermind.idealis.types.starknet.contracts import ContractImplementation
from nethermind.idealis.utils import to_bytes, to_hex

GET_CAMEL_SELECTOR = starknet_keccak(b"getImplementation")
GET_SNAKE_SELECTOR = starknet_keccak(b"get_implementation")
GET_HASH_CAMEL_SELECTOR = starknet_keccak(b"getImplementationHash")
GET_HASH_SNAKE_SELECTOR = starknet_keccak(b"get_implementation_hash")
IMPL_SNAKE_SELECTOR = starknet_keccak(b"implementation")

root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("starknet").getChild("rpc").getChild("contracts")


def is_contract(felt: bytes, rpc_url: str) -> bool:
    """
    Check if a given felt is a contract address on Starknet

    :param felt:  Felt to check
    :param rpc_url:  URL for Starknet RPC
    """
    response = requests.post(
        rpc_url,
        json={
            "jsonrpc": "2.0",
            "method": "starknet_getClassHashAt",
            "params": {
                "block_id": "latest",
                "contract_address": to_hex(felt, pad=32),
            },
            "id": 1,
        },
        timeout=20,
    )
    return "error" not in response.json()


def is_class(felt: bytes, rpc_url: str) -> bool:
    """
    Check if a given felt is a class hash on Starknet

    :param felt:  Felt to check
    :param rpc_url:  URL for Starknet RPC
    """
    response = requests.post(
        rpc_url,
        json={
            "jsonrpc": "2.0",
            "method": "starknet_getClass",
            "params": {
                "block_id": "latest",
                "class_hash": to_hex(felt, pad=32),
            },
            "id": 1,
        },
        timeout=40,
    )
    return "error" not in response.json()


def _is_proxy(decoder: DecodingDispatcher, target_impl: bytes) -> tuple[bool, bytes | None]:
    """

    :param decoder:
    :param target_impl:
    :return:  [is-proxy, proxy-method-selector]
    """

    target_impl_abi = decoder.get_class(target_impl)

    if target_impl_abi is None:
        logger.error(f"ABI for class 0x{target_impl.hex()} not in ABI Decoder")
        return False, None

    if GET_SNAKE_SELECTOR[-8:] in target_impl_abi.function_ids:
        proxy_method_selector = GET_SNAKE_SELECTOR

    elif GET_HASH_CAMEL_SELECTOR[-8:] in target_impl_abi.function_ids:
        proxy_method_selector = GET_HASH_CAMEL_SELECTOR

    elif GET_CAMEL_SELECTOR[-8:] in target_impl_abi.function_ids:
        proxy_method_selector = GET_CAMEL_SELECTOR

    elif GET_HASH_SNAKE_SELECTOR[-8:] in target_impl_abi.function_ids:
        proxy_method_selector = GET_HASH_SNAKE_SELECTOR

    elif IMPL_SNAKE_SELECTOR[-8:] in target_impl_abi.function_ids:
        proxy_method_selector = IMPL_SNAKE_SELECTOR

    else:
        proxy_method_selector = None

    if proxy_method_selector is None:
        return False, None

    function_type_id = target_impl_abi.function_ids[proxy_method_selector[-8:]].decoder_reference
    _, output_types = decoder.function_types[function_type_id]

    if len(output_types) != 1 or output_types[0] not in [  # implementation function returns single value
        StarknetCoreType.Felt,
        StarknetCoreType.ContractAddress,
        StarknetCoreType.ClassHash,
    ]:
        raise ValueError(
            f"Class 0x{target_impl.hex()} implements a proxy method 0x{proxy_method_selector.hex()} "
            f"which returns an invalid ABI Type: [{','.join(t.id_str() for t in output_types)}] -- "
            f"Proxy functions must return [Felt] or [ContractAddress]"
        )

    return True, proxy_method_selector


async def get_implemented_class(
    contract: bytes,
    block_number: int,
    aiohttp_session: ClientSession,
    rpc_url: str,
) -> bytes | None:
    async with aiohttp_session.post(
        rpc_url,
        json={
            "jsonrpc": "2.0",
            "method": "starknet_getClassHashAt",
            "params": {
                "contract_address": to_hex(contract, pad=32),
                "block_id": _starknet_block_id(block_number),
            },
            "id": 1,
        },
    ) as response:
        response_json = await response.json()  # Async read response bytes
        response.release()  # Release the connection back to the pool, keeping TCP conn alive

        if "error" in response_json:
            return None
        return to_bytes(response_json["result"], pad=True)


async def get_proxied_felt(
    contract: bytes,
    block_number: int,
    aiohttp_session: ClientSession,
    rpc_url: str,
    proxy_method: bytes,
) -> bytes | None:
    """
    Get the felt value returned by a proxy method of a contract at a given block number.  This returned value is
    typically a class hash on modern contracts, but can be another contract, or a random felt value that does not
    exist on chain...

    :param contract: Contract Address Bytes
    :param block_number: Block number to call the proxy method at
    :param aiohttp_session: Async HTTP Client Session
    :param rpc_url: URL of Starknet Node or API Service
    :param proxy_method:
        selector of the proxy method to call.  Computed with
        starknet_abi.utils.starknet_keccak(b'get_implementation')

    :return: Felt value returned by the proxy method, or None if the method call fails
    """

    async with aiohttp_session.post(
        rpc_url,
        json={
            "jsonrpc": "2.0",
            "method": "starknet_call",
            "params": {
                "request": {
                    "contract_address": to_hex(contract, pad=32),
                    "entry_point_selector": to_hex(proxy_method, pad=32),
                    "calldata": [],
                },
                "block_id": _starknet_block_id(block_number),
            },
            "id": 1,
        },
    ) as response:
        response_json = await response.json()  # Async read response bytes
        response.release()  # Release the connection back to the pool, keeping TCP conn alive

        if "error" in response_json:
            return None
        return to_bytes(response_json["result"][0])


async def get_contract_upgrade(
    aiohttp_session: ClientSession,
    rpc_url: str,
    contract_address: bytes,
    old_class: bytes | None = None,
    from_block: int = 0,
    to_block: int | None = None,
) -> tuple[bytes | None, int]:
    """
    Get the updated implementation class for a contract address, and the block_number of the deploy/upgrade
    """

    low, high = from_block, to_block if to_block else sync_get_current_block(rpc_url)

    while low < high:
        mid = low + (high - low) // 2
        impl_class = await get_implemented_class(contract_address, mid, aiohttp_session, rpc_url)
        if impl_class == old_class:
            low = mid + 1
        else:
            high = mid

    return (
        await get_implemented_class(contract_address, low, aiohttp_session, rpc_url),
        low,
    )


async def get_proxy_upgrade(
    aiohttp_session: ClientSession,
    rpc_url: str,
    contract_address: bytes,
    old_implementation: bytes,
    proxy_method: bytes,
    from_block: int,
    to_block: int,
):
    """
    Performs a bisection to find a block such that
    impl_at_block(b) != old_implementation && impl_at_block(b - 1) == old_implementation
    """
    low, high = from_block, to_block

    while low < high:
        mid = low + (high - low) // 2
        proxy_impl = await get_proxied_felt(contract_address, mid, aiohttp_session, rpc_url, proxy_method)
        if proxy_impl == old_implementation:
            low = mid + 1
        else:
            high = mid

    return (
        await get_proxied_felt(contract_address, low, aiohttp_session, rpc_url, proxy_method),
        low,
    )


async def get_class_history(
    aiohttp_session: ClientSession,
    rpc_url: str,
    contract_address: bytes,
    to_block: int | None,
    from_block: int = 0,
    old_class: bytes | None = None,
    target_implementation: bytes | None = None,
) -> dict[int, str] | None:
    """

    Get the contract history of implementation classes and their deploy/upgrade blocks

    :param aiohttp_session:  ClientSession for Async requests
    :param rpc_url: URL for RPC server
    :param contract_address:  Contract address to query
    :param to_block:
    :param from_block:
    :param old_class:
    :param target_implementation:
    :return:
    """
    if to_block is None:
        to_block = sync_get_current_block(rpc_url)

    implementation_history: dict[int, str] = {}

    if target_implementation is None:
        target_implementation = await get_implemented_class(
            contract=contract_address,
            block_number=to_block,
            aiohttp_session=aiohttp_session,
            rpc_url=rpc_url,
        )

    if target_implementation is None:
        logger.warning(f"Contract 0x{contract_address.hex()} not found at block {to_block}")
        return None

    while old_class != target_implementation:
        old_class, from_block = await get_contract_upgrade(
            aiohttp_session=aiohttp_session,
            rpc_url=rpc_url,
            contract_address=contract_address,
            old_class=old_class,
            from_block=from_block,
            to_block=to_block,
        )
        implementation_history.update({from_block: to_hex(old_class, pad=32)})

    return implementation_history


async def get_proxy_impl_history(
    aiohttp_session: ClientSession,
    rpc_url: str,
    contract_address: bytes,
    proxy_method: bytes,
    from_block: int,
    to_block: int,
) -> dict[str, str]:
    """
    Get the contract history of implementation classes and their deploy/upgrade blocks
    """

    initial_impl = await get_proxied_felt(
        contract=contract_address,
        block_number=from_block,
        aiohttp_session=aiohttp_session,
        rpc_url=rpc_url,
        proxy_method=proxy_method,
    )

    if initial_impl is None:
        logger.error(
            f"Initial Proxy Implementation for contract 0x{contract_address.hex()} not found at block {from_block}"
        )
        return {}

    target_impl = await get_proxied_felt(
        contract=contract_address,
        block_number=to_block,
        aiohttp_session=aiohttp_session,
        rpc_url=rpc_url,
        proxy_method=proxy_method,
    )

    if target_impl is None:
        logger.error(
            f"Target Proxy Implementation for contract 0x{contract_address.hex()} not found at block {to_block}"
        )
        return {}

    proxy_history = {str(from_block): to_hex(initial_impl, pad=32)}

    while initial_impl != target_impl:
        initial_impl, from_block = await get_proxy_upgrade(
            aiohttp_session=aiohttp_session,
            rpc_url=rpc_url,
            contract_address=contract_address,
            old_implementation=initial_impl,
            proxy_method=proxy_method,
            from_block=from_block,
            to_block=to_block,
        )

        proxy_history.update({str(from_block): to_hex(initial_impl, pad=32)})

    return proxy_history


async def generate_contract_implementation(
    class_decoder: DecodingDispatcher,
    rpc_url: str,
    aiohttp_session: ClientSession,
    contract_address: bytes,
    to_block: int | None,
) -> ContractImplementation | None:
    if to_block is None:
        to_block = sync_get_current_block(rpc_url)

    class_history = await get_class_history(aiohttp_session, rpc_url, contract_address, to_block)
    if class_history is None:
        return None

    class_history_items = list(class_history.items())

    contract_impl_history = {}

    for item_idx, (block, class_hash) in enumerate(class_history_items):
        # runs once for each unique impl class of the contract

        # Check if the class has a proxy method, and the selector of this method
        is_proxy, proxy_method = _is_proxy(class_decoder, to_bytes(class_hash))

        if not is_proxy:
            contract_impl_history.update({str(block): class_hash})
            continue

        # Proxy Handling Logic
        if len(class_history_items) - 1 == item_idx:
            proxy_to_block = to_block
        else:
            # 1 block before the next root class is deployed
            proxy_to_block = class_history_items[item_idx + 1][0] - 1

        proxy_impl_history = await get_proxy_impl_history(
            aiohttp_session=aiohttp_session,
            rpc_url=rpc_url,
            contract_address=contract_address,
            proxy_method=proxy_method,
            from_block=block,
            to_block=proxy_to_block,
        )

        contract_impl_history.update({str(block): {"proxy_class": class_hash, **proxy_impl_history}})

    return ContractImplementation(
        contract_address=contract_address,
        update_block=to_block,
        history=contract_impl_history,
    )


async def update_contract_implementation(
    class_decoder: DecodingDispatcher,
    aiohttp_session: ClientSession,
    rpc_url: str,
    contract_history: ContractImplementation,
    to_block: int,
) -> ContractImplementation:
    """

    Get the contract history of implementation classes and their deploy/upgrade blocks

    :param class_decoder: ABI Decoder for Starknet Classes
    :param aiohttp_session:  ClientSession for Async requests
    :param rpc_url: URL for RPC server
    :param contract_history:  Contract address to query
    :param to_block:
    :return:
    """

    target_implementation = await get_implemented_class(
        contract=contract_history.contract_address,
        block_number=to_block,
        aiohttp_session=aiohttp_session,
        rpc_url=rpc_url,
    )

    latest_impl_key = max(int(k) for k in contract_history.history.keys())
    latest_impl = contract_history.history[str(latest_impl_key)]

    latest_root_impl = (
        to_bytes(latest_impl, pad=True)
        if isinstance(latest_impl, str)
        else to_bytes(latest_impl["proxy_class"], pad=True)
    )

    if latest_root_impl != target_implementation:
        # The root contract has upgraded its class
        class_history = await get_class_history(
            aiohttp_session=aiohttp_session,
            rpc_url=rpc_url,
            contract_address=contract_history.contract_address,
            to_block=to_block,
            from_block=latest_impl_key,
            old_class=latest_root_impl,
        )

        # Update Root Class History
        contract_history.history.update({str(k): v for k, v in class_history.items()})

    latest_root_proxy, latest_root_proxy_method = _is_proxy(class_decoder, latest_root_impl)

    if latest_root_impl == target_implementation and not latest_root_proxy:
        # Implementation has not changed, and current root class is not proxy
        contract_history.update_block = to_block
        return contract_history

    sorted_keys = sorted(int(k) for k in contract_history.history.keys())

    for impl_idx, root_impl_block in enumerate(sorted_keys):
        if root_impl_block < latest_impl_key:
            continue  # Earlier class, proxies already handled

        root_impl = contract_history.history[str(root_impl_block)]

        root_impl_class = (
            to_bytes(root_impl, pad=True)
            if isinstance(root_impl, str)
            else to_bytes(root_impl["proxy_class"], pad=True)
        )

        is_proxy, proxy_method = _is_proxy(class_decoder, root_impl_class)

        if proxy_method is None:  # If proxy method is none, is_proxy is false
            continue  # No need to update proxy impls

        if isinstance(root_impl, str):  # No proxy history yet
            proxy_search_from = root_impl_block
            contract_history.history[str(root_impl_block)].update({"proxy_class": root_impl})
        else:
            proxy_search_from = max(int(k) for k in root_impl.keys() if k != "proxy_class")

        try:
            proxy_to_block = sorted_keys[impl_idx + 1] - 1
        except IndexError:
            proxy_to_block = to_block

        proxy_history = await get_proxy_impl_history(
            aiohttp_session=aiohttp_session,
            rpc_url=rpc_url,
            contract_address=contract_history.contract_address,
            proxy_method=latest_root_proxy_method,
            from_block=proxy_search_from,
            to_block=proxy_to_block,
        )

        contract_history.history[str(latest_impl_key)].update(proxy_history)
        # If proxy has not been updated, proxy history will check inital and latest impl..

    contract_history.update_block = to_block
    return contract_history


def get_implementation_proxy_felts(contract_implementation: ContractImplementation) -> list[bytes]:
    """
    Get a list of all proxy contracts used in the contract implementation history.  If there are no proxy classes,
    an empty list is returned.

    This function is useful for generating a list of all contracts that need to be loaded in order to get the impl
    class for a given contract address at a given block number even if proxies are in place.

    :param contract_implementation:
    :return:
    """
    proxy_felts = {  # remove duplicates w/ set
        to_bytes(proxy)
        for root_class in contract_implementation.history.values()
        if isinstance(root_class, dict)
        for key, proxy in root_class.items()
        if key != "proxy_class"
    }
    return list(proxy_felts)


def get_decode_class(
    contract_address: bytes,
    contract_implementations: dict[bytes, ContractImplementation],
    block_number: int,
) -> bytes:
    contract_impl = contract_implementations.get(contract_address)

    if contract_impl is None:
        raise ValueError(f"Contract {to_hex(contract_address, pad=32)} not present in implementation mapping")

    if contract_impl.update_block < block_number:
        raise ValueError(
            f"Implementation for contract {to_hex(contract_address, pad=32)} last updated at "
            f"block {contract_impl.update_block}... Cannot get decode class at block {block_number}"
        )

    block_history = sorted(int(b) for b in contract_impl.history.keys())
    if block_number < block_history[0]:
        raise ValueError(
            f"Contract 0x{contract_address.hex()} has no implementation before block {block_history[0]}. "
            f"Cannot get decode class at block {block_number}"
        )

    impl_block = (
        block_history[0] if len(block_history) == 1 else block_history[bisect_right(block_history, block_number) - 1]
    )

    impl_class = contract_impl.history[str(impl_block)]

    if isinstance(impl_class, str):
        return to_bytes(impl_class)

    # Handle proxy implementations
    proxy_block_history = sorted(int(b) for b in impl_class.keys() if b != "proxy_class")

    impl_block = (
        proxy_block_history[0]
        if len(proxy_block_history) == 1
        else proxy_block_history[bisect_right(proxy_block_history, block_number) - 1]
    )

    proxied_contract = to_bytes(impl_class[str(impl_block)])

    if proxied_contract not in contract_implementations:
        raise ValueError(f"Proxy contract 0x{proxied_contract.hex()} not present in implementation mapping")

    return get_decode_class(proxied_contract, contract_implementations, block_number)
