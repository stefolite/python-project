from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv


load_dotenv()


engine = create_async_engine(os.environ.get("DATABASE_URL"))
