import random
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

SAGE_GREENS = ["#3d6b4f", "#4a7c59", "#6b9468", "#87a878", "#9dc49a", "#b5ceb3"]
BURGUNDY = "#7a2332"

LIGHT = dict(bg="#fffbeb", secondary="#fef3c7", text="#5c1a1a", primary=BURGUNDY, grid="#e8d5a3")
DARK  = dict(bg="#1c1c1c", secondary="#2a2a2a", text="#f0e6d3", primary="#c4738a", grid="#3a3a3a")

TICKERS = ["AAPL", "MSFT", "GOOG", "AMZN", "NFLX", "META"]
IPO_YEAR = {"AAPL": 1980, "MSFT": 1986, "GOOG": 2004, "AMZN": 1997, "NFLX": 2002, "META": 2012}

ERA_FACTS = [
    ((2000, 2002), [
        "Between 1995 and March 2000 the Nasdaq surged 600%, then plummeted 78% by October 2002, erasing all gains. (Wikipedia: Dot-com bubble)",
        "In 1999 alone, Qualcomm shares rocketed 2,619%. Twelve other large-cap stocks each gained over 1,000% that same year. (Wikipedia: Dot-com bubble)",
        "Pets.com collapsed just nine months after its IPO in 2000, despite Amazon backing and a nationally televised sock-puppet ad campaign. (Wikipedia: Dot-com bubble)",
    ]),
    ((2003, 2006), [
        "By June 2005, Apple commanded 76% of the entire portable music device market — just four years after launching the iPod. (Wikipedia: History of Apple Inc.)",
        "The iTunes Store sold its 200 millionth song by December 2004, then hit 500 million downloads by July 2005. (Wikipedia: History of Apple Inc.)",
        "In Q1 2005 Apple earned $290 million — nearly six times the $46 million it earned in the same quarter a year earlier. (Wikipedia: History of Apple Inc.)",
    ]),
    ((2007, 2009), [
        "The Dow Jones fell 53% between October 2007 and March 2009, dropping nearly 8,000 points in its worst week in October 2008. (Wikipedia: Financial crisis of 2007–2008)",
        "Lehman Brothers’ September 2008 bankruptcy was the largest in US history, triggering a single-day market drop of 504 points. (Wikipedia: Financial crisis of 2007–2008)",
        "US household wealth fell $11 trillion in just 18 months — from $61.4 trillion in mid-2007 to $50.4 trillion by early 2009. (Wikipedia: Financial crisis of 2007–2008)",
    ]),
    ((2010, 2014), [
        "On 20 August 2012, Apple’s market cap hit a then-record $624 billion, surpassing Microsoft’s 1999 non-inflation-adjusted peak. (Wikipedia: Apple Inc.)",
        "Apple became the first publicly traded US company to reach a $1 trillion market valuation, achieving it in August 2018 after years of iPhone dominance. (Wikipedia: Apple Inc.)",
    ]),
    ((2015, 2019), [
        "In 2017 the Big Five tech companies — Apple, Alphabet, Amazon, Facebook and Microsoft — had a combined value exceeding $3.3 trillion. (Wikipedia: FAANG)",
        "Apple became the first US publicly traded company to exceed $1 trillion in market cap in August 2018, then hit $2 trillion by August 2020. (Wikipedia: Apple Inc.)",
    ]),
    ((2020, 2021), [
        "The Dow Jones lost over 2,000 points on 9 March 2020 alone — major indices dropped 20–30% in weeks, the fastest decline since 1987. (Wikipedia: COVID-19 recession)",
        "Despite the 2020 crash, most major economies’ GDP had returned to or exceeded pre-pandemic levels by April 2022. (Wikipedia: COVID-19 recession)",
        "Oil prices fell 30% in a single night on 8 March 2020 — the largest single-day drop since the 1991 Gulf War — adding to market panic. (Wikipedia: COVID-19 recession)",
    ]),
    ((2022, 2030), [
        "The Federal Reserve raised interest rates 11 times from March 2022, reaching the highest nominal rates since the early 2000s. (Wikipedia: 2022 stock market decline)",
        "The Nasdaq Composite fell 33% in 2022 — far exceeding the S&P 500’s 19% drop — as high-growth tech stocks bore the brunt of rate hikes. (Wikipedia: 2022 stock market decline)",
        "The S&P 500 fell 21% in the first half of 2022, the worst 6-month start to a year since 1970. (Wikipedia: 2022 stock market decline)",
    ]),
]

def get_era_fact(start_date, end_date):
    mid_year = (start_date.year + end_date.year) // 2
    for (era_start, era_end), facts in ERA_FACTS:
        if era_start <= mid_year <= era_end:
            return random.Random(era_start).choice(facts)
    return ERA_FACTS[-1][1][0]

def get_era_label(start_date, end_date):
    mid_year = (start_date.year + end_date.year) // 2
    for (era_start, era_end), _ in ERA_FACTS:
        if era_start <= mid_year <= era_end:
            return f"{era_start}–{era_end}"
    return f"{start_date.year}–{end_date.year}"

st.set_page_config(page_title="Stock Explorer", layout="wide")

dark_mode = st.sidebar.toggle("Dark mode", value=False)
T = DARK if dark_mode else LIGHT

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
{".stSelectbox label, .stNumberInput label { color: #ffffff !important; } .stSelectbox [data-baseweb='select'] span, .stSelectbox [data-baseweb='select'] div { color: #ffffff !important; }" if dark_mode else ""}

@media (max-width: 768px) {{
    .block-container {{
        padding: 0.75rem 0.6rem 2rem !important;
    }}
    h1  {{ font-size: 1.5rem  !important; line-height: 1.3 !important; }}
    h2  {{ font-size: 1.2rem  !important; }}
    h3  {{ font-size: 1.05rem !important; }}
    p, span, label {{ font-size: 0.95rem !important; }}
    [data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap !important;
    }}
    [data-testid="column"] {{
        width: 100% !important;
        flex: 0 0 100% !important;
        min-width: 0 !important;
    }}
    [data-testid="stSlider"] [role="slider"] {{
        width: 24px !important;
        height: 24px !important;
    }}
    .stNumberInput input, .stTextInput input {{
        min-height: 2.8rem !important;
        font-size: 1rem !important;
    }}
    [data-baseweb="select"] > div {{
        min-height: 2.8rem !important;
    }}
}}
</style>
""", unsafe_allow_html=True)

st.title("Stock Explorer")

@st.cache_data(ttl=3600, show_spinner="Fetching latest stock data from Yahoo Finance...")
def load_data():
    raw = yf.download(TICKERS, start="2000-01-01", auto_adjust=True, progress=False)
    close = raw["Close"] if not isinstance(raw.columns, pd.MultiIndex) else raw.xs("Close", axis=1, level=0)
    close.index = pd.to_datetime(close.index)
    close.index.name = "date"
    normed = close.div(close.apply(lambda col: col.dropna().iloc[0]))
    df = normed.reset_index()
    df.columns.name = None
    return df

with st.spinner("Loading data..."):
    df = load_data()

tickers = [c for c in df.columns if c != "date"]

chosen = st.sidebar.multiselect("Choose stocks", tickers, default=["AAPL", "MSFT", "GOOG"])
if not chosen:
    st.warning("Pick at least one stock from the sidebar.")
    st.stop()

late_ipos = {t: IPO_YEAR[t] for t in chosen if IPO_YEAR.get(t, 2000) > 2000}
if late_ipos:
    notes = ", ".join(f"{t} (from {y})" for t, y in late_ipos.items())
    st.caption(f"Note: some stocks have shorter histories — {notes}.")

min_date = df["date"].min().date()
max_date = df["date"].max().date()
date_range = st.slider(
    "Zoom into a period",
    min_value=min_date, max_value=max_date,
    value=(min_date, max_date), format="MMM YYYY",
)
mask = (df["date"].dt.date >= date_range[0]) & (df["date"].dt.date <= date_range[1])
dff = df[mask]

era_label = get_era_label(date_range[0], date_range[1])
st.caption(f"Showing data for **{date_range[0].strftime('%b %Y')} – {date_range[1].strftime('%b %Y')}** · era: {era_label}")

window_growth = {}
for t in chosen:
    series = dff[t].dropna()
    if len(series) >= 2:
        window_growth[t] = (series.iloc[-1] / series.iloc[0] - 1) * 100

if window_growth:
    top_ticker = max(window_growth, key=window_growth.get)
    top_growth = window_growth[top_ticker]
    st.success(f"**Top Grower** — {top_ticker} is up {top_growth:+.1f}% in the selected period")
else:
    st.info("Not enough data in the selected window to determine a top grower.")

daily_returns = dff[chosen].pct_change().dropna()
if not daily_returns.empty:
    volatility    = daily_returns.std() * 100
    most_volatile = volatility.idxmax()
    st.success(f"**Most Volatile** — {most_volatile} swung +/-{volatility[most_volatile]:.2f}% per day on average in the selected period")

for col, t in zip(st.columns(len(chosen)), chosen):
    series = dff[t].dropna()
    if len(series) >= 2:
        g = (series.iloc[-1] / series.iloc[0] - 1) * 100
        col.metric(t, f"{series.iloc[-1]:.2f}x", f"{g:+.1f}%")
    else:
        col.metric(t, "n/a", "no data")

fact = get_era_fact(date_range[0], date_range[1])
st.success(f"**Did You Know?** — {fact}")

title_font_color = "#e8ddd0" if dark_mode else T["text"]
CHART_LAYOUT = dict(
    paper_bgcolor=T["bg"],
    plot_bgcolor=T["bg"],
    font_color=T["text"],
    title_font=dict(size=22, color=title_font_color),
    margin=dict(l=40, r=40, t=60, b=40),
)

fig_line = px.line(
    dff, x="date", y=chosen,
    title=f"Normalized price — {date_range[0].strftime('%b %Y')} to {date_range[1].strftime('%b %Y')}",
    color_discrete_sequence=SAGE_GREENS, height=450,
)
fig_line.update_layout(**CHART_LAYOUT)
fig_line.update_xaxes(gridcolor=T["grid"], title="")
fig_line.update_yaxes(gridcolor=T["grid"], title="")
st.plotly_chart(fig_line, use_container_width=True)

bar_df = pd.DataFrame({"Stock": list(window_growth.keys()), "Growth (%)": list(window_growth.values())})
fig_bar = px.bar(
    bar_df, x="Stock", y="Growth (%)",
    title=f"Total growth in selected period ({era_label})",
    color="Growth (%)", color_continuous_scale=["#c8dbc9", "#6b9468", "#3d6b4f"],
    text_auto=".1f", height=450,
)
fig_bar.update_layout(**CHART_LAYOUT, coloraxis_showscale=False)
fig_bar.update_xaxes(gridcolor=T["grid"], title="")
fig_bar.update_yaxes(gridcolor=T["grid"], title="")
st.plotly_chart(fig_bar, use_container_width=True)

# ── Investment calculator ────────────────────────────────────────────
st.divider()
st.subheader("What if I had invested?")

col_stock, col_amt, col_yr = st.columns(3)
calc_ticker = col_stock.selectbox("Stock", tickers, index=tickers.index("AAPL") if "AAPL" in tickers else 0)
calc_years  = sorted(df.loc[df[calc_ticker].notna(), "date"].dt.year.unique().tolist())
amount      = col_amt.number_input("Investment amount (EUR)", min_value=1, value=1000, step=100)
year        = col_yr.selectbox("Year of investment", calc_years)

yr_df       = df.loc[df["date"].dt.year == year, calc_ticker].dropna()
start_price = yr_df.iloc[0]
end_price   = df[calc_ticker].dropna().iloc[-1]
end_date    = df["date"].iloc[-1].strftime("%b %Y")
multiplier  = end_price / start_price
final_value = amount * multiplier
profit      = final_value - amount

if profit >= 0:
    st.success(f"EUR {amount:,.0f} invested in {calc_ticker} at the start of {year} would be worth EUR {final_value:,.2f} by {end_date} — a gain of EUR {profit:,.2f} ({(multiplier-1)*100:+.1f}%)")
else:
    st.error(f"EUR {amount:,.0f} invested in {calc_ticker} at the start of {year} would be worth EUR {final_value:,.2f} by {end_date} — a loss of EUR {abs(profit):,.2f} ({(multiplier-1)*100:+.1f}%)")
