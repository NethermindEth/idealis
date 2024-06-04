from nethermind.idealis.rpc.ethereum.trace_parsing import (
    parse_call_trace,
    parse_create_trace,
    parse_reward_trace,
    parse_suicide_trace,
    unpack_debug_trace_block_response,
)
from nethermind.idealis.types.ethereum.enums import TraceType
from nethermind.idealis.utils import to_bytes
from tests.utils import load_rpc_response


def test_parse_call_trace():
    json_resp = {
        "action": {
            "from": "0xf326e4de8f66a0bdc0970b79e0924e33c79f1915",
            "callType": "delegatecall",
            "gas": "0x43fa",
            "input": "0x",
            "to": "0xd9db270c1b5e3bd161e8c8503c55ceabee709552",
            "value": "0x154a0cd220e76",
        },
        "blockHash": "0xfcde22d74521e2b11af0b1a08b1bf502d62590c804bd1750b6559f7417ab0a8a",
        "blockNumber": 16150105,
        "result": {"gasUsed": "0x5e0", "output": "0x"},
        "subtraces": 0,
        "traceAddress": [1, 0, 2, 0],
        "transactionHash": "0x6e506c143d6900ee98c9f8a0153ab426c3598c467a63d8fb0fd46ce70c658f2b",
        "transactionPosition": 2,
        "type": "call",
    }

    call_trace = parse_call_trace(json_resp)
    assert call_trace.block_number == 16150105
    assert call_trace.transaction_index == 2
    assert call_trace.trace_address == [1, 0, 2, 0]
    assert call_trace.error is None
    assert call_trace.from_address == to_bytes("0xf326e4de8f66a0bdc0970b79e0924e33c79f1915")
    assert call_trace.to_address == to_bytes("0xd9db270c1b5e3bd161e8c8503c55ceabee709552")
    assert call_trace.input == b""
    assert call_trace.gas_supplied == 17402
    assert call_trace.gas_used == 1504


def test_parse_create_trace():
    json_resp = {
        "action": {
            "from": "0xc4336629c1eb9248f1ca41b46b95011255717a7f",
            "gas": "0xd616",
            "init": "0x3d602d80600a3d3981f3363d3d373d3d3d363d73fe67f9a4776ea74d668915944df3139e9ba111635af43d82803e903d91602b57fd5bf3",
            "value": "0x0",
        },
        "blockHash": "0x3f3b71fa66a99ea7ffd6933bb691ce69b2c6cf102ad63ec33650aec2a33eeecb",
        "blockNumber": 16178054,
        "result": {
            "address": "0x511baa022d54f1f9612aec82f3e92ea8919b0876",
            "code": "0x363d3d373d3d3d363d73fe67f9a4776ea74d668915944df3139e9ba111635af43d82803e903d91602b57fd5bf3",
            "gasUsed": "0x2347",
        },
        "subtraces": 0,
        "traceAddress": [0],
        "transactionHash": "0x534c685bbb6691001d6ad0648a0d880b144f114d4f031b3ffbddf8f4f7b2c7df",
        "transactionPosition": 31,
        "type": "create",
    }

    create_trace = parse_create_trace(json_resp)
    assert create_trace.trace_type == TraceType.create
    assert create_trace.block_number == 16178054
    assert create_trace.transaction_index == 31
    assert create_trace.trace_address == [0]
    assert create_trace.error is None
    assert create_trace.from_address == to_bytes("0xc4336629c1eb9248f1ca41b46b95011255717a7f")
    assert create_trace.created_contract_address == to_bytes("0x511baa022d54f1f9612aec82f3e92ea8919b0876")
    assert create_trace.deployed_code == to_bytes(
        "0x363d3d373d3d3d363d73fe67f9a4776ea74d668915944df3139e9ba111635af43d82803e903d91602b57fd5bf3"
    )
    assert create_trace.gas_supplied == 54806
    assert create_trace.gas_used == 9031


def test_parse_reward_trace():
    json_resp = {
        "action": {
            "author": "0x99c85bb64564d9ef9a99621301f22c9993cb89e3",
            "rewardType": "block",
            "value": "0x1bc16d674ec80000",
        },
        "blockHash": "0xfae7185a5aaa70e0862e5c72d7cef16f72301c694feb328763269c80fb34be74",
        "blockNumber": 13179291,
        "result": None,
        "subtraces": 0,
        "traceAddress": [],
        "type": "reward",
    }

    reward_trace = parse_reward_trace(json_resp)

    assert reward_trace.block_number == 13179291
    assert reward_trace.author == to_bytes("0x99c85bb64564d9ef9a99621301f22c9993cb89e3")
    assert reward_trace.reward_type == "block"
    assert reward_trace.value == 2000000000000000000


def test_suicide_trace_parsing():
    json_resp = {
        "action": {
            "address": "0x11cd8bd32ccc81da0e4392960efa66c21a9ae29b",
            "refundAddress": "0xdb2f75e3b160d1b468f486c0f7b683b9c08b5315",
            "balance": "0x0",
        },
        "blockHash": "0xfcde22d74521e2b11af0b1a08b1bf502d62590c804bd1750b6559f7417ab0a8a",
        "blockNumber": 16150105,
        "result": None,
        "subtraces": 0,
        "traceAddress": [0, 3],
        "transactionHash": "0x3472fb02becb43d741bd0bf0d4a17dd2617ed7aa3145fbfe01199bdb811c598f",
        "transactionPosition": 258,
        "type": "suicide",
    }

    suicide_trace = parse_suicide_trace(json_resp)

    assert suicide_trace.refund_address == to_bytes("0xdb2f75e3b160d1b468f486c0f7b683b9c08b5315")
    assert suicide_trace.destroy_address == to_bytes("0x11cd8bd32ccc81da0e4392960efa66c21a9ae29b")
    assert suicide_trace.balance == 0
    assert suicide_trace.block_number == 16150105
    assert suicide_trace.transaction_index == 258


def test_debug_trace_parsing():
    trace_transaction_response = load_rpc_response("ethereum", "debug_traceBlock_19_000_000.json")

    call_traces, create_traces, _ = unpack_debug_trace_block_response(trace_transaction_response["result"], 19_000_000)

    assert len(call_traces) == 547
    assert len(create_traces) == 1
