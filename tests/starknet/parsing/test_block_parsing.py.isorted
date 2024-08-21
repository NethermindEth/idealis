from nethermind.idealis.parse.starknet.block import parse_block_with_tx_receipts
from nethermind.idealis.utils import to_bytes
from tests.utils import load_rpc_response


def test_parse_first_blocks():
    starknet_block = load_rpc_response("starknet", "get_block_with_txs_25.json")

    block, transactions, events = parse_block_with_tx_receipts(starknet_block["result"])


def test_parsing_v0_13_1_block_response():
    starknet_13_1_block = load_rpc_response("starknet", "get_block_with_txs_623_436.json")

    block, transactions, events = parse_block_with_tx_receipts(starknet_13_1_block["result"])
    assert block.block_number == 623436

    assert len(transactions) == 191

    assert len(events) == 1925

    assert events[0].tx_index == 0
    assert events[0].contract_address == to_bytes("0x59a943ca214c10234b9a3b61c558ac20c005127d183b86a99a8f3c60a08b4ff")
    assert events[0].event_index == 0

    assert events[-1].tx_index == 190
    assert events[-1].contract_address == to_bytes("0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7")
    assert events[-1].event_index == 9
