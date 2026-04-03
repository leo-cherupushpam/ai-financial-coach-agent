"""
AI Financial Coach Agent — v1.5
================================
Multi-agent financial analysis using OpenAI GPT-4o with structured outputs.

Features:
  - 4 specialized agents (Budget, Savings, Debt, Synthesis)
  - Session history (last 3 analyses stored locally)
  - Progress tracking (budget score & spending deltas)
  - Action completion tracking
  - Side-by-side comparison view

Tech: OpenAI API + Streamlit + Plotly + Local JSON storage
⚠️  Educational guidance only — not licensed financial advice.
"""

import json
import os
from datetime import datetime
from pathlib import Path
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

# Storage paths
SESSIONS_FILE = Path(__file__).parent / "sessions.json"
ACTIONS_FILE = Path(__file__).parent / "actions_tracking.json"

# ---------------------------------------------------------------------------
# Session Manager — handle persistence
# ---------------------------------------------------------------------------

class SessionManager:
    """Manages session history (last 3 analyses)."""

    @staticmethod
    def save_session(analysis_data: dict) -> str:
        """Save analysis and return session_id."""
        sessions = SessionManager.load_sessions()

        session_id = datetime.now().isoformat()
        session = {
            "id": session_id,
            "date": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "timestamp": session_id,
            "financial_data": analysis_data["financial_data"],
            "budget": analysis_data["budget"].model_dump(),
            "savings": analysis_data["savings"].model_dump(),
            "debt": analysis_data["debt"].model_dump() if analysis_data["debt"] else None,
            "plan": analysis_data["plan"].model_dump(),
        }

        sessions.insert(0, session)  # Most recent first
        sessions = sessions[:3]  # Keep only last 3

        with open(SESSIONS_FILE, "w") as f:
            json.dump(sessions, f, indent=2, default=str)

        return session_id

    @staticmethod
    def load_sessions() -> list:
        """Load all stored sessions."""
        if not SESSIONS_FILE.exists():
            return []
        with open(SESSIONS_FILE) as f:
            return json.load(f)

    @staticmethod
    def get_session(session_id: str) -> Optional[dict]:
        """Retrieve a specific session."""
        sessions = SessionManager.load_sessions()
        for s in sessions:
            if s["id"] == session_id:
                return s
        return None

    @staticmethod
    def compare_sessions(session1_id: str, session2_id: str) -> dict:
        """Compare two sessions and return deltas."""
        s1 = SessionManager.get_session(session1_id)
        s2 = SessionManager.get_session(session2_id)

        if not s1 or not s2:
            return {}

        return {
            "date1": s1["date"],
            "date2": s2["date"],
            "budget_score_delta": s2["budget"]["budget_health_score"] - s1["budget"]["budget_health_score"],
            "total_expenses_delta": s2["budget"]["total_expenses"] - s1["budget"]["total_expenses"],
            "total_expenses_pct_delta": ((s2["budget"]["total_expenses"] - s1["budget"]["total_expenses"]) / s1["budget"]["total_expenses"] * 100) if s1["budget"]["total_expenses"] > 0 else 0,
            "surplus_delta": s2["budget"]["surplus_deficit"] - s1["budget"]["surplus_deficit"],
            "savings_rate_delta": s2["savings"]["savings_rate_percentage"] - s1["savings"]["savings_rate_percentage"],
        }


class ActionTracker:
    """Track completion of recommended actions."""

    @staticmethod
    def save_action_completion(session_id: str, action_priority: int, completed: bool):
        """Mark an action as completed or incomplete."""
        tracking = ActionTracker.load_tracking()

        if session_id not in tracking:
            tracking[session_id] = {}

        tracking[session_id][str(action_priority)] = completed

        with open(ACTIONS_FILE, "w") as f:
            json.dump(tracking, f, indent=2)

    @staticmethod
    def load_tracking() -> dict:
        """Load action completion tracking."""
        if not ACTIONS_FILE.exists():
            return {}
        with open(ACTIONS_FILE) as f:
            return json.load(f)

    @staticmethod
    def get_session_completion(session_id: str) -> dict:
        """Get completion status for a session's actions."""
        tracking = ActionTracker.load_tracking()
        return tracking.get(session_id, {})


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
    action: str                   # specific, imperative
    impact: str                   # what this achieves
    effort: str                   # "5 minutes" | "30 minutes" | "1 hour"
    deadline: str                 # "today" | "this week" | "this month"


class ActionPlan(BaseModel):
    overall_health: str           # "critical" | "needs work" | "good" | "excellent"
    one_line_summary: str         # plain English, ≤ 20 words
    top_actions: list[ActionItem] # top 5
    one_year_outlook: str


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
Provide 4–5 concrete automation tips.
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

Available monthly surplus: ${max(0, budget.surplus_deficit):,.2f}

Calculate precisely:
  - Avalanche order (highest rate first): total interest paid, months to debt-free
  - Snowball order (smallest balance first): total interest paid, months to debt-free
  - Recommend one method with specific reason
  - How much interest savings with recommended method
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
        f"Total debt: ${debt.total_debt:,.2f}. Recommended: {debt.recommended_method}. "
        f"Debt-free in: {debt.months_to_debt_free_avalanche} months."
        if debt else "No debt."
    )
    prompt = f"""
Synthesize 3-agent analysis into a clear prioritized action plan.

Budget: Health {budget.budget_health_score}/100, Surplus: ${budget.surplus_deficit:,.2f}/mo
Savings: Rate {savings.savings_rate_percentage:.1f}%, Emergency fund: {savings.emergency_fund_months} months
Debt: {debt_summary}

Produce:
1. Overall health: critical / needs work / good / excellent
2. One-line summary (≤ 20 words, no jargon)
3. Top 5 SPECIFIC actionable steps (not "save more") with effort in minutes & deadline
4. One-year outlook if they follow the plan
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
        f"- Emergency Fund Target: ${savings.emergency_fund_target:,.0f}",
        f"- Monthly Savings: ${savings.monthly_savings_amount:,.0f}",
        f"- Savings Rate: {savings.savings_rate_percentage:.1f}%",
    ]
    if debt:
        lines += [
            "",
            f"## Debt Plan",
            f"- Total Debt: ${debt.total_debt:,.0f}",
            f"- Recommended: {debt.recommended_method.title()}",
            f"- Debt-free in: {debt.months_to_debt_free_avalanche} months",
            f"- Interest savings: ${debt.interest_savings_with_recommended:,.0f}",
        ]
    lines += [
        "",
        f"## 12-Month Outlook",
        plan.one_year_outlook,
        "",
        "---",
        "*Powered by AI Financial Coach v1.5 · OpenAI GPT-4o*",
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
    "v1.5 · Powered by **OpenAI GPT-4o** · 4 Agents + Session History + Progress Tracking  "
    "· ⚠️ *Educational guidance only — not licensed financial advice*"
)

# Initialize session state
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "sample_loaded" not in st.session_state:
    st.session_state.sample_loaded = False

# Tab navigation
tab1, tab2, tab3 = st.tabs(["📊 Analyze", "📈 History & Progress", "✅ Track Actions"])

# ===========================================================================
# TAB 1: ANALYZE
# ===========================================================================
with tab1:
    with st.sidebar:
        st.header("📊 Your Financial Data")

        if st.button("⚡ Load Sample Data", use_container_width=True):
            st.session_state.sample_loaded = True

        use_sample = st.session_state.sample_loaded

        income = st.number_input(
            "Monthly Income ($)", min_value=0,
            value=SAMPLE_DATA["income"] if use_sample else 5000, step=100,
        )
        dependents = st.number_input(
            "Dependents", min_value=0,
            value=SAMPLE_DATA["dependents"] if use_sample else 0, step=1,
        )
        existing_savings = st.number_input(
            "Existing Savings ($)", min_value=0,
            value=SAMPLE_DATA["existing_savings"] if use_sample else 0, step=500,
        )

        st.subheader("Monthly Expenses")

        uploaded_file = st.file_uploader("Upload CSV (Category, Amount)", type="csv")

        expenses: dict[str, float] = {}

        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                if {"Category", "Amount"}.issubset(df.columns):
                    expenses = df.groupby("Category")["Amount"].sum().to_dict()
                    st.success(f"✅ {len(df)} transactions")
                else:
                    st.error("CSV needs 'Category' and 'Amount' columns")
            except Exception as e:
                st.error(f"Error: {e}")

        if not expenses:
            st.caption("Sample loaded" if use_sample else "Enter expenses:")
            for cat in [
                "Housing / Rent", "Food & Groceries", "Transportation",
                "Utilities", "Healthcare", "Entertainment",
                "Clothing", "Education", "Subscriptions", "Other",
            ]:
                default_val = int(SAMPLE_DATA["expenses"].get(cat, 0)) if use_sample else 0
                val = st.number_input(cat, min_value=0, value=default_val, step=50, key=f"exp_{cat}")
                if val > 0:
                    expenses[cat] = float(val)

        template_df = pd.DataFrame({
            "Date": ["2026-01-01"], "Category": ["Housing / Rent"], "Amount": [1500],
        })
        st.download_button(
            "⬇️ CSV Template", template_df.to_csv(index=False),
            "template.csv", "text/csv", use_container_width=True,
        )

        st.subheader("Debts (optional)")
        default_num_debts = len(SAMPLE_DATA["debts"]) if use_sample else 0
        num_debts = st.number_input(
            "Number of debts", min_value=0, max_value=10,
            value=default_num_debts, step=1,
        )

        debts = []
        for i in range(int(num_debts)):
            sample = SAMPLE_DATA["debts"][i] if (use_sample and i < len(SAMPLE_DATA["debts"])) else {}
            with st.expander(f"Debt #{i + 1}", expanded=use_sample):
                d_name = st.text_input("Name", value=sample.get("name", ""), key=f"dn_{i}")
                d_bal = st.number_input("Balance ($)", min_value=0, value=sample.get("balance", 0), step=100, key=f"db_{i}")
                d_rate = st.number_input("Rate (%)", min_value=0.0, max_value=100.0, value=sample.get("rate", 0.0), step=0.5, key=f"dr_{i}")
                d_min = st.number_input("Min Payment ($)", min_value=0, value=sample.get("min_payment", 0), step=25, key=f"dm_{i}")
                if d_name and d_bal > 0:
                    debts.append({"name": d_name, "balance": d_bal, "rate": d_rate, "min_payment": d_min})

        analyze = st.button("🚀 Analyze My Finances", type="primary", use_container_width=True)

    if analyze:
        if not expenses or sum(expenses.values()) == 0:
            st.warning("Enter at least one expense.")
            st.stop()

        financial_data = {
            "income": float(income),
            "expenses": expenses,
            "dependents": int(dependents),
            "existing_savings": float(existing_savings),
            "debts": debts,
        }

        progress = st.progress(0, text="Starting analysis…")

        with st.spinner(""):
            progress.progress(10, text="💸 Budget Agent…")
            budget = run_budget_agent(financial_data)

            progress.progress(35, text="🏦 Savings Agent…")
            savings = run_savings_agent(financial_data, budget)

            progress.progress(60, text="📉 Debt Agent…")
            debt = run_debt_agent(financial_data, budget)

            progress.progress(80, text="🎯 Synthesis Agent…")
            plan = run_synthesis_agent(financial_data, budget, savings, debt)

            progress.progress(100, text="✅ Complete!")

        progress.empty()

        # Save session
        analysis = {
            "financial_data": financial_data,
            "budget": budget,
            "savings": savings,
            "debt": debt,
            "plan": plan,
        }
        session_id = SessionManager.save_session(analysis)
        st.session_state.current_session_id = session_id

        # Health banner
        health_config = {
            "critical":   {"emoji": "🔴", "bg": "#fdf0f0", "color": "#e74c3c"},
            "needs work": {"emoji": "🟡", "bg": "#fef9f0", "color": "#f39c12"},
            "good":       {"emoji": "🟢", "bg": "#f0fdf4", "color": "#2ecc71"},
            "excellent":  {"emoji": "✅", "bg": "#f0fdf4", "color": "#27ae60"},
        }
        h = health_config.get(plan.overall_health.lower(), health_config["needs work"])

        st.markdown(
            f"""<div style="background:{h['bg']};border-left:5px solid {h['color']};
                padding:1rem 1.5rem;border-radius:8px;margin-bottom:1rem;">
                <h3 style="margin:0;color:{h['color']};">{h['emoji']} {plan.overall_health.upper()}</h3>
                <p style="margin:0.25rem 0 0;">{plan.one_line_summary}</p>
            </div>""",
            unsafe_allow_html=True,
        )

        report_md = generate_report(financial_data, budget, savings, debt, plan)
        st.download_button(
            "⬇️ Download Report",
            report_md,
            file_name=f"financial_report_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
        )

        st.divider()

        # Budget results
        st.header("💸 Budget Analysis")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Income", f"${budget.total_income:,.0f}")
        c2.metric("Expenses", f"${budget.total_expenses:,.0f}")
        c3.metric("Surplus", f"${abs(budget.surplus_deficit):,.0f}",
                 delta="+" if budget.surplus_deficit >= 0 else "−")
        score = budget.budget_health_score
        c4.metric("Health Score", f"{score}/100")

        if budget.spending_categories:
            df_cats = pd.DataFrame([
                {
                    "Category": c.category,
                    "Amount": c.amount,
                    "Your %": c.percentage_of_income,
                    "Benchmark %": c.benchmark_percentage,
                    "Status": c.status,
                }
                for c in budget.spending_categories
            ])
            col_pie, col_bench = st.columns(2)

            with col_pie:
                fig_pie = px.pie(
                    df_cats, values="Amount", names="Category",
                    title="Expense Breakdown", hole=0.4,
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_bench:
                df_bench = df_cats[["Category", "Your %", "Benchmark %"]].copy()
                fig_bench = go.Figure()
                fig_bench.add_trace(go.Bar(
                    name="Your %", x=df_bench["Category"], y=df_bench["Your %"],
                    marker_color="#e74c3c",
                ))
                fig_bench.add_trace(go.Scatter(
                    name="Benchmark %", x=df_bench["Category"], y=df_bench["Benchmark %"],
                    mode="markers", marker=dict(symbol="line-ew", size=12, color="#333"),
                ))
                fig_bench.update_layout(title="Your Spending vs. Benchmark", xaxis_tickangle=-30)
                st.plotly_chart(fig_bench, use_container_width=True)

        st.divider()

        # Savings results
        st.header("🏦 Savings Strategy")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Emergency Fund Target", f"${savings.emergency_fund_target:,.0f}")
        s2.metric("Monthly Savings", f"${savings.monthly_savings_amount:,.0f}")
        s3.metric("Savings Rate", f"{savings.savings_rate_percentage:.1f}%")
        s4.metric("Months to E-Fund", f"{savings.months_to_emergency_fund}")

        if savings.savings_allocation:
            df_alloc = pd.DataFrame([
                {"Bucket": a.bucket, "Monthly": a.monthly_amount}
                for a in sorted(savings.savings_allocation, key=lambda x: x.priority)
            ])
            fig_bar = px.bar(
                df_alloc, x="Bucket", y="Monthly",
                title="Monthly Savings Allocation", text="Monthly",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        # Debt results
        if debt:
            st.header("📉 Debt Plan")
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Total Debt", f"${debt.total_debt:,.0f}")
            d2.metric("Avalanche", f"{debt.months_to_debt_free_avalanche} mo")
            d3.metric("Snowball", f"{debt.months_to_debt_free_snowball} mo")
            d4.metric("Interest Saved", f"${debt.interest_savings_with_recommended:,.0f}")

            rec_emoji = "🏔️" if debt.recommended_method.lower() == "avalanche" else "⛄"
            st.info(f"**{rec_emoji} Recommended: {debt.recommended_method.title()}**\n{debt.recommended_reason}")

        st.divider()

        # Action plan (moved to bottom for better UX)
        st.header("🎯 Your Prioritized Action Plan")
        st.caption("Start with these 5 actions this week to improve your financial health.")

        domain_colors = {"budget": "#e74c3c", "savings": "#2ecc71", "debt": "#3498db"}

        for item in plan.top_actions:
            color = domain_colors.get(item.domain.lower(), "#95a5a6")
            with st.container(border=True):
                col_num, col_content = st.columns([0.08, 0.92])
                with col_num:
                    st.markdown(f"<h2 style='color:{color};margin:0;'>#{item.priority}</h2>", unsafe_allow_html=True)
                with col_content:
                    st.markdown(f"**{item.action}**")
                    st.caption(f"📈 {item.impact}  ·  ⏱️ {item.effort}  ·  📅 {item.deadline.title()}")
                    st.markdown(f"<span style='background:{color}22;color:{color};padding:2px 8px;border-radius:12px;font-size:0.75rem;font-weight:600;'>{item.domain.upper()}</span>", unsafe_allow_html=True)

        st.divider()
        st.caption("⚠️ Educational guidance only — not licensed financial advice.")


# ===========================================================================
# TAB 2: HISTORY & PROGRESS
# ===========================================================================
with tab2:
    st.header("📈 History & Progress")

    sessions = SessionManager.load_sessions()

    if not sessions:
        st.info("No analysis history yet. Run an analysis in the **Analyze** tab to get started.")
    else:
        st.subheader("Your Past Analyses")
        for i, s in enumerate(sessions):
            with st.expander(f"📅 {s['date']} — Score: {s['budget']['budget_health_score']}/100"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Health Score", s["budget"]["budget_health_score"])
                c2.metric("Expenses", f"${s['budget']['total_expenses']:,.0f}")
                c3.metric("Surplus", f"${s['budget']['surplus_deficit']:,.0f}")
                c4.metric("Savings Rate", f"{s['savings']['savings_rate_percentage']:.1f}%")

        if len(sessions) >= 2:
            st.subheader("📊 Compare Sessions")
            col1, col2 = st.columns(2)
            with col1:
                s1 = st.selectbox(
                    "Older session",
                    [s["date"] for s in reversed(sessions)],
                    key="compare1"
                )
            with col2:
                s2 = st.selectbox(
                    "Newer session",
                    [s["date"] for s in reversed(sessions)],
                    key="compare2"
                )

            if st.button("Compare"):
                s1_id = next((s["id"] for s in sessions if s["date"] == s1), None)
                s2_id = next((s["id"] for s in sessions if s["date"] == s2), None)

                if s1_id and s2_id:
                    comparison = SessionManager.compare_sessions(s1_id, s2_id)

                    if comparison:
                        st.subheader(f"Changes from {s1} → {s2}")

                        col_a, col_b, col_c, col_d = st.columns(4)

                        delta_score = comparison["budget_score_delta"]
                        score_color = "green" if delta_score > 0 else "red"
                        col_a.metric(
                            "Budget Health Score",
                            f"{delta_score:+d}",
                            delta_color="normal" if delta_score > 0 else "inverse",
                        )

                        delta_exp = comparison["total_expenses_delta"]
                        col_b.metric(
                            "Total Expenses",
                            f"${delta_exp:+,.0f}",
                            delta=f"{comparison['total_expenses_pct_delta']:+.1f}%",
                            delta_color="inverse" if delta_exp > 0 else "normal",
                        )

                        delta_surplus = comparison["surplus_delta"]
                        col_c.metric(
                            "Surplus",
                            f"${delta_surplus:+,.0f}",
                            delta_color="normal" if delta_surplus > 0 else "inverse",
                        )

                        delta_rate = comparison["savings_rate_delta"]
                        col_d.metric(
                            "Savings Rate",
                            f"{delta_rate:+.1f}%",
                            delta_color="normal" if delta_rate > 0 else "inverse",
                        )

                        st.success("✅ You're making progress!" if delta_score > 0 or delta_exp < 0 else "Keep going — track next month!")


# ===========================================================================
# TAB 3: TRACK ACTIONS
# ===========================================================================
with tab3:
    st.header("✅ Action Completion Tracker")

    sessions = SessionManager.load_sessions()

    if not sessions:
        st.info("No analyses yet. Run one in the **Analyze** tab.")
    else:
        latest_session = sessions[0]
        session_id = latest_session["id"]

        st.subheader(f"📋 Actions from {latest_session['date']}")

        tracking = ActionTracker.get_session_completion(session_id)

        actions = latest_session["plan"]["top_actions"]

        completed_count = 0
        for action in actions:
            is_completed = tracking.get(str(action["priority"]), False)
            if is_completed:
                completed_count += 1

            # Checkbox
            new_status = st.checkbox(
                f"**{action['priority']}. {action['action']}**  \n{action['impact']} ⏱️ {action['effort']}",
                value=is_completed,
                key=f"action_{action['priority']}",
            )

            if new_status != is_completed:
                ActionTracker.save_action_completion(session_id, action["priority"], new_status)

        st.divider()

        progress_pct = (completed_count / len(actions)) * 100
        st.metric("Completion Rate", f"{progress_pct:.0f}%")

        if progress_pct == 100:
            st.balloons()
            st.success("🎉 All actions completed! Run a new analysis to see your progress.")
        elif progress_pct > 0:
            st.info(f"Great progress! {completed_count}/{len(actions)} actions done.")
