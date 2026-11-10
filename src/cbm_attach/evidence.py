"""Generic evidence input adapters.

The four-piece CBM path still uses :func:`cbm_attach.reports.identity_errors`.
This module exposes the same report data as a neutral EvidenceInput so other
subjects and producers can be checked without hard-coding ``package_id=cbm``.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .reports import Report, load_report


@dataclass(frozen=True)
class EvidenceInput:
    kind: str
    path: Path
    package_id: str
    producer_id: str | None
    version: str
    tag: str | None
    sha256: str
    data: dict

    @classmethod
    def from_report(cls, report: Report) -> "EvidenceInput":
        return cls(
            kind=report.kind,
            path=report.path,
            package_id=report.package_id,
            producer_id=report.producer_id,
            version=report.version,
            tag=report.data.get("tag"),
            sha256=report.sha256,
            data=report.data,
        )


def load_evidence(path: str | Path, kind: str) -> EvidenceInput:
    return EvidenceInput.from_report(load_report(path, kind))


def identity_errors_for(
    evidence: Iterable[EvidenceInput],
    *,
    subject_package_id: str,
    producers: set[str],
) -> list[str]:
    """Check subject/producer identity for arbitrary evidence inputs."""
    errors: list[str] = []
    for item in evidence:
        label = item.kind.upper()
        if item.package_id != subject_package_id:
            errors.append(
                f"{label} package_id={item.package_id!r} expected {subject_package_id!r}"
            )
        if item.producer_id is not None and item.producer_id not in producers:
            errors.append(
                f"{label} producer_id={item.producer_id!r} expected one of {sorted(producers)!r}"
            )
    return errors
