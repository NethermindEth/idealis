import logging
from typing import Sequence

from nethermind.idealis.types.starknet.enums import ProxyKind
from nethermind.starknet_abi.abi_types import StarknetCoreType, StarknetType
from nethermind.starknet_abi.decoding_types import AbiEvent, AbiParameter
from nethermind.starknet_abi.dispatch import DecodingDispatcher, StarknetAbi, _id_hash
from nethermind.starknet_abi.utils import starknet_keccak

# ERC20 & ERC721 Functions -----------------------------------

ERC_NAME = ["name"]
ERC_SYMBOL = ["symbol"]
ERC_DECIMALS = ["decimals"]
ERC_BALANCE_OF = ["balanceOf", "balance_of"]
ERC_OWNER_OF = ["ownerOf", "owner_of"]
ERC_ALLOWANCE = ["allowance"]
ERC_TRANSFER = ["transfer"]
ERC_TRANSFER_FROM = ["transferFrom", "transfer_from"]
ERC_SAFE_TRANSFER_FROM = ["safeTransferFrom", "safe_transfer_from"]
ERC_APPROVE = ["approve"]
ERC_SET_APPROVAL_FOR_ALL = ["setApprovalForAll", "set_approval_for_all"]
ERC_GET_APPROVED = ["getApproved", "get_approved"]
ERC_IS_APPROVED_FOR_ALL = ["isApprovedForAll", "is_approved_for_all"]

# ERC20 & ERC721 Events ---------------------------------------

ERC_TRANSFER_EVENT = "Transfer"
ERC_APPROVAL_EVENT = "Approval"
ERC_APPROVAL_FOR_ALL_EVENT = "ApprovalForAll"

# Proxy Selectors & Events ------------------------------------

CONSTRUCTOR_SIGNATURE = starknet_keccak(b"constructor")
UPGRADED_EVENT = AbiEvent(
    name="Upgraded",
    parameters=["implementation"],
    data={"implementation": StarknetCoreType.Felt},
    keys={},
)
ADMIN_CHANGED_EVENT = AbiEvent(
    name="AdminChanged",
    parameters=["previousAdmin", "newAdmin"],
    data={"previousAdmin": StarknetCoreType.Felt, "newAdmin": StarknetCoreType.Felt},
    keys={},
)
UPGRADED_EVENT_SELECTOR = starknet_keccak(UPGRADED_EVENT.name.encode())
UPGRADED_FUNCTION_TYPE_ID = _id_hash(UPGRADED_EVENT.id_str())
ADMIN_CHANGED_SELECTOR = starknet_keccak(ADMIN_CHANGED_EVENT.name.encode())
ADMIN_CHANGED_EVENT_TYPE_ID = _id_hash(ADMIN_CHANGED_EVENT.id_str())


root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("parse").getChild("starknet").getChild("abi")


def is_class_account(class_abi: StarknetAbi) -> bool:
    return all(
        func in class_abi.functions
        for func in ["__validate__", "__execute__", "__validate_declare__", "__validate_deploy__"]
    )


def _check_proxy_function(function_name: str, output_types: Sequence[StarknetType], class_hash: bytes | None = None):
    """
    Verify that a proxy function returns a single value, and that value is a Felt, ClassHash or ContractAddress
    """
    if len(output_types) != 1 or output_types[0] not in [  # implementation function returns single value
        StarknetCoreType.Felt,
        StarknetCoreType.ContractAddress,
        StarknetCoreType.ClassHash,
    ]:
        class_id = f"0x{class_hash.hex()}" if class_hash else "Unknown"

        raise ValueError(
            f"Class {class_id} implements proxy method '{function_name}' "
            f"which returns an invalid ABI Type: [{','.join(t.id_str() for t in output_types)}] -- "
            f"Proxy functions must return [Felt] [ContractAddress] or [ClassHash]"
        )


def is_class_proxy(class_abi: StarknetAbi) -> ProxyKind | None:
    """
    Check if a class is a proxy.  If it implements a proxy standard, return it as ProxyKind.  If class is not a proxy,
    return None.
    """

    for proxy_func in ProxyKind.supported_functions():
        if proxy_func.function_name() in class_abi.functions:
            abi_function_info = class_abi.functions[proxy_func.function_name()]
            try:
                _check_proxy_function(proxy_func.function_name(), abi_function_info.outputs, class_abi.class_hash)
                return proxy_func
            except ValueError:  # Proxy func returns too much data or wrong types
                return None

    if (
        "Upgraded" in class_abi.events
        and "AdminChanged" in class_abi.events
        and class_abi.constructor
        and  # Constructor is not none
        # One of the arguments to constructor contains implementation
        "implementation" in [p.name.lower() for p in class_abi.constructor.inputs]
    ):
        return ProxyKind.oz_event_proxy

    return None


def is_dispatcher_class_proxy(decoder: DecodingDispatcher, class_hash: bytes) -> ProxyKind | None:
    """
    Checks a DecodingDispatcher if a class is a proxy and returns it as ProxyKind.
    # TODO: Refactor & Comment this evil shit
    """

    class_abi_data = decoder.get_class(class_hash)
    if class_abi_data is None:
        return None  # Class hash not loaded, or if pessimism enabled... invalid class

    for proxy_func in ProxyKind.supported_functions():
        if proxy_func.function_selector()[-8:] in class_abi_data.function_ids:
            abi_function_info = class_abi_data.function_ids[proxy_func.function_selector()[-8:]]
            _, output_types = decoder.function_types[abi_function_info.decoder_reference]
            try:
                _check_proxy_function(proxy_func.function_name(), output_types, class_hash)
                return proxy_func
            except ValueError:  # Proxy func returns too much data or wrong types
                return None

    if (
        UPGRADED_EVENT_SELECTOR[-8:] in class_abi_data.event_ids
        and ADMIN_CHANGED_SELECTOR[-8:] in class_abi_data.event_ids
        and CONSTRUCTOR_SIGNATURE[-8:] in class_abi_data.function_ids
    ):
        # One of the arguments to constructor contains implementation
        constructor_args = [
            param.name.lower()
            for param in decoder.function_types[
                class_abi_data.function_ids[CONSTRUCTOR_SIGNATURE[-8:]].decoder_reference
            ][0]
        ]
        if not any("implementation" in arg.lower() for arg in constructor_args):
            return None  # implementation isn't in constructor args

        return ProxyKind.oz_event_proxy

    return None


def is_class_erc20_token(class_abi: StarknetAbi) -> bool:
    has_erc20_functions = all(
        any(param in class_abi.functions for param in supported_params)
        for supported_params in (
            ERC_NAME,
            ERC_SYMBOL,
            ERC_DECIMALS,
            ERC_BALANCE_OF,
            ERC_ALLOWANCE,
            ERC_TRANSFER,
            ERC_TRANSFER_FROM,
            ERC_APPROVE,
        )
    )

    has_erc20_events = all(event in class_abi.events for event in (ERC_TRANSFER_EVENT, ERC_APPROVAL_EVENT))

    return has_erc20_functions and has_erc20_events


def is_class_erc721_token(class_abi: StarknetAbi) -> bool:
    has_erc721_functions = all(
        any(param in class_abi.functions for param in supported_params)
        for supported_params in (
            ERC_BALANCE_OF,
            ERC_OWNER_OF,
            ERC_SAFE_TRANSFER_FROM,
            ERC_TRANSFER_FROM,
            ERC_APPROVE,
            ERC_SET_APPROVAL_FOR_ALL,
            ERC_GET_APPROVED,
            ERC_IS_APPROVED_FOR_ALL,
        )
    )

    has_erc721_events = all(
        event in class_abi.events for event in (ERC_TRANSFER_EVENT, ERC_APPROVAL_EVENT, ERC_APPROVAL_FOR_ALL_EVENT)
    )

    return has_erc721_functions and has_erc721_events
