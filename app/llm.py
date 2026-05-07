from __future__ import annotations

import logging
import os
from typing import Any

import requests

from app.accounting import ALLOWED_ACCOUNTS


logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "90"))


class OllamaError(RuntimeError):
    pass


def build_prompt(ocr_text: str) -> str:
    accounts = "\n".join(f"- {account}" for account in sorted(ALLOWED_ACCOUNTS))
    return f"""
You are an accounting journal entry assistant for a Principles of Accounting demo.
Use IFRS-style basic journal logic and the evidence text below.

Return ONLY valid JSON. Do not wrap it in markdown.

Allowed accounts:
{accounts}

Rules:
- Debit total must equal credit total for every transaction.
- Expense increases are debits.
- Liability increases are credits.
- Revenue increases are credits.
- Corporate credit card payments should normally credit "Credit Card Payable", not "Cash and Cash Equivalents" or "Bank Account".
- Do not recognize revenue from a mere order or letter of credit.
- Recognize revenue only when delivery, transfer of control, invoice issuance, or performance obligation satisfaction is present in the evidence.
- If evidence is insufficient, return status "insufficient_information" instead of inventing missing facts.
- Use KRW integer amounts. Do not guess missing amounts.
- The demo scope is at most 3 transactions.

JSON shape:
{{
  "status": "ok",
  "reason": "short explanation",
  "currency": "KRW",
  "transactions": [
    {{
      "no": 1,
      "date": "YY-MM-DD",
      "evidence_summary": "short summary of the OCR evidence",
      "lines": [
        {{
          "account": "Employee Benefits Expense",
          "description": "Staff refreshments",
          "debit": 5000,
          "credit": 0
        }},
        {{
          "account": "Credit Card Payable",
          "description": "Corporate credit card settlement payable",
          "debit": 0,
          "credit": 5000
        }}
      ]
    }}
  ]
}}

For insufficient evidence:
{{
  "status": "insufficient_information",
  "reason": "The evidence does not show enough accounting facts.",
  "currency": "KRW",
  "transactions": []
}}

Evidence OCR text:
\"\"\"
{ocr_text}
\"\"\"
""".strip()


def generate_journal(prompt: str) -> str:
    payload: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "top_p": 0.8,
        },
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.ConnectionError as exc:
        logger.exception("Ollama server unavailable")
        raise OllamaError("Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인해 주세요.") from exc
    except requests.Timeout as exc:
        logger.exception("Ollama request timed out")
        raise OllamaError("Ollama 응답 시간이 초과되었습니다. 더 작은 모델을 사용하거나 다시 시도해 주세요.") from exc
    except requests.RequestException as exc:
        logger.exception("Ollama request failed")
        raise OllamaError("Ollama 호출 중 오류가 발생했습니다.") from exc

    if response.status_code == 404:
        raise OllamaError(f"Ollama 모델을 찾을 수 없습니다: {OLLAMA_MODEL}")
    if response.status_code >= 400:
        logger.error("Ollama HTTP error %s: %s", response.status_code, response.text[:1000])
        raise OllamaError("Ollama 서버가 오류를 반환했습니다.")

    try:
        data = response.json()
    except ValueError as exc:
        logger.error("Ollama returned non-JSON HTTP body: %s", response.text[:1000])
        raise OllamaError("Ollama 응답을 해석할 수 없습니다.") from exc

    if "error" in data:
        message = str(data["error"])
        if "not found" in message.lower():
            raise OllamaError(f"Ollama 모델을 찾을 수 없습니다: {OLLAMA_MODEL}")
        raise OllamaError(f"Ollama 오류: {message}")

    generated = str(data.get("response", "")).strip()
    if not generated:
        raise OllamaError("Ollama가 빈 응답을 반환했습니다.")
    return generated
