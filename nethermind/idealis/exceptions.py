class RPCError(Exception):
    """

    Raised when issues occur with backfilling data

    """


class RPCRateLimitError(RPCError):
    """Raised when gateway rate limits are implmented by the remote host"""


class RPCHostError(RPCError):
    """Raised when the remote host returns error, fails to provide correct data, or when timeout occurs"""


class RPCTimeoutError(RPCError):
    """
    Raised when RPC Server Times Out
    """


class StateError(Exception):
    """
    Raised when requested state is not found, or operation is not possible on the current state.

    Raised if an operation requires an Archive Node
    """


class BlockNotFoundError(Exception):
    """
    Raised when the requested block is not found
    """


class DatabaseError(Exception):
    """

    Raised when issues occur with database operations

    """


class DecodingError(Exception):
    """

    Raised when issues occur with input decoding during data backfills

    """
