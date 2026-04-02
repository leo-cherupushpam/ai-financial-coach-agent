"""
AI Financial Coach Agent
========================
Multi-agent financial analysis using OpenAI GPT-4o with structured outputs.

Agents:
  1. Budget Agent   — spending breakdown, health score, reduction opportunities
  2. Savings Agent  — emergency fund sizing, savings rate, automation tips
  3. Debt Agent     — avalanche vs. snowball comparison, recommendation

Tech: OpenAI API (structured outputs) + Streamlit + Plotly
⚠️  Educational guidance only — not licensed financial advice.
"""

import json
import os
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4o"
SYSTEM_DISCLAIMER = (
    "You are an expert financial analyst providing educational guidance. "
    "Base ALL analysis strictly on user-provided data. "
    "Never predict market returns or future income. "
    "This is educational guidance only — not licensed financial advice."
)


# ---------------------------------------------------------------------------
# Pydantic schemas for structured outputs
# ---------------------------------------------------------------------------

class SpendingCategory(BaseModel):
    category: str
    amount: float
    percentage_of_income: float
    benchmark_percentage: float   # industry benchmark (e.g. housing ≤ 30%)
    status: str                   # "healthy" | "over" | "under"
    recommendation: str


class BudgetAnalysis(BaseModel):
    total_income: float
    total_expenses: float
    surplus_deficit: float
    savings_potential: float
    spending_categories: list[SpendingCategory]
    top_reduction_opportunities: list[str]
    budget_health_score: int      # 1–100
    health_score_rationale: str


class SavingsAllocation(BaseModel):
    bucket: str
    monthly_amount: float
    priority: int
    rationale: str


class SavingsStrategy(BaseModel):
    emergency_fund_target: float
    emergency_fund_months: int
    months_to_emergency_fund: int
    monthly_savings_amount: float
    savings_rate_percentage: float
    savings_allocation: list[SavingsAllocation]
    automation_tips: list[str]


class DebtItem(BaseModel):
    name: str
    balance: float
    interest_rate: float
    monthly_payment: float


class DebtReduction(BaseModel):
    total_debt: float
    avalanche_order: list[DebtItem]
    snowball_order: list[DebtItem]
    recommended_method: str       # "avalanche" | "snowball"
    recommended_reason: str
    months_to_debt_free_avalanche: int
    months_to_debt_free_snowball: int
    total_interest_avalanche: float
    total_interest_snowball: float
    interest_savings_with_recommended: float


# ---------------------------------------------------------------------------
# Agent functions (each is one OpenAI structured-output call)
# ---------------------------------------------------------------------------

def run_budget_agent(financial_data: dict) -> BudgetAnalysis:
    prompt = f"""
Analyze this user's monthly financial picture and return a detailed budget analysis.

Monthly Income: ${financial_data['income']:,.2f}
Dependents: {financial_data.get('dependents', 0)}
Expenses by category:
{json.dumps(financial_data['expenses'], indent=2)}

Score their budget health 1–100 (100 = perfect). Compare each category to standard
benchmarks (e.g. housing ≤ 30%, food ≤ 15%, savings ≥ 20%). Identify the top 3
specific, actionable reduction opportunities.
"""
    response = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_DISCLAIMER},
            {"role": "user", "content": prompt},
        ],
        response_format=BudgetAnalysis,
    )
    return response.choices[0].message.parsed


def run_savings_agent(
    financial_data: dict, budget: BudgetAnalysis
) -> SavingsStrategy:
    prompt = f"""
Design a personalized savings plan based on this budget analysis.

Budget Summary:
  - Monthly Income:   ${budget.total_income:,.2f}
  - Monthly Expenses: ${budget.total_expenses:,.2f}
  - Surplus/Deficit:  ${budget.surplus_deficit:,.2f}
  - Savings Potential:${budget.savings_potential:,.2f}
  - Health Score:     {budget.budget_health_score}/100

User context:
  - Dependents: {financial_data.get('dependents', 0)}
  - Existing savings: ${financial_data.get('existing_savings', 0):,.2f}

Standard emergency fund = 3–6 months of expenses. Allocate savings across
meaningful buckets (emergency fund, retirement, short-term goals). Provide
3–5 concrete automation tips.
"""
    response = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_DISCLAIMER},
            {"role": "user", "content": prompt},
        ],
        response_format=SavingsStrategy,
    )
    return response.choices[0].message.parsed


def run_debt_agent(
    financial_data: dict, budget: BudgetAnalysis
) -> Optional[DebtReduction]:
    if not financial_data.get("debts"):
        return None

    prompt = f"""
Compare avalanche vs. snowball debt payoff strategies and recommend the best one.

Debts:
{json.dumps(financial_data['debts'], indent=2)}

Available monthly payment budget (surplus after expenses): ${max(0, budget.surplus_deficit):,.2f}

Calculate precisely:
  - Avalanche: highest interest rate first — total interest paid & months to debt-free
  - Snowball: smallest balance first — total interest paid & months to debt-free
  - Recommend one method with a clear, specific reason for THIS user's situation
  - Compute how much interest the recommended method saves vs. the other
"""
    response = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_DISCLAIMER},
            {"role": "user", "content": prompt},
        ],
        response_format=DebtReduction,
    )
    return response.choices[0].message.parsed


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Financial Coach",
    page_icon="💰",
    layout="wide",
)

st.title("💰 AI Financial Coach Agent")
st.caption(
    "Powered by **OpenAI GPT-4o** · 3-Agent Analysis: Budget → Savings → Debt  "
    "· ⚠️ *Educational guidance only — not licensed financial advice*"
)

# ---------------------------------------------------------------------------
# Sidebar — data input
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📊 Your Financial Data")

    income = st.number_input("Monthly Income ($)", min_value=0, value=5000, step=100)
    dependents = st.number_input("Number of Dependents", min_value=0, value=0, step=1)
    existing_savings = st.number_input("Existing Savings ($)", min_value=0, value=0, step=500)

    st.subheader("Monthly Expenses")

    uploaded_file = st.file_uploader(
        "Upload CSV (columns: Category, Amount)",
        type="csv",
        help="Download template below if needed.",
    )

    expenses: dict[str, float] = {}

    if uploaded_file:
        try:
            df_upload = pd.read_csv(uploaded_file)
            required_cols = {"Category", "Amount"}
            if required_cols.issubset(df_upload.columns):
                expenses = (
                    df_upload.groupby("Category")["Amount"]
                    .sum()
                    .to_dict()
                )
                st.success(f"✅ Loaded {len(df_upload)} transactions across {len(expenses)} categories.")
                with st.expander("Preview"):
                    st.dataframe(df_upload.head(10), use_container_width=True)
            else:
                st.error("CSV must have 'Category' and 'Amount' columns.")
        except Exception as e:
            st.error(f"Could not read CSV: {e}")

    if not expenses:
        st.caption("Or enter manually:")
        default_categories = [
            "Housing / Rent",
            "Food & Groceries",
            "Transportation",
            "Utilities",
            "Healthcare",
            "Entertainment",
            "Clothing",
            "Education",
            "Subscriptions",
            "Other",
        ]
        for cat in default_categories:
            val = st.number_input(cat, min_value=0, value=0, step=50, key=f"exp_{cat}")
            if val > 0:
                expenses[cat] = float(val)

    # CSV template download
    template_df = pd.DataFrame({
        "Date": ["2026-01-01", "2026-01-05"],
        "Category": ["Housing / Rent", "Food & Groceries"],
        "Amount": [1500, 400],
    })
    st.download_button(
        "⬇️ Download CSV Template",
        template_df.to_csv(index=False),
        "template.csv",
        "text/csv",
        use_container_width=True,
    )

    st.subheader("Debts (optional)")
    num_debts = st.number_input("Number of debts to analyze", min_value=0, max_value=10, value=0, step=1)

    debts = []
    for i in range(int(num_debts)):
        with st.expander(f"Debt #{i + 1}"):
            d_name = st.text_input("Name (e.g. Visa Card)", key=f"dname_{i}")
            d_balance = st.number_input("Outstanding Balance ($)", min_value=0, value=0, step=100, key=f"dbal_{i}")
            d_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key=f"drate_{i}")
            d_min = st.number_input("Minimum Monthly Payment ($)", min_value=0, value=0, step=25, key=f"dmin_{i}")
            if d_name and d_balance > 0:
                debts.append({
                    "name": d_name,
                    "balance": d_balance,
                    "rate": d_rate,
                    "min_payment": d_min,
                })

    analyze = st.button("🚀 Analyze My Finances", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Main — results
# ---------------------------------------------------------------------------
if analyze:
    if not expenses or sum(expenses.values()) == 0:
        st.warning("Please enter at least one expense category before analyzing.")
        st.stop()

    financial_data = {
        "income": float(income),
        "expenses": expenses,
        "dependents": int(dependents),
        "existing_savings": float(existing_savings),
        "debts": debts,
    }

    # Run the 3 agents sequentially (each feeds context to the next)
    progress = st.progress(0, text="Starting analysis…")

    with st.spinner(""):
        progress.progress(10, text="💸 Budget Agent — analyzing spending patterns…")
        budget = run_budget_agent(financial_data)

        progress.progress(50, text="🏦 Savings Agent — building your savings plan…")
        savings = run_savings_agent(financial_data, budget)

        progress.progress(80, text="📉 Debt Agent — comparing payoff strategies…")
        debt = run_debt_agent(financial_data, budget)

        progress.progress(100, text="✅ Analysis complete!")

    progress.empty()
    st.success("3-agent analysis complete!")
    st.divider()

    # -------------------------------------------------------------------
    # Budget Results
    # -------------------------------------------------------------------
    st.header("💸 Budget Analysis")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Monthly Income", f"${budget.total_income:,.0f}")
    c2.metric("Monthly Expenses", f"${budget.total_expenses:,.0f}")
    surplus_label = "Surplus" if budget.surplus_deficit >= 0 else "Deficit"
    c3.metric(
        "Surplus / Deficit",
        f"${abs(budget.surplus_deficit):,.0f}",
        delta=surplus_label,
        delta_color="normal" if budget.surplus_deficit >= 0 else "inverse",
    )
    score = budget.budget_health_score
    score_color = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
    c4.metric("Budget Health Score", f"{score_color} {score}/100")

    with st.expander("Score Rationale"):
        st.write(budget.health_score_rationale)

    # Expense pie chart
    if budget.spending_categories:
        df_cats = pd.DataFrame([
            {
                "Category": c.category,
                "Amount ($)": c.amount,
                "% of Income": c.percentage_of_income,
                "Status": c.status,
            }
            for c in budget.spending_categories
        ])
        col_chart, col_table = st.columns([1, 1])
        with col_chart:
            fig_pie = px.pie(
                df_cats,
                values="Amount ($)",
                names="Category",
                title="Expense Breakdown",
                hole=0.4,
                color="Status",
                color_discrete_map={"healthy": "#2ecc71", "over": "#e74c3c", "under": "#f39c12"},
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_table:
            st.dataframe(
                df_cats.style.applymap(
                    lambda v: "color: #e74c3c" if v == "over" else "color: #2ecc71" if v == "healthy" else "",
                    subset=["Status"],
                ),
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("🔍 Top Reduction Opportunities"):
        for opp in budget.top_reduction_opportunities:
            st.markdown(f"- {opp}")

    st.divider()

    # -------------------------------------------------------------------
    # Savings Results
    # -------------------------------------------------------------------
    st.header("🏦 Savings Strategy")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric(
        "Emergency Fund Target",
        f"${savings.emergency_fund_target:,.0f}",
        help=f"{savings.emergency_fund_months} months of expenses",
    )
    s2.metric("Monthly Savings", f"${savings.monthly_savings_amount:,.0f}")
    s3.metric("Savings Rate", f"{savings.savings_rate_percentage:.1f}%")
    s4.metric("Months to Emergency Fund", f"{savings.months_to_emergency_fund} mo")

    if savings.savings_allocation:
        df_alloc = pd.DataFrame([
            {"Bucket": a.bucket, "Monthly ($)": a.monthly_amount, "Priority": a.priority, "Why": a.rationale}
            for a in sorted(savings.savings_allocation, key=lambda x: x.priority)
        ])
        col_bar, col_tips = st.columns([1, 1])
        with col_bar:
            fig_bar = px.bar(
                df_alloc,
                x="Bucket",
                y="Monthly ($)",
                title="Monthly Savings Allocation",
                color="Bucket",
                text="Monthly ($)",
            )
            fig_bar.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
            st.plotly_chart(fig_bar, use_container_width=True)
        with col_tips:
            st.subheader("⚡ Automation Tips")
            for tip in savings.automation_tips:
                st.markdown(f"- {tip}")

    st.divider()

    # -------------------------------------------------------------------
    # Debt Results
    # -------------------------------------------------------------------
    if debt:
        st.header("📉 Debt Reduction Plan")

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Total Debt", f"${debt.total_debt:,.0f}")
        d2.metric("Debt-Free (Avalanche)", f"{debt.months_to_debt_free_avalanche} mo")
        d3.metric("Debt-Free (Snowball)", f"{debt.months_to_debt_free_snowball} mo")
        d4.metric(
            "Interest Saved (Recommended)",
            f"${debt.interest_savings_with_recommended:,.0f}",
        )

        rec_emoji = "🏔️" if debt.recommended_method.lower() == "avalanche" else "⛄"
        st.info(
            f"**{rec_emoji} Recommended: {debt.recommended_method.title()}**  \n{debt.recommended_reason}"
        )

        # Interest comparison bar chart
        fig_debt = go.Figure(data=[
            go.Bar(
                name="Avalanche",
                x=["Total Interest Paid"],
                y=[debt.total_interest_avalanche],
                marker_color="#2ecc71",
                text=[f"${debt.total_interest_avalanche:,.0f}"],
                textposition="outside",
            ),
            go.Bar(
                name="Snowball",
                x=["Total Interest Paid"],
                y=[debt.total_interest_snowball],
                marker_color="#e74c3c",
                text=[f"${debt.total_interest_snowball:,.0f}"],
                textposition="outside",
            ),
        ])
        fig_debt.update_layout(title="Total Interest: Avalanche vs. Snowball", barmode="group")
        st.plotly_chart(fig_debt, use_container_width=True)

        col_av, col_sb = st.columns(2)
        with col_av:
            st.subheader("🏔️ Avalanche Order (Highest Rate First)")
            for i, d in enumerate(debt.avalanche_order, 1):
                st.markdown(
                    f"{i}. **{d.name}** — ${d.balance:,.0f} @ {d.interest_rate:.1f}% "
                    f"· Min: ${d.monthly_payment:,.0f}/mo"
                )
        with col_sb:
            st.subheader("⛄ Snowball Order (Smallest Balance First)")
            for i, d in enumerate(debt.snowball_order, 1):
                st.markdown(
                    f"{i}. **{d.name}** — ${d.balance:,.0f} @ {d.interest_rate:.1f}% "
                    f"· Min: ${d.monthly_payment:,.0f}/mo"
                )

    else:
        st.info("No debt data entered — skip this section or add debts in the sidebar.")

    st.divider()
    st.caption(
        "⚠️ This analysis is for **educational purposes only** and does not constitute licensed financial advice. "
        "Please consult a Certified Financial Planner (CFP) for personalized professional guidance."
    )
