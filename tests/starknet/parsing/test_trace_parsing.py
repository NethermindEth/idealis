from nethermind.idealis.parse.shared.trace import get_toplevel_child_traces
from nethermind.idealis.parse.starknet.trace import (
    get_execute_trace,
    get_user_operations,
    unpack_trace_block_response,
    unpack_trace_response,
)
from nethermind.idealis.types.starknet.core import DecodedOperation, Trace
from nethermind.idealis.utils import to_bytes
from tests.utils import load_rpc_response

# fmt: off


def test_parse_v0_block_traces():
    json_resp = load_rpc_response("starknet", "trace_block_25.json")
    traces = unpack_trace_block_response(json_resp, 25)


def test_parse_block_traces():
    json_resp = load_rpc_response("starknet", "trace_block_480_000.json")
    traces = unpack_trace_block_response(json_resp, 480_000)

def test_parse_v0_invoke_trace():
    invoke_trace = {'trace_root': {'type': 'INVOKE', 'execute_invocation': {'contract_address': '0x10065efa1ff23687be422bc36805aef69452fcec19feb8129038d779fb68e83', 'calldata': ['0x37c50b49bcbb955cc8c9d97b7700c236ff7ae3272426d6d1fefe994869b3e9e', '0x1f4f5599bc27fe7e3d49f06cdf91a4e10d35c6d6447cba5fc8e2cb5c645da5'], 'caller_address': '0x0', 'result': [], 'calls': [], 'events': [], 'messages': [], 'execution_resources': {'steps': 25}}}, 'transaction_hash': '0x695cdfed585226f62b53411cd17f9dd068df65cbf2e2dd69c8b60125b4e5179'}

    parsed_traces = unpack_trace_response(invoke_trace, 25, 0)


def test_parse_insufficient_fee_revert_trace():
    fee_revert_trace = {'trace_root': {'type': 'INVOKE', 'validate_invocation': {'contract_address': '0x51179303c2b1b3e5ee4ebc673be6a8a251c56b00f41edc388d9685db3266176', 'entry_point_selector': '0x162da33a4585851fe8d3af3c2a9c60b557814e221e0d4f30ff0b2189d9c7775', 'calldata': ['0x2', '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', '0x219209e083275171774dab1df80982e9df2096516f06319c5c6d71ae0a8480c', '0x0', '0x3', '0x4270219d365d6b017231b52e92b3fb5d7c8378b05e9abc97724537a80e93b0f', '0x1171593aa5bdadda4d6b0efde6cc94ee7649c3163d5efeb19da6c16d63a2a63', '0x3', '0x13', '0x16', '0x4270219d365d6b017231b52e92b3fb5d7c8378b05e9abc97724537a80e93b0f', '0x161f202ba74819', '0x0', '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', '0x161f202ba74819', '0x0', '0x6f15ec4b6ff0b7f7a216c4b2ccdefc96cbf114d6242292ca82971592f62273b', '0x15b969ff608b34a7c84c', '0x0', '0x159d9b6338618cb64db2', '0x0', '0x51179303c2b1b3e5ee4ebc673be6a8a251c56b00f41edc388d9685db3266176', '0x0', '0x0', '0x1', '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', '0x6f15ec4b6ff0b7f7a216c4b2ccdefc96cbf114d6242292ca82971592f62273b', '0x1114c7103e12c2b2ecbd3a2472ba9c48ddcbf702b1c242dd570057e26212111', '0x64', '0x2', '0x452add90bc93d620f2ea539fa16276b437445314e76ed23b17ac2e67395c99', '0xfc04eac8170ff7cc0d7415a4a'], 'caller_address': '0x0', 'class_hash': '0x3131fa018d520a037686ce3efddeab8f28895662f019ca3ca18a626650f7d1e', 'entry_point_type': 'EXTERNAL', 'call_type': 'CALL', 'result': [], 'calls': [{'contract_address': '0x51179303c2b1b3e5ee4ebc673be6a8a251c56b00f41edc388d9685db3266176', 'entry_point_selector': '0x162da33a4585851fe8d3af3c2a9c60b557814e221e0d4f30ff0b2189d9c7775', 'calldata': ['0x2', '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', '0x219209e083275171774dab1df80982e9df2096516f06319c5c6d71ae0a8480c', '0x0', '0x3', '0x4270219d365d6b017231b52e92b3fb5d7c8378b05e9abc97724537a80e93b0f', '0x1171593aa5bdadda4d6b0efde6cc94ee7649c3163d5efeb19da6c16d63a2a63', '0x3', '0x13', '0x16', '0x4270219d365d6b017231b52e92b3fb5d7c8378b05e9abc97724537a80e93b0f', '0x161f202ba74819', '0x0', '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', '0x161f202ba74819', '0x0', '0x6f15ec4b6ff0b7f7a216c4b2ccdefc96cbf114d6242292ca82971592f62273b', '0x15b969ff608b34a7c84c', '0x0', '0x159d9b6338618cb64db2', '0x0', '0x51179303c2b1b3e5ee4ebc673be6a8a251c56b00f41edc388d9685db3266176', '0x0', '0x0', '0x1', '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', '0x6f15ec4b6ff0b7f7a216c4b2ccdefc96cbf114d6242292ca82971592f62273b', '0x1114c7103e12c2b2ecbd3a2472ba9c48ddcbf702b1c242dd570057e26212111', '0x64', '0x2', '0x452add90bc93d620f2ea539fa16276b437445314e76ed23b17ac2e67395c99', '0xfc04eac8170ff7cc0d7415a4a'], 'caller_address': '0x0', 'class_hash': '0x5dec330eebf36c8672b60db4a718d44762d3ae6d1333e553197acb47ee5a062', 'entry_point_type': 'EXTERNAL', 'call_type': 'DELEGATE', 'result': [], 'calls': [], 'events': [], 'messages': [], 'execution_resources': {'steps': 669, 'memory_holes': 74, 'pedersen_builtin_applications': 1, 'range_check_builtin_applications': 11, 'ecdsa_builtin_applications': 1}}], 'events': [], 'messages': [], 'execution_resources': {'steps': 729, 'memory_holes': 74, 'pedersen_builtin_applications': 1, 'range_check_builtin_applications': 11, 'ecdsa_builtin_applications': 1}}, 'execute_invocation': {'revert_reason': 'Insufficient fee token balance'}, 'fee_transfer_invocation': {'contract_address': '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', 'entry_point_selector': '0x83afd3f4caedc6eebf44246fe54e38c95e3179a5ec9ea81740eca5b482d12e', 'calldata': ['0x1176a1bd84444c89232ec27754698e5d2e7e1a7f1539f12027f28b23ec9f3d8', '0xfb4f32109de5', '0x0'], 'caller_address': '0x51179303c2b1b3e5ee4ebc673be6a8a251c56b00f41edc388d9685db3266176', 'class_hash': '0xd0e183745e9dae3e4e78a8ffedcce0903fc4900beace4e0abf192d4c202da3', 'entry_point_type': 'EXTERNAL', 'call_type': 'CALL', 'result': ['0x1'], 'calls': [{'contract_address': '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', 'entry_point_selector': '0x83afd3f4caedc6eebf44246fe54e38c95e3179a5ec9ea81740eca5b482d12e', 'calldata': ['0x1176a1bd84444c89232ec27754698e5d2e7e1a7f1539f12027f28b23ec9f3d8', '0xfb4f32109de5', '0x0'], 'caller_address': '0x51179303c2b1b3e5ee4ebc673be6a8a251c56b00f41edc388d9685db3266176', 'class_hash': '0x2760f25d5a4fb2bdde5f561fd0b44a3dee78c28903577d37d669939d97036a0', 'entry_point_type': 'EXTERNAL', 'call_type': 'DELEGATE', 'result': ['0x1'], 'calls': [], 'events': [{'order': 0, 'keys': ['0x99cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9'], 'data': ['0x51179303c2b1b3e5ee4ebc673be6a8a251c56b00f41edc388d9685db3266176', '0x1176a1bd84444c89232ec27754698e5d2e7e1a7f1539f12027f28b23ec9f3d8', '0xfb4f32109de5', '0x0']}], 'messages': [], 'execution_resources': {'steps': 526, 'memory_holes': 42, 'pedersen_builtin_applications': 4, 'range_check_builtin_applications': 21}}], 'events': [], 'messages': [], 'execution_resources': {'steps': 586, 'memory_holes': 42, 'pedersen_builtin_applications': 4, 'range_check_builtin_applications': 21}}}, 'transaction_hash': '0x1e912713f5dd9d0d750048de51e84ea8b07d387617be222399982841a409a8c'}

    parsed_traces = unpack_trace_response(fee_revert_trace, 480_000, 0)

    assert len(parsed_traces.execute_events) == 0
    assert len(parsed_traces.execute_traces) == 1

    assert parsed_traces.execute_traces[0].trace_address == [0]
    assert parsed_traces.execute_traces[0].error == "Insufficient fee token balance"

    assert parsed_traces.validate_traces[-1].trace_address == [0]
    assert len(parsed_traces.validate_traces[-1].calldata) == 32
    assert (
        parsed_traces.validate_traces[-1].selector
        == to_bytes("0162da33a4585851fe8d3af3c2a9c60b557814e221e0d4f30ff0b2189d9c7775")
    )
    assert (
        parsed_traces.validate_traces[-1].class_hash
        == to_bytes("0x03131fa018d520a037686ce3efddeab8f28895662f019ca3ca18a626650f7d1e")
    )


def test_parse_constructor_trace():
    constructor_trace = {'trace_root': {'type': 'DEPLOY_ACCOUNT', 'validate_invocation': {'contract_address': '0x483a91c3778b1fa26afa2dc10a8cabc210e64e9a38d245c8b2b214f28ad9cb6', 'entry_point_selector': '0x36fcbf06cd96843058359e1a75928beacfac10727dab22a3972f0af8aa92895', 'calldata': ['0x25ec026985a3bf9d0cc1fe17326b245dfdc3ff89b8fde106542a3ea56c5a918', '0x17fc658b4a0e68136cfcb700270030569aaea5247fcd4dd734de2b303cfba4a', '0x33434ad846cdd5f23eb73ff09fe6fddd568284a0fb7d1be20ee482f044dabe2', '0x79dc0da7c54b95f10aa182ad0a46400db63156920adb65eca2654c0945a463', '0x2', '0x17fc658b4a0e68136cfcb700270030569aaea5247fcd4dd734de2b303cfba4a', '0x0'], 'caller_address': '0x0', 'class_hash': '0x25ec026985a3bf9d0cc1fe17326b245dfdc3ff89b8fde106542a3ea56c5a918', 'entry_point_type': 'EXTERNAL', 'call_type': 'CALL', 'result': [], 'calls': [{'contract_address': '0x483a91c3778b1fa26afa2dc10a8cabc210e64e9a38d245c8b2b214f28ad9cb6', 'entry_point_selector': '0x36fcbf06cd96843058359e1a75928beacfac10727dab22a3972f0af8aa92895', 'calldata': ['0x25ec026985a3bf9d0cc1fe17326b245dfdc3ff89b8fde106542a3ea56c5a918', '0x17fc658b4a0e68136cfcb700270030569aaea5247fcd4dd734de2b303cfba4a', '0x33434ad846cdd5f23eb73ff09fe6fddd568284a0fb7d1be20ee482f044dabe2', '0x79dc0da7c54b95f10aa182ad0a46400db63156920adb65eca2654c0945a463', '0x2', '0x17fc658b4a0e68136cfcb700270030569aaea5247fcd4dd734de2b303cfba4a', '0x0'], 'caller_address': '0x0', 'class_hash': '0x33434ad846cdd5f23eb73ff09fe6fddd568284a0fb7d1be20ee482f044dabe2', 'entry_point_type': 'EXTERNAL', 'call_type': 'DELEGATE', 'result': [], 'calls': [], 'events': [], 'messages': [], 'execution_resources': {'steps': 127, 'range_check_builtin_applications': 1, 'ecdsa_builtin_applications': 1}}], 'events': [], 'messages': [], 'execution_resources': {'steps': 187, 'range_check_builtin_applications': 1, 'ecdsa_builtin_applications': 1}}, 'fee_transfer_invocation': {'contract_address': '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', 'entry_point_selector': '0x83afd3f4caedc6eebf44246fe54e38c95e3179a5ec9ea81740eca5b482d12e', 'calldata': ['0x1176a1bd84444c89232ec27754698e5d2e7e1a7f1539f12027f28b23ec9f3d8', '0x62c708e2b816', '0x0'], 'caller_address': '0x483a91c3778b1fa26afa2dc10a8cabc210e64e9a38d245c8b2b214f28ad9cb6', 'class_hash': '0xd0e183745e9dae3e4e78a8ffedcce0903fc4900beace4e0abf192d4c202da3', 'entry_point_type': 'EXTERNAL', 'call_type': 'CALL', 'result': ['0x1'], 'calls': [{'contract_address': '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', 'entry_point_selector': '0x83afd3f4caedc6eebf44246fe54e38c95e3179a5ec9ea81740eca5b482d12e', 'calldata': ['0x1176a1bd84444c89232ec27754698e5d2e7e1a7f1539f12027f28b23ec9f3d8', '0x62c708e2b816', '0x0'], 'caller_address': '0x483a91c3778b1fa26afa2dc10a8cabc210e64e9a38d245c8b2b214f28ad9cb6', 'class_hash': '0x2760f25d5a4fb2bdde5f561fd0b44a3dee78c28903577d37d669939d97036a0', 'entry_point_type': 'EXTERNAL', 'call_type': 'DELEGATE', 'result': ['0x1'], 'calls': [], 'events': [{'order': 0, 'keys': ['0x99cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9'], 'data': ['0x483a91c3778b1fa26afa2dc10a8cabc210e64e9a38d245c8b2b214f28ad9cb6', '0x1176a1bd84444c89232ec27754698e5d2e7e1a7f1539f12027f28b23ec9f3d8', '0x62c708e2b816', '0x0']}], 'messages': [], 'execution_resources': {'steps': 530, 'memory_holes': 40, 'pedersen_builtin_applications': 4, 'range_check_builtin_applications': 21}}], 'events': [], 'messages': [], 'execution_resources': {'steps': 590, 'memory_holes': 40, 'pedersen_builtin_applications': 4, 'range_check_builtin_applications': 21}}, 'constructor_invocation': {'contract_address': '0x483a91c3778b1fa26afa2dc10a8cabc210e64e9a38d245c8b2b214f28ad9cb6', 'entry_point_selector': '0x28ffe4ff0f226a9107253e17a904099aa4f63a02a5621de0576e5aa71bc5194', 'calldata': ['0x33434ad846cdd5f23eb73ff09fe6fddd568284a0fb7d1be20ee482f044dabe2', '0x79dc0da7c54b95f10aa182ad0a46400db63156920adb65eca2654c0945a463', '0x2', '0x17fc658b4a0e68136cfcb700270030569aaea5247fcd4dd734de2b303cfba4a', '0x0'], 'caller_address': '0x0', 'class_hash': '0x25ec026985a3bf9d0cc1fe17326b245dfdc3ff89b8fde106542a3ea56c5a918', 'entry_point_type': 'CONSTRUCTOR', 'call_type': 'CALL', 'result': [], 'calls': [{'contract_address': '0x483a91c3778b1fa26afa2dc10a8cabc210e64e9a38d245c8b2b214f28ad9cb6', 'entry_point_selector': '0x79dc0da7c54b95f10aa182ad0a46400db63156920adb65eca2654c0945a463', 'calldata': ['0x17fc658b4a0e68136cfcb700270030569aaea5247fcd4dd734de2b303cfba4a', '0x0'], 'caller_address': '0x0', 'class_hash': '0x33434ad846cdd5f23eb73ff09fe6fddd568284a0fb7d1be20ee482f044dabe2', 'entry_point_type': 'EXTERNAL', 'call_type': 'DELEGATE', 'result': [], 'calls': [], 'events': [{'order': 0, 'keys': ['0x10c19bef19acd19b2c9f4caa40fd47c9fbe1d9f91324d44dcd36be2dae96784'], 'data': ['0x483a91c3778b1fa26afa2dc10a8cabc210e64e9a38d245c8b2b214f28ad9cb6', '0x17fc658b4a0e68136cfcb700270030569aaea5247fcd4dd734de2b303cfba4a', '0x0']}], 'messages': [], 'execution_resources': {'steps': 148}}], 'events': [], 'messages': [], 'execution_resources': {'steps': 226, 'range_check_builtin_applications': 1}}}, 'transaction_hash': '0x4263158f4821405f58aed29b05280b7032fb76751fc41fa35e2253275e10c7'}

    parsed_traces = unpack_trace_response(constructor_trace, 480_000, 72)


empty_trace = {
    "block_number": 0,
    "tx_index": 0,
    "contract_address": b'',
    "calldata": [],
    "result": [],
    "caller_address": b'',
    "class_hash": b'',
    "entry_point_type":  None,
    "call_type": None,
    "execution_resources": {},
    "error": None,
    "decoded_outputs": None,
}


def test_trace_ordering():

    traces = [
        Trace(
            trace_address=[0],
            selector=to_bytes("015d40a3d6ca2ac30f4031e42be28da9b056fef9bb7357ac5e85627ee876e5ad"),
            function_name="__execute__",
            decoded_inputs={},
            **empty_trace
        ),
        Trace(
            trace_address=[0, 0],
            selector=b'',
            function_name="transfer",
            decoded_inputs={"from": "0x1234", "amount": 2010},
            **empty_trace
        ),
        Trace(
            trace_address=[0, 0, 1, 2],
            selector=b'',
            function_name="_internal",
            decoded_inputs={},
            **empty_trace
        ),
        Trace(
            trace_address=[0, 1],
            selector=b'',
            function_name="swap",
            decoded_inputs={"token": "0xabcd", "amount": 2100},
            **empty_trace
        ),
        Trace(
            trace_address=[0, 1, 0],
            selector=b'',
            function_name="_internal",
            decoded_inputs={},
            **empty_trace
        ),
        Trace(
            trace_address=[0, 2],
            selector=b'',
            function_name="clear_minimum",
            decoded_inputs={"min_amount_out": 2000},
            **empty_trace
        ),
        Trace(
            trace_address=[0, 3],
            selector=b'',
            function_name="clear",
            decoded_inputs={"minimum_cleared": True},
            **empty_trace
        )
    ]
    execute_trace = get_execute_trace(traces)

    assert execute_trace.selector == to_bytes("015d40a3d6ca2ac30f4031e42be28da9b056fef9bb7357ac5e85627ee876e5ad")
    assert execute_trace.trace_address == [0]

    root_child_traces = get_toplevel_child_traces(traces, [0])
    assert len(root_child_traces) == 4
    for child_trace in root_child_traces:
        assert len(child_trace.trace_address) == 2
        assert child_trace.trace_address[0] == 0

    user_operations = get_user_operations(traces)

    assert len(user_operations) == 4
    assert user_operations[0].operation_name == "transfer"
    assert user_operations[1].operation_name == "swap"
    assert user_operations[2].operation_name == "clear_minimum"
    assert user_operations[3].operation_name == "clear"
