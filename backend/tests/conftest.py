import asyncio
import pytest

from backend.main import app
from backend.database import Base
from backend.models import Conversation
from backend.tests.database import (
    test_engine,
    test_session_factory
)
from backend.database import get_session, get_session_factory
from backend.tests.database import (
    get_test_session,
    get_test_session_factory
)


app.dependency_overrides[get_session] = get_test_session
app.dependency_overrides[get_session_factory] = get_test_session_factory


async def setup_database():
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    async with test_session_factory() as test_session:
        test_session.add(Conversation(id=1, name="general"))
        test_session.add(Conversation(id=2, name="python"))
        await test_session.commit()


async def teardown_database():
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def prepare_database():
    asyncio.run(setup_database())

    yield

    asyncio.run(teardown_database())
