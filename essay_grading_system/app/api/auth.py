# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.users import UserCreate, UserLogin, TokenResponse, UserResponse
from app.services.auth_service import AuthService, get_current_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    user = AuthService.register_user(db, user_data)
    access_token = AuthService.create_access_token({"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
        "user_id": user.id
    }


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = AuthService.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 创建令牌
    access_token = AuthService.create_access_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
        "user_id": user.id
    }


# 可以添加其他认证相关接口
@router.post("/logout")
async def logout():
    """用户退出登录（前端删除token即可）"""
    return {"message": "退出成功"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user=Depends(get_current_user)
):
    """获取当前登录用户信息"""
    return current_user
