# Robo-advisor – QARM II project (HEC Lausanne)

A Streamlit web app that works like a robo-advisor:

1. **Your profile**: a Holt-Laury lottery questionnaire gives the client's risk aversion γ (willingness),
   factual questions give a minimum γ (capacity, as in FinSO Art. 17).
2. **Your products & constraints**: we propose products and constraints for the profile; the client can change
   them (21 ETFs and cryptos), and we warn when the choice is riskier than our recommendation.
3. **Your portfolio**: four methods with the client's γ and constraints: mean-variance, resampled
   mean-variance (Michaud), Black-Litterman with the client's own views, and risk parity (ERC).
   Weights, risk contributions, efficient frontier, beta, tracking error and a composition map.
4. **Backtest**: out-of-sample; the client chooses the period, the benchmark, the rebalancing frequency,
   the transaction cost and a turnover limit. Cost-aware optimisation as in lecture LN3.
5. **Time machine**: replays the 2008, 2020 and 2022 crises with the client's portfolio and checks
   if the loss is within what the client said they could accept.

Everything can be shown in USD or CHF. The app downloads all the prices directly from Yahoo Finance
when it starts (again every day, or with the "Update data now" button): no script or data file is needed.

## Run the app

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1          (Windows)
pip install -r requirements.txt
python -m streamlit run app.py
```

## Code structure

```
app.py                  menu of the app (Streamlit navigation)
app_pages/              one file per page of the app
src/holt_laury.py       Holt-Laury questionnaire -> gamma
src/client_profile.py   gamma from willingness and capacity, constraints
src/data.py             products, automatic download of prices, returns, risk-free rate (USD or CHF)
src/optimizer.py        constraints, mean-variance (lab QP), LN3 transaction costs, resampling, risk parity, frontier
src/black_litterman.py  equilibrium returns and Black-Litterman posterior
src/portfolios.py       builds the four portfolios of the client and the benchmarks
src/backtest.py         out-of-sample backtest with transaction costs and performance measures
src/time_machine.py     crisis replay
```

## Data

21 ETFs and cryptos from Yahoo Finance (equities, bonds, gold, commodities, Bitcoin, Ethereum),
the USD/CHF rate (CHF=X) and the 13-week US T-bill rate (^IRX). For CHF the risk-free rate is the
approximate SNB policy rate.
