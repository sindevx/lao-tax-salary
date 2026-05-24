import streamlit as st

# ─── Constants ────────────────────────────────────────────────────────────────
LSSO_RATE = 0.055
LSSO_CAP_LAK = 4_500_000
DEFAULT_EXCHANGE_RATE = 21_630

PIT_BRACKETS = [
    (0,          1_300_000,   0.00),
    (1_300_001,  5_000_000,   0.05),
    (5_000_001,  15_000_000,  0.10),
    (15_000_001, 25_000_000,  0.15),
    (25_000_001, 65_000_000,  0.20),
    (65_000_001, float("inf"), 0.25),
]


# ─── Calculation helpers ───────────────────────────────────────────────────────
def calc_lsso(gross_lak: float, include: bool) -> float:
    if not include:
        return 0.0
    return min(gross_lak, LSSO_CAP_LAK) * LSSO_RATE


def calc_pit(taxable: float) -> tuple[float, list[dict]]:
    total_tax = 0.0
    details: list[dict] = []
    for lo, hi, rate in PIT_BRACKETS:
        if taxable < lo:
            break
        portion = (min(taxable, hi) - lo + 1) * rate
        if portion > 0:
            total_tax += portion
            hi_label = "∞" if hi == float("inf") else f"{hi:,.0f}"
            details.append({"Range (LAK)": f"{lo:,} – {hi_label}", "Rate": f"{rate:.0%}", "Tax (LAK)": portion})
    return total_tax, details


def fmt_lak(amount: float) -> str:
    return f"{amount:,.0f} ກີບ"


def fmt_usd(amount: float) -> str:
    return f"${amount:,.2f} USD"


# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lao PDR Salary Tax Calculator",
    page_icon="🇱🇦",
    layout="centered",
)

st.title("🇱🇦 Lao PDR Salary Tax Calculator")
st.caption("Estimates LSSO, PIT, and net monthly salary · 2025 tax rules · Not official tax advice")

# ─── Inputs ───────────────────────────────────────────────────────────────────
with st.form("calculator"):
    col_currency, col_salary = st.columns([1, 2])

    with col_currency:
        currency = st.selectbox("Currency", ["LAK", "USD"])

    with col_salary:
        salary_input = st.number_input(
            "Monthly Gross Salary",
            min_value=0.0,
            value=0.0,
            step=1000.0 if currency == "LAK" else 10.0,
            format="%.2f",
        )

    if currency == "USD":
        exchange_rate = st.number_input(
            "Exchange Rate (1 USD = ? LAK)",
            min_value=1.0,
            value=float(DEFAULT_EXCHANGE_RATE),
            step=10.0,
            format="%.2f",
        )
    else:
        exchange_rate = float(DEFAULT_EXCHANGE_RATE)

    with st.expander("Allowances & Benefits (optional)"):
        col_ot, col_other = st.columns(2)
        with col_ot:
            overtime = st.number_input("Overtime (OT)", min_value=0.0, value=0.0, step=1000.0)
        with col_other:
            other_allowances = st.number_input("Other Allowances", min_value=0.0, value=0.0, step=1000.0)
        allowance_currency = st.radio(
            "Allowance currency",
            ["Same as salary", "Always LAK"],
            horizontal=True,
        )

    include_lsso = st.radio(
        "Social Security (LSSO) — 5.5%, capped at 4,500,000 LAK",
        ["Yes (5.5%)", "No (Exempt)"],
        horizontal=True,
    )

    submitted = st.form_submit_button("Calculate Net Salary", use_container_width=True, type="primary")

# ─── Calculation & results ────────────────────────────────────────────────────
if submitted:
    salary_lak = salary_input * exchange_rate if currency == "USD" else salary_input

    if allowance_currency == "Same as salary" and currency == "USD":
        allowances_lak = (overtime + other_allowances) * exchange_rate
    else:
        allowances_lak = overtime + other_allowances

    total_gross_lak = salary_lak + allowances_lak

    lsso = calc_lsso(total_gross_lak, include_lsso == "Yes (5.5%)")
    taxable = max(0.0, total_gross_lak - lsso)
    pit, pit_details = calc_pit(taxable)
    net_lak = total_gross_lak - lsso - pit
    net_usd = net_lak / exchange_rate
    total_deductions = lsso + pit
    effective_rate = (total_deductions / total_gross_lak * 100) if total_gross_lak > 0 else 0.0

    # ── Net salary highlight ──────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Result")

    col1, col2 = st.columns(2)
    col1.metric("Net Salary (LAK)", fmt_lak(net_lak))
    col2.metric("Net Salary (USD)", fmt_usd(net_usd))

    # ── Breakdown ─────────────────────────────────────────────────────────────
    st.markdown("##### Breakdown")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Total Gross", fmt_lak(total_gross_lak))
    b2.metric("LSSO", f"−{fmt_lak(lsso)}")
    b3.metric("PIT", f"−{fmt_lak(pit)}")
    b4.metric("Effective Rate", f"{effective_rate:.1f}%")

    # ── Detail rows ───────────────────────────────────────────────────────────
    with st.expander("Detailed breakdown"):
        rows = {
            "Gross Salary": fmt_lak(salary_lak),
            "Total Allowances": fmt_lak(allowances_lak),
            "Total Gross": fmt_lak(total_gross_lak),
            "LSSO Deduction": f"−{fmt_lak(lsso)}",
            "Taxable Income (after LSSO)": fmt_lak(taxable),
            "PIT": f"−{fmt_lak(pit)}",
            "Net Salary": fmt_lak(net_lak),
        }
        for label, value in rows.items():
            c1, c2 = st.columns([2, 1])
            c1.write(label)
            c2.write(value)

    # ── PIT bracket table ─────────────────────────────────────────────────────
    if pit_details:
        with st.expander("PIT bracket details"):
            import pandas as pd
            df = pd.DataFrame(pit_details)
            df["Tax (LAK)"] = df["Tax (LAK)"].map(lambda x: f"{x:,.0f}")
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Annual summary ────────────────────────────────────────────────────────
    with st.expander("Annual summary (× 12 months)"):
        a1, a2, a3 = st.columns(3)
        a1.metric("Annual Gross", fmt_lak(total_gross_lak * 12))
        a2.metric("Annual LSSO", fmt_lak(lsso * 12))
        a3.metric("Annual PIT", fmt_lak(pit * 12))
        st.metric("Annual Net Salary", fmt_lak(net_lak * 12))

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "2025 Lao PDR tax rules · LSSO: 5.5% capped at 4,500,000 LAK/month · "
    "PIT brackets: 0% → 5% → 10% → 15% → 20% → 25% · "
    "This tool provides estimates only — verify with [MoF](https://www.mof.gov.la/)."
)
