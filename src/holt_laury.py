import numpy as np
from scipy.optimize import brentq


class HoltLaury:
    """
    Holt-Laury (2002) lottery questionnaire, reframed as an investment of 100 CHF over one year.

    In each of the 10 rows the client chooses between:
        Option A (less risky): 108 CHF with probability p, otherwise 96 CHF
        Option B (more risky): 150 CHF with probability p, otherwise 92 CHF
    p goes from 10% (row 1) to 100% (row 10). The row where the client switches
    from A to B reveals their relative risk aversion gamma (CRRA utility).
    """

    OPTION_A = (108, 96)  # (good outcome, bad outcome) in CHF
    OPTION_B = (150, 92)
    PROBABILITIES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    def __init__(self):
        # cutoffs[i] = gamma at which a client is indifferent between A and B in row i+1
        # (row 10 has no cutoff: B is always better when p = 100%)
        self.cutoffs = [self.indifference_gamma(p) for p in self.PROBABILITIES[:-1]]

    @staticmethod
    def utility(wealth, gamma):
        """CRRA utility."""
        if abs(gamma - 1) < 1e-8:
            return np.log(wealth)
        return wealth ** (1 - gamma) / (1 - gamma)

    def expected_utility(self, option, p, gamma):
        good, bad = option
        return p * self.utility(good, gamma) + (1 - p) * self.utility(bad, gamma)

    def indifference_gamma(self, p):
        """Gamma that makes the client indifferent between A and B for probability p."""
        diff = lambda g: self.expected_utility(self.OPTION_A, p, g) - self.expected_utility(self.OPTION_B, p, g)
        return brentq(diff, 0.01, 100)

    @staticmethod
    def is_consistent(choices):
        """Consistent = only A's, then only B's (one single switch), and B in the last row."""
        n_safe = choices.count("A")
        return choices == ["A"] * n_safe + ["B"] * (len(choices) - n_safe) and choices[-1] == "B"

    def compute_gamma(self, choices):
        """
        choices: list of 10 answers, each "A" or "B".
        Returns gamma, or None if the answers are inconsistent.
        """
        if not self.is_consistent(choices):
            return None

        n_safe = choices.count("A")
        if n_safe == 0:  # always chose B: very low risk aversion
            return self.cutoffs[0]
        if n_safe == 9:  # chose A until row 9: very high risk aversion
            return self.cutoffs[-1]
        # gamma lies between the cutoff of the last A row and the cutoff of the first B row
        return (self.cutoffs[n_safe - 1] + self.cutoffs[n_safe]) / 2
