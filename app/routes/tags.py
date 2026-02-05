from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.config.database import SessionLocal
from app.dto.tags import TagCreatePayload
from app.models.tagModel import Tag
from app.utils.tags import make_slug, normalize_tag_name

router = APIRouter(prefix="/tags", tags=["Tags"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def search_tags(
    user_id_line: str = Query(...),
    q: str = Query("", max_length=50),
    db: Session = Depends(get_db),
):
    query = db.query(Tag).filter(Tag.user_id_line == user_id_line)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(Tag.name.ilike(like))
    return query.order_by(Tag.name.asc()).limit(30).all()


@router.post("")
def create_tag(payload: TagCreatePayload, db: Session = Depends(get_db)):
    name = normalize_tag_name(payload.name)
    if not name:
        raise HTTPException(status_code=400, detail="Tag name is required")

    slug = make_slug(name)

    existing = db.query(Tag).filter(
        Tag.user_id_line == payload.userIdLine,
        Tag.slug == slug
    ).first()

    if existing:
        return existing

    tag = Tag(user_id_line=payload.userIdLine, name=name, slug=slug)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag
