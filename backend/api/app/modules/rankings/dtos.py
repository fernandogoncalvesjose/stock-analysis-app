from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.modules.stocks.models import Recommendation


class DividendRankingItemDTO(BaseModel):
    position: int
    ticker: str
    company_name: str
    sector: str | None
    dividend_yield: Decimal | None
    payout_ratio: Decimal | None
    dividend_score: Decimal | None
    final_score: Decimal
    risk_score: Decimal | None
    recommendation: Recommendation


class DividendRankingDTO(BaseModel):
    reference_date: date | None
    items: list[DividendRankingItemDTO]
