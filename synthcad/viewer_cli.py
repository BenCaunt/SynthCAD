from __future__ import annotations

import argparse
import json
import mimetypes
import shutil
import threading
import webbrowser
from dataclasses import asdict
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

from synthcad.build import BUILD_TARGETS, BuildTarget
from synthcad.paths import GENERATED_DIR, ROOT
from synthcad.report_cli import filter_targets_by_project
from synthcad.review_assets import build_display_snapshot


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
WEBVIEWER_DIR = Path(__file__).resolve().with_name("webviewer")
DEFAULT_MANIFEST_PATH = GENERATED_DIR / "manifest.json"
DEFAULT_INSPECTION_REPORT_PATH = GENERATED_DIR / "inspection" / "inspection-report.json"
DEFAULT_INTERFERENCE_REPORT_PATH = (
    GENERATED_DIR / "inspection" / "interference" / "show-interference-report.json"
)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _serializable_target_record(target: BuildTarget) -> dict[str, Any]:
    record = asdict(target)
    record.pop("factory", None)
    record.pop("inspection_factory", None)
    return record


class ViewerData:
    def __init__(
        self,
        targets: list[BuildTarget],
        *,
        initial_target: str | None = None,
    ) -> None:
        self.targets = targets
        self.target_lookup = {target.name: target for target in targets}
        self.initial_target = initial_target if initial_target in self.target_lookup else None
        self._detail_cache: dict[str, dict[str, Any]] = {}
        self._detail_lock = threading.Lock()
        self.manifest_index = self._load_manifest_index()
        self.inspection_subjects = self._load_subjects(DEFAULT_INSPECTION_REPORT_PATH)
        self.interference_subjects = self._load_subjects(DEFAULT_INTERFERENCE_REPORT_PATH)

    def _load_manifest_index(self) -> dict[str, dict[str, Any]]:
        manifest = _read_json(DEFAULT_MANIFEST_PATH)
        if not isinstance(manifest, list):
            return {}
        return {
            entry["name"]: entry
            for entry in manifest
            if isinstance(entry, dict) and isinstance(entry.get("name"), str)
        }

    def _load_subjects(self, report_path: Path) -> dict[str, dict[str, Any]]:
        report = _read_json(report_path)
        if not isinstance(report, dict):
            return {}
        subjects = report.get("subjects", [])
        if not isinstance(subjects, list):
            return {}
        return {
            subject["name"]: subject
            for subject in subjects
            if isinstance(subject, dict) and isinstance(subject.get("name"), str)
        }

    def _generated_url(self, path: str | Path | None) -> str | None:
        if path is None:
            return None
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = (ROOT / candidate).resolve()
        else:
            candidate = candidate.resolve()
        try:
            relative = candidate.relative_to(GENERATED_DIR.resolve())
        except ValueError:
            return None
        return f"/generated/{relative.as_posix()}"

    def _glb_path(self, target: BuildTarget) -> Path:
        return target.output_prefix().with_suffix(".glb")

    def _snapshot_path(self, target: BuildTarget) -> Path:
        manifest_entry = self.manifest_index.get(target.name, {})
        manifest_snapshot = manifest_entry.get("display_snapshot")
        if isinstance(manifest_snapshot, str) and manifest_snapshot:
            return Path(manifest_snapshot)
        return target.output_prefix().with_suffix(".snapshot.json")

    def _projection_urls(self, target_name: str, subject: dict[str, Any] | None) -> list[str]:
        output_paths = []
        if isinstance(subject, dict):
            output_paths = list(subject.get("projection_outputs", []) or [])
        if output_paths:
            return [
                url
                for url in (self._generated_url(path) for path in output_paths)
                if url is not None
            ]
        return [
            f"/generated/inspection/{path.name}"
            for path in sorted((GENERATED_DIR / "inspection").glob(f"{target_name}-*.svg"))
            if path.is_file()
        ]

    def _interference_overlay_urls(self, target_name: str, subject: dict[str, Any] | None) -> list[str]:
        output_paths = []
        if isinstance(subject, dict):
            output_paths = list(subject.get("red_overlay_outputs", []) or [])
        if output_paths:
            return [
                url
                for url in (self._generated_url(path) for path in output_paths)
                if url is not None
            ]
        return [
            f"/generated/inspection/interference/{path.name}"
            for path in sorted(
                (GENERATED_DIR / "inspection" / "interference").glob(
                    f"{target_name}-*-interference.svg"
                )
            )
            if path.is_file()
        ]

    def _default_target_name(self) -> str | None:
        if self.initial_target:
            return self.initial_target

        with_glb = [target for target in self.targets if self._glb_path(target).exists()]
        assembly_with_glb = [target for target in with_glb if target.is_assembly]
        if assembly_with_glb:
            return assembly_with_glb[0].name
        if with_glb:
            return with_glb[0].name
        if self.targets:
            return self.targets[0].name
        return None

    def _overview_entry(self, target: BuildTarget) -> dict[str, Any]:
        manifest_entry = self.manifest_index.get(target.name)
        glb_path = self._glb_path(target)
        inspection_subject = self.inspection_subjects.get(target.name)
        interference_subject = self.interference_subjects.get(target.name)
        return {
            "name": target.name,
            "kind": target.kind,
            "project": target.project,
            "status": target.status,
            "printable": target.printable,
            "has_glb": glb_path.exists(),
            "glb_url": self._generated_url(glb_path) if glb_path.exists() else None,
            "projection_count": len(
                (inspection_subject or {}).get("projection_outputs", [])
                if isinstance(inspection_subject, dict)
                else []
            ),
            "interference_count": len(
                ((interference_subject or {}).get("interference_check", {}) or {}).get(
                    "interferences", []
                )
                if isinstance(interference_subject, dict)
                else []
            ),
            "manifest_present": manifest_entry is not None,
        }

    def index_payload(self) -> dict[str, Any]:
        return {
            "default_target": self._default_target_name(),
            "generated_dir": str(GENERATED_DIR),
            "targets": [self._overview_entry(target) for target in self.targets],
        }

    def detail_payload(self, target_name: str) -> dict[str, Any]:
        with self._detail_lock:
            cached = self._detail_cache.get(target_name)
            if cached is not None:
                return cached

            if target_name not in self.target_lookup:
                raise KeyError(target_name)

            target = self.target_lookup[target_name]
            snapshot_path = self._snapshot_path(target)
            snapshot = _read_json(snapshot_path)
            detail_source = "prebuilt-snapshot"

            if not isinstance(snapshot, dict):
                model = target.factory()
                snapshot = build_display_snapshot(target, model)
                detail_source = "live-snapshot"

            inspection_subject = self.inspection_subjects.get(target.name)
            interference_subject = self.interference_subjects.get(target.name)
            glb_path = self._glb_path(target)
            artifact_urls = {
                fmt: self._generated_url(target.output_prefix().with_suffix(f".{fmt}"))
                for fmt in target.formats
                if target.output_prefix().with_suffix(f".{fmt}").exists()
            }

            if isinstance(interference_subject, dict):
                interference_check = interference_subject.get("interference_check", {})
            elif isinstance(inspection_subject, dict):
                interference_check = inspection_subject.get("interference_check", {})
            else:
                interference_check = {}

            detail = {
                "target": _serializable_target_record(target),
                "manifest_entry": self.manifest_index.get(target.name),
                "glb_url": self._generated_url(glb_path) if glb_path.exists() else None,
                "artifact_urls": artifact_urls,
                "model_summary": snapshot.get("model_summary", {}),
                "children": list(snapshot.get("children", []) or []),
                "detail_source": detail_source,
                "display_snapshot_url": (
                    self._generated_url(snapshot_path) if snapshot_path.exists() else None
                ),
                "inspection": {
                    "subject": inspection_subject,
                    "projection_urls": self._projection_urls(target.name, inspection_subject),
                },
                "interference": {
                    "subject": interference_subject,
                    "check": interference_check,
                    "overlay_urls": self._interference_overlay_urls(target.name, interference_subject),
                },
            }
            self._detail_cache[target_name] = detail
            return detail


class ViewerRequestHandler(SimpleHTTPRequestHandler):
    server_version = "synthcad-view/0.1"

    def __init__(self, *args, directory: str | None = None, viewer_data: ViewerData, **kwargs):
        self.viewer_data = viewer_data
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/index":
            self._send_json(self.viewer_data.index_payload())
            return

        if parsed.path.startswith("/api/targets/"):
            target_name = unquote(parsed.path.removeprefix("/api/targets/")).strip()
            if not target_name:
                self.send_error(HTTPStatus.NOT_FOUND, "Missing build target name")
                return
            try:
                payload = self.viewer_data.detail_payload(target_name)
            except KeyError:
                self.send_error(HTTPStatus.NOT_FOUND, f"Unknown build target {target_name!r}")
                return
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to load target: {exc}")
                return
            self._send_json(payload)
            return

        if parsed.path.startswith("/generated/"):
            relative = parsed.path.removeprefix("/generated/")
            self._serve_file_from_base(GENERATED_DIR, relative)
            return

        super().do_GET()

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file_from_base(self, base: Path, relative_path: str) -> None:
        candidate = (base / relative_path).resolve()
        try:
            candidate.relative_to(base.resolve())
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND, "Path escaped generated directory")
            return

        if not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        content_type = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(candidate.stat().st_size))
        self.end_headers()
        with candidate.open("rb") as handle:
            shutil.copyfileobj(handle, self.wfile)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Launch a local Three.js viewer for synthcad generated GLB artifacts, "
            "inspection views, and interference evidence."
        )
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Build target names to include in the viewer. Defaults to all targets.",
    )
    parser.add_argument(
        "--target",
        dest="target_options",
        action="append",
        default=[],
        help="Build target name to include. May be repeated.",
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        help="Project metadata name to include. May be repeated.",
    )
    parser.add_argument(
        "--assemblies-only",
        action="store_true",
        help="Restrict the viewer list to targets whose kind includes 'assembly'.",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host interface to bind. Defaults to {DEFAULT_HOST}.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"HTTP port to bind. Defaults to {DEFAULT_PORT}.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open the browser automatically.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List build targets, then exit.",
    )
    return parser.parse_args()


def _resolve_targets(args: argparse.Namespace) -> list[BuildTarget]:
    requested_names = [*args.target_options, *args.targets]
    lookup = {target.name: target for target in BUILD_TARGETS}

    if requested_names:
        unknown = [name for name in requested_names if name not in lookup]
        if unknown:
            available = ", ".join(sorted(lookup))
            raise SystemExit(
                f"Unknown build target(s): {', '.join(unknown)}. Available targets: {available}"
            )
        targets = [lookup[name] for name in requested_names]
    else:
        targets = list(BUILD_TARGETS)

    try:
        targets = filter_targets_by_project(targets, args.project)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if args.assemblies_only:
        targets = [target for target in targets if target.is_assembly]

    if not targets:
        raise SystemExit("No build targets matched the selected filters.")

    return targets


def _print_inventory(targets: list[BuildTarget]) -> None:
    print("Build targets:")
    for target in targets:
        glb_state = "glb" if target.output_prefix().with_suffix(".glb").exists() else "no-glb"
        print(f"  {target.name} ({target.kind}) [{target.project}] {glb_state}")


def main() -> int:
    args = _parse_args()
    targets = _resolve_targets(args)

    if args.list:
        _print_inventory(targets)
        return 0

    viewer_data = ViewerData(targets)
    initial_target = viewer_data._default_target_name()

    def handler(*handler_args, **handler_kwargs):
        return ViewerRequestHandler(
            *handler_args,
            directory=str(WEBVIEWER_DIR),
            viewer_data=viewer_data,
            **handler_kwargs,
        )

    server = ThreadingHTTPServer((args.host, args.port), handler)
    query = f"?target={quote(initial_target)}" if initial_target else ""
    url = f"http://{args.host}:{args.port}/{query}"

    print(f"synthcad viewer serving {len(targets)} target(s) at {url}")
    print("Press Ctrl+C to stop.")

    if not args.no_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping viewer.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
