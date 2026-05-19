from dataclasses import dataclass


@dataclass(frozen=True)
class NarrativeInput:
    ticker: str
    company_name: str
    recommendation: str
    score_breakdown: dict[str, float]
    risk_flags: list[str]


class NarrativePort:
    async def generate(self, data: NarrativeInput) -> str:
        raise NotImplementedError


class TemplateNarrativeGenerator(NarrativePort):
    async def generate(self, data: NarrativeInput) -> str:
        risks = ", ".join(data.risk_flags) if data.risk_flags else "sem riscos criticos"
        return (
            f"{data.company_name} ({data.ticker}) recebeu recomendacao "
            f"{data.recommendation}. Principais riscos monitorados: {risks}."
        )
