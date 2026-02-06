from pydantic import BaseModel, Field
from typing import Optional, List
from app.dto.transactions import FilterMode


class ReportTagRequest(BaseModel):
    user_id_line: str = Field(..., description="LINE user id")
    mode: FilterMode = Field(..., description="today/date/month/year/range")

    date: Optional[str] = None
    month: Optional[int] = None
    year: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    top_n_enabled: bool = True
    top_n: int = Field(default=5, ge=1, le=50)
    include_others: bool = True


class ReportSummaryDto(BaseModel):
    income: float
    expense: float
    net: float


class ReportTagRowDto(BaseModel):
    tag_id: int
    tag_name: str
    income: float
    expense: float
    net: float
    percent_of_expense: float
    color_index: int


class ReportChartPointDto(BaseModel):
    x: str
    y: float
    label: Optional[str] = None


class ReportChartsDto(BaseModel):
    bar: List[ReportChartPointDto]
    donut: List[ReportChartPointDto]


class ReportTagResponse(BaseModel):
    start: str
    end: str
    summary: ReportSummaryDto
    tags: List[ReportTagRowDto]
    charts: ReportChartsDto
