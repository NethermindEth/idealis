def get_root_trace(traces):
    """
    Returns the trace with a trace address of [0]

    :param traces: List of Trace dataclasses posessing a trace_address member
    :return: Trace dataclass where trace_address == [0]
    """
    root_trace = [t for t in traces if t.trace_address == [0]]
    if len(root_trace) != 1:
        raise ValueError(f"Array of Traces has more than once trace with address of [0]: {root_trace}")
    return root_trace[0]


def get_toplevel_child_traces(traces, parent_trace_address: list[int]) -> list:
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
