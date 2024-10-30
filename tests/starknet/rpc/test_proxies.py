import pytest

from nethermind.idealis.parse.starknet.abi import (
    ADMIN_CHANGED_SELECTOR,
    UPGRADED_EVENT_SELECTOR,
    is_dispatcher_class_proxy,
)
from nethermind.idealis.types.starknet.enums import ProxyKind
from nethermind.idealis.utils import to_bytes


@pytest.mark.asyncio
async def test_open_zeppelin_event_proxy(starknet_class_decoder):
    # Proxy.cairo with no impl view function
    class_hash = to_bytes("0x01067c8f4aa8f7d6380cc1b633551e2a516d69ad3de08af1b3d82e111b4feda4")

    class_decoder = await starknet_class_decoder([class_hash])

    proxy_kind = is_dispatcher_class_proxy(class_decoder, class_hash)

    assert proxy_kind
    assert proxy_kind == ProxyKind.oz_event_proxy


@pytest.mark.asyncio
async def test_implementation_proxy(starknet_class_decoder):
    # implementation() -> ?
    class_hash = to_bytes("0x00d0e183745e9dae3e4e78a8ffedcce0903fc4900beace4e0abf192d4c202da3")

    class_decoder = await starknet_class_decoder([class_hash])

    proxy_kind = is_dispatcher_class_proxy(class_decoder, class_hash)
    assert proxy_kind
    assert proxy_kind == ProxyKind.implementation


@pytest.mark.asyncio
async def test_get_implementation_camel(starknet_class_decoder):
    # getImplementation() -> ?
    # TODO: Find class hash with getImplementation function & no OpenZeppelin Events

    class_hash = to_bytes("0x05c748a01c1f7c05712b12716d1a14e03844bd92e3ffe2624d12185d30a4912c")

    class_decoder = await starknet_class_decoder([class_hash])

    proxy_kind = is_dispatcher_class_proxy(class_decoder, class_hash)

    assert proxy_kind
    assert proxy_kind == ProxyKind.get_impl_camel


@pytest.mark.asyncio
async def test_get_implementation_snake(starknet_class_decoder):
    # get_implementation() -> ?

    class_hash = to_bytes("0x03530cc4759d78042f1b543bf797f5f3d647cde0388c33734cf91b7f7b9314a9")

    class_decoder = await starknet_class_decoder([class_hash])

    proxy_kind = is_dispatcher_class_proxy(class_decoder, class_hash)
    assert proxy_kind
    assert proxy_kind == ProxyKind.get_impl_snake


@pytest.mark.asyncio
async def test_get_implementation_hash_proxy_camel(starknet_class_decoder):
    # getImplementationHash() -> ?
    class_hash = to_bytes("0x07e35b811e3d4e2678d037b632a0c8a09a46d82185187762c0d429363e3ef9cf")

    class_decoder = await starknet_class_decoder([class_hash])

    proxy_kind = is_dispatcher_class_proxy(class_decoder, class_hash)

    assert proxy_kind
    assert proxy_kind == ProxyKind.get_hash_camel


@pytest.mark.asyncio
async def test_get_implementation_hash_snake(starknet_class_decoder):
    # get_implementation_hash() => ?
    class_hash = to_bytes("0x04f245cfc0891cba20dbe00a97a01139fda3a1c6863f651967e1d5ba72fef9b4")

    class_decoder = await starknet_class_decoder([class_hash])

    proxy_kind = is_dispatcher_class_proxy(class_decoder, class_hash)

    assert proxy_kind
    assert proxy_kind == ProxyKind.get_hash_snake
