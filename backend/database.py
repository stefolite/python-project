from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker
)
import os
from dotenv import load_dotenv


load_dotenv()


engine = create_async_engine(os.environ["DATABASE_URL"])
session_factory = async_sessionmaker(engine, expire_on_commit=False)
