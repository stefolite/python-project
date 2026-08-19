from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)
import os
from dotenv import load_dotenv
from collections.abc import AsyncGenerator
from sqlalchemy.pool import NullPool


load_dotenv()


test_engine = create_async_engine(
    os.environ["TEST_DATABASE_URL"],
    poolclass=NullPool
)
test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)


async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as test_session:
        yield test_session


def get_test_session_factory():
    return test_session_factory
