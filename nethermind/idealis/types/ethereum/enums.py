from enum import Enum
from typing import Any, Optional


class TraceType(Enum):
    call = "call"
    create = "create"
    reward = "reward"
    suicide = "suicide"


class TraceCallType(Enum):
    call = "call"
    delegatecall = "delegatecall"
    staticcall = "staticcall"


class TraceError(Enum):
    reverted = "reverted"
    out_of_gas = "out_of_gas"
    bad_instruction = "bad_instruction"
    bad_jump_dest = "bad_jump_dest"
    stack_underflow = "stack_underflow"
    mutable_call = "mutable_call"
    no_error = None

    @classmethod
    def from_json(cls, json_val: str | None) -> Optional["TraceError"]:
        """
        Hacky, but if->elif is fast for 99% of cases and simplifies DB interfacing
        :param json_val:
        :return:
        """
        if json_val is None:
            return None
        if json_val == "execution reverted":  # debug_traceTransaction
            return cls.reverted
        if json_val == "Reverted":  # trace_transaction
            return cls.reverted
        if json_val == "out of gas":
            return cls.out_of_gas
        if json_val == "Bad instruction":
            return cls.bad_instruction
        if json_val == "Bad jump destination":
            return cls.bad_jump_dest
        if json_val == "Stack underflow":
            return cls.stack_underflow
        if json_val == "Mutable Call In Static Context":
            return cls.mutable_call

        raise ValueError(f"Invalid TraceError: {json_val}")
