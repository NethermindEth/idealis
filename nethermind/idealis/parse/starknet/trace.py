from dataclasses import dataclass
from dataclasses import fields as dataclass_fields
from typing import Any, Sequence

from nethermind.idealis.parse.shared.trace import (
    get_root_trace,
    get_toplevel_child_traces,
)
from nethermind.idealis.types.starknet.core import (
    DecodedOperation,
    Event,
    StateDiff,
    Trace,
    TraceCall,
)
from nethermind.idealis.types.starknet.enums import EntryPointType, TraceCallType
from nethermind.idealis.utils import to_bytes
from nethermind.starknet_abi.utils import starknet_keccak

EXECUTE_SELECTOR = starknet_keccak(b"__execute__")


def get_execute_trace(traces: list[Trace]) -> Trace | None:
    """
    Gets the deepest trace with a selector of __execute__ from a list of traces.

    :return:
    """

    filtered_traces = [trace for trace in traces if trace.selector == EXECUTE_SELECTOR]

    if not filtered_traces:
        return None

    elif len(filtered_traces) == 1:
        return filtered_traces[0]

    else:
        return max(filtered_traces, key=lambda trace: len(trace.trace_address))


def get_user_operations(traces: list[Trace] | None) -> list[DecodedOperation]:
    if traces is None or len(traces) == 0:
        return []

    execute_trace = get_execute_trace(traces)
    if execute_trace is None:
        top_trace = get_root_trace(traces)
        return [
            DecodedOperation(
                operation_name=top_trace.function_name,
                operation_params=top_trace.decoded_inputs,
            )
        ]

    multicalls: Sequence[Trace] = get_toplevel_child_traces(traces, execute_trace.trace_address)
    multicalls = sorted(multicalls, key=lambda t: t.trace_address)
    decoded_ops = []
    for call in multicalls:
        if call.function_name is None and call.decoded_inputs is None:
            continue

        decoded_ops.append(
            DecodedOperation(
                operation_name=call.function_name or "",
                operation_params=call.decoded_inputs or {},
            )
        )
    return decoded_ops


@dataclass
class ParsedTransactionTrace:
    state_diff: StateDiff | None

    validate_traces: list[Trace]
    constructor_traces: list[Trace]
    execute_traces: list[Trace]
    fee_transfer_traces: list[Trace]

    validate_events: list[Event]
    constructor_events: list[Event]
    execute_events: list[Event]
    fee_transfer_events: list[Event]


# TODO: Improve this spaghetti
@dataclass(slots=True)
class ParsedBlockTrace(ParsedTransactionTrace):
    state_diff: list[StateDiff]

    @classmethod
    def init(cls):
        return ParsedBlockTrace(**{field.name: list() for field in dataclass_fields(ParsedBlockTrace)})

    def add_transaction_trace(self, transaction_trace: ParsedTransactionTrace):
        for dataclass_field in dataclass_fields(transaction_trace):
            if dataclass_field.name == "state_diff":
                if isinstance(transaction_trace.state_diff, StateDiff):
                    self.state_diff += [transaction_trace.state_diff]
                continue

            tx_field = getattr(transaction_trace, dataclass_field.name)
            if len(tx_field):
                block_field = getattr(self, dataclass_field.name)
                block_field += tx_field

    def add_block_trace(self, block_trace: "ParsedBlockTrace"):
        for dataclass_field in dataclass_fields(block_trace):
            block_field = getattr(self, dataclass_field.name)
            add_data = getattr(block_trace, dataclass_field.name)
            if add_data is None:
                continue

            block_field += add_data

    @classmethod
    def from_block_traces(cls, block_traces: Sequence["ParsedBlockTrace"]) -> "ParsedBlockTrace":
        output_trace = block_traces[0]
        if output_trace.state_diff is None:
            output_trace.state_diff = []

        for block_trace in block_traces[1:]:
            output_trace.add_block_trace(block_trace)

        return output_trace


def unpack_trace_block_response(
    trace_response: list[dict[str, Any]],
    block_number: int,
) -> ParsedBlockTrace:
    """
    Unpack the trace response into a list of Trace dataclasses.
    Generates TraceAddresses for each unpacked trace

    :param trace_response: JSON decoded Trace response.
    :param block_number: The block number of the trace response.

    :return:
    """
    block_trace = ParsedBlockTrace.init()

    for transaction_index, trace_dict in enumerate(trace_response):
        transaction_trace = unpack_trace_response(
            trace_response=trace_dict,
            block_number=block_number,
            transaction_index=transaction_index,
        )

        block_trace.add_transaction_trace(transaction_trace)

    return block_trace


def _get_root_call(
    trace_root_json: dict[str, Any],
    block_number: int,
    transaction_index: int,
) -> Trace:
    """
    Gets trace where trace_address==[0]
    This is useful to get the original tx calldata array, and the original tx sender address, and information
    like the block_number and transaction_index.  If a revert error occurs, this method will get the original calldata from
    the validate invocation, and tie it to the errored execute trace.

    :return:
    """

    if "validate_invocation" in trace_root_json:
        contract_address = to_bytes(trace_root_json["validate_invocation"]["contract_address"], pad=32)
        selector = to_bytes(trace_root_json["validate_invocation"]["entry_point_selector"], pad=32)
        calldata = [to_bytes(c) for c in trace_root_json["validate_invocation"]["calldata"]]
        caller_address = to_bytes(trace_root_json["validate_invocation"]["caller_address"], pad=32)
        class_hash = to_bytes(trace_root_json["validate_invocation"]["class_hash"], pad=32)
        entry_point_type = EntryPointType(trace_root_json["validate_invocation"]["entry_point_type"])
        call_type = TraceCallType(trace_root_json["validate_invocation"]["call_type"])

    else:
        contract_address = b""
        selector = b""
        calldata = []
        caller_address = b""
        class_hash = b""
        entry_point_type = None
        call_type = ""

    return Trace(
        block_number=block_number,
        transaction_index=transaction_index,
        trace_address=[0],
        contract_address=contract_address,
        selector=selector,
        calldata=calldata,
        result=[],
        caller_address=caller_address,
        class_hash=class_hash,
        entry_point_type=entry_point_type,
        call_type=call_type,
        execution_resources={},
        error=None,
    )


def unpack_trace_response(
    trace_response: dict[str, Any],
    block_number: int,
    transaction_index: int,
    tx_hash: bytes | None = None,
) -> ParsedTransactionTrace:
    """
    Unpack the trace response into a list of Trace dataclasses.
    Generates TraceAddresses for each unpacked trace

    :param trace_response: JSON decoded Trace response.
    :param block_number:
    :param transaction_index:
    :param tx_hash:

    :return:
    """
    if tx_hash is None:
        tx_hash = to_bytes(trace_response["transaction_hash"], pad=32)

    trace_root = trace_response["trace_root"] if "trace_root" in trace_response else trace_response

    root_call = _get_root_call(trace_root, block_number, transaction_index)

    validate_traces, validate_events = parse_validate_traces(trace_root, root_call)

    execute_traces, execute_events = parse_execute_trace(trace_root, root_call)

    if "fee_transfer_invocation" in trace_root:
        fee_transfer_traces, fee_transfer_events = parse_trace_call(
            trace_call_dict=trace_root["fee_transfer_invocation"],
            root_call=root_call,
            trace_path=[0],
        )
    else:
        fee_transfer_traces, fee_transfer_events = [], []

    if "state_diff" in trace_root:
        state_diff = parse_state_diff(
            state_diff=trace_root["state_diff"],
            block_number=block_number,
            tx_hash=tx_hash,
        )
    else:
        state_diff = None

    if "constructor_invocation" in trace_root:
        constructor_traces, constructor_events = parse_constructor_trace(
            trace_root["constructor_invocation"], root_call
        )
    else:
        constructor_traces, constructor_events = [], []

    return ParsedTransactionTrace(
        state_diff=state_diff,
        validate_traces=validate_traces,
        constructor_traces=constructor_traces,
        execute_traces=execute_traces,
        fee_transfer_traces=fee_transfer_traces,
        validate_events=validate_events,
        constructor_events=constructor_events,
        execute_events=execute_events,
        fee_transfer_events=fee_transfer_events,
    )


def parse_validate_traces(
    trace_root: dict[str, Any],
    root_call: Trace,
) -> tuple[list[Trace], list[Event]]:
    # Early Starknet Impl Had no __validate__ invocation
    if "validate_invocation" not in trace_root:
        return [], []

    return parse_trace_call(
        trace_call_dict=trace_root["validate_invocation"],
        root_call=root_call,
        trace_path=[0],
    )


def parse_execute_trace(
    trace_root: dict[str, Any],
    root_call: Trace,
) -> tuple[list[Trace], list[Event]]:
    """
    Parses JSON Response from trace_root['execute_invocation']
    If revert error occurs, parses revert reason into a failed trace.

    :param trace_root: trace['trace_root']
    :param root_call: root call for trace

    :return: (list[execute_traces], list[execute_events])
    """
    if "execute_invocation" not in trace_root:
        return [], []

    execute_trace_json = trace_root["execute_invocation"]
    if "revert_reason" in execute_trace_json:
        execute_traces = [
            Trace(
                block_number=root_call.block_number,
                transaction_index=root_call.transaction_index,
                trace_address=[0],
                contract_address=root_call.contract_address,
                selector=root_call.selector,
                calldata=root_call.calldata,
                result=[],
                caller_address=root_call.caller_address,
                class_hash=root_call.class_hash,
                entry_point_type=root_call.entry_point_type,
                call_type=root_call.call_type,
                execution_resources={},
                error=execute_trace_json["revert_reason"],
            )
        ]
        execute_events: list[Event] = []

    else:
        execute_traces, execute_events = parse_trace_call(
            trace_call_dict=execute_trace_json,
            root_call=root_call,
            trace_path=[0],
        )

    return execute_traces, execute_events


def parse_constructor_trace(
    constructor_trace_json: dict[str, Any], root_call: Trace
) -> tuple[list[Trace], list[Event]]:
    return parse_trace_call(
        trace_call_dict=constructor_trace_json,
        root_call=root_call,
        trace_path=[0],
    )


def parse_trace_call(
    trace_call_dict: dict[str, Any],
    root_call: Trace,
    trace_path: list[int],
) -> tuple[
    list[Trace],  # traces
    list[Event],  # events
    # list[Message],  # messages
]:
    child_traces, child_events = [], []

    # Does nothing if calls array is empty
    for subcall_idx, subcall_dict in enumerate(trace_call_dict["calls"]):
        traces, events = parse_trace_call(
            trace_call_dict=subcall_dict,
            root_call=root_call,
            trace_path=trace_path + [subcall_idx],
        )
        child_traces += traces
        child_events += events

    class_hash = to_bytes(trace_call_dict.get("class_hash", "0x0"), pad=32)

    # Does nothing if events array is empty
    called_contract = to_bytes(trace_call_dict["contract_address"], pad=32)
    call_events = parse_events(
        trace_call_dict=trace_call_dict["events"],
        contract_address=called_contract,
        block_number=root_call.block_number,
        transaction_index=root_call.transaction_index,
        class_hash=class_hash,
    )
    call_trace = Trace(
        contract_address=called_contract,
        block_number=root_call.block_number,
        transaction_index=root_call.transaction_index,
        trace_address=trace_path,
        selector=to_bytes(trace_call_dict.get("entry_point_selector", "0x0"), pad=32),
        calldata=[to_bytes(data) for data in trace_call_dict["calldata"]],
        result=[to_bytes(data) for data in trace_call_dict["result"]],
        caller_address=to_bytes(trace_call_dict["caller_address"], pad=32),
        class_hash=class_hash,
        error=None,
        entry_point_type=(
            EntryPointType(trace_call_dict["entry_point_type"]) if "entry_point_type" in trace_call_dict else None
        ),
        call_type=(TraceCallType(trace_call_dict["call_type"]) if "call_type" in trace_call_dict else None),
        execution_resources=trace_call_dict["execution_resources"],
    )

    return [call_trace] + child_traces, call_events + child_events


def parse_events(
    trace_call_dict: list[dict[str, Any]],
    contract_address: bytes,
    block_number: int,
    transaction_index: int,
    class_hash: bytes,
) -> list[Event]:
    return [
        Event(
            contract_address=contract_address,
            block_number=block_number,
            transaction_index=transaction_index,
            event_index=event["order"],
            keys=[to_bytes(key, pad=32) for key in event["keys"]],
            data=[to_bytes(data) for data in event["data"]],
            class_hash=class_hash,
        )
        for event in trace_call_dict
    ]


def parse_state_diff(
    state_diff: dict[str, Any],
    block_number: int,
    tx_hash: bytes,
) -> StateDiff:
    return StateDiff(
        block_number=block_number,
        tx_hash=tx_hash,
        storage_diffs=state_diff["storage_diffs"],
        nonces=state_diff["nonces"],
        deployed_contracts=state_diff["deployed_contracts"],
        deprecated_declared_classes=state_diff["deprecated_declared_classes"],
        declared_classes=state_diff["declared_classes"],
        replaced_classes=state_diff["replaced_classes"],
    )


def replace_delegate_calls(traces: list[Trace]) -> list[Trace]:
    """
    Given a sorted list of traces, replace call traces with their delegates where applicable,
    correcting trace addresses when applicable

    :param traces:
    :return:
    """
    tx_grouped_traces: dict[tuple[int, int], list[Trace]] = {}

    for trace in traces:
        if (trace.block_number, trace.transaction_index) not in tx_grouped_traces:
            tx_grouped_traces.update({(trace.block_number, trace.transaction_index): []})

        tx_grouped_traces[(trace.block_number, trace.transaction_index)].append(trace)

    output_traces = []

    for tx_traces in tx_grouped_traces.values():
        output_traces += replace_delegate_calls_for_tx(tx_traces)

    return output_traces


def replace_delegate_calls_for_tx(traces: list[Trace]) -> list[Trace]:
    output_traces = []
    trace_queue = traces.copy()

    while len(trace_queue):
        trace = trace_queue.pop(0)
        if len(trace_queue):
            next_trace = trace_queue[0]
            if next_trace.call_type == TraceCallType.delegate and next_trace.trace_address[:-1] == trace.trace_address:
                new_trace_address, trace_addr_len = trace.trace_address, len(next_trace.trace_address)

                for child in [t for t in trace_queue if t.trace_address[:trace_addr_len] == next_trace.trace_address]:
                    child.trace_address = new_trace_address + child.trace_address[trace_addr_len:]

                trace = trace_queue.pop(0)
                trace.trace_address = new_trace_address

        output_traces.append(trace)

    return output_traces


def parse_traces_into_calls(traces: list[Trace]) -> list[TraceCall]:
    """
    Given a list of traces, parse them into a list of TraceCall dataclasses
    """
    return [
        TraceCall(
            block_number=trace.block_number,
            transaction_index=trace.transaction_index,
            trace_address=trace.trace_address,
            class_hash=trace.class_hash,
            caller_address=trace.caller_address,
            contract_address=trace.contract_address,
            function_name=trace.function_name,
            decoded_inputs=trace.decoded_inputs,
            decoded_outputs=trace.decoded_outputs,
        )
        for trace in traces
        if trace.function_name is not None
    ]
