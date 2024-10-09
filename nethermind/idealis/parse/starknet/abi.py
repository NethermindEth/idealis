import logging

from nethermind.starknet_abi.abi_types import StarknetCoreType
from nethermind.starknet_abi.dispatch import DecodingDispatcher, StarknetAbi
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


# Proxy Functions & Selectors --------------------------------
GET_CAMEL_FUNC = "getImplementation"
GET_SNAKE_FUNC = "get_implementation"
GET_HASH_CAMEL_FUNC = "getImplementationHash"
GET_HASH_SNAKE_FUNC = "get_implementation_hash"
IMPL_SNAKE_FUNC = "implementation"

GET_CAMEL_SELECTOR = starknet_keccak(GET_CAMEL_FUNC.encode())
GET_SNAKE_SELECTOR = starknet_keccak(GET_SNAKE_FUNC.encode())
GET_HASH_CAMEL_SELECTOR = starknet_keccak(GET_HASH_CAMEL_FUNC.encode())
GET_HASH_SNAKE_SELECTOR = starknet_keccak(GET_HASH_SNAKE_FUNC.encode())
IMPL_SNAKE_SELECTOR = starknet_keccak(IMPL_SNAKE_FUNC.encode())


root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("parse").getChild("starknet").getChild("abi")


def is_class_account(class_abi: StarknetAbi) -> bool:
    return all(
        func in class_abi.functions
        for func in ["__validate__", "__execute__", "__validate_declare__", "__validate_deploy__"]
    )


def is_class_proxy(class_abi: StarknetAbi) -> bool:
    return any(
        proxy_func in class_abi.functions
        for proxy_func in (
            GET_CAMEL_FUNC,
            GET_SNAKE_FUNC,
            GET_HASH_CAMEL_FUNC,
            GET_HASH_SNAKE_FUNC,
            IMPL_SNAKE_FUNC,
        )
    )


def is_dispatcher_impl_proxy(decoder: DecodingDispatcher, target_impl: bytes) -> tuple[bool, bytes | None]:
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


def is_class_erc20_token(class_abi: StarknetAbi) -> bool:
    has_erc_20_functions = all(
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

    has_erc_20_events = all(event in class_abi.events for event in (ERC_TRANSFER_EVENT, ERC_APPROVAL_EVENT))

    return has_erc_20_functions and has_erc_20_events


def is_class_erc721_token(class_abi: StarknetAbi) -> bool:
    has_erc_721_functions = all(
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

    has_erc_721_events = all(
        event in class_abi.events for event in (ERC_TRANSFER_EVENT, ERC_APPROVAL_EVENT, ERC_APPROVAL_FOR_ALL_EVENT)
    )

    return has_erc_721_functions and has_erc_721_events
