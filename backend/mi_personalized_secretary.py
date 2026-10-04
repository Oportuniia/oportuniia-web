"""Privacy-first candidate signals for personalized Premium document secretary.

Strictly suggestions. Analyze text only in an authorized private worker after
owner-scoped file access and security scanning. Never store source text or
automatically infer tax obligations; show extracted labels and provenance for
explicit owner confirmation before creating calendar entries.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone

CANDIDATES = frozenset({"PAYROLL_PAYMENT_DAY", "PAYROLL_PERIOD",
                        "TAX_RESIDENCY_DECLARED", "FILING_PERIOD_DECLARED"})
MAX_TEXT = 40_000


def suggest_document_signals(text: str, *, document_kind: str,
                             file_id: str) -> list[dict]:
    """Suggest narrow labeled candidates without retaining raw document text."""
    if not isinstance(text, str) or len(text) > MAX_TEXT:
        raise ValueError("invalid analyzed document text")
    if not re.fullmatch(r"[0-9a-f]{32}", file_id):
        raise ValueError("invalid private file identifier")
    if document_kind not in {"NOMINA", "RENTA"}:
        return []
    clean = re.sub(r"\s+", " ", text.lower())
    suggestions = []
    if document_kind == "NOMINA":
        # A source payroll date is historical, NEVER assume next payday.
        match = re.search(
            r"(?:fecha de pago|fecha de abono|fecha de transferencia)"
            r"\s*[:\-]?\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})",
            clean,
        )
        if match:
            try:
                value = date(int(match.group(3)),int(match.group(2)),int(match.group(1)))
            except ValueError:
                value = None
            if value:
                suggestions.append({
                    "kind": "PAYROLL_PAYMENT_DAY", "candidate_value": value.day,
                    "source_date": value.isoformat(), "source_file_id": file_id,
                    "needs_owner_confirmation": True,
                    "warning": "Una nómina antigua no acredita el próximo día de cobro",
                })
        period = re.search(
            r"(?:periodo de liquidaci[oó]n|periodo de devengo)\s*[:\-]?\s*"
            r"(mensual|semanal|quincenal)", clean,
        )
        if period:
            suggestions.append({
                "kind": "PAYROLL_PERIOD", "candidate_value": period.group(1),
                "source_file_id": file_id, "needs_owner_confirmation": True,
            })
    if document_kind == "RENTA":
        match = re.search(
            r"(?:residencia fiscal declarada|residencia fiscal)\s*[:\-]?\s*"
            r"(españa|espana)", clean,
        )
        if match:
            suggestions.append({
                "kind": "TAX_RESIDENCY_DECLARED", "candidate_value": "ES",
                "source_file_id": file_id, "needs_owner_confirmation": True,
                "warning": "La residencia de un documento puede haber cambiado",
            })
        # Do not produce annual tax filing deadlines from document content.
    return suggestions


def confirm_secretary_signal(*, actor_id: str, candidate: dict,
                             value, confirmed_at: datetime) -> dict:
    """Store an explicit user confirmation, never a tax determination."""
    if not actor_id.startswith("mi_") or candidate.get("needs_owner_confirmation") is not True:
        raise ValueError("verified owner confirmation required")
    if candidate.get("kind") not in CANDIDATES:
        raise ValueError("unsupported signal")
    if not isinstance(confirmed_at, datetime) or confirmed_at.tzinfo is None:
        raise ValueError("confirmation timestamp must be aware")
    kind = candidate["kind"]
    if kind == "PAYROLL_PAYMENT_DAY":
        if type(value) is not int or not 1 <= value <= 28:
            # Unambiguous next-month scheduling only for days 1–28.
            raise ValueError("supported recurring payment day is 1–28")
    elif kind == "PAYROLL_PERIOD":
        if value not in ("mensual","quincenal","semanal"):
            raise ValueError("unsupported periodicity")
    elif kind == "TAX_RESIDENCY_DECLARED":
        if value != "ES":
            raise ValueError("unsupported declaration")
    else:
        raise ValueError("tax dates must be set explicitly after verification")
    return {
        "actor_id": actor_id, "kind": kind, "confirmed_value": value,
        "source_file_id": candidate.get("source_file_id"),
        "owner_confirmed_at": confirmed_at.astimezone(timezone.utc),
        "active": True, "source": "OWNER_CONFIRMED_DOCUMENT_PROPOSAL",
        "tax_advice": False,
    }
