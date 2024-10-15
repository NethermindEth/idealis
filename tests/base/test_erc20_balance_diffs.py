from nethermind.idealis.parse.shared.erc_20_tokens import (
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

    transfer_diffs = generate_balance_diffs(
        transfers=transfers, reference_block=200, zero_address=STARKNET_NULL_ADDRESS
    )
    assert len(transfer_diffs) == 4

    null_addr = [d for d in transfer_diffs if d.holder_address == STARKNET_NULL_ADDRESS][0]
    account_1 = [d for d in transfer_diffs if d.holder_address == STARKNET_ACCOUNT_1][0]
    account_2 = [d for d in transfer_diffs if d.holder_address == STARKNET_ACCOUNT_2][0]
    account_3 = [d for d in transfer_diffs if d.holder_address == STARKNET_ACCOUNT_3][0]

    assert null_addr.balance_diff == -50
    assert null_addr.transfers_sent == 1
    assert null_addr.transfers_received == 0

    assert account_1.balance_diff == -50
    assert account_1.transfers_sent == 1
    assert account_1.transfers_received == 1

    assert account_2.balance_diff == -100
    assert account_2.transfers_sent == 1
    assert account_2.transfers_received == 1

    assert account_3.balance_diff == 200
    assert account_3.transfers_sent == 0
    assert account_3.transfers_received == 1


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

    transfer_diffs = generate_balance_diffs(
        transfers=transfers, reference_block=100, zero_address=STARKNET_NULL_ADDRESS
    )
    assert len(transfer_diffs) == 5

    null_addrs = [d for d in transfer_diffs if d.holder_address == STARKNET_NULL_ADDRESS]
    assert len(null_addrs) == 2
    eth_null = [d for d in null_addrs if d.token_address == STARKNET_ETH][0]
    usdc_null = [d for d in null_addrs if d.token_address == STARKNET_USDC][0]

    assert eth_null.balance_diff == -400
    assert eth_null.transfers_sent == 1
    assert eth_null.transfers_received == 0

    assert usdc_null.balance_diff == -100
    assert usdc_null.transfers_sent == 1
    assert usdc_null.transfers_received == 0

    account_1_eth = [d for d in transfer_diffs if d.holder_address == STARKNET_ACCOUNT_1]
    assert len(account_1_eth) == 1
    assert account_1_eth[0].transfers_received == 1
    assert account_1_eth[0].transfers_sent == 1
    assert account_1_eth[0].balance_diff == 0
    assert account_1_eth[0].token_address == STARKNET_ETH

    account_2 = [d for d in transfer_diffs if d.holder_address == STARKNET_ACCOUNT_2]
    assert len(account_2) == 2

    account_2_eth = [d for d in account_2 if d.token_address == STARKNET_ETH][0]
    account_2_usdc = [d for d in account_2 if d.token_address == STARKNET_USDC][0]

    assert account_2_eth.balance_diff == 400
    assert account_2_eth.transfers_sent == 0
    assert account_2_eth.transfers_received == 1

    assert account_2_usdc.transfers_sent == 0
    assert account_2_usdc.transfers_received == 1
    assert account_2_usdc.balance_diff == 100
