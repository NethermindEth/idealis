import pytest
from starknet_abi.utils import starknet_keccak

from nethermind.idealis.rpc.starknet.contract import (
    generate_contract_implementation,
    get_contract_upgrade,
    get_decode_class,
    get_implemented_class,
    get_proxied_felt,
    update_contract_implementation,
)
from nethermind.idealis.utils import to_bytes, to_hex


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
    starknet_eth_address = to_bytes("0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7")
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
        contract_address=starknet_eth_address,
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
        starknet_eth_address: starknet_eth_impl,
        starknet_eth_proxy: proxy_impl,
    }

    assert get_decode_class(starknet_eth_address, contract_mapping, 3000) == to_bytes(proxy_impl_addr)

    assert get_decode_class(starknet_eth_address, contract_mapping, 600_000) == to_bytes(impl_b)


@pytest.mark.asyncio
@pytest.mark.slow
async def test_update_contract_impl(starknet_rpc_url, async_http_session, starknet_class_decoder):
    starknet_eth_address = to_bytes("0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7")

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
        contract_address=starknet_eth_address,
        to_block=640_000,
    )

    incremental_impl = await generate_contract_implementation(
        class_decoder=class_decoder,
        aiohttp_session=async_http_session,
        rpc_url=starknet_rpc_url,
        contract_address=starknet_eth_address,
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
