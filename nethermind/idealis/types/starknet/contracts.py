import pickle
from dataclasses import dataclass

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
