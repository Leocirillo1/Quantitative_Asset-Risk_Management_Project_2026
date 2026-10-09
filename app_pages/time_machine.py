"""Page 5: time machine. Replay past crises with the client's portfolio."""
import pandas as pd
import plotly.express as px
import streamlit as st

from src.app_helpers import get_benchmark, get_choices, get_currency, get_data, get_portfolios, get_profile, get_views
from src.portfolios import METHODS
from src.time_machine import CRISES, crisis_summary, replay

profile = get_profile()
tickers, c = get_choices()
currency = get_currency()
benchmark_name, benchmark = get_benchmark(tickers, c)

st.title("⏳ Time machine")
st.write("What if you had bought your portfolio just before a crisis? "
         "We buy it on the day the market was at its peak and hold it.")

returns, rf, prices = get_data(currency)
portfolios = get_portfolios(currency, tickers, profile.gamma, c, get_views())
portfolios["Benchmark"] = benchmark

col1, col2, col3 = st.columns(3)
crisis = col1.selectbox("Crisis", list(CRISES))
method = col2.selectbox("Your portfolio", METHODS, index=METHODS.index(st.session_state.get("method", METHODS[0])))
amount = col3.number_input(f"Amount invested ({currency})", min_value=1000, value=100_000, step=10_000)

start, end, story = CRISES[crisis]
st.info(f"**{crisis}** ({pd.Timestamp(start):%b %Y} → {pd.Timestamp(end):%b %Y}): {story}")

# ---------- Value during the crisis and one year after ----------
show_until = pd.Timestamp(end) + pd.DateOffset(years=1)
paths = pd.DataFrame({name: amount * replay(prices, portfolios[name], start, show_until)
                      for name in [method, "Benchmark"]})
paths = paths.rename(columns={"Benchmark": f"Benchmark: {benchmark_name}"})
fig = px.line(paths, title=f"Your {amount:,.0f} {currency} during the crisis (and one year after)")
fig.add_vline(x=pd.Timestamp(end), line_dash="dash")
fig.update_layout(yaxis_title=currency, xaxis_title=None, legend_title=None)
st.plotly_chart(fig)

# ---------- Worst loss and recovery ----------
loss, months = crisis_summary(prices, portfolios[method], start, end)
col1, col2, col3 = st.columns(3)
col1.metric("Worst loss", f"{loss:.1%}")
col2.metric(f"Worst loss in {currency}", f"{loss * amount:,.0f}")
col3.metric("Time to get your money back", "not yet" if months is None else f"{months} months")

if loss < profile.max_loss:
    st.error(f"This portfolio lost {-loss:.1%}, more than the {-profile.max_loss:.0%} you told us you could accept. "
             "Would you have stayed invested? Maybe choose a more prudent profile or method.")
else:
    st.success(f"This portfolio lost {-loss:.1%}, within the {-profile.max_loss:.0%} you told us you could accept.")

missing = [t for t in portfolios[method].index if prices[t].loc[:start].isna().all()]
if missing:
    st.caption(f"{', '.join(missing)} did not exist yet: this part of the portfolio is kept as cash.")

# ---------- All crises, all portfolios ----------
st.subheader("All crises at a glance")
rows = {}
for name, w in portfolios.items():
    row = {}
    for crisis_name, (s, e, _) in CRISES.items():
        l, m = crisis_summary(prices, w, s, e)
        row[f"{crisis_name}: worst loss"] = f"{l:.1%}"
        row[f"{crisis_name}: months to recover"] = "not yet" if m is None else str(m)
    rows[name] = row
st.dataframe(pd.DataFrame(rows).T)
