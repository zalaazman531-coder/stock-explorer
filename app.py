import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Stock Explorer", layout="wide")
st.title("📈 Stock Explorer")

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
st.success(f"🏆 **Top grower:** {top_ticker} — {top_growth:+.1f}% since Jan 2018")

# Most volatile indicator — highest std dev of daily % returns within the selected window
daily_returns = dff[chosen].pct_change().dropna()
volatility = daily_returns.std() * 100
most_volatile = volatility.idxmax()
st.warning(f"🌪️ **Most volatile in selected period:** {most_volatile} — daily swings of ±{volatility[most_volatile]:.2f}% on average")

# Key numbers: total growth for each chosen stock (full dataset)
cols = st.columns(len(chosen))
for col, t in zip(cols, chosen):
    growth = (df[t].iloc[-1] - 1) * 100
    col.metric(t, f"{df[t].iloc[-1]:.2f}x", f"{growth:+.1f}%")

# Did you know?
st.info('💡 **Did you know?** Microsoft\'s 1986 IPO made 3 billionaires and an estimated 12,000 millionaires among its employees.')

# Line chart + bar chart side by side
chart_col, bar_col = st.columns([3, 2])

with chart_col:
    fig_line = px.line(dff, x="date", y=chosen, title="Normalized price over time")
    st.plotly_chart(fig_line, use_container_width=True)

with bar_col:
    # Growth % from start of selected window to end
    window_growth = {t: (dff[t].iloc[-1] / dff[t].iloc[0] - 1) * 100 for t in chosen}
    bar_df = pd.DataFrame({"Stock": list(window_growth.keys()), "Growth (%)": list(window_growth.values())})
    fig_bar = px.bar(
        bar_df, x="Stock", y="Growth (%)", title="Total growth in selected period",
        color="Growth (%)", color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
        text_auto=".1f",
    )
    fig_bar.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()
st.subheader("💶 What if I had invested in AAPL?")

years = sorted(df["date"].dt.year.unique().tolist())
col_amt, col_yr = st.columns(2)
amount = col_amt.number_input("Investment amount (€)", min_value=1, value=1000, step=100)
year = col_yr.selectbox("Year of investment", years)

# Find the first trading day of the chosen year and use its AAPL normalized value
start_price = df[df["date"].dt.year == year]["AAPL"].iloc[0]
end_price = df["AAPL"].iloc[-1]
end_date = df["date"].iloc[-1].strftime("%b %Y")
multiplier = end_price / start_price
final_value = amount * multiplier
profit = final_value - amount

if profit >= 0:
    st.success(f"€{amount:,.0f} invested in AAPL at the start of {year} would be worth **€{final_value:,.2f}** by {end_date} — a gain of **€{profit:,.2f}** ({(multiplier-1)*100:+.1f}%)")
else:
    st.error(f"€{amount:,.0f} invested in AAPL at the start of {year} would be worth **€{final_value:,.2f}** by {end_date} — a loss of **€{abs(profit):,.2f}** ({(multiplier-1)*100:+.1f}%)")
