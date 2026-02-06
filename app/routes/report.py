from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.dto.report import ReportTagRequest, ReportTagResponse
from app.utils.reportTags import build_tag_report

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/tags", response_model=ReportTagResponse)
def report_by_tags(payload: ReportTagRequest, db: Session = Depends(get_db)):
    try:
        return build_tag_report(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
