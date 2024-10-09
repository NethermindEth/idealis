import pickle
from dataclasses import dataclass
from typing import Any

from nethermind.idealis.types.base import DataclassDBInterface


@dataclass(slots=True)
class StarknetClass:
    """
    Represents a StarknetClass in the Database
    """

    name: str | None
    abi_json: list[dict[str, str]]

    class_hash: bytes
    class_version: str
    declaration_block: int
    declaration_transaction: bytes


@dataclass(slots=True)
class ContractImplementation(DataclassDBInterface):
    """
    Represents a ContractImplementation in the Database
    """

    contract_address: bytes
    update_block: int

    history: dict[str, str | dict[str, str]]
    """
        Standard impl --> {<block>: <impl_class>}
        Proxy impl --> {<block> : {proxy_class: <class>, <proxy impl block>: <proxied contract>, ...}, ...}
        
        If the implemented class is a dict, that means its a proxy.  The class is accessible at the 'proxy_class' key,
        and the proxy contract history is accessible at str(block_number) keys
        
        To get the impl class, lookup the class for the proxy contract
    """

    def __sizeof__(self):
        return (
            65  # __sizeof__() 32 bytes + obj overhead
            + 28  # __sizeof__() 8 byte C-integer + obj overhead
            + pickle.dumps(self.history).__sizeof__()  # size of history dict
        )


@dataclass(slots=True)
class ClassDeclaration(DataclassDBInterface):
    class_hash: bytes
    declaration_block: int
    declaration_timestamp: int
    declare_transaction_hash: bytes

    is_account: bool
    is_proxy: bool
    is_erc_20: bool
    is_erc_721: bool


@dataclass(slots=True)
class ContractDeployment(DataclassDBInterface):
    contract_address: bytes
    initial_class_hash: bytes

    deploy_transaction_hash: bytes
    deploy_block: int
    deploy_timestamp: int

    constructor_args: dict[str, Any] | None  # Decoded constructor args
