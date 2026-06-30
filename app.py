import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

SAGE_GREENS = ["#3d6b4f", "#4a7c59", "#6b9468", "#87a878", "#9dc49a", "#b5ceb3"]
BURGUNDY = "#7a2332"

LIGHT = dict(bg="#fffbeb", secondary="#fef3c7", text="#5c1a1a", primary=BURGUNDY, grid="#e8d5a3")
DARK  = dict(bg="#1c1c1c", secondary="#2a2a2a", text="#f0e6d3", primary="#c4738a", grid="#3a3a3a")

# Real tickers — META replaces FB (renamed 2021)
TICKERS = ["AAPL", "MSFT", "GOOG", "AMZN", "NFLX", "META"]

# IPO / listing year for each ticker (data before this year doesn't exist)
IPO_YEAR = {"AAPL": 1980, "MSFT": 1986, "GOOG": 2004, "AMZN": 1997, "NFLX": 2002, "META": 2012}

st.set_page_config(page_title="Stock Explorer", layout="wide")

dark_mode  = st.sidebar.toggle("Dark mode",  value=False)
phone_mode = st.sidebar.toggle("Phone mode", value=False)
T = DARK if dark_mode else LIGHT

# ── CSS ────────────────────────────────────────────────────────────────────────────
phone_css = """
    .block-container { padding: 0.75rem 0.6rem 2rem !important; }
    h1  { font-size: 1.5rem  !important; line-height: 1.3 !important; }
    h2  { font-size: 1.2rem  !important; }
    h3  { font-size: 1.05rem !important; }
    p, span, label { font-size: 0.95rem !important; }
    [data-testid="stSlider"] [role="slider"] { width: 22px !important; height: 22px !important; }
    .stNumberInput input, .stTextInput input { min-height: 2.6rem !important; font-size: 1rem !important; }
    [data-baseweb="select"] > div { min-height: 2.6rem !important; }
""" if phone_mode else ""

st.markdown(f"""
<style>
.stApp,
[data-testid="stAppViewContainer"] > .main {{
    background-color: {T['bg']} !important;
}}
[data-testid="stSidebar"] {{
    background-color: {T['secondary']} !important;
}}
[data-testid="stHeader"] {{
    background-color: {T['bg']} !important;
}}
p, span, label, h1, h2, h3, h4,
.stMarkdown, .stCaption,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {{
    color: {T['text']} !important;
}}
.stNumberInput input, .stTextInput input {{
    border: 1.5px solid {T['primary']} !important;
    border-radius: 6px !important;
    background-color: {T['secondary']} !important;
    color: {T['text']} !important;
}}
[data-baseweb="select"] > div {{
    border: 1.5px solid {T['primary']} !important;
    border-radius: 6px !important;
    background-color: {T['secondary']} !important;
}}
[data-baseweb="tag"] span {{
    color: #ffffff !important;
}}
{phone_css}
</style>
""", unsafe_allow_html=True)

# ── Data ───────────────────────────────────────────────────────────────────────────
st.title("Stock Explorer")

@st.cache_data(ttl=3600, show_spinner="Fetching latest stock data from Yahoo Finance...")
def load_data():
    raw = yf.download(TICKERS, start="2000-01-01", auto_adjust=True, progress=False)
    # Handle both old (<0.2) and new (>=0.2) yfinance column layouts
    close = raw["Close"] if not isinstance(raw.columns, pd.MultiIndex) else raw.xs("Close", axis=1, level=0)
    close.index = pd.to_datetime(close.index)
    close.index.name = "date"
    # Normalize each stock to 1.0 at its own first available trading day
    normed = close.div(close.apply(lambda col: col.dropna().iloc[0]))
    df = normed.reset_index()
    df.columns.name = None
    return df

with st.spinner("Loading data..."):
    df = load_data()

tickers = [c for c in df.columns if c != "date"]

# ── Sidebar ───────────────────────────────────────────────────────────────────────
chosen = st.sidebar.multiselect("Choose stocks", tickers, default=["AAPL", "MSFT", "GOOG"])
if not chosen:
    st.warning("Pick at least one stock from the sidebar.")
    st.stop()

# IPO note for stocks that didn't exist in 2000
late_ipos = {t: IPO_YEAR[t] for t in chosen if IPO_YEAR.get(t, 2000) > 2000}
if late_ipos:
    notes = ", ".join(f"{t} (from {y})" for t, y in late_ipos.items())
    st.caption(f"Note: some stocks have shorter histories — {notes}.")

# ── Date slider ─────────────────────────────────────────────────────────────────────
min_date = df["date"].min().date()
max_date = df["date"].max().date()
date_range = st.slider(
    "Zoom into a period",
    min_value=min_date, max_value=max_date,
    value=(min_date, max_date), format="MMM YYYY",
)
mask = (df["date"].dt.date >= date_range[0]) & (df["date"].dt.date <= date_range[1])
dff = df[mask]

st.caption("Each line shows price growth indexed to 1.00 at each stock's first available trading day.")

# ── Banners ───────────────────────────────────────────────────────────────────────
growth_values = {t: (df[t].dropna().iloc[-1] - 1) * 100 for t in chosen}
top_ticker    = max(growth_values, key=growth_values.get)
top_growth    = growth_values[top_ticker]
st.success(f"**Top Grower** — {top_ticker} is up {top_growth:+.1f}% since its first trading day")

daily_returns = dff[chosen].pct_change().dropna()
volatility    = daily_returns.std() * 100
most_volatile = volatility.idxmax()
st.success(f"**Most Volatile** — {most_volatile} swung +/-{volatility[most_volatile]:.2f}% per day on average in the selected period")

# ── Metric cards ────────────────────────────────────────────────────────────────────
cards_per_row = 2 if phone_mode else len(chosen)
for i in range(0, len(chosen), cards_per_row):
    row = chosen[i : i + cards_per_row]
    for col, t in zip(st.columns(len(row)), row):
        growth = (df[t].dropna().iloc[-1] - 1) * 100
        col.metric(t, f"{df[t].dropna().iloc[-1]:.2f}x", f"{growth:+.1f}%")

st.success("**Did You Know?** — Amazon started as an online bookstore in 1994. By 2000 it had expanded to music, DVDs and electronics — and its stock had already fallen over 90% from its dot-com peak.")

# ── Charts ───────────────────────────────────────────────────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor=T["bg"],
    plot_bgcolor=T["bg"],
    font_color=T["text"],
    margin=dict(l=10, r=10, t=40, b=10) if phone_mode else dict(l=40, r=40, t=50, b=40),
)
chart_h = 320 if phone_mode else 450

fig_line = px.line(
    dff, x="date", y=chosen, title="Normalized price over time (2000 – present)",
    color_discrete_sequence=SAGE_GREENS, height=chart_h,
)
fig_line.update_layout(**CHART_LAYOUT)
fig_line.update_xaxes(gridcolor=T["grid"], title="")
fig_line.update_yaxes(gridcolor=T["grid"], title="")
st.plotly_chart(fig_line, use_container_width=True)

window_growth = {t: (dff[t].dropna().iloc[-1] / dff[t].dropna().iloc[0] - 1) * 100 for t in chosen if dff[t].dropna().shape[0] > 0}
bar_df = pd.DataFrame({"Stock": list(window_growth.keys()), "Growth (%)": list(window_growth.values())})
fig_bar = px.bar(
    bar_df, x="Stock", y="Growth (%)", title="Total growth in selected period",
    color="Growth (%)", color_continuous_scale=["#c8dbc9", "#6b9468", "#3d6b4f"],
    text_auto=".1f", height=chart_h,
)
fig_bar.update_layout(**CHART_LAYOUT, coloraxis_showscale=False)
fig_bar.update_xaxes(gridcolor=T["grid"], title="")
fig_bar.update_yaxes(gridcolor=T["grid"], title="")
st.plotly_chart(fig_bar, use_container_width=True)

# ── Investment calculator ─────────────────────────────────────────────────────────
st.divider()
st.subheader("What if I had invested in AAPL?")

aapl_years = sorted(df.loc[df["AAPL"].notna(), "date"].dt.year.unique().tolist())

if phone_mode:
    amount = st.number_input("Investment amount (EUR)", min_value=1, value=1000, step=100)
    year   = st.selectbox("Year of investment", aapl_years)
else:
    col_amt, col_yr = st.columns(2)
    amount = col_amt.number_input("Investment amount (EUR)", min_value=1, value=1000, step=100)
    year   = col_yr.selectbox("Year of investment", aapl_years)

yr_df       = df.loc[df["date"].dt.year == year, "AAPL"].dropna()
start_price = yr_df.iloc[0]
end_price   = df["AAPL"].dropna().iloc[-1]
end_date    = df["date"].iloc[-1].strftime("%b %Y")
multiplier  = end_price / start_price
final_value = amount * multiplier
profit      = final_value - amount

if profit >= 0:
    st.success(f"EUR {amount:,.0f} invested in AAPL at the start of {year} would be worth EUR {final_value:,.2f} by {end_date} — a gain of EUR {profit:,.2f} ({(multiplier-1)*100:+.1f}%)")
else:
    st.error(f"EUR {amount:,.0f} invested in AAPL at the start of {year} would be worth EUR {final_value:,.2f} by {end_date} — a loss of EUR {abs(profit):,.2f} ({(multiplier-1)*100:+.1f}%)")
