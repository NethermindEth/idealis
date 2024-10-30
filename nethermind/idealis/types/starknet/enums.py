from enum import Enum

from nethermind.starknet_abi.utils import starknet_keccak


class BlockDataAvailabilityMode(Enum):
    """
    Enum for the different L1 Data Availability modes
    """

    blob = "BLOB"
    calldata = "CALLDATA"


class StarknetFeeUnit(Enum):
    """
    Enum for the different units of the fee
    """

    wei = "WEI"
    fri = "FRI"


class StarknetTxType(Enum):
    invoke = "INVOKE"
    declare = "DECLARE"
    deploy = "DEPLOY"
    deploy_account = "DEPLOY_ACCOUNT"
    l1_handler = "L1_HANDLER"


class ERCTokenType(Enum):
    erc20 = "ERC20"
    erc721 = "ERC721"
    erc1155 = "ERC1155"


class EntryPointType(Enum):
    external = "EXTERNAL"
    l1_handler = "L1_HANDLER"
    constructor = "CONSTRUCTOR"


class TraceCallType(Enum):
    library_call = "LIBRARY_CALL"
    delegate = "DELEGATE"
    call = "CALL"


class TraceInvocationType(Enum):
    execute = "execute"
    validate = "validate"
    fee_transfer = "fee_transfer"
    function_handler = "function_handler"


class TransactionStatus(Enum):
    """
    State for L2 Transaction Type
    """

    not_received = "not_received"
    received = "received"  # Finality - Received, execution - None
    rejected = "rejected"  # Finality - Received, execution - Rejected
    reverted = "reverted"  # Finality - Received, execution - Reverted
    accepted_on_l2 = "accepted_on_l2"  # Finality - Accepted on L2, execution - Succeeded
    accepted_on_l1 = "accepted_on_l1"  # Finality - Accepted on L1, execution - Succeeded


class MessageStatus(Enum):
    send_from_l2_to_l1 = "Send from L2 to L1"
    log_message_l2_to_l1 = "Log message L2 to L1"
    consumed_message_l2_to_l1 = "Consumed message L2 to L1"
    log_message_l1_to_l2 = "Log message L1 to L2"
    accepted_message_l1_to_l2 = "Accepted message L1 to L2"
    consumed_message_l1_to_l2 = "Consumed message L1 to L2"
    message_l1_to_l2_cancellation_started = "Message L1 to L2 cancellation started"
    message_l1_to_l2_canceled = "Message L1 to L2 canceled"


class MessageDirection(Enum):
    l1_to_l2 = "L1->L2"
    l2_to_l1 = "L2->L1"


class ClassType(Enum):
    """
    Enum for the different class types
    """

    unknown = "Unknown"
    proxy = "Proxy"
    argentx = "ArgentX"
    braavos = "Braavos"
    account = "Account"
    erc20 = "ERC20"
    erc721 = "ERC721"
    erc1155 = "ERC1155"


class ProxyKind(Enum):
    # Event based proxies...  Proxies impls are pulled from events
    oz_event_proxy = "oz_event_proxy"  # Openzeppelin proxy class with Upgraded and AdminChanged events

    # Function based proxies...  proxy impls generated with bisection algorithm
    get_impl_snake = "get_impl_snake"  # get_implementation() -> felt
    get_impl_camel = "get_impl_camel"  # getImplementation() -> felt
    get_hash_snake = "get_hash_snake"  # get_implementation_hash() -> felt
    get_hash_camel = "get_hash_camel"  # getImplementationHash() -> felt
    implementation = "implementation"  # implementation() -> felt

    @classmethod
    def supported_functions(cls) -> list["ProxyKind"]:
        """Return List of supported Proxy Functions"""
        return [
            ProxyKind.get_impl_snake,
            ProxyKind.get_impl_camel,
            ProxyKind.get_hash_snake,
            ProxyKind.get_hash_camel,
            ProxyKind.implementation,
        ]

    def function_name(self) -> str:
        """Map ProxyKind to ABI Function Name"""
        match self:
            case ProxyKind.oz_event_proxy:
                raise ValueError("ProxyKind.oz_event_proxy does not have a function name")
            case ProxyKind.get_impl_snake:
                return "get_implementation"
            case ProxyKind.get_impl_camel:
                return "getImplementation"
            case ProxyKind.get_hash_snake:
                return "get_implementation_hash"
            case ProxyKind.get_hash_camel:
                return "getImplementationHash"
            case ProxyKind.implementation:
                return "implementation"
            case _:
                raise ValueError(f"{self} does not have a function name")

    def function_selector(self) -> bytes:
        """Map ProxyKind to ABI Function Selector"""
        match self:
            case ProxyKind.oz_event_proxy:
                raise ValueError("ProxyKind.oz_event_proxy does not have a function selector")
            case _:
                return starknet_keccak(self.function_name().encode())
