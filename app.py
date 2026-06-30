import pandas as pd
import plotly.express as px
import streamlit as st

SAGE_GREENS = ["#3d6b4f", "#4a7c59", "#6b9468", "#87a878", "#9dc49a", "#b5ceb3"]
BURGUNDY = "#7a2332"

LIGHT = dict(
    bg="#fffbeb", secondary="#fef3c7", text="#5c1a1a",
    primary=BURGUNDY, grid="#e8d5a3",
)
DARK = dict(
    bg="#1c1c1c", secondary="#2a2a2a", text="#f0e6d3",
    primary="#c4738a", grid="#3a3a3a",
)

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
</style>
""", unsafe_allow_html=True)

st.title("Stock Explorer")

@st.cache_data
def load_data():
    # This stock dataset is built into plotly — no file to download or push!
    df = px.data.stocks()              # columns: date + 6 big tech stocks
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()
tickers = [c for c in df.columns if c != "date"]

# Sidebar: pick which stocks to compare
chosen = st.sidebar.multiselect("Choose stocks", tickers, default=["AAPL", "MSFT", "GOOG"])
if not chosen:
    st.warning("Pick at least one stock from the sidebar.")
    st.stop()

# Date-range slider
min_date, max_date = df["date"].min().date(), df["date"].max().date()
date_range = st.slider(
    "Zoom into a period",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="MMM YYYY",
)
mask = (df["date"].dt.date >= date_range[0]) & (df["date"].dt.date <= date_range[1])
dff = df[mask]

st.caption("Prices are indexed to 1.00 at the start, so each line shows growth since Jan 2018.")

# Top grower banner (over full dataset)
growth_values = {t: (df[t].iloc[-1] - 1) * 100 for t in chosen}
top_ticker = max(growth_values, key=growth_values.get)
top_growth = growth_values[top_ticker]
st.success(f"Top grower: {top_ticker} — {top_growth:+.1f}% since Jan 2018")

# Most volatile indicator — same style as top grower
daily_returns = dff[chosen].pct_change().dropna()
volatility = daily_returns.std() * 100
most_volatile = volatility.idxmax()
st.success(f"Most volatile in selected period: {most_volatile} — daily swings of +/-{volatility[most_volatile]:.2f}% on average")

# Key numbers: total growth for each chosen stock (full dataset)
cols = st.columns(len(chosen))
for col, t in zip(cols, chosen):
    growth = (df[t].iloc[-1] - 1) * 100
    col.metric(t, f"{df[t].iloc[-1]:.2f}x", f"{growth:+.1f}%")

# Did you know — same style as top grower
st.success("Did you know? Microsoft's 1986 IPO made 3 billionaires and an estimated 12,000 millionaires among its employees.")

# Line chart + bar chart side by side
chart_col, bar_col = st.columns([3, 2])

CHART_LAYOUT = dict(
    paper_bgcolor=T["bg"],
    plot_bgcolor=T["bg"],
    font_color=T["text"],
)

with chart_col:
    fig_line = px.line(
        dff, x="date", y=chosen, title="Normalized price over time",
        color_discrete_sequence=SAGE_GREENS,
    )
    fig_line.update_layout(**CHART_LAYOUT)
    fig_line.update_xaxes(gridcolor=T["grid"])
    fig_line.update_yaxes(gridcolor=T["grid"])
    st.plotly_chart(fig_line, use_container_width=True)

with bar_col:
    window_growth = {t: (dff[t].iloc[-1] / dff[t].iloc[0] - 1) * 100 for t in chosen}
    bar_df = pd.DataFrame({"Stock": list(window_growth.keys()), "Growth (%)": list(window_growth.values())})
    fig_bar = px.bar(
        bar_df, x="Stock", y="Growth (%)", title="Total growth in selected period",
        color="Growth (%)", color_continuous_scale=["#c8dbc9", "#6b9468", "#3d6b4f"],
        text_auto=".1f",
    )
    fig_bar.update_layout(**CHART_LAYOUT, coloraxis_showscale=False)
    fig_bar.update_xaxes(gridcolor=T["grid"])
    fig_bar.update_yaxes(gridcolor=T["grid"])
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()
st.subheader("What if I had invested in AAPL?")

years = sorted(df["date"].dt.year.unique().tolist())
col_amt, col_yr = st.columns(2)
amount = col_amt.number_input("Investment amount (EUR)", min_value=1, value=1000, step=100)
year = col_yr.selectbox("Year of investment", years)

start_price = df[df["date"].dt.year == year]["AAPL"].iloc[0]
end_price = df["AAPL"].iloc[-1]
end_date = df["date"].iloc[-1].strftime("%b %Y")
multiplier = end_price / start_price
final_value = amount * multiplier
profit = final_value - amount

if profit >= 0:
    st.success(f"EUR {amount:,.0f} invested in AAPL at the start of {year} would be worth EUR {final_value:,.2f} by {end_date} — a gain of EUR {profit:,.2f} ({(multiplier-1)*100:+.1f}%)")
else:
    st.error(f"EUR {amount:,.0f} invested in AAPL at the start of {year} would be worth EUR {final_value:,.2f} by {end_date} — a loss of EUR {abs(profit):,.2f} ({(multiplier-1)*100:+.1f}%)")
