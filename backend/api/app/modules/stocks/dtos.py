from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.stocks.models import Recommendation


class StockDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    company_name: str
    sector: str | None = None
    exchange: str
    is_active: bool


class ScoreBreakdownDTO(BaseModel):
    fundamental: Decimal | None = None
    dividend: Decimal | None = None
    technical: Decimal | None = None
    risk: Decimal | None = None


class StockSnapshotDTO(BaseModel):
    ticker: str
    company_name: str
    sector: str | None
    reference_date: date
    recommendation: Recommendation
    composite_score: Decimal = Field(ge=0, le=100)
    dividend_yield: Decimal | None = None
    score_breakdown: ScoreBreakdownDTO = Field(default_factory=ScoreBreakdownDTO)
    ai_summary: str | None = None
    risk_flags: list[str] = Field(default_factory=list)
    updated_at: datetime


class StockSearchResultDTO(BaseModel):
    ticker: str
    company_name: str
    sector: str | None = None


class StockScoreDTO(BaseModel):
    ticker: str
    reference_date: date
    dividend_score: Decimal | None = None
    value_score: Decimal | None = None
    growth_score: Decimal | None = None
    profitability_score: Decimal | None = None
    risk_score: Decimal | None = None
    final_score: Decimal = Field(ge=0, le=100)
    recommendation: Recommendation
    payload: dict = Field(default_factory=dict)


class RecalculateResponseDTO(BaseModel):
    ok: bool
    result: StockScoreDTO | None = None
    reason: str | None = None
    error: str | None = None
