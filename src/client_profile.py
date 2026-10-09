class ClientProfile:
    """
    Combines:
      - risk willingness: gamma from the Holt-Laury questionnaire
      - risk capacity: factual questions -> minimum gamma + portfolio constraints
    Final gamma = the more conservative (higher) of the two.
    """

    # Answer -> capacity points (more points = can afford more risk)
    AGE = {"Under 30": 3, "30-45": 2, "46-60": 1, "Over 60": 0}
    HORIZON = {"Less than 3 years": 0, "3-7 years": 1, "7-15 years": 2, "More than 15 years": 3}
    NEEDS_MONEY = {"Yes": 0, "No": 2}
    INCOME = {"No regular income": 0, "Fairly stable": 1, "Very stable": 2}
    MAX_LOSS = {"-5%": 0, "-10%": 1, "-20%": 2, "-30% or more": 3}

    # Constraints linked to some answers
    MAX_EQUITY_HORIZON = {"Less than 3 years": 0.3, "3-7 years": 0.6, "7-15 years": 0.8, "More than 15 years": 1.0}
    MAX_EQUITY_LOSS = {"-5%": 0.2, "-10%": 0.4, "-20%": 0.7, "-30% or more": 1.0}

    # "Don't invest where you work": job sector -> sector ETF to limit
    SECTOR_ETF = {
        "None / other": None,
        "Banking & finance": "XLF",
        "Pharma & healthcare": "XLV",
        "Technology": "XLK",
        "Energy": "XLE",
        "Industry & manufacturing": "XLI",
        "Food & consumer staples": "XLP",
        "Retail, luxury & watchmaking": "XLY",
        "Real estate": "XLRE",
    }

    MAX_WEIGHT_PER_ASSET = 0.4
    MAX_WEIGHT_OWN_SECTOR = 0.05

    def __init__(self, gamma_willingness, age, horizon, needs_money, income, max_loss, sector, crypto):
        self.gamma_willingness = gamma_willingness

        # Risk capacity score (0 to 13)
        self.capacity_score = (self.AGE[age] + self.HORIZON[horizon] + self.NEEDS_MONEY[needs_money]
                               + self.INCOME[income] + self.MAX_LOSS[max_loss])
        self.gamma_capacity = self.gamma_from_capacity(self.capacity_score)

        # Final gamma: the more conservative of willingness and capacity
        self.gamma = max(self.gamma_willingness, self.gamma_capacity)
        self.label = self.profile_label(self.gamma)

        self.constraints = {
            "max_equity": min(self.MAX_EQUITY_HORIZON[horizon], self.MAX_EQUITY_LOSS[max_loss]),
            "min_bonds": 0.3 if needs_money == "Yes" else 0.0,
            "max_weight_per_asset": self.MAX_WEIGHT_PER_ASSET,
            "own_sector_etf": self.SECTOR_ETF[sector],
            "max_weight_own_sector": self.MAX_WEIGHT_OWN_SECTOR,
            "allow_crypto": crypto == "Yes",
        }

    @staticmethod
    def gamma_from_capacity(score):
        """Low capacity -> the client must be treated as at least this risk averse."""
        if score <= 4:
            return 12.0
        if score <= 8:
            return 6.0
        return 2.0

    @staticmethod
    def profile_label(gamma):
        if gamma <= 4:
            return "Aggressive"
        if gamma <= 9:
            return "Balanced"
        return "Conservative"
