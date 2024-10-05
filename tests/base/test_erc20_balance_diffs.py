from idlelib.pyparse import trans

from nethermind.idealis.parse.shared.erc_20_tokens import (
    ERC20BalanceDiffs,
    ERC20Transfer,
    generate_balance_diffs,
)
from tests.addresses import (
    STARKNET_ACCOUNT_1,
    STARKNET_ACCOUNT_2,
    STARKNET_ACCOUNT_3,
    STARKNET_ETH,
    STARKNET_NULL_ADDRESS,
    STARKNET_USDC,
)


def test_generate_single_token_balance_diffs():
    transfer_defaults = {
        "block_number": 100,
        "transaction_index": 0,
        "event_index": 0,
    }

    transfers = [
        ERC20Transfer(
            token_address=STARKNET_ETH,
            from_address=STARKNET_ACCOUNT_1,
            to_address=STARKNET_ACCOUNT_2,
            value=100,
            **transfer_defaults,
        ),
        ERC20Transfer(
            token_address=STARKNET_ETH,
            from_address=STARKNET_NULL_ADDRESS,
            to_address=STARKNET_ACCOUNT_1,
            value=50,
            **transfer_defaults,
        ),
        ERC20Transfer(
            token_address=STARKNET_ETH,
            from_address=STARKNET_ACCOUNT_2,
            to_address=STARKNET_ACCOUNT_3,
            value=200,
            **transfer_defaults,
        ),
    ]

    transfer_diffs = generate_balance_diffs(transfers, 200)
    assert len(transfer_diffs) == 3

    account_1 = [d for d in transfer_diffs if d.holder_address == STARKNET_ACCOUNT_1][0]
    account_2 = [d for d in transfer_diffs if d.holder_address == STARKNET_ACCOUNT_2][0]
    account_3 = [d for d in transfer_diffs if d.holder_address == STARKNET_ACCOUNT_3][0]

    assert account_1.balance_diff == -50
    assert account_2.balance_diff == -100
    assert account_3.balance_diff == 200


def test_multi_token_transfer_state():
    transfer_defaults = {
        "block_number": 100,
        "transaction_index": 0,
        "event_index": 0,
    }

    transfers = [
        ERC20Transfer(
            token_address=STARKNET_ETH,
            from_address=STARKNET_ACCOUNT_1,
            to_address=STARKNET_ACCOUNT_2,
            value=400,
            **transfer_defaults,
        ),
        ERC20Transfer(
            token_address=STARKNET_ETH,
            from_address=STARKNET_NULL_ADDRESS,
            to_address=STARKNET_ACCOUNT_1,
            value=400,
            **transfer_defaults,
        ),
        ERC20Transfer(
            token_address=STARKNET_USDC,
            from_address=STARKNET_NULL_ADDRESS,
            to_address=STARKNET_ACCOUNT_2,
            value=100,
            **transfer_defaults,
        ),
    ]

    transfer_diffs = generate_balance_diffs(transfers, 100)
    assert len(transfer_diffs) == 2

    account_2 = [d for d in transfer_diffs if d.holder_address == STARKNET_ACCOUNT_2]
    assert len(account_2) == 2

    account_2_eth = [d for d in account_2 if d.token_address == STARKNET_ETH][0]
    account_2_usdc = [d for d in account_2 if d.token_address == STARKNET_USDC][0]

    assert account_2_eth.balance_diff == 400
    assert account_2_usdc.balance_diff == 100
