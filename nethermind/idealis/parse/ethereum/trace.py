from typing import Any

from nethermind.idealis.types.ethereum.core import (
    CallTraceResponse,
    CreateTraceResponse,
    Event,
    RewardTraceResponse,
    SuicideTraceResponse,
)
from nethermind.idealis.types.ethereum.enums import TraceCallType, TraceError
from nethermind.idealis.utils import hex_to_int, to_bytes


def unpack_debug_trace_block_response(
    block_traces: list[dict[str, Any]], block_number: int
) -> tuple[list[CallTraceResponse], list[CreateTraceResponse], list[Event],]:
    return_call_traces = []
    return_create_traces = []
    return_events = []

    for transaction_index, tx_trace_dict in enumerate(block_traces):
        call_traces, create_traces, events = unpack_debug_trace_transaction_response(
            trace_dict=tx_trace_dict,
            block_number=block_number,
            transaction_index=transaction_index,
        )
        return_call_traces += call_traces
        return_create_traces += create_traces
        return_events += events

    return return_call_traces, return_create_traces, return_events


def unpack_debug_trace_transaction_response(
    trace_dict: dict[str, Any], block_number: int, transaction_index: int
) -> tuple[list[CallTraceResponse], list[CreateTraceResponse], list[Event]]:
    if "result" in trace_dict.keys():
        # Geth Returns these these as lists responses
        # tx_hash = trace_dict["txHash"]
        trace_call = trace_dict["result"]
    else:
        # Nethermind Returns these as a single response
        trace_call = trace_dict

    call_traces, create_traces, events = parse_trace_call(
        trace_call=trace_call,
        block_number=block_number,
        transaction_index=transaction_index,
        trace_address=[],
    )

    return call_traces, create_traces, events


def parse_trace_call(
    trace_call: dict[str, Any],
    block_number: int,
    transaction_index: int,
    trace_address: list[int],
) -> tuple[list[CallTraceResponse], list[CreateTraceResponse], list[Event]]:
    return_call_traces = []
    return_create_traces = []
    return_events = []

    for subcall_index, trace_call in enumerate(trace_call.get("calls", [])):
        call_traces, create_traces, events = parse_trace_call(
            trace_call=trace_call,
            block_number=block_number,
            transaction_index=transaction_index,
            trace_address=trace_address + [subcall_index],
        )
        return_call_traces += call_traces
        return_create_traces += create_traces
        return_events += events

    return_events += [
        Event(
            block_number=block_number,
            transaction_index=transaction_index,
            event_index=event["index"],
            contract_address=to_bytes(event["address"], pad=20),
            data=to_bytes(event.get("data")),
            topics=[to_bytes(topic, pad=32) for topic in event["topics"]],
            event_name=None,
            decoded_params=None,
        )
        for event in trace_call.get("logs", [])
    ]

    if "revertReason" in trace_call:
        # Geth separates into error and error_text
        error = TraceError.from_json(trace_call.get("error"))
        error_text = trace_call["revertReason"]
    else:
        # Nethermind Prefixes error_text with "error type"
        error_text = trace_call.get("error")
        error = TraceError.reverted if error_text and error_text.startswith("Reverted") else None

    if trace_call["type"] in ["CREATE", "CREATE2"]:
        return_create_traces.append(
            CreateTraceResponse(
                block_number=block_number,
                transaction_index=transaction_index,
                trace_address=trace_address,
                error=error,
                from_address=to_bytes(trace_call["from"], pad=20),
                deployed_code=to_bytes(trace_call["output"]),
                created_contract_address=to_bytes(trace_call["to"], pad=20),
                gas_supplied=hex_to_int(trace_call["gas"]),
                gas_used=hex_to_int(trace_call["gasUsed"]),
            )
        )

    else:
        return_call_traces.append(
            CallTraceResponse(
                block_number=block_number,
                transaction_index=transaction_index,
                trace_address=trace_address,
                error=error,
                error_text=error_text,
                from_address=to_bytes(trace_call["from"], pad=20),
                to_address=to_bytes(trace_call["to"], pad=20),
                input=to_bytes(trace_call["input"]),
                gas_supplied=hex_to_int(trace_call["gas"]),
                gas_used=hex_to_int(trace_call["gasUsed"]),
                output=to_bytes(trace_call.get("output", "")),
                call_type=TraceCallType(trace_call["type"].lower()),
                value=hex_to_int(trace_call.get("value", "0")),
            )
        )

    return return_call_traces, return_create_traces, return_events


def unpack_trace_block_response(
    trace_response: list[dict[str, Any]],
) -> tuple[list[CallTraceResponse], list[CreateTraceResponse], list[RewardTraceResponse], list[SuicideTraceResponse]]:
    """
    Unpack the trace_block RPC Response into a list of TraceResponse dataclasses.
    :param trace_response: JSON decoded Trace response.
    :return: list[traces]
    """
    call_traces = []
    create_traces = []
    reward_traces = []
    suicide_traces = []

    for trace_dict in trace_response:
        match trace_dict["type"]:
            case "call":
                call_traces.append(parse_call_trace(trace_dict))
            case "create":
                create_traces.append(parse_create_trace(trace_dict))
            case "reward":
                reward_traces.append(parse_reward_trace(trace_dict))
            case "suicide":
                suicide_traces.append(parse_suicide_trace(trace_dict))
            case _:
                raise TypeError("Unexpected Trace Returned from RPC: ", trace_dict)

    return (call_traces, create_traces, reward_traces, suicide_traces)


def parse_call_trace(
    trace_dict: dict[str, Any],
) -> CallTraceResponse:
    trace_result = trace_dict.get("result")  # None if error
    return CallTraceResponse(
        block_number=trace_dict["blockNumber"],
        transaction_index=trace_dict["transactionPosition"],
        trace_address=trace_dict["traceAddress"],
        error=TraceError.from_json(trace_dict.get("error")),
        error_text=None,
        from_address=to_bytes(trace_dict["action"]["from"], pad=20),
        to_address=to_bytes(trace_dict["action"]["to"], pad=20),
        input=to_bytes(trace_dict["action"]["input"]),
        gas_supplied=hex_to_int(trace_dict["action"]["gas"]),
        gas_used=hex_to_int(trace_result["gasUsed"]) if trace_result else 0,
        output=to_bytes(trace_result["output"]) if trace_result else None,
        call_type=TraceCallType(trace_dict["action"]["callType"]),
        value=hex_to_int(trace_dict["action"].get("value", "0")),
    )


def parse_create_trace(trace_dict: dict[str, Any]) -> CreateTraceResponse:
    return CreateTraceResponse(
        block_number=trace_dict["blockNumber"],
        transaction_index=trace_dict["transactionPosition"],
        trace_address=trace_dict["traceAddress"],
        error=TraceError.from_json(trace_dict.get("error")),
        from_address=to_bytes(trace_dict["action"]["from"], pad=20),
        deployed_code=to_bytes(trace_dict["result"]["code"]),
        created_contract_address=to_bytes(trace_dict["result"]["address"], pad=20),
        gas_supplied=hex_to_int(trace_dict["action"]["gas"]),
        gas_used=hex_to_int(trace_dict["result"]["gasUsed"]),
    )


def parse_reward_trace(trace_dict: dict[str, Any]) -> RewardTraceResponse:
    return RewardTraceResponse(
        block_number=trace_dict["blockNumber"],
        author=to_bytes(trace_dict["action"]["author"]),
        reward_type=trace_dict["action"]["rewardType"],
        value=hex_to_int(trace_dict["action"]["value"]),
    )


def parse_suicide_trace(trace_dict: dict[str, Any]) -> SuicideTraceResponse:
    return SuicideTraceResponse(
        block_number=trace_dict["blockNumber"],
        transaction_index=trace_dict["transactionPosition"],
        trace_address=trace_dict["traceAddress"],
        destroy_address=to_bytes(trace_dict["action"]["address"]),
        refund_address=to_bytes(trace_dict["action"]["refundAddress"]),
        balance=hex_to_int(trace_dict["action"]["balance"]),
        error=TraceError.from_json(trace_dict.get("error")),
    )
