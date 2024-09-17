import warnings

from nethermind.idealis.types.base import ERC20Transfer
from nethermind.idealis.utils import to_bytes

NULL_ADDRESS = [
    to_bytes("0x00", pad=32),
    to_bytes("0x00", pad=20),
]


def _apply_credits(
    balance_state: dict[bytes, int],
    transfer: ERC20Transfer,
):
    warnings.warn(
        "This function is un-tested & may not work as expected",
        DeprecationWarning,
        stacklevel=2,
    )

    if transfer.to_address in NULL_ADDRESS:
        if balance_state[b"total_supply"] < transfer.value:
            raise ValueError(f"Cannot Burn more tokens than the total supply")

        balance_state[b"total_supply"] -= transfer.value

    elif transfer.to_address not in balance_state:
        balance_state.update({transfer.to_address: transfer.value})
    else:
        balance_state[transfer.to_address] += transfer.value


def _apply_debits(
    balance_state: dict[bytes, int],
    transfer: ERC20Transfer,
):
    warnings.warn("This function is un-tested & may not work as expected", DeprecationWarning, stacklevel=2)

    if transfer.from_address not in NULL_ADDRESS and transfer.from_address not in balance_state:
        raise ValueError(f"Address {transfer.from_address.hex()} has 0 tokens.  Cannot transfer from this address")

    if transfer.from_address in NULL_ADDRESS:
        balance_state[b"total_supply"] += transfer.value
    else:
        if transfer.value > balance_state[transfer.from_address]:
            raise ValueError(f"Address {transfer.from_address.hex()} has insufficient tokens to transfer")

        balance_state[transfer.from_address] -= transfer.value


def generate_balance_state(transfers: list[ERC20Transfer]) -> dict[bytes, int]:
    warnings.warn("This function is un-tested & may not work as expected", DeprecationWarning, stacklevel=2)
    balance_state = {b"total_supply": 0}

    for transfer in transfers:
        if transfer.value <= 0:
            raise ValueError(f"Cannot parse negative token transfers")

        _apply_credits(balance_state, transfer)
        _apply_debits(balance_state, transfer)

    return balance_state


def generate_balance_state_history(
    transfers: list[ERC20Transfer],
    snapshot_frequency: int = 100_000,
) -> dict[int, dict[bytes, int]]:
    """
    Given a list of **SORTED** ERC20 transfers, parse the state of the balances for each address at
    block_number snapshots.

    Requires the ERC20 token to emit a Transfer events to & from the null address when minting/burning.  If the
    ERC20 token does not do this, generate ERC20 transfer events from that tokens mint/burn events & pass them to
    this function

    :param transfers: ordered list of ERC20Transfers
    :param snapshot_frequency: Capture the balance state every snapshot_frequency blocks
    :return: balance_state

    {
        800,000: {
            b"total_supply": 300,
            b"\x12\x34": 100,
            b"\x56\x78": 200
        },
        900,000: {
            b"total_supply": 800,
            b"\x12\x34": 200,
            b"\x56\x78": 600
        }
    }
    """

    warnings.warn("This function is un-tested & may not work as expected", DeprecationWarning, stacklevel=2)

    last_snapshot = ((transfers[0].block_number // snapshot_frequency) + 1) * snapshot_frequency
    balance_state: dict[bytes, int] = {b"total_supply": 0}
    histories: dict[int, dict[bytes, int]] = {}

    for transfer in transfers:
        if transfer.block_number > last_snapshot:
            histories.update({last_snapshot: balance_state.copy()})
            last_snapshot += snapshot_frequency

        if transfer.value <= 0:
            raise ValueError(f"Cannot parse negative token transfers")

        _apply_credits(balance_state, transfer)  # Credit balances based on to_address

        _apply_debits(balance_state, transfer)  # Debit balances based on from_address

    return histories


def apply_transfers_to_balance_state(
    balance_state: dict[bytes, int], transfers: list[ERC20Transfer]
) -> dict[bytes, int]:
    """
    Given a balance state history, a block number, and a list of transfers for the token from the latest snapshot
    to the block_number, calculate the balance state at the block_number

    :param balance_state: *THIS STATE IS MUTATED*
    :param transfers:
    :return:
    """

    warnings.warn("This function is un-tested & may not work as expected", DeprecationWarning, stacklevel=2)

    for transfer in transfers:
        if transfer.value <= 0:
            raise ValueError(f"Cannot parse negative token transfers")

        _apply_credits(balance_state, transfer)  # Credit balances based on to_address

        _apply_debits(balance_state, transfer)  # Debit balances based on from_address

    return balance_state
