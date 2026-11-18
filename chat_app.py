#!/usr/bin/env python3
"""
Three-pane workbench — LLM-only | Unmanaged RAG | Managed RAG.

- LLM-only: no vault retrieve (ungrounded fluency teaching pane).
- Unmanaged: soup index, no status filter.
- Managed: YAML metadata; filters status=active; cites circular.

Run:
  python3 chat_app.py  →  http://127.0.0.1:7860
"""
from __future__ import annotations

import json
import re
import webbrowser
from dataclasses import asdict, dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

HOST, PORT = "127.0.0.1", 7860
SAMPLES = Path(__file__).resolve().parent / "samples"


@dataclass
class Doc:
    doc_id: str
    filename: str
    text: str
    title: str = ""
    effective_date: str = ""
    status: str = "unknown"
    region: str = ""
    managed: bool = False


@dataclass
class Store:
    name: str
    managed: bool
    docs: list[Doc] = field(default_factory=list)
    last_error: str = ""

    def clear(self) -> None:
        self.docs.clear()
        self.last_error = ""

    def add(self, doc: Doc) -> None:
        # replace same doc_id / filename
        self.docs = [
            d for d in self.docs
            if d.doc_id != doc.doc_id and d.filename != doc.filename
        ]
        self.docs.append(doc)


UNMANAGED = Store("Unmanaged Knowledge Bot", managed=False)
MANAGED = Store("Managed Policy Assistant", managed=True)


def parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    meta: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, parts[2].lstrip("\n")


def score(query: str, text: str) -> float:
    q = {w.lower() for w in re.findall(r"[A-Za-z0-9]+", query) if len(w) > 2}
    t = {w.lower() for w in re.findall(r"[A-Za-z0-9]+", text) if len(w) > 2}
    if not q:
        return 0.0
    return len(q & t) / len(q)


def retrieve(store: Store, query: str, k: int = 3) -> list[tuple[Doc, float]]:
    pool = store.docs
    if store.managed:
        pool = [d for d in pool if d.status == "active"]
    ranked = sorted(
        ((d, score(query, d.text)) for d in pool),
        key=lambda x: x[1],
        reverse=True,
    )
    return ranked[:k]


def build_reply(store: Store, query: str) -> dict[str, Any]:
    hits = retrieve(store, query, k=3)
    if not hits:
        return {
            "reply": (
                "No matching document in the active set. "
                + ("Managed app abstains when nothing passes the filter." if store.managed else "Index is empty.")
            ),
            "cite": None,
            "hits": [],
            "mode": "managed" if store.managed else "unmanaged",
        }
    top, top_score = hits[0]
    # Short, projector-friendly answer line (not the whole circular).
    body_lines = [
        ln.strip()
        for ln in top.text.strip().splitlines()
        if ln.strip() and not ln.strip().startswith("#") and not ln.strip().startswith("---")
    ]
    snippet = body_lines[0] if body_lines else (top.text.strip().splitlines() or [""])[0]
    if len(snippet) > 160:
        snippet = snippet[:157].rstrip() + "…"
    if store.managed:
        reply = f"{snippet}"
    else:
        reply = f"{snippet}"
    # Evidence preview: a few lines only — UI clamps further
    evidence_lines = body_lines[:3] if body_lines else [snippet]
    excerpt = " ".join(evidence_lines)
    if len(excerpt) > 220:
        excerpt = excerpt[:217].rstrip() + "…"
    return {
        "reply": reply,
        "excerpt": excerpt,
        "cite": {
            "doc_id": top.doc_id,
            "filename": top.filename,
            "title": top.title,
            "effective_date": top.effective_date,
            "status": top.status,
            "score": round(top_score, 3),
        },
        "hits": [
            {
                "doc_id": d.doc_id,
                "filename": d.filename,
                "status": d.status,
                "effective_date": d.effective_date,
                "score": round(s, 3),
                "preview": d.text.strip().splitlines()[0][:120],
            }
            for d, s in hits
        ],
        "mode": "managed" if store.managed else "unmanaged",
    }


def build_llm_only_reply(query: str) -> dict[str, Any]:
    """Teaching pane: no vault retrieve — fluent but ungrounded."""
    q = (query or "").lower()
    if "emi" in q or "job loss" in q or "relief" in q or "branch" in q:
        reply = (
            "Many banks now offer digital hardship options. You can likely apply in the "
            "mobile app for a few months of EMI relief after job loss, without visiting a branch."
        )
    else:
        reply = (
            "Based on general industry practice, there is usually a customer-friendly digital "
            "path for this kind of request. Check your bank’s app or website for the latest options."
        )
    return {
        "reply": reply,
        "excerpt": None,
        "cite": None,
        "hits": [],
        "mode": "llm_only",
        "warning": "UNGROUNDED — no Credit Ops vault retrieve ran. Fluent ≠ current circular.",
    }


def ingest_bytes(store: Store, filename: str, content: bytes) -> dict[str, Any]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return {"ok": False, "error": f"{filename}: only UTF-8 text (.txt/.md) supported in this demo."}

    meta, body = parse_frontmatter(text)
    body = body.strip() or text.strip()
    if not body:
        return {"ok": False, "error": f"{filename}: empty file."}

    if store.managed:
        # Managed path: metadata required
        effective_date = meta.get("effective_date", "").strip()
        status = meta.get("status", "").strip().lower()
        doc_id = meta.get("doc_id", "").strip() or Path(filename).stem
        if not effective_date:
            store.last_error = f"REJECTED {filename}: managed app requires effective_date (use .managed.txt samples)."
            return {"ok": False, "error": store.last_error}
        if status not in {"active", "superseded"}:
            store.last_error = f"REJECTED {filename}: managed app requires status=active|superseded."
            return {"ok": False, "error": store.last_error}
        doc = Doc(
            doc_id=doc_id,
            filename=filename,
            text=body,
            title=meta.get("title", filename),
            effective_date=effective_date,
            status=status,
            region=meta.get("region", ""),
            managed=True,
        )
        # Conflict gate: cannot have two active for same region after add
        store.add(doc)
        actives = [d for d in store.docs if d.status == "active" and d.region == doc.region]
        if len(actives) > 1 and doc.region:
            # roll back this doc
            store.docs = [d for d in store.docs if d.doc_id != doc.doc_id]
            store.last_error = (
                f"REJECTED {filename}: two active SOPs for region={doc.region}. "
                "Supersede the old one first."
            )
            return {"ok": False, "error": store.last_error}
        # Soft teaching note: multiple actives without region still warned
        if sum(1 for d in store.docs if d.status == "active") > 1 and not doc.region:
            store.last_error = "Warning: more than one active SOP in index."
        else:
            store.last_error = ""
        return {"ok": True, "doc": asdict(doc), "message": f"Indexed in managed app: {doc.doc_id} ({doc.status})"}

    # Unmanaged: ignore / strip frontmatter meaning — soup index
    doc = Doc(
        doc_id=Path(filename).stem,
        filename=filename,
        text=body,
        title=filename,
        effective_date=meta.get("effective_date", ""),
        status=meta.get("status", "unknown"),
        region=meta.get("region", ""),
        managed=False,
    )
    store.add(doc)
    store.last_error = ""
    return {"ok": True, "doc": asdict(doc), "message": f"Dumped into unmanaged soup: {filename}"}


def load_unmanaged_samples() -> dict[str, Any]:
    """Plain Credit Ops circulars → unmanaged soup only."""
    UNMANAGED.clear()
    results = []
    for name in ("credit_ops_v2024.txt", "credit_ops_v2025.txt"):
        results.append(ingest_bytes(UNMANAGED, name, (SAMPLES / name).read_bytes()))
    return {
        "ok": True,
        "message": "Loaded plain 2024 + 2025 circulars into unmanaged soup (no status filter).",
        "results": results,
        "stores": snapshot(),
    }


def load_managed_samples() -> dict[str, Any]:
    """Metadata circulars → managed vault only."""
    MANAGED.clear()
    results = []
    for name in ("credit_ops_v2024.managed.txt", "credit_ops_v2025.managed.txt"):
        results.append(ingest_bytes(MANAGED, name, (SAMPLES / name).read_bytes()))
    return {
        "ok": True,
        "message": "Loaded managed circulars: 2024 superseded + 2025 active.",
        "results": results,
        "stores": snapshot(),
    }


def load_samples_into_both() -> dict[str, Any]:
    """Load both vaults (shortcut / reset-to-full)."""
    u = load_unmanaged_samples()
    m = load_managed_samples()
    return {
        "ok": True,
        "message": "Same Credit Ops circulars loaded into both apps (unmanaged plain + managed metadata).",
        "results": {"unmanaged": u["results"], "managed": m["results"]},
        "stores": snapshot(),
    }

def snapshot() -> dict[str, Any]:
    def side(store: Store) -> dict[str, Any]:
        return {
            "name": store.name,
            "managed": store.managed,
            "count": len(store.docs),
            "last_error": store.last_error,
            "docs": [
                {
                    "doc_id": d.doc_id,
                    "filename": d.filename,
                    "title": d.title,
                    "effective_date": d.effective_date,
                    "status": d.status,
                    "region": d.region,
                    "preview": d.text.strip().replace("\n", " ")[:140],
                }
                for d in store.docs
            ],
        }

    return {"unmanaged": side(UNMANAGED), "managed": side(MANAGED)}


UI_PATH = Path(__file__).resolve().parent / "ui.html"


def load_html() -> bytes:
    return UI_PATH.read_bytes()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print(f"[dual-app] {args[0]}")

    def _json(self, code: int, obj: Any) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._html(load_html())
            return
        if path == "/api/state":
            self._json(200, snapshot())
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/load_samples":
            self._json(200, load_samples_into_both())
            return
        if path == "/api/load_unmanaged":
            self._json(200, load_unmanaged_samples())
            return
        if path == "/api/load_managed":
            self._json(200, load_managed_samples())
            return
        if path == "/api/clear":
            UNMANAGED.clear()
            MANAGED.clear()
            self._json(200, {"ok": True, "stores": snapshot()})
            return
        if path == "/api/upload":
            import base64

            payload = self._read_json()
            app = payload.get("app")
            filename = payload.get("filename") or "upload.txt"
            try:
                content = base64.b64decode(payload.get("content_b64") or "")
            except Exception:
                self._json(400, {"ok": False, "error": "bad content_b64"})
                return
            store = MANAGED if app == "managed" else UNMANAGED
            result = ingest_bytes(store, filename, content)
            result["stores"] = snapshot()
            self._json(200 if result.get("ok") else 400, result)
            return
        if path == "/api/ask":
            payload = self._read_json()
            store = MANAGED if payload.get("app") == "managed" else UNMANAGED
            q = (payload.get("query") or "").strip()
            self._json(200, build_reply(store, q))
            return
        if path == "/api/ask_both":
            payload = self._read_json()
            q = (payload.get("query") or "").strip()
            llm_only = build_llm_only_reply(q)
            unmanaged = build_reply(UNMANAGED, q)
            managed = build_reply(MANAGED, q)
            lesson = (
                "Three panes, one question. "
                "LLM-only never opens the vault — fluent but ungrounded. "
                "Unmanaged RAG retrieves nearest text — Credit Ops 2024 (Branch Manager only) can win. "
                "Managed RAG filters status=active — Credit Ops 2025 digital EMI path with citation. "
                "Same LLM class of writing; different data system; different truth."
            )
            self._json(
                200,
                {
                    "query": q,
                    "llm_only": llm_only,
                    "unmanaged": unmanaged,
                    "managed": managed,
                    "lesson": lesson,
                },
            )
            return
        if path == "/api/ask_llm":
            payload = self._read_json()
            q = (payload.get("query") or "").strip()
            self._json(200, build_llm_only_reply(q))
            return
        self._json(404, {"error": "not found"})


def main() -> None:
    if not SAMPLES.exists():
        raise SystemExit(f"Missing samples folder: {SAMPLES}")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print("=" * 64)
    print("Workbench: LLM-only | Unmanaged RAG | Managed RAG")
    print(f"Open: {url}")
    print("Cursor: Cmd+Shift+P → Simple Browser: Show → paste URL")
    print(f"Samples: {SAMPLES}")
    print("1) Click 'Load sample pack'")
    print("2) Ask the golden EMI question across all three panes")
    print("Stop: Ctrl+C")
    print("=" * 64)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
