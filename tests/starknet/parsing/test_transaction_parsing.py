# fmt: off
import pytest

from nethermind.idealis.parse.starknet.transaction import (
    parse_transaction,
    parse_transaction_responses,
)
from nethermind.idealis.types.starknet.enums import StarknetTxType


@pytest.mark.skip("TODO")
def test_version_0_invoke():
    pass


def test_version_1_invoke():
    tx_json = {'transaction_hash': '0x1139643045af8ad540f84685aad59115073f7aae58b1c46fd57cffdef438657', 'type': 'INVOKE', 'version': '0x1', 'nonce': '0x45', 'max_fee': '0x8bb8f74723a7', 'sender_address': '0x2d46760b9253183269588e29123d5cb5770bbde47049d3369be3a21fb9a1f1c', 'signature': ['0x1', '0x5fa4f83501d55b68af607f8f0e16848052738d856d511c2ab25bfbb7c28b85c', '0x26d858383b0ed587d031d59007917a8d1df018cab20786f3456507b808c0f18'], 'calldata': ['0x1', '0x7c2e1e733f28daa23e78be3a4f6c724c0ab06af65f6a95b5e0545215f1abc1b', '0x3e8cfd4725c1e28fa4a6e3e468b4fcf75367166b850ac5f04e33ec843e82c1', '0x4', '0x2d46760b9253183269588e29123d5cb5770bbde47049d3369be3a21fb9a1f1c', '0x2d46760b9253183269588e29123d5cb5770bbde47049d3369be3a21fb9a1f1c', '0x1043d272d8b0538000', '0x0']}

    tx_response = parse_transaction(tx_json, 100, 0, 1234)
    parsed_tx = parse_transaction_responses([tx_response])[0]

def test_version_3_invoke():
    tx_json = {'transaction_hash': '0x7c04fd44c3f66121ab430e369d57e59c73809cf235dd182a3ae6342576dfdb2', 'type': 'INVOKE', 'version': '0x3', 'nonce': '0x16', 'sender_address': '0x1b9863ced0b4a85c77d65c66e81f84e1c4d41161a2ff14f36ec50f59af21d3f', 'signature': ['0xfc430e59f3d9a2f7e1879a5970dce226de2bc27229be569a357d0fa368b701', '0x63c8644310425c15bb0d0a9c9468fabe995709cca4a35250b8966dc712db62'], 'calldata': ['0x5', '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', '0x83afd3f4caedc6eebf44246fe54e38c95e3179a5ec9ea81740eca5b482d12e', '0x3', '0x2e0af29598b407c8716b17f6d2795eca1b471413fa03fb145a5e33722184067', '0xe4c0d39f63dac', '0x0', '0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8', '0x83afd3f4caedc6eebf44246fe54e38c95e3179a5ec9ea81740eca5b482d12e', '0x3', '0x2e0af29598b407c8716b17f6d2795eca1b471413fa03fb145a5e33722184067', '0xb71b00', '0x0', '0x2e0af29598b407c8716b17f6d2795eca1b471413fa03fb145a5e33722184067', '0x38c3244e92da3bec5e017783c62779e3fd5d13827570dc093ab2a55f16d41b9', '0xa', '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', '0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8', '0x20c49ba5e353f80000000000000000', '0x3e8', '0x0', '0x12afef8', '0x1', '0x12a81f8', '0x1', '0x1792a6fec705', '0x2e0af29598b407c8716b17f6d2795eca1b471413fa03fb145a5e33722184067', '0x292f3f4df7749c2ae1fdc3379303c2e6caa9bbc3033ee67709fde5b77f65836', '0x1', '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7', '0x2e0af29598b407c8716b17f6d2795eca1b471413fa03fb145a5e33722184067', '0x292f3f4df7749c2ae1fdc3379303c2e6caa9bbc3033ee67709fde5b77f65836', '0x1', '0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8'], 'resource_bounds': {'l1_gas': {'max_amount': '0x192', 'max_price_per_unit': '0x4892a4a62bba'}, 'l2_gas': {'max_amount': '0x0', 'max_price_per_unit': '0x0'}}, 'tip': '0x0', 'paymaster_data': [], 'account_deployment_data': [], 'nonce_data_availability_mode': 'L1', 'fee_data_availability_mode': 'L1'}

    parsed_tx = parse_transaction(tx_json, 100, 0, 1234)


@pytest.mark.skip("TODO")
def test_version_0_declare():
    pass


@pytest.mark.skip("TODO")
def test_version_1_declare():
    pass


def test_version_2_declare():
    tx_json = {'transaction_hash': '0x449eac40c57bae0651ab3ccd853444c39fc796128c173ad8846eb2b3faa9c57', 'type': 'DECLARE', 'version': '0x2', 'nonce': '0x1', 'max_fee': '0x434bd1e9bf6f4c', 'class_hash': '0x5555b911c145c702880e59bce19957f2f0b68d619363cfc24dda117a8f48235', 'sender_address': '0x568198d582d35b2afae25c4574edf47e5d0510aa47c3115384b524ecd2a184c', 'signature': ['0x6fa91ba602e8e3070efdce0e20762ba7eae0ec2e125deee2e2c3187de82d29b', '0x426881b1a11db0487164d0f461d221ea366dd595eae55be3be09b69d4f59761'], 'compiled_class_hash': '0x66203890694f0bf313358677bd13b366524acfe0184da871acad2748e57f933'}

    parsed_tx = parse_transaction(tx_json, 100, 0, 1234)

    assert parsed_tx.type == StarknetTxType.declare
    assert parsed_tx.version == 2
    assert parsed_tx.class_hash == bytes.fromhex('05555b911c145c702880e59bce19957f2f0b68d619363cfc24dda117a8f48235')


@pytest.mark.skip("TODO")
def test_version_3_declare():
    pass


@pytest.mark.skip("TODO")
def test_version_0_deploy_account():
    pass


@pytest.mark.skip("TODO")
def test_version_3_deploy_account():
    pass


@pytest.mark.skip("TODO")
def test_version_0_deploy():
    pass
