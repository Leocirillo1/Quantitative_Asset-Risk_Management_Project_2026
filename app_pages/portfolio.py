"""Page 3: the optimal portfolio of the client, with 4 methods."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.app_helpers import get_benchmark, get_choices, get_currency, get_data, get_portfolios, get_profile, get_views
from src.black_litterman import market_weights, posterior_returns, prior_returns
from src.data import ASSETS
from src.optimizer import beta, frontier, portfolio_stats, risk_contributions, tracking_error
from src.portfolios import METHODS, WINDOW, estimate

CLASS_COLORS = {"Equity": "#1f77b4", "Bond": "#2ca02c", "Other": "#ff7f0e", "Crypto": "#9467bd"}

profile = get_profile()
tickers, c = get_choices()
currency = get_currency()
benchmark_name, benchmark = get_benchmark(tickers, c)

st.title("Your portfolio")
returns, rf, prices = get_data(currency)
mu, cov = estimate(returns[tickers])
rf_now = rf.iloc[-1] * 12
st.caption(f"Profile: {profile.label} (γ = {profile.gamma:.1f}) · {len(tickers)} products · Currency: {currency} · "
           f"Estimated on the last {WINDOW} months of data")

# Monthly returns of the last 60 months, to compare with the benchmark (beta, tracking error)
past = returns[tickers].dropna().iloc[-WINDOW:]
benchmark_returns = returns.loc[past.index, benchmark.index].fillna(0) @ benchmark

method = st.radio("Choose a method", METHODS, horizontal=True,
                  index=METHODS.index(st.session_state.get("method", "Mean-variance")))
st.session_state["method"] = method

# ---------- Black-Litterman: the client gives his views ----------
if method == "Black-Litterman":
    st.subheader("Your views on the markets")
    prior = prior_returns(cov, rf_now)
    st.write("Without views, Black-Litterman uses the **market equilibrium** returns: the returns that make "
             "the world market portfolio optimal. Then you can add your own views.")
    st.dataframe(pd.DataFrame({
        "Product": [ASSETS[t][0] for t in mu.index],
        "Market weight": market_weights(mu.index),
        "Equilibrium return": prior,
        f"Historical return ({WINDOW} months)": mu,
    }).style.format({"Market weight": "{:.0%}", "Equilibrium return": "{:.1%}",
                     f"Historical return ({WINDOW} months)": "{:.1%}"}))

    old_views = get_views()
    chosen = st.multiselect("On which products do you have a view?", list(mu.index),
                            default=[t for t in old_views if t in mu.index])
    views = {}
    for t in chosen:
        q_old, conf_old = old_views.get(t, (round(prior[t] * 100) / 100, 0.5))
        col1, col2 = st.columns(2)
        q = col1.slider(f"Expected return of {t} ({ASSETS[t][0]}), % per year", -30, 50, int(round(q_old * 100)),
                        key=f"view_{t}")
        conf = col2.slider(f"Your confidence in this view, %", 5, 95, int(conf_old * 100), key=f"conf_{t}")
        views[t] = (q / 100, conf / 100)
    st.session_state["views"] = views

portfolios = get_portfolios(currency, tickers, profile.gamma, c, get_views())
weights = portfolios[method]

# Expected returns used by this method (Black-Litterman has its own)
mu_method = posterior_returns(cov, rf_now, get_views()) if method == "Black-Litterman" else mu

# ---------- Key numbers ----------
ret, vol = portfolio_stats(weights, mu_method, cov)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Expected return", f"{ret:.1%}")
col2.metric("Volatility", f"{vol:.1%}")
col3.metric("Sharpe ratio", f"{(ret - rf_now) / vol:.2f}")
col4.metric("Beta vs benchmark", f"{beta(past @ weights, benchmark_returns):.2f}",
            help=f"Benchmark: {benchmark_name} (you can change it on the backtest page)")

# ---------- Weights and risk contributions ----------
table = pd.DataFrame({
    "Product": [ASSETS[t][0] for t in weights.index],
    "Class": [ASSETS[t][1] for t in weights.index],
    "Weight": weights,
    "Risk contribution": risk_contributions(weights, cov),
})
col1, col2 = st.columns(2)
col1.plotly_chart(px.bar(table, x=table.index, y="Weight", color="Class", title="Weights",
                         color_discrete_map=CLASS_COLORS,
                         text_auto=".0%").update_layout(yaxis_tickformat=".0%", xaxis_title=None))
col2.plotly_chart(px.bar(table, x=table.index, y="Risk contribution", color="Class",
                         color_discrete_map=CLASS_COLORS,
                         title="Where does the risk come from?",
                         text_auto=".0%").update_layout(yaxis_tickformat=".0%", xaxis_title=None))

# ---------- Efficient frontier ----------
front = frontier(mu_method, cov, c)
fig = go.Figure()
fig.add_scatter(x=front["Volatility"], y=front["Return"], mode="lines", name="Efficient frontier (your constraints)")
fig.add_scatter(x=np.sqrt(np.diag(cov)), y=mu_method, mode="markers+text", text=list(mu.index),
                textposition="top center", name="Single products")
fig.add_scatter(x=[vol], y=[ret], mode="markers", marker=dict(size=16, symbol="star"), name="Your portfolio")
fig.update_layout(title="Efficient frontier", xaxis_title="Volatility", yaxis_title="Expected return",
                  xaxis_tickformat=".0%", yaxis_tickformat=".0%")
st.plotly_chart(fig)
if method == "Risk parity (ERC)":
    st.caption("Risk parity does not use expected returns, so it is usually below the frontier: "
               "it gives up some expected return to spread the risk.")

# ---------- Compare the 4 methods ----------
st.subheader("Compare the methods")
compare = pd.DataFrame(portfolios)
compare.index = [f"{t} ({ASSETS[t][0]})" for t in compare.index]
stats = pd.DataFrame({m: {"Volatility": portfolio_stats(w, mu, cov)[1],
                          "Beta vs benchmark": beta(past @ w, benchmark_returns),
                          "Tracking error vs benchmark": tracking_error(past @ w, benchmark_returns)}
                      for m, w in portfolios.items()})
st.dataframe(pd.concat([compare, stats]).style.format("{:.1%}").format(
    "{:.2f}", subset=pd.IndexSlice[["Beta vs benchmark"], :]))
st.caption(f"Benchmark: {benchmark_name}. Beta and tracking error (lab LN2) on the last {WINDOW} months.")

# ---------- Composition map (lab LN3): sensitivity to gamma ----------
st.subheader("What if your γ was different?")
st.write("Composition map (as in lab LN3): the optimal weights for every γ, with your constraints and "
         "the expected returns of the method. The dashed line is your γ.")
area = px.area(front, x="Gamma", y=list(mu.index), log_x=True)
area.add_vline(x=profile.gamma, line_dash="dash")
area.update_layout(yaxis_title="Weight", yaxis_tickformat=".0%", xaxis_title="γ (risk aversion)")
st.plotly_chart(area)
