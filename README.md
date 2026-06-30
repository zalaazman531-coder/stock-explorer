# 📈 Stock Explorer

A Streamlit app for exploring and comparing big tech stock performance since Jan 2018. Built with Plotly's built-in dataset — no downloads required.

## Live App

**[stock-explorer0.streamlit.app](https://stock-explorer0.streamlit.app/)**

## Features

- Compare up to 6 big tech stocks (AAPL, MSFT, GOOG, AMZN, NFLX, AAPL)
- Normalized price chart — all stocks indexed to 1.00 at Jan 2018
- Top grower banner and per-stock growth metrics
- Fully interactive Plotly chart (zoom, pan, download)

## Architecture

```mermaid
graph LR
    A[("📦 Plotly\nBuilt-in\nStock Data")]
    B["⚙️ app.py\nStreamlit App"]
    C[("🐙 GitHub\nstock-explorer")]
    D["☁️ Streamlit\nCloud"]
    E[("👤 User\nBrowser")]

    A -->|"px.data.stocks()"| B
    B -->|"git push"| C
    C -->|"auto-deploy"| D
    D -->|"https://stock-explorer0.streamlit.app"| E

    style A fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px
    style C fill:#f3f4f6,stroke:#6b7280,stroke-width:2px
    style D fill:#ede9fe,stroke:#8b5cf6,stroke-width:2px
    style E fill:#d1fae5,stroke:#10b981,stroke-width:2px
```

## Run Locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```
