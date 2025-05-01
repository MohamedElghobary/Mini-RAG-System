from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum
from sqlalchemy.future import select
from sqlalchemy import UUID, func

class ProjectModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance

    async def create_project(self, project: Project):
        async with self.db_client() as session:
            async with session.begin():
                session.add(project)
            await session.commit()
            await session.refresh(project)
        
        return project

    async def get_project_or_create_one(self, project_id: str, user_id: UUID):
        async with self.db_client() as session:
            async with session.begin():
                query = select(Project).where(Project.project_id == project_id)
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                if project is None:
                    project_rec = Project(
                        project_id = project_id,
                        user_id=user_id
                    )

                    project = await self.create_project(project=project_rec)
                    return project
                else:
                    return project

    async def get_all_projects(self, page: int=1, page_size: int=10):

        async with self.db_client() as session:
            async with session.begin():

                total_documents = await session.execute(select(
                    func.count( Project.project_id )
                ))

                total_documents = total_documents.scalar_one()

                total_pages = total_documents // page_size
                if total_documents % page_size > 0:
                    total_pages += 1

                query = select(Project).offset((page - 1) * page_size ).limit(page_size)
                projects = await session.execute(query).scalars().all()

                return projects, total_pages



    async def get_project_or_create_one_by_user(self, user_id: int):
        async with self.db_client() as session:
            async with session.begin():  # Transaction begins here
                # Check if the project already exists
                query = select(Project).where(Project.user_id == user_id)
                result = await session.execute(query)
                project = result.scalar_one_or_none()

                if project is None:
                    # Create a new project if it doesn't exist
                    new_project = Project(user_id=user_id)
                    session.add(new_project)  # Add the new project
                    await session.refresh(new_project)  # Refresh to get the latest state of the object
                    return new_project

                return project  # Return the existing project if found

            

    
    async def get_project_by_id(self, project_id: str):
        async with self.db_client() as session:
            async with session.begin():
                query = select(Project).where(Project.project_id == project_id)
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                
                if project:
                    print(" Project Found:", project.project_id)
                else:
                    print(" No project found with ID:", project_id)
                    
                return project
