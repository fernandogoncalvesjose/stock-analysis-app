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
    composite_score: Decimal
    recommendation: Recommendation


class DividendRankingDTO(BaseModel):
    reference_date: date | None
    items: list[DividendRankingItemDTO]
