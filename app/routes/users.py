from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4

from app.common.ErrorMessage import USER_NOT_FOUND
from app.dto.users import UserPayload, UserResponse, UserSyncPayload, UserUpdatePayload
from app.config.database import SessionLocal
from app.models.userModel import User

router = APIRouter(prefix="/users", tags=["Users"])


# Dependency สำหรับ DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# CREATE user
# -----------------------------
@router.post("/create", response_model=UserResponse)
def create_user(payload: UserPayload, db: Session = Depends(get_db)):
    try:
        # ตรวจสอบ user_id_line ซ้ำ
        existing_user = db.query(User).filter(
            User.user_id_line == payload.user_id_line
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400, detail="user_id_line already exists")

        user = User(
            username=payload.username,
            picture_url=payload.picture_url,
            role=payload.role.value,
            user_id_line=payload.user_id_line,
            created_at=datetime.now()
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            picture_url=user.picture_url,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
            user_id_line=user.user_id_line
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# GET all users
# -----------------------------
@router.get("/getAll", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        UserResponse(
            user_id=u.user_id,
            username=u.username,
            picture_url=u.picture_url,
            role=u.role,
            created_at=u.created_at,
            updated_at=u.updated_at,
            user_id_line=u.user_id_line
        )
        for u in users
    ]


# -----------------------------
# GET user by user_id_line
# -----------------------------
@router.post("/{user_id_line}", response_model=UserResponse)
def sync_user(
    user_id_line: str,
    payload: UserSyncPayload,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id_line == user_id_line).first()
    if not user:
        raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

    updated = False

    if payload.username is not None and payload.username != user.username:
        user.username = payload.username
        updated = True

    if payload.picture_url is not None and payload.picture_url != user.picture_url:
        user.picture_url = payload.picture_url
        updated = True

    if payload.role is not None and payload.role.value != user.role:
        user.role = payload.role.value
        updated = True

    if updated:
        db.commit()
        db.refresh(user)

    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        picture_url=user.picture_url,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
        user_id_line=user.user_id_line
    )


# -----------------------------
# PATCH update user
# -----------------------------
@router.patch("/{user_id_line}", response_model=UserResponse)
def update_user(user_id_line: str, payload: UserUpdatePayload, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id_line == user_id_line).first()
    if not user:
        raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

    # อัปเดต field ที่มีค่าเท่านั้น
    if payload.username is not None:
        user.username = payload.username
    if payload.picture_url is not None:
        user.picture_url = payload.picture_url
    if payload.role is not None:
        user.role = payload.role.value

    # updated_at จะอัปเดตอัตโนมัติจาก SQLAlchemy
    db.commit()
    db.refresh(user)

    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        picture_url=user.picture_url,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
        user_id_line=user.user_id_line
    )


# -----------------------------
# DELETE user
# -----------------------------
@router.delete("/{user_id_line}")
def delete_user(user_id_line: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id_line == user_id_line).first()
    if not user:
        raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

    db.delete(user)
    db.commit()
    return {"message": f"User {user_id_line} deleted successfully"}
