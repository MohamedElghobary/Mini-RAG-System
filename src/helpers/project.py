from fastapi import Depends, HTTPException, Request
from helpers.jwt import get_current_user
from models.ProjectModel import ProjectModel
from models.db_schemes.minirag.schemes.user import User

async def get_current_project_id(
    current_user: User = Depends(get_current_user),
    request: Request = None
) -> int:
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one_by_user(user_id=current_user.user_id)
    return project.project_id
