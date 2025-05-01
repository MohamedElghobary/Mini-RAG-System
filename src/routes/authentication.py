from fastapi import APIRouter, Depends, Request, HTTPException
from models.UserModel import UserModel
from typing import Annotated
from helpers.password import hash_password, verify_password
from helpers.jwt import create_token, get_current_user
from routes.schemes.auth import UserSignup, UserLogin

auth_router = APIRouter(
    prefix="/authentication",
    tags=["Auth"]
    )

@auth_router.post("/signup")
async def signup(user: UserSignup, request: Request):
    user_model = UserModel(request.app.db_client)
    existing_user = await user_model.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed = hash_password(user.password)
    new_user = await user_model.create_user(user.username, hashed)
    return {"user_id": new_user.user_id, "username": new_user.username}

@auth_router.post("/login")
async def login(user: UserLogin, request: Request):
    user_model = UserModel(request.app.db_client)
    db_user = await user_model.get_user_by_username(user.username)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(db_user.user_id)
    return {"access_token": token, "token_type": "bearer"}


@auth_router.get("/me")
async def get_me(current_user: Annotated[dict, Depends(get_current_user)]):
    return {"user_id": current_user["user_id"]}