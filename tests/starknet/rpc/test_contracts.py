import pytest

from nethermind.idealis.parse.starknet.transaction import filter_transactions_by_type
from nethermind.idealis.rpc.starknet import get_blocks_with_txns
from nethermind.idealis.rpc.starknet.classes import get_class_declarations
from nethermind.idealis.rpc.starknet.contract import (
    generate_contract_implementation,
    get_contract_upgrade,
    get_decode_class,
    get_implemented_class,
    get_proxied_felt,
    update_contract_implementation,
)
from nethermind.idealis.types.starknet.enums import ProxyKind
from nethermind.idealis.utils import to_bytes, to_hex
from nethermind.starknet_abi.utils import starknet_keccak
from tests.addresses import STARKNET_ETH


@pytest.mark.asyncio
async def test_get_contract_implementation(async_http_session, starknet_rpc_url):
    contract = to_bytes("0728e92e75852510F3Bac5914459098D8806923205D12CCE2ff7f4F6139353Ff")
    implemented_class = await get_implemented_class(
        contract,
        block_number=636_600,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
    )

    assert implemented_class == to_bytes("025ec026985a3bf9d0cc1fe17326b245dfdc3ff89b8fde106542a3ea56c5a918")

    proxied_felt = await get_proxied_felt(
        contract,
        block_number=636_600,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        proxy_method=starknet_keccak(b"get_implementation"),
    )

    assert proxied_felt == to_bytes("0x033434ad846cdd5f23eb73ff09fe6fddd568284a0fb7d1be20ee482f044dabe2")


@pytest.mark.asyncio
async def test_get_contract_deploy(starknet_rpc_url, async_http_session):
    contract = to_bytes("03156BA757f383c299Eca62dE7E34257399109c423C12334811166BAE88EaA35")

    impl_class, deploy_block = await get_contract_upgrade(
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=contract,
    )

    assert impl_class == to_bytes("025ec026985a3bf9d0cc1fe17326b245dfdc3ff89b8fde106542a3ea56c5a918")
    assert deploy_block == 7900


@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_contract_upgrade(async_http_session, starknet_rpc_url):
    contract = bytes.fromhex("03156BA757f383c299Eca62dE7E34257399109c423C12334811166BAE88EaA35")
    old_class = bytes.fromhex("025ec026985a3bf9d0cc1fe17326b245dfdc3ff89b8fde106542a3ea56c5a918")

    # https://voyager.online/tx/0x1fd22931641c4fa1cb7ca86cb46438f8950e68df5d5d6671fb1f3dcf8fdee8e
    impl_class, upgrade_block = await get_contract_upgrade(
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=contract,
        old_class=old_class,
        from_block=7900,
    )

    intermediate_class = bytes.fromhex("01a736d6ed154502257f02b1ccdf4d9d1089f80811cd6acad48e6b6a9d1f2003")

    assert impl_class == intermediate_class
    assert upgrade_block == 444_684

    # https://voyager.online/tx/0x57cd2adf15905d81060630694f20b51eb24709e8674ef27e6ac9a3939d54090
    impl_class, upgrade_block = await get_contract_upgrade(
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=contract,
        old_class=intermediate_class,
        from_block=444_684,
    )

    assert impl_class == bytes.fromhex("029927c8af6bccf3f6fda035981e765a7bdbf18a2dc0d630494f8758aa908e2b")
    assert upgrade_block == 624_759


@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_contract_history(starknet_class_decoder, async_http_session, starknet_rpc_url):
    class_a = "0x025ec026985a3bf9d0cc1fe17326b245dfdc3ff89b8fde106542a3ea56c5a918"
    class_b = "0x01a736d6ed154502257f02b1ccdf4d9d1089f80811cd6acad48e6b6a9d1f2003"
    class_c = "0x029927c8af6bccf3f6fda035981e765a7bdbf18a2dc0d630494f8758aa908e2b"

    class_decoder = await starknet_class_decoder(
        [
            to_bytes(class_a),
            to_bytes(class_b),
            to_bytes(class_c),
        ]
    )

    contract_implementation = await generate_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=bytes.fromhex("03156BA757f383c299Eca62dE7E34257399109c423C12334811166BAE88EaA35"),
        to_block=630_000,
    )

    assert contract_implementation.history == {
        "7900": {
            "proxy_class": class_a,
            "7900": "0x03e327de1c40540b98d05cbcb13552008e36f0ec8d61d46956d2f9752c294328",
            "18635": "0x033434ad846cdd5f23eb73ff09fe6fddd568284a0fb7d1be20ee482f044dabe2",
        },
        "444684": class_b,
        "624759": class_c,
    }

    assert contract_implementation.update_block == 630_000


@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_proxy_implementation_history(starknet_rpc_url, async_http_session, starknet_class_decoder):
    class_decoder = await starknet_class_decoder(
        [to_bytes("025ec026985a3bf9d0cc1fe17326b245dfdc3ff89b8fde106542a3ea56c5a918")]
    )

    contract_implementation = await generate_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=to_bytes("0728e92e75852510F3Bac5914459098D8806923205D12CCE2ff7f4F6139353Ff"),
        to_block=636_600,
    )

    assert contract_implementation.update_block == 636_600
    assert contract_implementation.history == {
        "636280": {
            "proxy_class": "0x025ec026985a3bf9d0cc1fe17326b245dfdc3ff89b8fde106542a3ea56c5a918",
            "636280": "0x033434ad846cdd5f23eb73ff09fe6fddd568284a0fb7d1be20ee482f044dabe2",
        }
    }


@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_contract_null_implementation(starknet_rpc_url, async_http_session, starknet_class_decoder):
    class_decoder = await starknet_class_decoder([])

    contract_impl = await generate_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=to_bytes("0x0329a6947da05e2b5916a4287e109d2a0bf1e8e391172b816a3a554b7453a0"),
        to_block=637_000,
    )

    assert contract_impl is None


@pytest.mark.asyncio
@pytest.mark.slow
async def test_complex_proxy_to_native_contract(starknet_rpc_url, async_http_session, starknet_class_decoder):
    starknet_eth_proxy = to_bytes("0x048624e084dc68d82076582219c7ed8cb0910c01746cca3cd72a28ecfe07e42d")

    impl_a = "0x00d0e183745e9dae3e4e78a8ffedcce0903fc4900beace4e0abf192d4c202da3"
    impl_b = "0x05ffbcfeb50d200a0677c48a129a11245a3fc519d1d98d76882d1c9a1b19c6ed"
    impl_c = "0x07f3777c99f3700505ea966676aac4a0d692c2a9f5e667f4c606b51ca1dd3420"
    proxy_impl_addr = "0x02760f25d5a4fb2bdde5f561fd0b44a3dee78c28903577d37d669939d97036a0"

    class_decoder = await starknet_class_decoder(
        [
            to_bytes(impl_a),
            to_bytes(impl_b),
            to_bytes(impl_c),
            to_bytes(proxy_impl_addr),
        ],
    )

    starknet_eth_impl = await generate_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=STARKNET_ETH,
        to_block=637_000,
    )

    proxy_impl = await generate_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=starknet_eth_proxy,
        to_block=637_000,
    )

    assert starknet_eth_impl.history == {
        "1407": {
            "proxy_class": impl_a,
            "1407": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "1472": "0x038c25d465b4c5edf024aefae63dc2f6266dd8ba303763de00da4430b5ee8759",
            "2823": to_hex(starknet_eth_proxy, pad=32),
            "541380": "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
        },
        "541384": impl_b,
        "629092": impl_c,
    }

    assert proxy_impl.history == {"2810": proxy_impl_addr}

    contract_mapping = {
        STARKNET_ETH: starknet_eth_impl,
        starknet_eth_proxy: proxy_impl,
    }

    assert get_decode_class(STARKNET_ETH, contract_mapping, 3000) == to_bytes(proxy_impl_addr)

    assert get_decode_class(STARKNET_ETH, contract_mapping, 600_000) == to_bytes(impl_b)


@pytest.mark.asyncio
@pytest.mark.slow
async def test_update_contract_impl(starknet_rpc_url, async_http_session, starknet_class_decoder):
    class_decoder = await starknet_class_decoder(
        [
            to_bytes("0x00d0e183745e9dae3e4e78a8ffedcce0903fc4900beace4e0abf192d4c202da3"),
            to_bytes("0x05ffbcfeb50d200a0677c48a129a11245a3fc519d1d98d76882d1c9a1b19c6ed"),
            to_bytes("0x07f3777c99f3700505ea966676aac4a0d692c2a9f5e667f4c606b51ca1dd3420"),
            to_bytes("0x02760f25d5a4fb2bdde5f561fd0b44a3dee78c28903577d37d669939d97036a0"),
        ],
    )

    full_generation_impl = await generate_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=STARKNET_ETH,
        to_block=640_000,
    )

    incremental_impl = await generate_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=STARKNET_ETH,
        to_block=200_000,
    )

    incremental_impl = await update_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_history=incremental_impl,
        to_block=300_000,
    )

    incremental_impl = await update_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_history=incremental_impl,
        to_block=600_000,
    )

    incremental_impl = await update_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_history=incremental_impl,
        to_block=640_000,
    )

    assert full_generation_impl == incremental_impl


@pytest.mark.slow
@pytest.mark.asyncio
async def test_oz_event_proxy_contract_implementation(starknet_rpc_url, async_http_session, starknet_class_decoder):
    # Proxy.cairo with no impl view function
    class_hash = to_bytes("0x01067c8f4aa8f7d6380cc1b633551e2a516d69ad3de08af1b3d82e111b4feda4")
    starknet_id_naming_contract = to_bytes("0x06ac597f8116f886fa1c97a23fa4e08299975ecaf6b598873ca6792b9bbfb678")

    class_decoder = await starknet_class_decoder([class_hash])
    contract_impl = await generate_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=starknet_id_naming_contract,
        to_block=620_000,
    )

    assert contract_impl.history == {
        "12628": {
            "proxy_class": "0x01067c8f4aa8f7d6380cc1b633551e2a516d69ad3de08af1b3d82e111b4feda4",
            "12628": "0x0280601107dd4067877f74b646c903a51852202bf6f5a3c4dda54e367ca16910",
            "15913": "0x000836790d91c2ac81755225055bfd06d00c2fd75391d71a90cf6b938b9bd5ff",
            "18060": "0x062d0d938c2c4c378a96de3d5d0504d17a5e6041b1fecb60af5a8d3f192bf388",
            "18806": "0x059739125413cd34b2e0e8282b6e0a693c69d565b013479510bff5da64dff85b",
            "19270": "0x048d5e541556b53836a58854a08f6e095f9551c5cb4089d4c3113000fd8ae1b1",
            "32185": "0x002d4c25ad2cefa737b06c1eac451c208b206c8d231ff550f8794c8efc676acb",
            "46181": "0x01797f258b41e27fa783bbe3ae13559a4507fd084d7205584a57c4ed246b2248",
            "137685": "0x0777ba3d99380d889d4cee7148a35c608c18bb4c993643cdfa013143346d9753",
            "194696": "0x07410053c3380c2c8141cb77776db8770c520139de7ea42bbf54bee291664113",
            "312211": "0x028a26116e6ede7e2c78e5a8971664326c8c2825039be7e9ff303439a7764724",
            "321725": "0x053f5080443e2aa66464b3f8bcbb59045fd2f2007967ba9a5c455dbd92a4867f",
            "445515": "0x00e092ac53e8a8752b96bcb6225f857ec10c571da5d5574a01bd3664b66fea22",
        },
        "607823": "0x05d7ef4ab1430f353a3b90d41b9cd56d7469155801d94355d397e1a8035ad570",
        "608390": "0x026abdaa32cdf02d10f6383d2ec3a5312ee78203a5f2614b9f186dedb37dcb26",
    }


# In this block, there is a deploy transaction at tx_idx 7 which creates a new class.
# At tx_idx 18, there is a declare transaction which then also declares this class.
# Both transactions are successful & accepted on L1.
# https://voyager.online/tx/0x01e282582472db2c8972e78b3e86cfea77038898f0f5f71fba5ebda3273eda72
# https://voyager.online/tx/0x05924ebd1b6dcec81636028d1e2ad2447dbffd50a46766ecd5832dc27d368638
@pytest.mark.asyncio
async def test_duplicate_class_declaration_parsing(async_http_session, starknet_rpc_url):
    _, transactions, _, _ = await get_blocks_with_txns([3806], starknet_rpc_url, async_http_session)

    filtered_txns = filter_transactions_by_type(transactions)

    class_declarations = get_class_declarations(
        filtered_txns.declare_transactions, filtered_txns.deploy_transactions, starknet_rpc_url
    )

    assert len(class_declarations) == 3
    assert (
        class_declarations[0].declare_transaction_hash.hex()
        == "05924ebd1b6dcec81636028d1e2ad2447dbffd50a46766ecd5832dc27d368638"
    )
    assert (
        class_declarations[1].declare_transaction_hash.hex()
        == "0068627beb69ae89caf55973e38b2870a1b23c9401d6c03712a34cfe11ffea7f"
    )
    assert (
        class_declarations[2].declare_transaction_hash.hex()
        == "038af55ce5bb6a3a5bf8381741199344c3c2da132b2a99bb2e3b49d5032a1753"
    )


@pytest.mark.slow
@pytest.mark.asyncio
async def test_event_and_function_proxies_match(starknet_class_decoder, async_http_session, starknet_rpc_url):
    avnu_exchange_contract = to_bytes("0x04270219d365d6b017231b52e92b3fb5d7c8378b05e9abc97724537a80e93b0f")

    impl_a = to_bytes("0x05ee939756c1a60b029c594da00e637bf5923bf04a86ff163e877e899c0840eb")

    class_decoder = await starknet_class_decoder([impl_a])

    proxy_function_impl = await generate_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=avnu_exchange_contract,
        to_block=300_000,
    )

    # Remove get_implementation function from Decoder, will change ProxyKind to OZ Event Proxy
    del class_decoder.class_ids[impl_a[-8:]].function_ids[ProxyKind.get_hash_camel.function_selector()[-8:]]

    oz_event_proxy_impl = await generate_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=avnu_exchange_contract,
        to_block=300_000,
    )

    assert proxy_function_impl == oz_event_proxy_impl
