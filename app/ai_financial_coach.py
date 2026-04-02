"""
AI Financial Coach Agent
========================
Multi-agent financial analysis using OpenAI GPT-4o with structured outputs.

Agents:
  1. Budget Agent     — spending breakdown, health score, benchmark comparison
  2. Savings Agent    — emergency fund sizing, savings rate, automation tips
  3. Debt Agent       — avalanche vs. snowball comparison, recommendation
  4. Synthesis Agent  — prioritized action plan across all 3 domains

Tech: OpenAI API (structured outputs) + Streamlit + Plotly
⚠️  Educational guidance only — not licensed financial advice.
"""

import json
import os
from datetime import datetime
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
# Sample data for instant demo
# ---------------------------------------------------------------------------
SAMPLE_DATA = {
    "income": 5000,
    "dependents": 1,
    "existing_savings": 2000,
    "expenses": {
        "Housing / Rent": 1800,
        "Food & Groceries": 650,
        "Transportation": 400,
        "Utilities": 150,
        "Entertainment": 320,
        "Subscriptions": 120,
        "Healthcare": 100,
        "Clothing": 80,
        "Other": 180,
    },
    "debts": [
        {"name": "Credit Card", "balance": 4500, "rate": 22.99, "min_payment": 90},
        {"name": "Student Loan", "balance": 18000, "rate": 5.5, "min_payment": 200},
        {"name": "Car Loan", "balance": 8000, "rate": 7.0, "min_payment": 175},
    ],
}

# ---------------------------------------------------------------------------
# Pydantic schemas for structured outputs
# ---------------------------------------------------------------------------

class SpendingCategory(BaseModel):
    category: str
    amount: float
    percentage_of_income: float
    benchmark_percentage: float
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
    recommended_method: str
    recommended_reason: str
    months_to_debt_free_avalanche: int
    months_to_debt_free_snowball: int
    total_interest_avalanche: float
    total_interest_snowball: float
    interest_savings_with_recommended: float


class ActionItem(BaseModel):
    priority: int                 # 1 = most urgent
    domain: str                   # "budget" | "savings" | "debt"
    action: str                   # specific, imperative ("Cancel Netflix and Hulu — save $30/mo")
    impact: str                   # what this achieves in plain English
    effort: str                   # "5 minutes" | "30 minutes" | "1 hour"
    deadline: str                 # "today" | "this week" | "this month"


class ActionPlan(BaseModel):
    overall_health: str           # "critical" | "needs work" | "good" | "excellent"
    one_line_summary: str         # plain English, ≤ 20 words
    top_actions: list[ActionItem] # top 5, ordered by priority
    one_year_outlook: str         # what their finances look like in 12 months if they follow this


# ---------------------------------------------------------------------------
# Agent functions
# ---------------------------------------------------------------------------

def run_budget_agent(financial_data: dict) -> BudgetAnalysis:
    prompt = f"""
Analyze this user's monthly financial picture and return a detailed budget analysis.

Monthly Income: ${financial_data['income']:,.2f}
Dependents: {financial_data.get('dependents', 0)}
Expenses by category:
{json.dumps(financial_data['expenses'], indent=2)}

Score their budget health 1–100 (100 = perfect). Compare each category to standard
benchmarks (housing ≤ 30%, food ≤ 15%, transport ≤ 10%, entertainment ≤ 5%,
savings ≥ 20%). Identify top 3 specific, actionable reduction opportunities.
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


def run_savings_agent(financial_data: dict, budget: BudgetAnalysis) -> SavingsStrategy:
    prompt = f"""
Design a personalized savings plan based on this budget analysis.

Budget Summary:
  - Monthly Income:    ${budget.total_income:,.2f}
  - Monthly Expenses:  ${budget.total_expenses:,.2f}
  - Surplus/Deficit:   ${budget.surplus_deficit:,.2f}
  - Savings Potential: ${budget.savings_potential:,.2f}
  - Health Score:      {budget.budget_health_score}/100

User context:
  - Dependents: {financial_data.get('dependents', 0)}
  - Existing savings: ${financial_data.get('existing_savings', 0):,.2f}

Standard emergency fund = 3–6 months of expenses. Allocate savings across
meaningful buckets (emergency fund, retirement, short-term goals).
Provide 4–5 concrete automation tips (specific apps, account types, amounts).
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


def run_debt_agent(financial_data: dict, budget: BudgetAnalysis) -> Optional[DebtReduction]:
    if not financial_data.get("debts"):
        return None

    prompt = f"""
Compare avalanche vs. snowball debt payoff strategies and recommend the best one.

Debts:
{json.dumps(financial_data['debts'], indent=2)}

Available monthly surplus (after all expenses): ${max(0, budget.surplus_deficit):,.2f}

Calculate precisely:
  - Avalanche order (highest rate first): total interest paid, months to debt-free
  - Snowball order (smallest balance first): total interest paid, months to debt-free
  - Recommend one method with a specific reason tied to THIS user's situation
  - How much interest the recommended method saves vs. the alternative
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


def run_synthesis_agent(
    financial_data: dict,
    budget: BudgetAnalysis,
    savings: SavingsStrategy,
    debt: Optional[DebtReduction],
) -> ActionPlan:
    debt_summary = (
        f"Total debt: ${debt.total_debt:,.2f}. Recommended method: {debt.recommended_method}. "
        f"Months to debt-free: {debt.months_to_debt_free_avalanche}."
        if debt else "No debt entered."
    )
    prompt = f"""
You are a senior financial coach. Synthesize the analysis from 3 specialist agents
into a clear, prioritized action plan for this user.

Budget Agent results:
  - Health score: {budget.budget_health_score}/100
  - Surplus/Deficit: ${budget.surplus_deficit:,.2f}/mo
  - Top opportunities: {budget.top_reduction_opportunities}

Savings Agent results:
  - Emergency fund target: ${savings.emergency_fund_target:,.2f} ({savings.months_to_emergency_fund} months away)
  - Recommended savings rate: {savings.savings_rate_percentage:.1f}%
  - Top automation tip: {savings.automation_tips[0] if savings.automation_tips else 'N/A'}

Debt Agent results:
  {debt_summary}

Produce:
1. An overall health rating: critical / needs work / good / excellent
2. A one-line plain-English summary (≤ 20 words, no jargon)
3. Top 5 prioritized actions — each must be SPECIFIC and ACTIONABLE (not "save more money")
   Include effort in minutes and a deadline (today / this week / this month)
4. A one-year outlook if they follow the plan
"""
    response = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_DISCLAIMER},
            {"role": "user", "content": prompt},
        ],
        response_format=ActionPlan,
    )
    return response.choices[0].message.parsed


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------

def generate_report(
    financial_data: dict,
    budget: BudgetAnalysis,
    savings: SavingsStrategy,
    debt: Optional[DebtReduction],
    plan: ActionPlan,
) -> str:
    date = datetime.now().strftime("%B %d, %Y")
    lines = [
        f"# AI Financial Coach Report",
        f"*Generated: {date}*",
        f"> ⚠️ Educational guidance only — not licensed financial advice.",
        "",
        f"## Overall Assessment",
        f"**Health:** {plan.overall_health.upper()}",
        f"**Summary:** {plan.one_line_summary}",
        f"**Budget Health Score:** {budget.budget_health_score}/100",
        "",
        f"## Your Top 5 Actions",
    ]
    for item in plan.top_actions:
        lines.append(f"{item.priority}. **[{item.domain.upper()}]** {item.action}")
        lines.append(f"   - Impact: {item.impact}")
        lines.append(f"   - Effort: {item.effort} | Deadline: {item.deadline}")
    lines += [
        "",
        f"## Budget Snapshot",
        f"- Monthly Income: ${budget.total_income:,.0f}",
        f"- Monthly Expenses: ${budget.total_expenses:,.0f}",
        f"- Surplus/Deficit: ${budget.surplus_deficit:,.0f}",
        "",
        "**Reduction Opportunities:**",
    ]
    for opp in budget.top_reduction_opportunities:
        lines.append(f"- {opp}")
    lines += [
        "",
        f"## Savings Plan",
        f"- Emergency Fund Target: ${savings.emergency_fund_target:,.0f} ({savings.emergency_fund_months} months)",
        f"- Monthly Savings: ${savings.monthly_savings_amount:,.0f}",
        f"- Savings Rate: {savings.savings_rate_percentage:.1f}%",
        f"- Months to Emergency Fund: {savings.months_to_emergency_fund}",
    ]
    if debt:
        lines += [
            "",
            f"## Debt Plan",
            f"- Total Debt: ${debt.total_debt:,.0f}",
            f"- Recommended Method: {debt.recommended_method.title()}",
            f"- Months to Debt-Free: {debt.months_to_debt_free_avalanche} (avalanche) / {debt.months_to_debt_free_snowball} (snowball)",
            f"- Interest Saved: ${debt.interest_savings_with_recommended:,.0f}",
        ]
    lines += [
        "",
        f"## 12-Month Outlook",
        plan.one_year_outlook,
        "",
        "---",
        "*Powered by AI Financial Coach · OpenAI GPT-4o*",
    ]
    return "\n".join(lines)


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
    "Powered by **OpenAI GPT-4o** · 4-Agent Analysis: Budget → Savings → Debt → Action Plan  "
    "· ⚠️ *Educational guidance only — not licensed financial advice*"
)

# ---------------------------------------------------------------------------
# Sidebar — data input
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📊 Your Financial Data")

    # Sample data loader
    if st.button("⚡ Load Sample Data", use_container_width=True, help="Instantly demo with realistic sample data"):
        st.session_state["sample_loaded"] = True

    use_sample = st.session_state.get("sample_loaded", False)

    income = st.number_input(
        "Monthly Income ($)", min_value=0,
        value=SAMPLE_DATA["income"] if use_sample else 5000, step=100,
    )
    dependents = st.number_input(
        "Number of Dependents", min_value=0,
        value=SAMPLE_DATA["dependents"] if use_sample else 0, step=1,
    )
    existing_savings = st.number_input(
        "Existing Savings ($)", min_value=0,
        value=SAMPLE_DATA["existing_savings"] if use_sample else 0, step=500,
    )

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
            if {"Category", "Amount"}.issubset(df_upload.columns):
                expenses = df_upload.groupby("Category")["Amount"].sum().to_dict()
                st.success(f"✅ {len(df_upload)} transactions across {len(expenses)} categories.")
                with st.expander("Preview"):
                    st.dataframe(df_upload.head(10), use_container_width=True)
            else:
                st.error("CSV must have 'Category' and 'Amount' columns.")
        except Exception as e:
            st.error(f"Could not read CSV: {e}")

    if not expenses:
        caption = "Sample data loaded — edit if needed:" if use_sample else "Enter monthly amounts:"
        st.caption(caption)
        default_categories = [
            "Housing / Rent", "Food & Groceries", "Transportation",
            "Utilities", "Healthcare", "Entertainment",
            "Clothing", "Education", "Subscriptions", "Other",
        ]
        for cat in default_categories:
            default_val = int(SAMPLE_DATA["expenses"].get(cat, 0)) if use_sample else 0
            val = st.number_input(cat, min_value=0, value=default_val, step=50, key=f"exp_{cat}")
            if val > 0:
                expenses[cat] = float(val)

    # CSV template download
    template_df = pd.DataFrame({
        "Date": ["2026-01-01", "2026-01-05"],
        "Category": ["Housing / Rent", "Food & Groceries"],
        "Amount": [1500, 400],
    })
    st.download_button(
        "⬇️ Download CSV Template", template_df.to_csv(index=False),
        "template.csv", "text/csv", use_container_width=True,
    )

    st.subheader("Debts (optional)")
    default_num_debts = len(SAMPLE_DATA["debts"]) if use_sample else 0
    num_debts = st.number_input(
        "Number of debts to analyze", min_value=0, max_value=10,
        value=default_num_debts, step=1,
    )

    debts = []
    for i in range(int(num_debts)):
        sample_debt = SAMPLE_DATA["debts"][i] if (use_sample and i < len(SAMPLE_DATA["debts"])) else {}
        with st.expander(f"Debt #{i + 1}", expanded=use_sample):
            d_name = st.text_input("Name", value=sample_debt.get("name", ""), key=f"dname_{i}")
            d_balance = st.number_input("Balance ($)", min_value=0, value=sample_debt.get("balance", 0), step=100, key=f"dbal_{i}")
            d_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=100.0, value=sample_debt.get("rate", 0.0), step=0.5, key=f"drate_{i}")
            d_min = st.number_input("Min Payment ($)", min_value=0, value=sample_debt.get("min_payment", 0), step=25, key=f"dmin_{i}")
            if d_name and d_balance > 0:
                debts.append({"name": d_name, "balance": d_balance, "rate": d_rate, "min_payment": d_min})

    analyze = st.button("🚀 Analyze My Finances", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Main — results
# ---------------------------------------------------------------------------
if analyze:
    if not expenses or sum(expenses.values()) == 0:
        st.warning("Please enter at least one expense before analyzing.")
        st.stop()

    financial_data = {
        "income": float(income),
        "expenses": expenses,
        "dependents": int(dependents),
        "existing_savings": float(existing_savings),
        "debts": debts,
    }

    progress = st.progress(0, text="Starting 4-agent analysis…")

    with st.spinner(""):
        progress.progress(10, text="💸 Budget Agent — analyzing spending patterns…")
        budget = run_budget_agent(financial_data)

        progress.progress(35, text="🏦 Savings Agent — building your savings plan…")
        savings = run_savings_agent(financial_data, budget)

        progress.progress(60, text="📉 Debt Agent — comparing payoff strategies…")
        debt = run_debt_agent(financial_data, budget)

        progress.progress(80, text="🎯 Synthesis Agent — building your action plan…")
        plan = run_synthesis_agent(financial_data, budget, savings, debt)

        progress.progress(100, text="✅ Analysis complete!")

    progress.empty()

    # -------------------------------------------------------------------
    # Financial Health Banner
    # -------------------------------------------------------------------
    health_config = {
        "critical":   {"color": "#e74c3c", "emoji": "🔴", "bg": "#fdf0f0"},
        "needs work": {"color": "#f39c12", "emoji": "🟡", "bg": "#fef9f0"},
        "good":       {"color": "#2ecc71", "emoji": "🟢", "bg": "#f0fdf4"},
        "excellent":  {"color": "#27ae60", "emoji": "✅", "bg": "#f0fdf4"},
    }
    h = health_config.get(plan.overall_health.lower(), health_config["needs work"])

    st.markdown(
        f"""
        <div style="background:{h['bg']};border-left:5px solid {h['color']};
                    padding:1rem 1.5rem;border-radius:8px;margin-bottom:1rem;">
            <h3 style="margin:0;color:{h['color']};">{h['emoji']} Financial Health: {plan.overall_health.upper()}</h3>
            <p style="margin:0.25rem 0 0;font-size:1.05rem;">{plan.one_line_summary}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Download report
    report_md = generate_report(financial_data, budget, savings, debt, plan)
    st.download_button(
        "⬇️ Download Full Report",
        report_md,
        file_name=f"financial_report_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown",
        help="Download your full analysis as a markdown report",
    )

    st.divider()

    # -------------------------------------------------------------------
    # Action Plan — synthesized output (the product's north star)
    # -------------------------------------------------------------------
    st.header("🎯 Your Action Plan")
    st.caption("Prioritized actions across budget, savings, and debt — ordered by impact.")

    domain_colors = {"budget": "#e74c3c", "savings": "#2ecc71", "debt": "#3498db"}
    effort_emoji = {"5 minutes": "⚡", "30 minutes": "🕐", "1 hour": "⏱️"}

    for item in plan.top_actions:
        color = domain_colors.get(item.domain.lower(), "#95a5a6")
        e_emoji = next((v for k, v in effort_emoji.items() if k in item.effort.lower()), "🕐")
        with st.container(border=True):
            col_num, col_content = st.columns([0.08, 0.92])
            with col_num:
                st.markdown(f"<h2 style='color:{color};margin:0;'>#{item.priority}</h2>", unsafe_allow_html=True)
            with col_content:
                st.markdown(f"**{item.action}**")
                st.caption(f"📈 {item.impact}  ·  {e_emoji} {item.effort}  ·  📅 {item.deadline.title()}")
                st.markdown(
                    f"<span style='background:{color}22;color:{color};padding:2px 8px;"
                    f"border-radius:12px;font-size:0.75rem;font-weight:600;'>{item.domain.upper()}</span>",
                    unsafe_allow_html=True,
                )

    with st.expander("🔭 12-Month Outlook"):
        st.info(plan.one_year_outlook)

    st.divider()

    # -------------------------------------------------------------------
    # Budget Results
    # -------------------------------------------------------------------
    st.header("💸 Budget Analysis")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Monthly Income", f"${budget.total_income:,.0f}")
    c2.metric("Monthly Expenses", f"${budget.total_expenses:,.0f}")
    c3.metric(
        "Surplus / Deficit",
        f"${abs(budget.surplus_deficit):,.0f}",
        delta="Surplus" if budget.surplus_deficit >= 0 else "Deficit",
        delta_color="normal" if budget.surplus_deficit >= 0 else "inverse",
    )
    score = budget.budget_health_score
    score_emoji = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
    c4.metric("Budget Health Score", f"{score_emoji} {score}/100")

    with st.expander("Score Rationale"):
        st.write(budget.health_score_rationale)

    if budget.spending_categories:
        df_cats = pd.DataFrame([
            {
                "Category": c.category,
                "Amount ($)": c.amount,
                "Your % of Income": c.percentage_of_income,
                "Benchmark %": c.benchmark_percentage,
                "Status": c.status,
            }
            for c in budget.spending_categories
        ])

        col_pie, col_bench = st.columns(2)

        with col_pie:
            fig_pie = px.pie(
                df_cats, values="Amount ($)", names="Category",
                title="Expense Breakdown", hole=0.4,
                color="Status",
                color_discrete_map={"healthy": "#2ecc71", "over": "#e74c3c", "under": "#f39c12"},
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_bench:
            # Spending vs benchmark chart
            df_bench = df_cats[["Category", "Your % of Income", "Benchmark %"]].copy()
            fig_bench = go.Figure()
            fig_bench.add_trace(go.Bar(
                name="Your Spending %",
                x=df_bench["Category"],
                y=df_bench["Your % of Income"],
                marker_color=[
                    "#e74c3c" if row["Your % of Income"] > row["Benchmark %"] else "#2ecc71"
                    for _, row in df_bench.iterrows()
                ],
            ))
            fig_bench.add_trace(go.Scatter(
                name="Benchmark %",
                x=df_bench["Category"],
                y=df_bench["Benchmark %"],
                mode="markers",
                marker=dict(symbol="line-ew", size=12, color="#333", line=dict(width=2, color="#333")),
            ))
            fig_bench.update_layout(
                title="Your Spending vs. Benchmark",
                xaxis_tickangle=-30,
                yaxis_title="% of Income",
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(fig_bench, use_container_width=True)

        with st.expander("🔍 Top Reduction Opportunities"):
            for opp in budget.top_reduction_opportunities:
                st.markdown(f"- {opp}")

    st.divider()

    # -------------------------------------------------------------------
    # Savings Results
    # -------------------------------------------------------------------
    st.header("🏦 Savings Strategy")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Emergency Fund Target", f"${savings.emergency_fund_target:,.0f}",
              help=f"{savings.emergency_fund_months} months of expenses")
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
                df_alloc, x="Bucket", y="Monthly ($)",
                title="Monthly Savings Allocation", color="Bucket", text="Monthly ($)",
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
        d4.metric("Interest Saved (Recommended)", f"${debt.interest_savings_with_recommended:,.0f}")

        rec_emoji = "🏔️" if debt.recommended_method.lower() == "avalanche" else "⛄"
        st.info(f"**{rec_emoji} Recommended: {debt.recommended_method.title()}**  \n{debt.recommended_reason}")

        fig_debt = go.Figure(data=[
            go.Bar(name="Avalanche", x=["Total Interest Paid"], y=[debt.total_interest_avalanche],
                   marker_color="#2ecc71", text=[f"${debt.total_interest_avalanche:,.0f}"], textposition="outside"),
            go.Bar(name="Snowball", x=["Total Interest Paid"], y=[debt.total_interest_snowball],
                   marker_color="#e74c3c", text=[f"${debt.total_interest_snowball:,.0f}"], textposition="outside"),
        ])
        fig_debt.update_layout(title="Total Interest: Avalanche vs. Snowball", barmode="group")
        st.plotly_chart(fig_debt, use_container_width=True)

        col_av, col_sb = st.columns(2)
        with col_av:
            st.subheader("🏔️ Avalanche (Highest Rate First)")
            for i, d in enumerate(debt.avalanche_order, 1):
                st.markdown(f"{i}. **{d.name}** — ${d.balance:,.0f} @ {d.interest_rate:.1f}% · Min: ${d.monthly_payment:,.0f}/mo")
        with col_sb:
            st.subheader("⛄ Snowball (Smallest Balance First)")
            for i, d in enumerate(debt.snowball_order, 1):
                st.markdown(f"{i}. **{d.name}** — ${d.balance:,.0f} @ {d.interest_rate:.1f}% · Min: ${d.monthly_payment:,.0f}/mo")

    else:
        st.info("No debt entered — add debts in the sidebar to see payoff comparison.")

    st.divider()
    st.caption(
        "⚠️ This analysis is **educational guidance only** and does not constitute licensed financial advice. "
        "Consult a Certified Financial Planner (CFP) for professional guidance."
    )
