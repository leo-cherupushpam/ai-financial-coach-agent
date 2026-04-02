# PRD: AI Financial Coach Agent
**Version:** 1.0
**Status:** Draft
**Author:** Leo Cherupushpam (AI Product Manager)
**Date:** 2026-04-02

---

## 1. Problem Statement

> "67% of Americans couldn't pass a basic financial literacy test. Personal finance advice is expensive ($150–$500/hr for a CFP), inaccessible, and generic."

### Root Problems
| Problem | Evidence | Severity |
|---|---|---|
| Financial advice is expensive and inaccessible | CFP costs $150–$500/hr; only 1 in 3 Americans has a financial advisor | Critical |
| Generic budgeting apps lack personalized guidance | Mint, YNAB — rules-based, no natural language coaching | High |
| Users don't act on financial data | 72% of users who track expenses still don't change behavior | High |
| Debt repayment is confusing | 43% of Americans don't know the difference between avalanche/snowball methods | Medium |

---

## 2. User Personas

### Primary Persona: "Struggling Steph"
- **Demographics:** 28–38 years old, household income $55–90K, 1–2 dependents
- **Jobs-to-be-Done:** "Help me figure out if I'm doing okay with money — and what to fix first"
- **Pain Points:**
  - Feels overwhelmed by debt + savings simultaneously
  - Has tried budgeting apps but doesn't know what to *do* with the data
  - Can't afford a financial advisor
- **Motivation:** Wants clarity and confidence, not complexity
- **Tech comfort:** Moderate — uses mobile apps daily, comfortable with chat UIs

### Secondary Persona: "Deliberate Dan"
- **Demographics:** 35–50 years old, income $100K+, planning for major life events
- **Jobs-to-be-Done:** "Give me a personalized roadmap to retire by 55"
- **Pain Points:**
  - Has data but lacks a trusted sounding board for major decisions
  - Doesn't want cookie-cutter advice
- **Motivation:** Optimization and confidence in specific decisions
- **Tech comfort:** High

---

## 3. Solution Overview

A multi-agent AI system that functions as a personal financial coach:
- Ingests financial data (CSV upload or manual entry)
- Routes analysis to three specialized agents in parallel:
  - **Budget Agent** — spending pattern analysis, category optimization
  - **Savings Agent** — emergency fund sizing, savings rate benchmarking, automation strategy
  - **Debt Agent** — payoff method comparison (avalanche vs. snowball), timeline visualization
- Synthesizes into a prioritized action plan with visual dashboards
- Maintains context across sessions (memory layer)

### What it is NOT
- Not a trading platform or investment advisor
- Not a bank or financial institution
- Not a replacement for a CFP for complex tax/estate situations

---

## 4. Success Metrics

### North Star Metric
**"% of users who complete at least 1 recommended action within 7 days of first session"**

Rationale: Behavior change is the product outcome — not just analysis generation.

### Supporting KPIs

| Metric | Baseline (Day 0) | Target (Day 90) | How Measured |
|---|---|---|---|
| Activation rate (upload CSV or enter data) | — | >60% of signups | App analytics |
| Advice action rate (1+ action in 7 days) | — | >35% | Self-report / follow-up session |
| Session completion rate | — | >70% | App analytics |
| Return visit rate (D7, D30) | — | D7: 40%, D30: 25% | App analytics |
| Net Promoter Score | — | >45 | In-app survey |
| Hallucination / bad advice rate | — | <2% | QA sampling (25 sessions/week) |
| Cost per session (API cost) | — | <$0.15 | Gemini usage logs |

---

## 5. AI-Specific Design Decisions

### 5.1 Model Choice: Gemini via Google ADK
- **Why Gemini:** Native integration with ADK, strong function calling, competitive cost at scale
- **Tradeoff accepted:** Vendor lock-in vs. faster time to market and tighter ADK integration
- **Revisit trigger:** If Gemini pricing increases >30% or quality degrades on financial reasoning

### 5.2 Multi-Agent vs. Single Agent
- **Decision:** Multi-agent (3 specialized agents)
- **Why:** Budget, savings, and debt are distinct problem domains with different reasoning patterns. Specialization improves output quality.
- **Tradeoff:** Higher latency (+1.5–2s per session) and complexity vs. deeper, more accurate analysis per domain
- **Revisit trigger:** If latency complaints exceed 15% of NPS verbatims

### 5.3 Memory Strategy
- **Decision:** Session-level context only for v1; persistent memory in v2
- **Why:** Reduces privacy/compliance risk in v1 while validating core value prop
- **Tradeoff:** Each session starts fresh — users must re-upload data
- **Revisit trigger:** >40% of users re-upload identical CSV in sessions 2+

### 5.4 Hallucination Risk Mitigation
- **Risk:** Financial advice hallucinations can cause real harm
- **Mitigations:**
  1. Ground all advice on user-provided data only (no market predictions)
  2. Add explicit disclaimers on advice output ("This is not financial advice from a licensed CFP")
  3. Implement QA sampling: review 25 random sessions/week for accuracy
  4. Add confidence flags: agent outputs flagged as "high certainty" vs. "exploratory"
- **Severity:** Critical — any hallucination in this domain is a trust-destroying event

---

## 6. Feature Roadmap

### v1.0 — MVP (Build now)
- [ ] CSV upload + manual expense entry
- [ ] 3-agent parallel analysis (Budget, Savings, Debt)
- [ ] Visual dashboard (charts for expense breakdown, debt timeline)
- [ ] Prioritized action plan output
- [ ] Disclaimer + data privacy notice
- [ ] Basic QA checklist before each session

### v1.5 — Retention Layer
- [ ] Session history (last 3 sessions stored locally)
- [ ] Week-over-week comparison ("You spent 12% more on dining this month")
- [ ] Action completion tracking ("Did you set up auto-transfer?")

### v2.0 — Personalization
- [ ] Persistent memory across sessions
- [ ] Goal-setting and milestone tracking (e.g., "Emergency fund: 43% complete")
- [ ] Behavioral nudges via email/notification (weekly check-in)
- [ ] Model experimentation: test Claude vs. Gemini on advice quality

---

## 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hallucinated financial advice harms user | Low | Critical | Ground outputs in user data only; disclaimers; QA sampling |
| Users don't upload real data (privacy fear) | Medium | High | Clear data policy; local-only processing option in v2 |
| Low activation (users browse, don't engage) | Medium | High | Reduce friction: add quick-start template CSVs |
| API cost spike at scale | Low | Medium | Cost per session monitoring; prompt optimization |
| Regulatory risk (unlicensed advice) | Medium | High | Strong disclaimers; "educational only" framing throughout |

---

## 8. Open Questions (for next user research session)

1. Do users trust AI for financial advice, or do they need a human "in the loop"?
2. What's the biggest drop-off point — data upload, waiting for analysis, or reading results?
3. Would users pay for this? What's the WTP for Steph vs. Dan?
4. Is the 3-agent approach perceivably better than a single agent to users?

---

## 9. Go-to-Market Framing (for Portfolio)

**Positioning:** "The first AI coach that turns your transaction data into a prioritized financial action plan — in 2 minutes, not 2 hours."

**Target channel:** Personal finance communities (r/personalfinance, financial literacy TikTok)

**Portfolio story:** Show the progression from problem discovery → architecture decisions → metrics → iteration plan. The PRD IS the artifact — not just the code.
