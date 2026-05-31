# AI Investment Assistant

A Streamlit stock research app with a public UI shell and private analysis engine integration.

This repository is safe to publish because proprietary recommendation, forecasting, and sentiment logic is not included here. The app calls a private backend when the following environment variables are configured:

```bash
STOCK_AI_ENGINE_URL=https://your-private-engine.example.com
STOCK_AI_ENGINE_TOKEN=your_private_engine_token
```

Without those variables, the app still loads market data and charts, but AI recommendations and forecasts fall back to neutral/unavailable responses.

## Features

- Search stocks, ETFs, and market listings.
- View live stock metadata and price charts.
- Show AI outlook, expected move, confidence, and risk when the private engine is configured.
- Open advanced forecast details in a modal without exposing engine internals.
- Manage watchlist and price alerts.
- Keep public code focused on UI, data loading, authentication, and integration contracts.

## Local Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

For Windows:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Private Engine Contract

The public app expects two private endpoints:

- `POST /forecast`
- `POST /recommendation`

Both endpoints receive JSON payloads containing market history, stock metadata, news items, and selected forecast horizon. They should return the UI-facing fields used by `utils/analysis/timesfm_forecast.py` and `utils/analysis/recommendation.py`.

The implementation of those endpoints should live in a private repository or private deployment.

## Public Repo Safety

If this project was previously committed with proprietary logic, do not simply make the existing repository public. Git history can still expose removed code.

Recommended safe options:

- Publish this branch into a fresh public repository with no old history.
- Or rewrite/remove sensitive history before changing repository visibility.

## Disclaimer

This project is for educational and personal research purposes only. It is not financial advice. Always do your own due diligence before investing.
