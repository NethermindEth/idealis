from nethermind.idealis.parse.starknet.transaction import parse_transaction_with_receipt
from nethermind.idealis.rpc.starknet.classes import (
    get_class_declarations,
    get_contract_deployments,
)
from nethermind.idealis.utils import to_bytes
from nethermind.idealis.utils.starknet import PessimisticDecoder


def test_parse_deploy_class_declaration(starknet_rpc_url):
    tx_and_receipt_json = {
        "transaction": {
            "transaction_hash": "0x4026b1598e5915737d439e8b8493cce9e47a5a334948e28f55c391bc2e0c2e2",
            "type": "DEPLOY",
            "version": "0x0",
            "contract_address_salt": "0x5b942baf7da405bf68dd37e64f519e0636b7b5342f59b22609ad71f97da3a7e",
            "class_hash": "0x74ddc960b4568092956dade86c2919a6f5c06524beefcb5a0a7b25ee3db250c",
            "constructor_calldata": [],
        },
        "receipt": {
            "type": "DEPLOY",
            "transaction_hash": "0x4026b1598e5915737d439e8b8493cce9e47a5a334948e28f55c391bc2e0c2e2",
            "actual_fee": {"amount": "0x0", "unit": "WEI"},
            "execution_status": "SUCCEEDED",
            "finality_status": "ACCEPTED_ON_L1",
            "messages_sent": [],
            "events": [],
            "contract_address": "0x7e568faae3cb2321e36655fb42b6bdd2b4834269b8136d7ccf2faa4fae74c25",
            "execution_resources": {"steps": 0, "data_availability": {"l1_gas": 0, "l1_data_gas": 0}},
        },
    }

    transaction_response, _, _ = parse_transaction_with_receipt(
        tx_and_receipt_json, block_number=146, transaction_index=9, block_timestamp=1638108551
    )

    class_declaration = get_class_declarations(
        declare_transactions=[], deploy_transactions=[transaction_response], json_rpc=starknet_rpc_url
    )

    assert len(class_declaration) == 1

    assert class_declaration[0].declare_transaction_hash == to_bytes(
        "0x4026b1598e5915737d439e8b8493cce9e47a5a334948e28f55c391bc2e0c2e2", pad=32
    )
    assert class_declaration[0].class_hash == to_bytes(
        "0x74ddc960b4568092956dade86c2919a6f5c06524beefcb5a0a7b25ee3db250c", pad=32
    )

    assert class_declaration[0].is_account == False
    assert class_declaration[0].is_proxy == False
    assert class_declaration[0].is_erc_20 == False


def test_parse_erc20_declare(starknet_rpc_url):
    tx_and_receipt_json = {
        "transaction": {
            "transaction_hash": "0x48d03ccfd58eb2a468779a7427a738e98dcb02a69923a185bd4a89d5a9985ef",
            "type": "DECLARE",
            "version": "0x2",
            "nonce": "0x2",
            "max_fee": "0x32a00eba106e79",
            "class_hash": "0x7f3777c99f3700505ea966676aac4a0d692c2a9f5e667f4c606b51ca1dd3420",
            "sender_address": "0x68e1e2e518c14fb0e19b56ffcefa5eb4d40abfea76d777b2847e062e7372dcf",
            "signature": [
                "0x301ef5239d00fdd58cac7a788e2de41c05601a978b0762aecf7ff98ed14a853",
                "0x3b550c193d59751c7e245b3ba0eb3431af9d803844544b63e2d7173782ee2f3",
            ],
            "compiled_class_hash": "0x5f1f3bae96c8f74d120be0e37ea8105d1a23d2f8ae2f65f254d677bb4375746",
        },
        "receipt": {
            "type": "DECLARE",
            "transaction_hash": "0x48d03ccfd58eb2a468779a7427a738e98dcb02a69923a185bd4a89d5a9985ef",
            "actual_fee": {"amount": "0x30dc06eafdfc21", "unit": "WEI"},
            "execution_status": "SUCCEEDED",
            "finality_status": "ACCEPTED_ON_L1",
            "messages_sent": [],
            "events": [
                {
                    "from_address": "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
                    "keys": ["0x99cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9"],
                    "data": [
                        "0x68e1e2e518c14fb0e19b56ffcefa5eb4d40abfea76d777b2847e062e7372dcf",
                        "0x1176a1bd84444c89232ec27754698e5d2e7e1a7f1539f12027f28b23ec9f3d8",
                        "0x30dc06eafdfc21",
                        "0x0",
                    ],
                }
            ],
            "execution_resources": {
                "steps": 3521,
                "pedersen_builtin_applications": 16,
                "range_check_builtin_applications": 75,
                "ec_op_builtin_applications": 3,
                "data_availability": {"l1_gas": 0, "l1_data_gas": 192},
            },
        },
    }

    transaction_response, _, _ = parse_transaction_with_receipt(
        tx_and_receipt_json, block_number=629084, transaction_index=25, block_timestamp=1711956804
    )

    class_declarations = get_class_declarations(
        declare_transactions=[transaction_response], deploy_transactions=[], json_rpc=starknet_rpc_url
    )

    assert len(class_declarations) == 1

    assert class_declarations[0].class_hash == to_bytes(
        "0x7f3777c99f3700505ea966676aac4a0d692c2a9f5e667f4c606b51ca1dd3420"
    )
    assert class_declarations[0].declare_transaction_hash == to_bytes(
        "0x48d03ccfd58eb2a468779a7427a738e98dcb02a69923a185bd4a89d5a9985ef"
    )

    assert class_declarations[0].is_erc_20 == True
    assert class_declarations[0].is_account == False


def test_parse_account_class(starknet_rpc_url):
    tx_and_receipt_json = {
        "transaction": {
            "transaction_hash": "0x1d9107b0ca6d3e612ae22a3e03b83390c8e864c62d8f52471d3bb89dfa35e6b",
            "type": "DECLARE",
            "version": "0x2",
            "nonce": "0x395a",
            "max_fee": "0x59308c296ae7",
            "class_hash": "0x816dd0297efc55dc1e7559020a3a825e81ef734b558f03c83325d4da7e6253",
            "sender_address": "0x2cb12823ceda26957cdd333a67afe1b8f760fb5558472ff3518635c91a7164",
            "signature": [
                "0x3862595f282bfab002ae2dd78d000654ed7461f32074dbcc58e3f96006bf32",
                "0x23acae7ed3ba90118012c3a3b3e5d5155c3845cadc86e48c30e86e612c8639f",
            ],
            "compiled_class_hash": "0x3b3c33049515b020e435d5803b2b8a6915398cbcd8f79ca545a04c286c5084b",
        },
        "receipt": {
            "type": "DECLARE",
            "transaction_hash": "0x1d9107b0ca6d3e612ae22a3e03b83390c8e864c62d8f52471d3bb89dfa35e6b",
            "actual_fee": {"amount": "0x23ad04dd5df6", "unit": "WEI"},
            "execution_status": "SUCCEEDED",
            "finality_status": "ACCEPTED_ON_L1",
            "messages_sent": [],
            "events": [
                {
                    "from_address": "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
                    "keys": ["0x99cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9"],
                    "data": [
                        "0x2cb12823ceda26957cdd333a67afe1b8f760fb5558472ff3518635c91a7164",
                        "0x1176a1bd84444c89232ec27754698e5d2e7e1a7f1539f12027f28b23ec9f3d8",
                        "0x23ad04dd5df6",
                        "0x0",
                    ],
                }
            ],
            "execution_resources": {
                "steps": 3646,
                "pedersen_builtin_applications": 15,
                "range_check_builtin_applications": 82,
                "ecdsa_builtin_applications": 1,
                "data_availability": {"l1_gas": 0, "l1_data_gas": 0},
            },
        },
    }

    transaction_response, _, _ = parse_transaction_with_receipt(
        tx_and_receipt_json, block_number=532944, transaction_index=54, block_timestamp=1707131436
    )

    class_declaration = get_class_declarations(
        declare_transactions=[transaction_response], deploy_transactions=[], json_rpc=starknet_rpc_url
    )

    assert len(class_declaration) == 1

    assert class_declaration[0].declare_transaction_hash == to_bytes(
        "0x1d9107b0ca6d3e612ae22a3e03b83390c8e864c62d8f52471d3bb89dfa35e6b"
    )
    assert class_declaration[0].is_erc_20 == False
    assert class_declaration[0].is_account == True
    assert class_declaration[0].declaration_block == 532944
    assert class_declaration[0].declaration_timestamp == 1707131436


def test_deploy_contract_parsing(starknet_rpc_url):
    tx_and_receipt_json = {
        "transaction": {
            "transaction_hash": "0x7f4249ef834c586b75855176bb156411f59f7fa572834cb9e2f231efe054224",
            "type": "DEPLOY",
            "version": "0x0",
            "contract_address_salt": "0x80b2b7cc679e8922a7c39a1280f7f33105fa476d81c86f98f023fdc6f5068c",
            "class_hash": "0x10455c752b86932ce552f2b0fe81a880746649b9aee7e0d842bf3f52378f9f8",
            "constructor_calldata": [
                "0x67c2665fbdd32ded72c0665f9658c05a5f9233c8de2002b3eba8ae046174efd",
                "0x2221def5413ed3e128051d5dff3ec816dbfb9db4454b98f4aa47804cb7a13d2",
            ],
        },
        "receipt": {
            "type": "DEPLOY",
            "transaction_hash": "0x7f4249ef834c586b75855176bb156411f59f7fa572834cb9e2f231efe054224",
            "actual_fee": {"amount": "0x0", "unit": "WEI"},
            "execution_status": "SUCCEEDED",
            "finality_status": "ACCEPTED_ON_L1",
            "messages_sent": [],
            "events": [],
            "contract_address": "0x4d56b8ac0ed905936da10323328cba5def12957a2936920f043d8bf6a1e902d",
            "execution_resources": {"steps": 29, "data_availability": {"l1_gas": 0, "l1_data_gas": 0}},
        },
    }

    transaction_response, _, _ = parse_transaction_with_receipt(
        tx_and_receipt_json, block_number=3, transaction_index=30, block_timestamp=1637091683
    )

    assert transaction_response.contract_address == to_bytes(
        "0x4d56b8ac0ed905936da10323328cba5def12957a2936920f043d8bf6a1e902d", pad=32
    )
    assert transaction_response.class_hash == to_bytes(
        "0x10455c752b86932ce552f2b0fe81a880746649b9aee7e0d842bf3f52378f9f8", pad=32
    )

    class_deployments = get_contract_deployments(
        deploy_account_transactions=[],
        deploy_transactions=[transaction_response],
        decoding_dispatcher=PessimisticDecoder(starknet_rpc_url),
    )

    assert len(class_deployments) == 1

    assert class_deployments[0].contract_address == to_bytes(
        "0x4d56b8ac0ed905936da10323328cba5def12957a2936920f043d8bf6a1e902d", pad=32
    )
    assert class_deployments[0].initial_class_hash == to_bytes(
        "0x10455c752b86932ce552f2b0fe81a880746649b9aee7e0d842bf3f52378f9f8", pad=32
    )
    assert class_deployments[0].constructor_args == {
        "address": "0x067c2665fbdd32ded72c0665f9658c05a5f9233c8de2002b3eba8ae046174efd",
        "value": "0x02221def5413ed3e128051d5dff3ec816dbfb9db4454b98f4aa47804cb7a13d2",
    }


def test_proxy_detection():
    # TODO: Assert that valid proxies are handled correctly...

    # The starknet ID proxy contract does not have a get_implementation view method....
    # https://voyager.online/class/0x01067c8f4aa8f7d6380cc1b633551e2a516d69ad3de08af1b3d82e111b4feda4
    # To detect proxies, add checks for constructor arguments and Upgraded events???

    pass
