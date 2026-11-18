# Credit Ops sample pack

| File | Pane | Meaning |
|------|------|---------|
| `credit_ops_v2024.txt` | Unmanaged | Old circular — branch / ~30 days |
| `credit_ops_v2025.txt` | Unmanaged | New circular — app / 90 days (still unfiltered in soup) |
| `credit_ops_v2024.managed.txt` | Managed | Same old body + YAML `status: superseded` |
| `credit_ops_v2025.managed.txt` | Managed | Same new body + YAML `status: active` |

Managed files start with YAML frontmatter (`doc_id`, `effective_date`, `status`, …).
