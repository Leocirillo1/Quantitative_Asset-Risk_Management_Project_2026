"""
Portfolio optimisation with the client's constraints.
The structure follows our labs (QP function, LinearConstraint, scipy minimize).

All inputs are annual and are pandas objects:
mu = expected returns (Series), cov = covariance matrix (DataFrame).
c = the client's constraints: max_equity, min_bonds, max_other, max_crypto, max_weight_per_asset.
"""
import numpy as np
import pandas as pd
from scipy.optimize import LinearConstraint, minimize

from src.data import ASSETS


def QP(x, sigma, mu, gamma):
    """Lab LN1: 0.5 x'Sigma x - gamma x'mu.
    Careful: here gamma is the risk TOLERANCE = 1 / risk aversion of the client."""
    return 0.5 * x.T @ sigma @ x - gamma * x.T @ mu


def client_constraints(tickers, c, extra_variables=0):
    """LN3 'asset class constraints' written as LinearConstraint (as in the labs).
    extra_variables: number of extra variables after the weights (used with transaction costs)."""
    classes = np.array([ASSETS[t][1] for t in tickers])
    pad = np.zeros(extra_variables)
    equity = np.concatenate([(classes == "Equity").astype(float), pad])
    bonds = np.concatenate([(classes == "Bond").astype(float), pad])
    other = np.concatenate([(classes == "Other").astype(float), pad])
    crypto = np.concatenate([(classes == "Crypto").astype(float), pad])
    return [
        LinearConstraint(equity, ub=c["max_equity"]),   # maximum in equities
        LinearConstraint(bonds, lb=c["min_bonds"]),     # minimum in bonds
        LinearConstraint(other, ub=c["max_other"]),     # maximum in gold and commodities
        LinearConstraint(crypto, ub=c["max_crypto"]),   # maximum in crypto
    ]


def weight_bounds(tickers, c):
    """No short selling and maximum weight per product: 0 <= x_i <= max."""
    return [(0, c["max_weight_per_asset"])] * len(tickers)


def check_constraints(tickers, c):
    """Return a list of problems if no portfolio can respect the constraints."""
    classes = [ASSETS[t][1] for t in tickers]
    w = c["max_weight_per_asset"]
    room = {k: classes.count(k) * w for k in ["Equity", "Bond", "Other", "Crypto"]}  # max per class
    room["Equity"] = min(room["Equity"], c["max_equity"])
    room["Other"] = min(room["Other"], c["max_other"])
    room["Crypto"] = min(room["Crypto"], c["max_crypto"])
    problems = []
    if len(tickers) < 2:
        problems.append("Choose at least 2 products.")
    if sum(room.values()) < 1:
        problems.append("With these products and limits you cannot invest 100%: "
                        "add products or raise your maximums.")
    if room["Bond"] < c["min_bonds"]:
        problems.append("Not enough bond products for your minimum in bonds: add bonds or lower the minimum.")
    return problems


def clean(x, tickers):
    """Remove tiny numerical errors (e.g. -0.0001%) and make the weights sum to 1."""
    w = np.clip(x, 0, 1)
    return pd.Series(w / w.sum(), index=tickers)


def mean_variance(mu, cov, risk_aversion, c):
    """Markowitz portfolio of a client with this risk aversion (gamma from the questionnaire)."""
    tickers = list(mu.index)
    n = len(tickers)
    rules = [LinearConstraint(np.ones(n), lb=1, ub=1)] + client_constraints(tickers, c)  # 100% invested
    res = minimize(QP, np.ones(n) / n, args=(cov.values, mu.values, 1 / risk_aversion),
                   bounds=weight_bounds(tickers, c), constraints=rules, method="SLSQP")
    return clean(res.x, tickers)


def mean_variance_with_costs(mu, cov, risk_aversion, c, x0, cost, max_turnover=2.0):
    """
    LN3 'transaction cost management' and 'turnover management'.
    We start from the current portfolio x0 and look for the new portfolio x:
        x = x0 + dx_plus - dx_minus   (dx_plus = what we buy, dx_minus = what we sell)
    Variables: X = (x, dx_minus, dx_plus), 3n numbers, as in the lecture.
        min 0.5 x'Sigma x - gamma (x'mu - c'dx_minus - c'dx_plus)
        u.c. sum(x) + c'dx_minus + c'dx_plus = 1     (the costs are paid from the portfolio)
             x + dx_minus - dx_plus = x0
             sum(dx_minus) + sum(dx_plus) <= max turnover
             client constraints on x, 0 <= X <= 1
    So we only trade when the gain in expected utility is larger than the cost.
    """
    tickers = list(mu.index)
    n = len(tickers)
    gamma = 1 / risk_aversion
    costs = np.full(n, cost)

    Q = np.zeros((3 * n, 3 * n))
    Q[:n, :n] = cov.values                                    # only x has risk
    R = gamma * np.concatenate([mu.values, -costs, -costs])   # expected return minus costs
    objective = lambda X: 0.5 * X @ Q @ X - X @ R

    I = np.eye(n)
    rules = [
        LinearConstraint(np.concatenate([np.ones(n), costs, costs]), lb=1, ub=1),  # budget
        LinearConstraint(np.hstack([I, I, -I]), lb=x0, ub=x0),                    # link with x0
        LinearConstraint(np.concatenate([np.zeros(n), np.ones(2 * n)]), ub=max_turnover),  # turnover
    ] + client_constraints(tickers, c, extra_variables=2 * n)
    bounds = weight_bounds(tickers, c) + [(0, 1)] * (2 * n)  # 0 <= dx_minus, dx_plus <= 1
    start = np.concatenate([x0, np.zeros(2 * n)])
    res = minimize(objective, start, bounds=bounds, constraints=rules, method="SLSQP")
    return clean(res.x[:n], tickers)


def risk_contributions(weights, cov):
    """Share of the portfolio risk that comes from each asset (sums to 100%)."""
    w, sigma = np.asarray(weights), np.asarray(cov)
    return w * (sigma @ w) / (w @ sigma @ w)


def risk_parity(cov, c):
    """Equal Risk Contribution (ERC): every asset brings the same share of risk.
    With the client's constraints we get as close as possible to equal shares."""
    tickers = list(cov.index)
    n = len(tickers)
    sigma = cov.values
    objective = lambda w: 1000 * ((risk_contributions(w, sigma) - 1 / n) ** 2).sum()
    rules = [LinearConstraint(np.ones(n), lb=1, ub=1)] + client_constraints(tickers, c)
    res = minimize(objective, np.ones(n) / n, bounds=weight_bounds(tickers, c), constraints=rules,
                   method="SLSQP")
    return clean(res.x, tickers)


def resampled(mu, cov, risk_aversion, c, n_sim=100, n_months=60):
    """Lab LN3, resampling of Michaud (2007):
    simulate returns, re-estimate mu and cov, optimise, and average the weights."""
    np.random.seed(42)  # same simulations every time, so the app always shows the same result
    all_weights = []
    for i in range(n_sim):
        simulated_r = np.random.multivariate_normal(mu / 12, cov / 12, n_months)  # monthly returns
        simulated_mu = pd.Series(simulated_r.mean(axis=0) * 12, index=mu.index)
        simulated_cov = pd.DataFrame(np.cov(simulated_r, rowvar=False) * 12, index=mu.index, columns=mu.index)
        all_weights.append(mean_variance(simulated_mu, simulated_cov, risk_aversion, c))
    return pd.concat(all_weights, axis=1).mean(axis=1)


def portfolio_stats(weights, mu, cov):
    """Expected return and volatility of a portfolio (annual)."""
    w = np.asarray(weights)
    return w @ mu.values, np.sqrt(w @ cov.values @ w)


def beta(portfolio_returns, market_returns):
    """Lab LN2, covariance method: beta = cov(R_p, R_m) / var(R_m)."""
    return portfolio_returns.cov(market_returns) / market_returns.var()


def tracking_error(portfolio_returns, benchmark_returns):
    """LN2: volatility of the difference between the portfolio and the benchmark (annual)."""
    return (portfolio_returns - benchmark_returns).std() * np.sqrt(12)


def frontier(mu, cov, c, gammas=np.geomspace(0.25, 200, 40)):
    """Efficient frontier and composition map (lab LN3): optimal portfolio for many gammas."""
    rows = []
    for g in gammas:
        w = mean_variance(mu, cov, g, c)
        ret, vol = portfolio_stats(w, mu, cov)
        rows.append({"Gamma": g, "Return": ret, "Volatility": vol, **w})
    return pd.DataFrame(rows)
