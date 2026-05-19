INSERT INTO stocks (id, ticker, company_name, sector, exchange, is_active)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'ITUB4', 'Itau Unibanco Holding S.A.', 'Financials', 'B3', true),
  ('00000000-0000-0000-0000-000000000002', 'BBAS3', 'Banco do Brasil S.A.', 'Financials', 'B3', true)
ON CONFLICT (ticker) DO NOTHING;

INSERT INTO stock_analysis_snapshots (
    id,
    stock_id,
    ticker,
    reference_date,
    recommendation,
    composite_score,
    dividend_yield,
    payload
)
VALUES
  (
    '10000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'ITUB4',
    CURRENT_DATE,
    'BUY',
    82.50,
    0.0725,
    '{
      "score_breakdown": {
        "fundamental": 84.0,
        "dividend": 78.0,
        "technical": 81.0,
        "risk": 87.0
      },
      "ai_summary": "Itau apresenta fundamentos robustos, boa rentabilidade e distribuicao de dividendos consistente.",
      "risk_flags": []
    }'::jsonb
  ),
  (
    '10000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000002',
    'BBAS3',
    CURRENT_DATE,
    'HOLD',
    68.20,
    0.0890,
    '{
      "score_breakdown": {
        "fundamental": 70.0,
        "dividend": 86.0,
        "technical": 61.0,
        "risk": 58.0
      },
      "ai_summary": "Banco do Brasil combina dividend yield atrativo com riscos monitorados ligados ao ciclo de credito.",
      "risk_flags": ["CREDIT_CYCLE_RISK"]
    }'::jsonb
  )
ON CONFLICT (ticker, reference_date) DO UPDATE SET
    recommendation = EXCLUDED.recommendation,
    composite_score = EXCLUDED.composite_score,
    dividend_yield = EXCLUDED.dividend_yield,
    payload = EXCLUDED.payload,
    updated_at = now();
