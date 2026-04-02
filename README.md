# 💰 AI Financial Coach Agent

A multi-agent AI system that turns your transaction data into a personalized financial action plan — in minutes, not hours.

Powered by **OpenAI GPT-4o** with structured outputs. Built as an AI Product Manager portfolio project.

---

## What It Does

Three specialized agents analyze your finances in sequence:

| Agent | What It Does |
|---|---|
| 💸 **Budget Agent** | Categorizes spending, benchmarks against standards, scores budget health (1–100) |
| 🏦 **Savings Agent** | Sizes emergency fund, sets savings rate, allocates across buckets, gives automation tips |
| 📉 **Debt Agent** | Compares avalanche vs. snowball methods, calculates total interest, recommends the better strategy |

Each agent feeds its output as context into the next — structured, sequential, and explainable.

---

## Demo

<img width="1905" height="963" alt="Screenshot 2026-04-02 at 15 36 34" src="https://github.com/user-attachments/assets/4be88fdd-9254-464f-bbd2-c8973f963f9b" />


> ⚠️ *Educational guidance only — not licensed financial advice. Consult a CFP for professional guidance.*

---

## Product Thinking

This project was built following AI PM best practices:

- **[PRD](docs/PRD.md)** — Problem statement, user personas, north star metric, AI-specific design decisions
- **Architecture decisions** — Why 3 agents vs. 1, why OpenAI over Gemini, why session-only memory in v1
- **Metrics defined upfront** — North star: % of users who complete 1 recommended action within 7 days
- **Risk register** — Hallucination mitigation, regulatory framing, privacy handling

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| LLM | GPT-4o | Best structured output reliability for complex Pydantic schemas |
| Structured outputs | `beta.chat.completions.parse()` | Native Pydantic support, no framework overhead |
| UI | Streamlit | Fast for portfolio demos; focus stays on product thinking |
| Data viz | Plotly | Interactive charts for expense breakdown and debt comparison |
| Data input | CSV upload + manual entry | Reduces activation friction for first-time users |

---

## Architecture

```
User Input (CSV / Manual)
        │
        ▼
┌─────────────────┐
│  Budget Agent   │  → Spending breakdown, health score, reduction opportunities
└────────┬────────┘
         │ (budget context passed forward)
         ▼
┌─────────────────┐
│  Savings Agent  │  → Emergency fund target, savings rate, allocation buckets
└────────┬────────┘
         │ (budget + savings context)
         ▼
┌─────────────────┐
│   Debt Agent    │  → Avalanche vs. snowball, interest savings, recommendation
└─────────────────┘
         │
         ▼
  Streamlit Dashboard (metrics + charts + action plan)
```

---

## Quickstart

```bash
git clone https://github.com/leo-cherupushpam/ai-financial-coach-agent
cd ai-financial-coach-agent/app

# Install dependencies
pip install -r requirements.txt

# Add your OpenAI API key
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-...

# Run
streamlit run ai_financial_coach.py
```

---

## Roadmap

| Version | Focus | Key Hypothesis Being Tested |
|---|---|---|
| **v1.0** (now) | MVP — analyze and recommend | Does AI-generated analysis drive action? |
| **v1.5** | Retention — session history, progress tracking | Does seeing progress increase return visits? |
| **v2.0** | Personalization — persistent memory, goals, nudges | Does memory increase savings rate behavior change? |

---

## Key Design Decisions

**Why 3 agents instead of 1?**
Budget, savings, and debt are genuinely different reasoning tasks with different context needs. Specialization improves output quality. Tradeoff: ~2s extra latency per session.

**Why session-only memory in v1?**
Reduces privacy/compliance complexity while validating the core value prop. Revisit trigger: if >40% of returning users re-upload the same CSV.

**Why OpenAI over Gemini?**
GPT-4o has stronger structured output reliability on complex nested Pydantic schemas. Also removes dependency on Google ADK v0.1.0 (unstable).

---

## Inspiration

Built on top of the [awesome-llm-apps](https://github.com/leo-cherupushpam/awesome-llm-apps) collection, rewritten with OpenAI API and product management documentation.
