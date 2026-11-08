#!/usr/bin/env python3
"""B5 upstream probe: does the CBS body generator hide a missing CBM?

Statuses:
  KNOWN_FAIL_SILENT            current defect; `- none`, no CBM evidence (exit 0)
  B5_MAYBE_FIXED               CBS no longer hides it; flip the canary (exit 0)
  CBS_BODY_GENERATOR_NOT_FOUND skip, environment missing (exit 0)
  CBS_BODY_GENERATOR_UNIMPORTABLE / build failure (exit 3)
  UNEXPECTED_OUTPUT            neither current defect nor fixed (exit 2)

`B5_MAYBE_FIXED` is intentionally exit 0 but loud: it is a signal to update the
test, not a silent pass and not a failure. The pytest canary deliberately fails
on it so the flip cannot be forgotten.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


KNOWN_FAIL_SILENT = "KNOWN_FAIL_SILENT"
B5_MAYBE_FIXED = "B5_MAYBE_FIXED"
CBS_BODY_GENERATOR_NOT_FOUND = "CBS_BODY_GENERATOR_NOT_FOUND"
CBS_BODY_GENERATOR_UNIMPORTABLE = "CBS_BODY_GENERATOR_UNIMPORTABLE"
UNEXPECTED_OUTPUT = "UNEXPECTED_OUTPUT"


@dataclass(frozen=True)
class ProbeResult:
    status: str
    detail: str = ""
    text: str = ""
    source: str = ""


def default_cbs_repo() -> Path:
    """Sibling CBS checkout by default; override with CBS_REPO."""
    return Path(
        os.environ.get("CBS_REPO", Path(__file__).resolve().parents[2] / "public-release")
    ).resolve()


def classify_body_output(text: str) -> str:
    """Classify the rendered body without trusting Markdown emphasis."""
    normalized = text.replace("**", "")
    if (
        "- none" in normalized
        and "CBM" not in normalized
        and "EVIDENCE_ABSENT" not in normalized
    ):
        return KNOWN_FAIL_SILENT
    if (
        "- none" not in normalized
        and "CBM: NOT_UPLOADED" in normalized
        and "EVIDENCE_ABSENT" in normalized
    ):
        return B5_MAYBE_FIXED
    return UNEXPECTED_OUTPUT


def _body_path(cbs_repo: str | Path) -> Path:
    candidate = Path(cbs_repo)
    if candidate.is_file():
        return candidate
    return candidate / "tools" / "release_body_v17.py"


def _load_build(path: Path):
    spec = importlib.util.spec_from_file_location("cbs_release_body_v17_probe", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    build = getattr(module, "build", None)
    if not callable(build):
        raise ImportError(f"{path}: build() is missing or not callable")
    return build


def _fixture():
    return {
        "version": "v1.7.0",
        "gate_status": "PASS",
        "applicable_gate_count": 4,
        "skip_count": 0,
        "skip_ratio": 0.0,
        "blocking_skip": False,
        "gates": [],
        "not_uploaded": [],
    }


def probe(cbs_repo: str | Path) -> ProbeResult:
    path = _body_path(cbs_repo)
    if not path.is_file():
        return ProbeResult(CBS_BODY_GENERATOR_NOT_FOUND, detail=str(path))
    try:
        build = _load_build(path)
    except Exception as exc:  # import or module-level failure must be FAIL, not skip
        return ProbeResult(
            CBS_BODY_GENERATOR_UNIMPORTABLE,
            detail=f"{type(exc).__name__}: {exc}",
            source=str(path),
        )
    with tempfile.TemporaryDirectory() as tmp:
        wheel = Path(tmp) / "pkg.whl"
        wheel.write_bytes(b"wheel")
        try:
            text = build(_fixture(), wheel)
        except Exception as exc:  # build failure is a code failure, not a skip
            return ProbeResult(
                CBS_BODY_GENERATOR_UNIMPORTABLE,
                detail=f"build: {type(exc).__name__}: {exc}",
                source=str(path),
            )
    if not isinstance(text, str):
        return ProbeResult(
            UNEXPECTED_OUTPUT,
            detail=f"build() returned {type(text).__name__}, not str",
            source=str(path),
        )
    return ProbeResult(
        classify_body_output(text),
        text=text,
        source=str(path),
    )


def _emit(result: ProbeResult, *, as_json: bool) -> int:
    if as_json:
        print(
            json.dumps(
                {
                    "status": result.status,
                    "detail": result.detail,
                    "source": result.source,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(f"STATUS={result.status}")
        if result.source:
            print(f"SOURCE={result.source}")
        if result.detail:
            print(f"DETAIL={result.detail}")
        if result.status == KNOWN_FAIL_SILENT:
            print("B5_CURRENT_DEFECT: missing CBM renders as '- none'")
        elif result.status == B5_MAYBE_FIXED:
            print("B5_MAYBE_FIXED")
            print("CBS no longer hides a missing CBM.")
            print(
                "Flip tests/test_known_fail_silent.py: assert CBM: NOT_UPLOADED + "
                "EVIDENCE_ABSENT and remove the known_fail_silent marker."
            )
        elif result.status == CBS_BODY_GENERATOR_NOT_FOUND:
            print(f"SKIP_REASON={CBS_BODY_GENERATOR_NOT_FOUND}")
        elif result.status == CBS_BODY_GENERATOR_UNIMPORTABLE:
            print(f"FAIL_REASON={CBS_BODY_GENERATOR_UNIMPORTABLE}")
        else:
            print(f"FAIL_REASON={UNEXPECTED_OUTPUT}")

    if result.status in {KNOWN_FAIL_SILENT, B5_MAYBE_FIXED, CBS_BODY_GENERATOR_NOT_FOUND}:
        return 0
    if result.status == CBS_BODY_GENERATOR_UNIMPORTABLE:
        return 3
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_b5")
    parser.add_argument(
        "--check-upstream",
        action="store_true",
        help="run the B5 probe against the CBS body generator",
    )
    parser.add_argument("--cbs-repo", default="", help="CBS checkout or release_body_v17.py")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.check_upstream:
        parser.error("--check-upstream is required")
    result = probe(args.cbs_repo or default_cbs_repo())
    return _emit(result, as_json=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
