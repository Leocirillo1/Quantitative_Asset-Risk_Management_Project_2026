"""
Small helpers shared by the pages of the app (with Streamlit cache, so pages load fast).
"""
import streamlit as st

from src.data import available_assets, load_prices, monthly_returns, risk_free
from src.optimizer import check_constraints
from src.portfolios import BENCHMARKS, benchmark_weights, build_portfolios, estimate


def get_profile():
    """Stop the page if the client has not filled in the questionnaire yet."""
    if "profile" not in st.session_state:
        st.warning("Please fill in your investor profile first.")
        st.page_link("app_pages/profile.py", label="Go to your profile", icon="🧑")
        st.stop()
    return st.session_state["profile"]


def get_choices():
    """Products and constraints chosen by the client (our recommendation by default)."""
    profile = get_profile()
    tickers = st.session_state.get("assets", profile.recommended_assets)
    tickers = [t for t in tickers if t in available_assets()]
    c = st.session_state.get("constraints", profile.recommended_constraints)
    problems = check_constraints(tickers, c)
    if problems:
        for p in problems:
            st.error(p)
        st.page_link("app_pages/choices.py", label="Change your products and constraints", icon="🧩")
        st.stop()
    return tickers, c


def get_currency():
    return st.session_state.get("currency", "USD")


def get_views():
    """Black-Litterman views of the client: {ticker: (expected return, confidence)}."""
    return st.session_state.get("views", {})


def get_benchmark(tickers, c):
    """Name and weights of the benchmark chosen on the backtest page (profile benchmark by default)."""
    name = st.session_state.get("benchmark", BENCHMARKS[0])
    return name, benchmark_weights(name, tickers, c)


@st.cache_data
def get_data(currency):
    """Monthly returns of all products, monthly risk-free rate, daily prices."""
    prices = load_prices(currency)
    return monthly_returns(prices), risk_free(currency), prices


@st.cache_data
def get_portfolios(currency, tickers, gamma, c, views):
    """Today's four portfolios for this client."""
    returns, rf, prices = get_data(currency)
    mu, cov = estimate(returns[tickers])
    return build_portfolios(mu, cov, rf.iloc[-1] * 12, gamma, c, views)
