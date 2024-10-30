import asyncio
import logging
import os
import sys
from pathlib import Path

import aiohttp
import pytest
import pytest_asyncio
from aiohttp import ClientSession
from dotenv import load_dotenv
from pytest import FixtureRequest

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False, help="run slow tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(scope="function")
def debug_logger(request: FixtureRequest) -> logging.Logger:
    log_filename = request.module.__name__.replace("tests.", "") + "." + request.function.__name__

    parent_dir = Path(__file__).parent
    log_file = parent_dir / "logs" / f"{log_filename}.log"

    formatter = logging.Formatter(
        "%(levelname)-8s | %(name)-36s | %(asctime)-15s | %(message)s \t\t (%(filename)s --> %(funcName)s)"
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger("nethermind")
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)

    logger.info("-" * 100)
    logger.info(f"\t\tInitializing New Run for Test: {request.function.__name__}")
    logger.info("-" * 100)

    return logger


@pytest.fixture()
def eth_rpc_url() -> str:
    load_dotenv()
    return os.environ["ETH_JSON_RPC"]


@pytest.fixture()
def starknet_rpc_url() -> str:
    load_dotenv()
    return os.environ["STARKNET_JSON_RPC"]


@pytest_asyncio.fixture()
async def async_http_session() -> ClientSession:
    session = ClientSession()

    return session
