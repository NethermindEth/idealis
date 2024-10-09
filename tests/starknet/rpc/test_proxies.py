import pytest

from nethermind.idealis.parse.starknet.abi import is_dispatcher_impl_proxy
from nethermind.idealis.utils import to_bytes
from nethermind.starknet_abi.utils import starknet_keccak


@pytest.mark.asyncio
async def test_implementation_proxy(starknet_class_decoder):
    # implementation() -> ?
    class_hash = to_bytes("0x00d0e183745e9dae3e4e78a8ffedcce0903fc4900beace4e0abf192d4c202da3")

    class_decoder = await starknet_class_decoder([class_hash])

    is_proxy, proxy_method = is_dispatcher_impl_proxy(class_decoder, class_hash)
    assert is_proxy
    assert proxy_method == starknet_keccak(b"implementation")


@pytest.mark.asyncio
async def test_get_implementation_camel(starknet_class_decoder):
    # getImplementation() -> ?

    class_hash = to_bytes("0x05c748a01c1f7c05712b12716d1a14e03844bd92e3ffe2624d12185d30a4912c")

    class_decoder = await starknet_class_decoder([class_hash])

    is_proxy, proxy_method = is_dispatcher_impl_proxy(class_decoder, class_hash)

    assert is_proxy
    assert proxy_method == starknet_keccak(b"getImplementation")


@pytest.mark.asyncio
async def test_get_implementation_snake(starknet_class_decoder):
    # get_implementation() -> ?

    class_hash = to_bytes("0x03530cc4759d78042f1b543bf797f5f3d647cde0388c33734cf91b7f7b9314a9")

    class_decoder = await starknet_class_decoder([class_hash])

    is_proxy, proxy_method = is_dispatcher_impl_proxy(class_decoder, class_hash)
    assert is_proxy
    assert proxy_method == starknet_keccak(b"get_implementation")


@pytest.mark.asyncio
async def test_get_implementation_hash_proxy_camel(starknet_class_decoder):
    # getImplementationHash() -> ?
    class_hash = to_bytes("0x07e35b811e3d4e2678d037b632a0c8a09a46d82185187762c0d429363e3ef9cf")

    class_decoder = await starknet_class_decoder([class_hash])

    is_proxy, proxy_method = is_dispatcher_impl_proxy(class_decoder, class_hash)

    assert is_proxy
    assert proxy_method == starknet_keccak(b"getImplementationHash")


@pytest.mark.asyncio
async def test_get_implementation_hash_snake(starknet_class_decoder):
    class_hash = to_bytes("0x04f245cfc0891cba20dbe00a97a01139fda3a1c6863f651967e1d5ba72fef9b4")

    class_decoder = await starknet_class_decoder([class_hash])

    is_proxy, proxy_method = is_dispatcher_impl_proxy(class_decoder, class_hash)

    assert is_proxy
    assert proxy_method == starknet_keccak(b"get_implementation_hash")
