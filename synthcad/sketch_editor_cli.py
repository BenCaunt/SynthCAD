from __future__ import annotations

import argparse
import ast
import json
import threading
import webbrowser
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


@dataclass
class EditableConstant:
    name: str
    value: Any
    line: int


def _literal_value(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def discover_editable_constants(module_path: Path) -> list[EditableConstant]:
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    constants: list[EditableConstant] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not target.id.isupper():
            continue
        value = _literal_value(node.value)
        if isinstance(value, (int, float, bool, str)):
            constants.append(EditableConstant(target.id, value, node.lineno))
            continue
        if isinstance(value, tuple) and all(isinstance(item, (int, float)) for item in value):
            constants.append(EditableConstant(target.id, value, node.lineno))
    return constants


def apply_constant_updates(module_path: Path, updates: dict[str, Any]) -> None:
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()

    edits: list[tuple[int, int, str]] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        name = target.id
        if name not in updates:
            continue
        start = node.lineno - 1
        end = node.end_lineno - 1
        replacement = f"{name} = {repr(updates[name])}"
        edits.append((start, end, replacement))

    for start, end, replacement in sorted(edits, reverse=True):
        lines[start : end + 1] = [replacement]

    module_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


HTML = """<!doctype html>
<html><head><meta charset='utf-8'/><title>SynthCAD Sketch Editor Prototype</title>
<style>body{font-family:system-ui;margin:2rem;background:#111827;color:#e5e7eb} .row{display:flex;gap:1rem;align-items:center;margin:.4rem 0} input{padding:.3rem} button{padding:.5rem 1rem;margin-top:1rem}</style>
</head><body>
<h1>SynthCAD Sketch Editor (Prototype)</h1>
<p>Editing module: <code id='modulePath'></code></p>
<div id='form'></div>
<button id='save'>Apply changes</button><pre id='status'></pre>
<script>
async function boot(){
 const schema = await fetch('/api/schema').then(r=>r.json());
 document.getElementById('modulePath').textContent = schema.module;
 const form = document.getElementById('form');
 for (const c of schema.constants){
   const row = document.createElement('div'); row.className='row';
   const label = document.createElement('label'); label.textContent = c.name; label.style.width='320px';
   const input = document.createElement('input'); input.id = c.name; input.value = JSON.stringify(c.value);
   row.append(label, input); form.appendChild(row);
 }
 document.getElementById('save').onclick = async ()=>{
   const updates = {};
   for (const c of schema.constants){ updates[c.name] = JSON.parse(document.getElementById(c.name).value); }
   const res = await fetch('/api/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({updates})});
   const body = await res.json();
   document.getElementById('status').textContent = JSON.stringify(body,null,2);
 }
}
boot();
</script></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Prototype browser editor for top-level CAD constants")
    parser.add_argument("module", nargs="?", default="synthcad/projects/flat_disk_robot/robot.py")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    module_path = Path(args.module).resolve()

    class Handler(BaseHTTPRequestHandler):
        def _json(self, payload: Any, status: int = 200) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/":
                data = HTML.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if self.path == "/api/schema":
                constants = discover_editable_constants(module_path)
                return self._json({"module": str(module_path), "constants": [c.__dict__ for c in constants]})
            self._json({"error": "not found"}, status=404)

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/api/apply":
                return self._json({"error": "not found"}, status=404)
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            updates = payload.get("updates", {})
            apply_constant_updates(module_path, updates)
            self._json({"ok": True, "updated": sorted(updates.keys())})

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Sketch editor running at http://127.0.0.1:{args.port} for {module_path}")
    if not args.no_browser:
        threading.Timer(0.3, lambda: webbrowser.open(f"http://127.0.0.1:{args.port}")).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
