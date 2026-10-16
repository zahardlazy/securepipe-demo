#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security Quality Gate — SecurePipe Sprint 2, Week 3 (Mlo Tay).

Task (Fri 16/10): "Integrate Security Quality Gate logic (Critical -> fail)".
Task (Thu 15/10): "Tune Quality Gate severity thresholds".

Gia tri tra ve (exit code):
  0 = PASS  — khong co finding vuot nguong chan
  1 = FAIL  — co finding Critical (Trivy) hoac finding SAST ERROR chua duoc
              chap nhan trong docs/accepted-findings.json

Nguong (chi tiet + ly do: docs/quality-gate.md):

Cach dung:
  python3 quality_gate.py \
      --trivy   trivy-results.json \
      --semgrep semgrep-results.json \
      --baseline docs/accepted-findings.json

Luu y:
  - Trivy chay voi --trivyignore .trivyignore trong workflow truoc khi ghi
    JSON, nen nhung CVE da duoc chap nhan KHONG con xuat hien o day.
  - Semgrep KHONG che finding theo duong dan source (nguyen tac cua repo:
    finding phai nhin thay duoc). Nen Semgrep ERROR finding chi duoc phep
    "song" neu fingerprint cua no co trong baseline kem ly do.
"""

import argparse
import json
import sys
from datetime import date

# ---------------------------------------------------------------------------
# NGUONG CHAT LUONG — ban sao phai khop voi docs/quality-gate.md
# ---------------------------------------------------------------------------
TRIVY_FAIL = {"CRITICAL"}          # chan build
TRIVY_WARN = {"HIGH"}              # canh bao, khong chan
SEMGREP_FAIL = {"ERROR"}           # chan build neu KHONG co trong baseline
SEMGREP_WARN = set()               # WARNING/INFO: chi bao cao

HEADER = r"""
============================================================
  SECURITY QUALITY GATE  (Sprint 2 W3 — Critical = fail)
============================================================
"""


def load_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        print(f"::error::Khong doc duoc {path} — gate khong the danh gia (fail-closed).")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"::error::{path} khong phai JSON hop le: {exc}")
        sys.exit(1)


def parse_trivy(data):
    """Trivy JSON: Results[].Vulnerabilities[]"""
    findings = []
    for result in data.get("Results") or []:
        for vuln in result.get("Vulnerabilities") or []:
            findings.append({
                "id": vuln.get("VulnerabilityID", "?"),
                "pkg": "{}:{}".format(vuln.get("PkgName", "?"), vuln.get("InstalledVersion", "?")),
                "severity": (vuln.get("Severity") or "UNKNOWN").upper(),
            })
    return findings


def parse_semgrep(data):
    """Semgrep JSON: results[].extra.severity"""
    findings = []
    for res in data.get("results") or []:
        extra = res.get("extra") or {}
        findings.append({
            "rule": res.get("check_id", "?"),
            "path": (res.get("path") or "").replace("\\", "/"),
            "line": (res.get("start") or {}).get("line", 0),
            "severity": (extra.get("severity") or "INFO").upper(),
        })
    return findings


def fingerprint(finding):
    """Dinh dang fingerprint: <path>:<rule>:<line> — giong he thong .gitleaksignore."""
    return "{}:{}:{}".format(finding["path"], finding["rule"], finding["line"])


def load_baseline(path):
    data = load_json(path)
    entries = data.get("semgrep_error_findings", [])
    return {e["fingerprint"]: e for e in entries}


def review_overdue(entry):
    """Bao cao entry baseline den han review (khong chan build)."""
    try:
        return date.today() > date.fromisoformat(entry.get("review_by", "9999-12-31"))
    except ValueError:
        return False


def main():
    ap = argparse.ArgumentParser(description="Security Quality Gate")
    ap.add_argument("--trivy", required=True, help="trivy-results.json")
    ap.add_argument("--semgrep", required=True, help="semgrep-results.json")
    ap.add_argument("--baseline", required=True, help="docs/accepted-findings.json")
    args = ap.parse_args()

    print(HEADER)
    print("Nguong: Trivy {} = CHAN | Trivy {} = canh bao".format(
        "/".join(sorted(TRIVY_FAIL)), "/".join(sorted(TRIVY_WARN)) or "-"))
    print("        Semgrep {} = CHAN neu ngoai baseline | WARNING/INFO = bao cao\n".format(
        "/".join(sorted(SEMGREP_FAIL))))

    violations = []

    # ------------------------------------------------------------------
    # 1. Trivy (SCA) — Critical -> fail
    # ------------------------------------------------------------------
    trivy = parse_trivy(load_json(args.trivy))
    trivy_fail = [f for f in trivy if f["severity"] in TRIVY_FAIL]
    trivy_warn = [f for f in trivy if f["severity"] in TRIVY_WARN]

    print("[1] Trivy SCA — {} finding (sau khi ap dung .trivyignore)".format(len(trivy)))
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"):
        count = sum(1 for f in trivy if f["severity"] == sev)
        if count:
            print("    {:<9} : {}".format(sev, count))
    for f in trivy_fail:
        print("::error::TRIVY CHAN — {} ({}) {}".format(f["id"], f["pkg"], f["severity"]))
        violations.append("Trivy {} ({})".format(f["id"], f["pkg"]))
    for f in trivy_warn:
        print("::warning::Trivy HIGH — {} ({}): khong chan, xu ly truoc khi Sprint review".format(
            f["id"], f["pkg"]))

    # ------------------------------------------------------------------
    # 2. Semgrep (SAST) — ERROR ngoai baseline -> fail
    # ------------------------------------------------------------------
    semgrep = parse_semgrep(load_json(args.semgrep))
    baseline = load_baseline(args.baseline)
    semgrep_fail = [f for f in semgrep if f["severity"] in SEMGREP_FAIL]
    semgrep_warn = [f for f in semgrep if f["severity"] not in SEMGREP_FAIL and f["severity"] in {"WARNING"}]

    accepted, blocking = [], []
    for f in semgrep_fail:
        fp = fingerprint(f)
        if fp in baseline:
            accepted.append((fp, baseline[fp]))
        else:
            blocking.append(f)

    print("\n[2] Semgrep SAST — {} finding ERROR / {} WARNING".format(
        len(semgrep_fail), len(semgrep_warn)))
    print("    Da chap nhan trong baseline: {} (van hien trong scan — theo nguyen tac 'finding phai nhin thay')".format(len(accepted)))
    for fp, entry in accepted:
        note = " — QUEN REVIEW (qua han {})".format(entry["review_by"]) if review_overdue(entry) else ""
        print("    [accepted] {}{}".format(fp, note))
        if note:
            print("::warning::Baseline entry qua han review: {}".format(fp))
    for f in blocking:
        print("::error::SEMGREP CHAN — {} (dong {})".format(fingerprint(f), f["line"]))
        violations.append("Semgrep {} ({}:{})".format(f["rule"], f["path"], f["line"]))

    # ------------------------------------------------------------------
    # 3. Ket luan
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    if violations:
        print("QUALITY GATE: FAIL — {} vi pham".format(len(violations)))
        for v in violations:
            print("  - {}".format(v))
        print("Xu ly: sua code, hoac triage vao docs/accepted-findings.json / .trivyignore kem ly do.")
        sys.exit(1)
    print("QUALITY GATE: PASS — khong co finding Critical chua duoc giai thich.")
    sys.exit(0)


if __name__ == "__main__":
    main()
