# Live demo — step-by-step guide (progressive)

**Session:** Jerusalem College FDP · RAG in Practice  
**App folder:** `Sessions/Jerusalem College/demo/`  
**Start:** `python3 chat_app.py` → http://127.0.0.1:7860

---

## The question (say it aloud every time)

> **Can a customer get EMI relief after job loss without visiting the branch?**

This is the **only** question used in the tour. It stays visible at the top of the workbench.

| What a correct answer needs | Where it lives |
|-----------------------------|----------------|
| Digital / app path (no branch) | Credit Ops **2025** |
| Up to 90 days · EMI ≤ ₹25k gate | Credit Ops **2025** |
| Old rule: branch + Branch Manager · 30 days | Credit Ops **2024** (superseded) |

---

## How to present (guided tour · recommended)

Use the big blue button on the page. Do **not** load both vaults first.

### Step 1 — LLM only (no files)

1. Click **1 · Ask LLM-only**  
2. Point at the red pane: fluent digital-path guess + **UNGROUNDED** + no citation  
3. Say: *“Sounds helpful. Never opened Credit Ops.”*  
4. Improvement panel: LLM = fluent guess  

### Step 2a — Load unmanaged files

1. Click **2a · Load unmanaged files**  
2. Amber pane shows `credit_ops_v2024.txt` + `credit_ops_v2025.txt` with **UNKNOWN** status  
3. Say: *“Both circulars dumped into a soup. No status filter.”*

### Step 2b — Ask unmanaged

1. Click **2b · Ask unmanaged**  
2. Often lands on **2024** (branch / 30 days)  
3. Say: *“We retrieved something — wrong edition can still win.”*  
4. Improvement panel: better than pure guess, still unsafe  

### Step 3a — Load managed files

1. Click **3a · Load managed files**  
2. Green pane shows 2024 **SUPERSEDED** + 2025 **ACTIVE**  
3. Say: *“Same content. Now metadata is queryable.”*

### Step 3b — Ask managed

1. Click **3b · Ask managed**  
2. **2025** app path + citation `active`  
3. Say: *“Same question. Filter then cite. That is the upgrade.”*

### Step 4 — Compare improvement

1. Read the **How the answer improves** card with the room  
2. Thesis: *“We did not swap the LLM. We governed retrieve.”*

| Stage | What improved |
|-------|----------------|
| LLM-only | — (no evidence) |
| Unmanaged | Has evidence, but edition may be wrong |
| Managed | Active-only evidence + citation |

---

## Timing (~10–12 min)

| Min | Beat |
|-----|------|
| 0–1 | Start app · show the golden question |
| 1–3 | Step 1 Ask LLM |
| 3–6 | Step 2 Load + ask unmanaged |
| 6–10 | Step 3 Load + ask managed |
| 10–12 | Step 4 Compare · thesis |

---

## Optional shortcuts

- **Ask all three** — only after both vaults are loaded (or use **Load both vaults**)  
- Manual upload still works via Choose files on each pane  
- **Reset tour** clears vaults and restarts at Step 1  

---

## If live fails

Use the deck **Demo backup** slide. Same three canned answers. Do not debug more than ~30 seconds.

---

## Quick start commands

```bash
cd "/Users/gunasekaran/Documents/Workspace/Speaker sessions/Sessions/Jerusalem College/demo"
python3 chat_app.py
```

Open http://127.0.0.1:7860 → follow the blue **guided** button.
