from typing import Any, Protocol


class TraceProtocol(Protocol):
    trace_address: list[int]


def get_root_trace(traces: list[TraceProtocol]):
    """
    Returns the trace with a trace address of [0]

    :param traces: List of Trace dataclasses posessing a trace_address member
    :return: Trace dataclass where trace_address == [0]
    """
    root_trace = [t for t in traces if t.trace_address == [0]]
    if len(root_trace) != 1:
        raise ValueError(f"Array of Traces has more than once trace with address of [0]: {root_trace}")
    return root_trace[0]


def get_toplevel_child_traces(traces: list[TraceProtocol], parent_trace_address: list[int]) -> list:
    """
    Returns list of traces that are children of the parent_trace_address.

    :param traces: List of Trace dataclasses with a trace_address member
    :param parent_trace_address:
    :return:
    """

    return [
        trace
        for trace in traces
        if trace.trace_address[: len(parent_trace_address)] == parent_trace_address
        and len(trace.trace_address) == len(parent_trace_address) + 1
    ]


def group_traces(traces: list[TraceProtocol]) -> Any:  # TODO: type this with a protocol
    """
    Groups traces into a nested list structure.

    Trace A -> [0]
    Trace B -> [0, 0]
    Trace C -> [0, 1]
    Trace D -> [0, 1, 0]
    Trace E -> [0, 2]

    Grouped:
    (Trace A, [(Trace B, None), (Trace C, [(Trace D, None)]), (Trace E, None)])
    """

    def group_traces_recursive(parent_trace_address: list[int]) -> Any:
        children = get_toplevel_child_traces(traces, parent_trace_address)
        if not children:
            return None

        return [(child, group_traces_recursive(child.trace_address)) for child in children]

    return traces[0], group_traces_recursive(traces[0].trace_address)
