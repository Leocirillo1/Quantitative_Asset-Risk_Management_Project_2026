"""Page 1: questionnaire -> risk aversion gamma and constraints of the client."""
import pandas as pd
import streamlit as st

from src.client_profile import ClientProfile
from src.holt_laury import HoltLaury

st.title("Robo-advisor: your investor profile")

hl = HoltLaury()

with st.form("questionnaire"):
    # ---------- Part 1: Holt-Laury ----------
    st.header("1. Your attitude to risk")
    st.write("Imagine these **100 CHF** are your whole portfolio, invested for one year. "
             "In each row, choose the option you prefer.")

    a_good, a_bad = HoltLaury.OPTION_A
    b_good, b_bad = HoltLaury.OPTION_B
    choices = []
    for i, p in enumerate(HoltLaury.PROBABILITIES):
        col1, col2, col3 = st.columns([3, 3, 2])
        col1.write(f"**A:** {p:.0%} → {a_good} CHF, {1 - p:.0%} → {a_bad} CHF")
        col2.write(f"**B:** {p:.0%} → {b_good} CHF, {1 - p:.0%} → {b_bad} CHF")
        choice = col3.radio(f"Row {i + 1}", ["A", "B"], index=None, horizontal=True,
                            label_visibility="collapsed", key=f"hl_{i}")
        choices.append(choice)

    # ---------- Part 2: Risk capacity ----------
    st.header("2. Your situation")
    age = st.selectbox("Your age", list(ClientProfile.AGE))
    horizon = st.selectbox("How long do you plan to invest?", list(ClientProfile.HORIZON))
    needs_money = st.radio("Will you need a large part of this money in the next 3 years?",
                           list(ClientProfile.NEEDS_MONEY), horizontal=True)
    income = st.selectbox("How stable is your income?", list(ClientProfile.INCOME))
    max_loss = st.selectbox("What is the largest loss in one year you could accept?", list(ClientProfile.MAX_LOSS))
    crypto = st.radio("Do you want crypto in your portfolio?", ["No", "Yes"], horizontal=True)

    submitted = st.form_submit_button("Compute my profile")

# ---------- Compute profile ----------
if submitted:
    if None in choices:
        st.error("Answer all 10 rows of part 1, then compute your profile again.")
    else:
        gamma_hl = hl.compute_gamma(choices)
        if gamma_hl is None:
            st.error("Your choices in part 1 switch back and forth between A and B. "
                     "Pick A until the row where B becomes better for you, then B for all the rows below.")
        else:
            st.session_state["profile"] = ClientProfile(gamma_hl, age, horizon, needs_money,
                                                        income, max_loss, crypto)
            # new profile -> we start again from our recommended products and constraints
            for key in ["assets", "constraints"]:
                st.session_state.pop(key, None)

# ---------- Show profile (stays visible for the next pages) ----------
if "profile" in st.session_state:
    profile = st.session_state["profile"]
    st.header(f"Your profile: {profile.label}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Risk willingness (γ)", f"{profile.gamma_willingness:.1f}")
    col2.metric("Minimum γ from your situation", f"{profile.gamma_capacity:.1f}")
    col3.metric("Final γ", f"{profile.gamma:.1f}")

    st.subheader("Our recommended constraints for you")
    c = profile.recommended_constraints
    st.table(pd.DataFrame({
        "Constraint": ["Maximum in equities", "Minimum in bonds", "Maximum in gold and commodities",
                       "Maximum in crypto", "Maximum per product"],
        "Value": [f"{c['max_equity']:.0%}", f"{c['min_bonds']:.0%}", f"{c['max_other']:.0%}",
                  f"{c['max_crypto']:.0%}", f"{c['max_weight_per_asset']:.0%}"],
    }))

    with st.expander("How is γ computed?"):
        st.write("Each row has a γ at which you are indifferent between A and B. "
                 "Your γ is the midpoint between the last row where you chose A and the first where you chose B.")
        st.table(pd.DataFrame({"Row": range(1, 10), "Indifference γ": [round(g, 2) for g in hl.cutoffs]}))

    st.page_link("app_pages/choices.py", label="Next: choose your products and constraints", icon="➡️")
