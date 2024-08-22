from nethermind.idealis.parse.ethereum.execution import parse_get_block_response
from nethermind.idealis.utils import to_bytes
from tests.utils import load_rpc_response


def test_parse_block_without_transactions():
    block = load_rpc_response("ethereum", "getBlockByNumber_no_tx_16592887.json")

    parsed_block, transactions = parse_get_block_response(block["result"])

    assert parsed_block.block_number == 0xFD2FF7
    assert parsed_block.timestamp == 0x63E536BB
    assert parsed_block.base_fee_per_gas == 0x120E61B4C1

    assert len(transactions) == 0


def test_parse_block_with_transactions():
    json_response = load_rpc_response("ethereum", "getBlockByNumber_txs_14422234.json")

    parsed_block, transactions = parse_get_block_response(json_response["result"])

    assert parsed_block.block_number == 14422234
    assert parsed_block.timestamp == 1647765799
    assert parsed_block.base_fee_per_gas == 9434638213

    assert len(transactions) == 145

    assert transactions[0].block_number == 14422234
    assert transactions[0].from_address == to_bytes("0x7b018835d45f02cac14fe9b38f5aae2f5205200e", pad=20)
    assert transactions[0].transaction_index == 0
