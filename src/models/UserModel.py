from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.db_schemes.minirag.schemes.user import User  # assuming your User model is defined here
from .BaseDataModel import BaseDataModel

class UserModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        return cls(db_client)

    async def create_user(self, username: str, hashed_password: str):
        new_user = User(username=username, hashed_password=hashed_password)
        async with self.db_client() as session:
            async with session.begin():
                session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
        return new_user

    async def get_user_by_username(self, username: str):
        async with self.db_client() as session:
            query = select(User).where(User.username == username)
            result = await session.execute(query)
            return result.scalar_one_or_none()


