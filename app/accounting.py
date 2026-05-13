from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


logger = logging.getLogger(__name__)


ALLOWED_ACCOUNTS = {
    "Cash and Cash Equivalents",
    "Bank Account",
    "Credit Card Payable",
    "Accounts Payable",
    "Accounts Receivable",
    "Sales Revenue",
    "Sales Discounts",
    "Employee Benefits Expense",
    "Office Supplies Expense",
    "Inventory",
    "Cost of Goods Sold",
    "VAT Receivable",
    "VAT Payable",
}


class JournalValidationError(ValueError):
    """Raised when the model output cannot be trusted as a journal entry."""


@dataclass(frozen=True)
class NormalizedLine:
    transaction_no: int
    transaction_date: str
    account: str
    description: str
    debit: int | float
    credit: int | float


def parse_model_json(raw_text: str) -> dict[str, Any]:
    if not raw_text or not raw_text.strip():
        raise JournalValidationError("모델 응답이 비어 있습니다.")

    text = raw_text.strip()
    text = _strip_code_fence(text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            logger.warning("No JSON object found in model response: %s", raw_text[:500])
            raise JournalValidationError("모델 응답이 JSON 형식이 아닙니다.")
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            logger.warning("JSON parsing failed: %s; response=%s", exc, raw_text[:1000])
            raise JournalValidationError("모델 응답 JSON을 해석할 수 없습니다.") from exc

    if not isinstance(data, dict):
        raise JournalValidationError("모델 응답 JSON의 최상위 값은 객체여야 합니다.")
    return data


def validate_and_normalize(data: dict[str, Any]) -> tuple[dict[str, Any], list[NormalizedLine]]:
    status = data.get("status")
    if status not in {"ok", "insufficient_information"}:
        raise JournalValidationError("모델 응답의 status 값이 올바르지 않습니다.")

    currency = data.get("currency", "KRW")
    if not isinstance(currency, str) or not currency:
        raise JournalValidationError("통화 정보가 올바르지 않습니다.")

    reason = data.get("reason", "")
    if not isinstance(reason, str):
        raise JournalValidationError("reason 값이 문자열이 아닙니다.")

    transactions = data.get("transactions", [])
    if not isinstance(transactions, list):
        raise JournalValidationError("transactions 값이 배열이 아닙니다.")

    if status == "insufficient_information":
        normalized = {
            "status": status,
            "reason": reason,
            "currency": currency,
            "transactions": [],
        }
        return normalized, []

    if not transactions:
        raise JournalValidationError("분개 거래가 비어 있습니다.")
    if len(transactions) > 3:
        raise JournalValidationError("데모 범위는 최대 3개 거래까지입니다.")

    normalized_transactions: list[dict[str, Any]] = []
    flattened: list[NormalizedLine] = []

    for index, transaction in enumerate(transactions, start=1):
        if not isinstance(transaction, dict):
            raise JournalValidationError("거래 항목 형식이 올바르지 않습니다.")

        no = _coerce_int(transaction.get("no", index), "거래 번호")
        date = str(transaction.get("date", "")).strip()
        if not date:
            raise JournalValidationError("거래 일자가 비어 있습니다.")

        evidence_summary = str(transaction.get("evidence_summary", "")).strip()
        lines = transaction.get("lines", [])
        if not isinstance(lines, list) or not lines:
            raise JournalValidationError("분개 라인이 비어 있습니다.")

        debit_total = Decimal("0")
        credit_total = Decimal("0")
        normalized_lines: list[dict[str, Any]] = []

        for line in lines:
            if not isinstance(line, dict):
                raise JournalValidationError("분개 라인 형식이 올바르지 않습니다.")

            account = str(line.get("account", "")).strip()
            if account not in ALLOWED_ACCOUNTS:
                raise JournalValidationError(f"허용되지 않은 계정과목입니다: {account or '(비어 있음)'}")

            description = str(line.get("description", "")).strip()
            if not description:
                raise JournalValidationError("분개 설명이 비어 있습니다.")

            debit_amount = _coerce_amount(line.get("debit", 0), "차변 금액")
            credit_amount = _coerce_amount(line.get("credit", 0), "대변 금액")
            debit = _json_amount(debit_amount)
            credit = _json_amount(credit_amount)
            if debit > 0 and credit > 0:
                raise JournalValidationError("한 분개 라인에 차변과 대변 금액이 동시에 입력되었습니다.")
            if debit == 0 and credit == 0:
                raise JournalValidationError("금액이 0인 분개 라인이 포함되어 있습니다.")

            debit_total += debit_amount
            credit_total += credit_amount

            normalized_line = {
                "account": account,
                "description": description,
                "debit": debit,
                "credit": credit,
            }
            normalized_lines.append(normalized_line)
            flattened.append(
                NormalizedLine(
                    transaction_no=no,
                    transaction_date=date,
                    account=account,
                    description=description,
                    debit=debit,
                    credit=credit,
                )
            )

        if debit_total != credit_total:
            raise JournalValidationError(
                f"{no}번 거래의 차변 합계({_json_amount(debit_total):,})와 대변 합계({_json_amount(credit_total):,})가 일치하지 않습니다."
            )

        normalized_transactions.append(
            {
                "no": no,
                "date": date,
                "evidence_summary": evidence_summary,
                "lines": normalized_lines,
                "debit_total": _json_amount(debit_total),
                "credit_total": _json_amount(credit_total),
            }
        )

    normalized = {
        "status": status,
        "reason": reason,
        "currency": currency,
        "transactions": normalized_transactions,
    }
    return normalized, flattened


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _coerce_int(value: Any, label: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise JournalValidationError(f"{label}이 숫자가 아닙니다.") from exc


def _coerce_amount(value: Any, label: str) -> Decimal:
    if isinstance(value, str):
        value = value.replace(",", "").strip()
        if value == "":
            value = "0"

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise JournalValidationError(f"{label}을 숫자로 해석할 수 없습니다.") from exc

    if amount < 0:
        raise JournalValidationError(f"{label}은 음수일 수 없습니다.")
    if amount.quantize(Decimal("0.01")) != amount:
        raise JournalValidationError(f"{label}은 소수점 둘째 자리까지만 허용됩니다.")
    return amount


def _json_amount(amount: Decimal) -> int | float:
    if amount == amount.to_integral_value():
        return int(amount)
    return float(amount)
