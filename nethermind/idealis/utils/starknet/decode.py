import json
import logging

from nethermind.idealis.rpc.starknet import sync_get_class_abi
from nethermind.starknet_abi.dispatch import (
    ClassDispatcher,
    DecodingDispatcher,
    StarknetAbi,
)

root_logger = logging.getLogger("nethermind")
logger = root_logger.getChild("starknet").getChild("decoding")


def get_parsed_class(class_hash, rpc_url) -> StarknetAbi | None:
    class_abi = sync_get_class_abi(class_hash, rpc_url)
    if isinstance(class_abi, str):
        try:
            class_abi = json.loads(class_abi)
        except json.JSONDecodeError:
            logger.error(f"Invalid ABI for class 0x{class_hash.hex()}.  Could not parse ABI JSON...")
            return None
    if class_abi is None or len(class_abi) == 0:
        logger.warning(f"Empty ABI for class 0x{class_hash.hex()}.  Skipping...")
        return None
    try:
        return StarknetAbi.from_json(abi_json=class_abi, class_hash=class_hash, abi_name="")
    except BaseException as e:
        logger.error(f"Error parsing ABI for class 0x{class_hash.hex()}...  {e}")


class PessimisticDecoder(DecodingDispatcher):
    rpc_url: str
    """ Starknet RPC URL to use for fetching class ABIs """

    invalid_class_ids: set[bytes]
    """ Set of class IDs that have been fetched but are not valid decode classes """

    def __init__(self, rpc_url: str):
        super().__init__()
        self.rpc_url = rpc_url
        self.invalid_class_ids = set()

    def get_class(self, class_hash: bytes) -> ClassDispatcher | None:
        class_id = class_hash[-8:]

        if class_id in self.class_ids:
            return self.class_ids[class_id]

        if class_id in self.invalid_class_ids:
            return None

        class_abi = get_parsed_class(class_hash, self.rpc_url)
        if class_abi is None:
            self.invalid_class_ids.add(class_id)
            return None

        self.add_abi(class_abi)
        return self.class_ids[class_id]
