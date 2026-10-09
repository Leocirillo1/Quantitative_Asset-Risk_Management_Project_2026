"""Page 5: short explanation of the methods, data and limitations (useful for questions)."""
import streamlit as st

from src.black_litterman import DELTA, TAU
from src.data import ASSETS

st.title("How it works")

st.header("1. Your profile")
st.write("Swiss law (FinSO Art. 17) asks for the client's **willingness** and **capacity** to take risk.")
st.markdown("""
- **Willingness**: Holt-Laury (2002) lotteries. With CRRA utility, the row where you switch from A to B gives your
  relative risk aversion γ.
- **Capacity**: age, horizon, liquidity needs, income, maximum loss → a minimum γ and constraints.
- **Final γ** = the more prudent (higher) of the two.
- We **recommend** products and constraints for the profile. The client can change them (page 2): we only warn
  when the choice is riskier than our recommendation (suitability check).
""")

st.header("2. Data")
st.write("The app downloads the daily prices directly from Yahoo Finance when it starts (again every day, or "
         "with the button 'Update data now'). Nothing has to be run before. We use monthly returns; "
         "expected returns and covariances are estimated on the last 60 months. In CHF, prices are converted "
         "with the USD/CHF rate.")
st.table({"Ticker": list(ASSETS), "Product": [a[0] for a in ASSETS.values()],
          "Class": [a[1] for a in ASSETS.values()]})

st.header("3. Methods")
st.subheader("Mean-variance (Markowitz, lab LN1)")
st.latex(r"\min_x \; \tfrac{1}{2} x^\top \Sigma x - \tfrac{1}{\gamma} x^\top \mu "
         r"\quad \text{s.t. } \textstyle\sum x_i = 1,\; 0 \le x_i \le x^+,\; \text{class constraints}")
st.write("Same QP as in the lab, where the lab's γ is the risk tolerance = 1 / our risk aversion.")

st.subheader("Resampled mean-variance (Michaud 2007, lab LN3)")
st.write("Expected returns are very uncertain, so mean-variance weights are unstable. We simulate 100 new "
         "samples of 60 months from N(μ, Σ), optimise each one and average the weights.")

st.subheader("Black-Litterman (1992)")
st.latex(r"\pi = r_f + \delta \Sigma w_{mkt}")
st.latex(r"\mu_{BL} = \left[(\tau\Sigma)^{-1} + P^\top \Omega^{-1} P\right]^{-1}"
         r"\left[(\tau\Sigma)^{-1}\pi + P^\top \Omega^{-1} Q\right]")
st.write(f"π: equilibrium returns of the world market portfolio (δ = {DELTA}, τ = {TAU}). "
         "Q: your views, P: which asset each view is about, Ω: uncertainty of the views "
         "(Ω = τσ²(1−c)/c, with c your confidence). Then we run mean-variance with μ_BL.")

st.subheader("Risk parity / Equal Risk Contribution")
st.latex(r"RC_i = \frac{x_i (\Sigma x)_i}{x^\top \Sigma x} = \frac{1}{n}")
st.write("Does not use expected returns at all: every asset brings the same share of risk.")

st.header("4. Risk measures (lab LN2)")
st.write("Beta with the covariance method β = cov(R_p, R_b) / var(R_b) and tracking error = volatility of "
         "R_p − R_b, both against the benchmark chosen by the client (by default: SPY up to the client's equity maximum, the rest in AGG).")

st.header("5. Backtest with transaction costs (LN3)")
st.write("Out-of-sample: at each rebalancing we only use the past 60 months. Between rebalancings the weights "
         "drift with the markets. The client chooses the period, the benchmark, the rebalancing frequency, "
         "the cost and a turnover limit.")
st.write("Cost-aware mean-variance (LN3): we start from the current weights x⁰ and add what we buy (Δx⁺) "
         "and what we sell (Δx⁻):")
st.latex(r"\min_{x,\Delta x^-,\Delta x^+} \; \tfrac{1}{2} x^\top \Sigma x - \tfrac{1}{\gamma}"
         r"\left(x^\top \mu - c^\top \Delta x^- - c^\top \Delta x^+\right)")
st.latex(r"\text{s.t. } \textstyle\sum x_i + c^\top(\Delta x^- + \Delta x^+) = 1,\quad "
         r"x = x^0 + \Delta x^+ - \Delta x^-,\quad \sum (\Delta x^-_i + \Delta x^+_i) \le \tau^+")
st.write("So the portfolio only trades when the gain is larger than the cost. Resampled MV and risk parity "
         "move towards their new target, but never trade more than the turnover limit τ⁺.")

st.header("6. Time machine")
st.write("Buy and hold from the market peak of 2008, 2020 and 2022, compared with the loss the client said "
         "he could accept.")

st.header("7. Limitations")
st.markdown("""
- Past returns are a noisy guess of future returns (this is why we offer Black-Litterman and resampling).
- 60 months is a short window; a longer one is more stable but reacts slower.
- In CHF, we do not hedge the currency risk; the CHF risk-free rate is an approximation (SNB policy rate).
- Market weights for Black-Litterman are rounded approximations.
- We do not shrink the covariance matrix (Ledoit-Wolf): with about 10 products and 60 months, the estimation
  error of Σ is small compared to the error on μ. With many more products, shrinkage would become useful.
- Bid-ask costs are the same for every product; in reality crypto and small markets cost more.
""")

st.header("Sources")
st.markdown("""
Holt & Laury (2002) · Markowitz (1952) · Black & Litterman (1992) · He & Litterman (1999) ·
Michaud (2007) · Maillard, Roncalli & Teiletche (2010) · Doeswijk, Lam & Swinkels (2014) · Roncalli (2013) ·
QARM II lecture notes and labs (HEC Lausanne)
""")
