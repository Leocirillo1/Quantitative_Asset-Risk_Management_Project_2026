from src.data import RECOMMENDED, RECOMMENDED_CRYPTO


class ClientProfile:
    """
    Combines:
      - risk willingness: gamma from the Holt-Laury questionnaire
      - risk capacity: factual questions -> minimum gamma + RECOMMENDED portfolio constraints
    Final gamma = the more conservative (higher) of the two.
    The client can then change the recommended products and constraints (page "Your choices").
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

    MAX_WEIGHT_PER_ASSET = 0.4
    MAX_CRYPTO = 0.10  # maximum in crypto for a client who wants crypto
    MAX_OTHER = 0.20   # maximum in gold and commodities (volatile, no income)

    # Largest acceptable one-year loss, as a number (used by the time machine)
    MAX_LOSS_VALUE = {"-5%": -0.05, "-10%": -0.10, "-20%": -0.20, "-30% or more": -0.30}

    def __init__(self, gamma_willingness, age, horizon, needs_money, income, max_loss, crypto):
        self.gamma_willingness = gamma_willingness
        self.max_loss = self.MAX_LOSS_VALUE[max_loss]

        # Risk capacity score (0 to 13)
        self.capacity_score = (self.AGE[age] + self.HORIZON[horizon] + self.NEEDS_MONEY[needs_money]
                               + self.INCOME[income] + self.MAX_LOSS[max_loss])
        self.gamma_capacity = self.gamma_from_capacity(self.capacity_score)

        # Final gamma: the more conservative of willingness and capacity
        self.gamma = max(self.gamma_willingness, self.gamma_capacity)
        self.label = self.profile_label(self.gamma)

        # Our recommendation (the client can change it)
        self.recommended_constraints = {
            "max_equity": min(self.MAX_EQUITY_HORIZON[horizon], self.MAX_EQUITY_LOSS[max_loss]),
            "min_bonds": 0.3 if needs_money == "Yes" else 0.0,
            "max_weight_per_asset": self.MAX_WEIGHT_PER_ASSET,
            "max_other": self.MAX_OTHER,
            "max_crypto": self.MAX_CRYPTO if crypto == "Yes" else 0.0,
        }
        self.recommended_assets = RECOMMENDED + (RECOMMENDED_CRYPTO if crypto == "Yes" else [])

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
