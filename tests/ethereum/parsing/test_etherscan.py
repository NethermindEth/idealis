from nethermind.idealis.utils import to_bytes
from nethermind.idealis.wrapper.etherscan import _parse_etherscan_transactions
from tests.utils import load_rpc_response


def test_parse_account_activity_txns():
    json_response = load_rpc_response("ethereum", "etherscan_account_activity.json")

    transactions = _parse_etherscan_transactions(json_response["result"])

    assert len(transactions) == 2

    assert transactions[0].block_number == 14923678
    assert transactions[0].from_address == to_bytes("0x9aa99c23f67c81701c772b106b4f83f6e858dd2e", pad=20)
    assert transactions[0].to_address is None
    assert transactions[0].transaction_index == 61

    assert transactions[1].block_number == 14923692
    assert transactions[1].transaction_index == 27
    assert transactions[1].function_name == "transfer"
