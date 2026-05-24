import streamlit as st
import pandas as pd

# ─── Constants ────────────────────────────────────────────────────────────────
LSSO_RATE = 0.055
LSSO_CAP_LAK = 4_500_000
DEFAULT_EXCHANGE_RATE = 21_630

PIT_BRACKETS = [
    (0,          1_300_000,    0.00),
    (1_300_001,  5_000_000,    0.05),
    (5_000_001,  15_000_000,   0.10),
    (15_000_001, 25_000_000,   0.15),
    (25_000_001, 65_000_000,   0.20),
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
            details.append({
                "Range (LAK)": f"{lo:,} – {hi_label}",
                "Rate": f"{rate:.0%}",
                "Tax (LAK)": f"{portion:,.0f}",
            })
    return total_tax, details


def fmt_lak(v: float) -> str:
    return f"{v:,.0f} ກີບ"


def fmt_usd(v: float) -> str:
    return f"${v:,.2f} USD"


# ─── Styled HTML blocks ────────────────────────────────────────────────────────
def hero_card(net_lak, net_usd, total_gross, total_deductions, effective_rate):
    return f"""
<div style="background:linear-gradient(135deg,#4caf50,#43a047,#388e3c);border-radius:16px;
            padding:16px;color:#fff;box-shadow:0 8px 24px rgba(76,175,80,.35);margin-bottom:12px;">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;">
    <div style="flex:1;min-width:0;">
      <p style="font-size:.7rem;color:#c8e6c9;margin:0 0 2px;">Your Net Salary</p>
      <p style="font-size:1.6rem;font-weight:800;margin:0;word-break:break-word;">{fmt_lak(net_lak)}</p>
      <p style="font-size:.8rem;color:#a5d6a7;margin:4px 0 0;">{fmt_usd(net_usd)}</p>
    </div>
    <div style="width:36px;height:36px;background:rgba(255,255,255,.2);border-radius:10px;
                display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-left:8px;">
      <svg width="20" height="20" fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round"
          d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
    </div>
  </div>
  <div style="margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,.25);
              display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
    <div>
      <p style="font-size:.65rem;color:#c8e6c9;margin:0 0 2px;">Gross</p>
      <p style="font-size:.8rem;font-weight:700;margin:0;word-break:break-word;">{fmt_lak(total_gross)}</p>
    </div>
    <div>
      <p style="font-size:.65rem;color:#c8e6c9;margin:0 0 2px;">Deductions</p>
      <p style="font-size:.8rem;font-weight:700;margin:0;color:#ffcdd2;word-break:break-word;">{fmt_lak(total_deductions)}</p>
    </div>
    <div>
      <p style="font-size:.65rem;color:#c8e6c9;margin:0 0 2px;">Tax Rate</p>
      <p style="font-size:.8rem;font-weight:700;margin:0;">{effective_rate:.1f}%</p>
    </div>
  </div>
</div>
"""


def breakdown_row(icon_svg, icon_bg, icon_color, label, sublabel, value, value_color="#111827", bg=""):
    bg_style = f"background:{bg};" if bg else ""
    return f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:10px 12px;{bg_style}border-bottom:1px solid #f3f4f6;">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:32px;height:32px;background:{icon_bg};border-radius:8px;flex-shrink:0;
                display:flex;align-items:center;justify-content:center;">
      <svg width="16" height="16" fill="none" stroke="{icon_color}" stroke-width="2" viewBox="0 0 24 24">
        {icon_svg}
      </svg>
    </div>
    <div>
      <p style="font-size:.75rem;font-weight:600;color:#111827;margin:0;">{label}</p>
      <p style="font-size:.7rem;color:#6b7280;margin:0;">{sublabel}</p>
    </div>
  </div>
  <p style="font-size:.75rem;font-weight:700;color:{value_color};margin:0;text-align:right;">{value}</p>
</div>
"""


def section_header(title):
    return f"""
<div style="padding:8px 12px;background:#f9fafb;border-bottom:1px solid #e5e7eb;">
  <p style="font-size:.8rem;font-weight:600;color:#111827;margin:0;">{title}</p>
</div>
"""


def card_wrap(content):
    return f"""
<div style="background:#fff;border:1px solid #e5e7eb;border-radius:16px;
            overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.06);margin-bottom:12px;">
  {content}
</div>
"""


# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lao PDR Salary Tax Calculator",
    page_icon="🇱🇦",
    layout="centered",
)

st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
  <div style="width:40px;height:40px;background:linear-gradient(135deg,#4caf50,#388e3c);
              border-radius:12px;display:flex;align-items:center;justify-content:center;
              box-shadow:0 4px 12px rgba(76,175,80,.3);">
    <svg width="20" height="20" fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round"
        d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
    </svg>
  </div>
  <div>
    <h1 style="font-size:1.1rem;font-weight:800;color:#111827;margin:0;line-height:1.2;">Lao PDR Salary Tax</h1>
    <p style="font-size:.7rem;color:#6b7280;margin:0;">Calculate LSSO, PIT &amp; Net Salary</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Disclaimer note ──────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;gap:10px;background:#fffbeb;border:1px solid #fde68a;
            border-radius:12px;padding:10px 12px;margin:8px 0 16px;">
  <svg width="18" height="18" fill="none" stroke="#d97706" stroke-width="2"
       viewBox="0 0 24 24" style="flex-shrink:0;margin-top:1px;">
    <path stroke-linecap="round" stroke-linejoin="round"
      d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
  </svg>
  <p style="font-size:.7rem;color:#92400e;margin:0;line-height:1.6;">
    <strong>Note:</strong> Using 2025 tax rules. Verify USD-LAK rate.
    Estimates only — not official tax advice.
  </p>
</div>
""", unsafe_allow_html=True)

# ─── Inputs ───────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("**Salary Information**")

    col_currency, col_salary = st.columns([1, 2])
    with col_currency:
        currency = st.selectbox("Currency", ["LAK", "USD"], label_visibility="visible")
    with col_salary:
        salary_input = st.number_input(
            "Monthly Gross Salary",
            min_value=0.0,
            value=0.0,
            step=1_000.0 if currency == "LAK" else 10.0,
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
        overtime = st.number_input("Overtime (OT)", min_value=0.0, value=0.0, step=1_000.0)
    with col_other:
        other_allowances = st.number_input("Other Allowances", min_value=0.0, value=0.0, step=1_000.0)
    allowance_currency = st.radio(
        "Allowance currency",
        ["Same as salary", "Always LAK"],
        horizontal=True,
    )

with st.container(border=True):
    st.markdown("**Social Security (LSSO)**")
    st.caption("5.5% of gross salary, capped at 4,500,000 LAK/month")
    include_lsso = st.radio(
        "LSSO",
        ["Yes (5.5%)", "No (Exempt)"],
        horizontal=True,
        label_visibility="collapsed",
    )

col_calc, col_reset = st.columns([3, 1])
with col_calc:
    submitted = st.button("Calculate Net Salary", use_container_width=True, type="primary")
with col_reset:
    reset = st.button("Reset", use_container_width=True)

if reset:
    st.rerun()

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

    st.markdown("---")

    # ── Hero card ─────────────────────────────────────────────────────────────
    st.markdown(
        hero_card(net_lak, net_usd, total_gross_lak, total_deductions, effective_rate),
        unsafe_allow_html=True,
    )

    # ── Detailed breakdown ────────────────────────────────────────────────────
    breakdown_html = section_header("Detailed Breakdown")

    breakdown_html += breakdown_row(
        '<path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>',
        "#eff6ff", "#2563eb",
        "Base Salary", currency,
        fmt_lak(salary_lak),
    )
    breakdown_html += breakdown_row(
        '<path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>',
        "#f0fdf4", "#16a34a",
        "Total Allowances", "All benefits included",
        fmt_lak(allowances_lak), "#16a34a",
    )
    breakdown_html += breakdown_row(
        '<path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>',
        "#f0fdf4", "#4caf50",
        "Gross Salary", "Before deductions",
        fmt_lak(total_gross_lak), "#166534", "#f0fdf4",
    )
    breakdown_html += breakdown_row(
        '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>',
        "#fef2f2", "#dc2626",
        "LSSO Deduction", "5.5% of gross salary",
        f"−{fmt_lak(lsso)}", "#dc2626",
    )
    breakdown_html += breakdown_row(
        '<path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>',
        "#fefce8", "#ca8a04",
        "Taxable Income", "After LSSO",
        fmt_lak(taxable),
    )
    breakdown_html += breakdown_row(
        '<path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>',
        "#fff7ed", "#ea580c",
        "PIT Tax", "Personal Income Tax",
        f"−{fmt_lak(pit)}", "#ea580c",
    )
    # Net salary row (green highlight, no bottom border)
    breakdown_html += f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:12px;background:linear-gradient(135deg,#f0fdf4,#ecfdf5);">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:36px;height:36px;background:linear-gradient(135deg,#22c55e,#059669);
                border-radius:8px;flex-shrink:0;display:flex;align-items:center;justify-content:center;
                box-shadow:0 2px 8px rgba(34,197,94,.3);">
      <svg width="18" height="18" fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
      </svg>
    </div>
    <div>
      <p style="font-size:.8rem;font-weight:700;color:#111827;margin:0;">Net Salary</p>
      <p style="font-size:.7rem;color:#4b5563;margin:0;">Take home pay</p>
    </div>
  </div>
  <div style="text-align:right;">
    <p style="font-size:.9rem;font-weight:800;color:#16a34a;margin:0;">{fmt_lak(net_lak)}</p>
    <p style="font-size:.7rem;color:#22c55e;margin:0;">{fmt_usd(net_usd)}</p>
  </div>
</div>
"""

    st.markdown(card_wrap(breakdown_html), unsafe_allow_html=True)

    # ── PIT brackets ──────────────────────────────────────────────────────────
    if pit_details:
        brackets_html = section_header("Tax Brackets Applied")
        for row in pit_details:
            brackets_html += f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:8px 12px;border-bottom:1px solid #f3f4f6;">
  <div>
    <p style="font-size:.7rem;color:#374151;margin:0;">{row["Range (LAK)"]} LAK</p>
  </div>
  <div style="display:flex;align-items:center;gap:16px;">
    <span style="font-size:.7rem;font-weight:600;background:#fff7ed;color:#c2410c;
                 padding:2px 8px;border-radius:999px;">{row["Rate"]}</span>
    <p style="font-size:.75rem;font-weight:700;color:#ea580c;margin:0;">{row["Tax (LAK)"]} ກີບ</p>
  </div>
</div>
"""
        st.markdown(card_wrap(brackets_html), unsafe_allow_html=True)

    # ── Annual summary ────────────────────────────────────────────────────────
    with st.expander("Annual Summary (× 12 months)"):
        annual_html = ""
        annual_rows = [
            ("Annual Gross Salary", fmt_lak(total_gross_lak * 12), "#111827"),
            ("Annual LSSO", f"−{fmt_lak(lsso * 12)}", "#dc2626"),
            ("Annual PIT", f"−{fmt_lak(pit * 12)}", "#ea580c"),
            ("Annual Net Salary", fmt_lak(net_lak * 12), "#16a34a"),
        ]
        for label, value, color in annual_rows:
            annual_html += f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            padding:8px 12px;border-bottom:1px solid #f3f4f6;">
  <p style="font-size:.75rem;font-weight:600;color:#374151;margin:0;">{label}</p>
  <p style="font-size:.8rem;font-weight:700;color:{color};margin:0;">{value}</p>
</div>
"""
        st.markdown(card_wrap(annual_html), unsafe_allow_html=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "2025 Lao PDR tax rules · LSSO 5.5% capped at 4,500,000 LAK/month · "
    "PIT: 0% → 5% → 10% → 15% → 20% → 25% · "
    "Estimates only — verify with [MoF](https://www.mof.gov.la/)"
)
