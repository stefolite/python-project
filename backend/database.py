from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)
from sqlalchemy.orm import DeclarativeBase
from collections.abc import AsyncGenerator
import os
from dotenv import load_dotenv


load_dotenv()


engine = create_async_engine(os.environ["DATABASE_URL"])
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


class Base(DeclarativeBase):
    pass
