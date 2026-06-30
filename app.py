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

st.caption("Prices are indexed to 1.00 at the start, so each line shows growth since Jan 2018.")

# Top grower banner
growth_values = {t: (df[t].iloc[-1] - 1) * 100 for t in chosen}
top_ticker = max(growth_values, key=growth_values.get)
top_growth = growth_values[top_ticker]
st.success(f"🏆 **Top grower:** {top_ticker} — {top_growth:+.1f}% since Jan 2018")

# Key numbers: total growth for each chosen stock
cols = st.columns(len(chosen))
for col, t in zip(cols, chosen):
    growth = (df[t].iloc[-1] - 1) * 100
    col.metric(t, f"{df[t].iloc[-1]:.2f}x", f"{growth:+.1f}%")

# Did you know?
st.info('💡 **Did you know?** Microsoft\'s 1986 IPO made 3 billionaires and an estimated 12,000 millionaires among its employees.')

# Line chart comparing the chosen stocks over time
fig = px.line(df, x="date", y=chosen, title="Normalized price over time")
st.plotly_chart(fig, use_container_width=True)
