# How to run the Meridian Credit Ops demo

## What this demo proves

Same question, three systems:

1. **LLM-only** — fluent, no vault → ungrounded  
2. **Unmanaged RAG** — soup index, no status filter → wrong edition can win  
3. **Managed RAG** — filter `status=active` → cite current circular  

Reliability improves because the **data system** improves — not because the LLM changes.

---

## The question (used in every section)

> Can a customer get EMI relief after job loss without visiting the branch?

| Edition | Policy |
|---------|--------|
| Credit Ops **2024** | Branch visit · Branch Manager · max 30 days |
| Credit Ops **2025** (correct) | Mobile app · up to 90 days · EMI ≤ ₹25k gate |

---

## Requirements

- Python 3.10+ (standard library only — no `pip install`)
- A browser

---

## Start the demo

```bash
cd rag-credit-ops-demo   # this repo
python3 chat_app.py
```

Open: **http://127.0.0.1:7860**

---

## Live walkthrough (click order)

### Step 1 — LLM only
1. Confirm the question at the top.  
2. Click **Ask LLM-only**.  
3. Show the answer box: fluent text + **UNGROUNDED** + no citation.  
4. Say: *“Sounds helpful. Never opened Credit Ops.”*

### Step 2 — Unmanaged RAG
1. Click **Load unmanaged files**.  
2. Confirm both plain files appear (status **UNKNOWN**).  
3. Click **Ask unmanaged**.  
4. Show answer: may be 2024 branch / 30-day rule.  
5. Say: *“Retrieved something — wrong edition can still win.”*

### Step 3 — Managed RAG
1. Click **Load managed files**.  
2. Confirm 2024 **SUPERSEDED** + 2025 **ACTIVE**.  
3. Click **Ask managed**.  
4. Show answer: 2025 digital path + citation.  
5. Say: *“Same question. Filter then cite. That is the upgrade.”*

### Close
Point at **How the answer improves** at the bottom. Thesis: governed retrieve beats fluent guesswork.

---

## Sample files

| File | Section |
|------|---------|
| `samples/credit_ops_v2024.txt` | Unmanaged |
| `samples/credit_ops_v2025.txt` | Unmanaged |
| `samples/credit_ops_v2024.managed.txt` | Managed (`status: superseded`) |
| `samples/credit_ops_v2025.managed.txt` | Managed (`status: active`) |

---

## Stop / reset

- Stop server: `Ctrl+C` in the terminal  
- Clear UI state: **Reset all**  
- Port busy: change `PORT` in `chat_app.py` or free port 7860  

---

## Timing (~10 minutes)

| Min | Beat |
|-----|------|
| 0–1 | Start app · show question |
| 1–3 | Ask LLM-only |
| 3–6 | Load + ask unmanaged |
| 6–9 | Load + ask managed |
| 9–10 | Improvement summary |
