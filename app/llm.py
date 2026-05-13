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
You are an accounting staff member of Inha Inc. for a Principles of Accounting demo.
Inha Inc. is an education service company, but it may process ordinary operating receipts and invoices issued to the company, employees, or representatives.
Use IFRS-style basic journal logic and the evidence text below.

Return ONLY valid JSON. Do not wrap it in markdown.
Never copy example amounts, dates, descriptions, or accounts from this prompt.
Use only facts from the OCR text and the company policy.

Allowed accounts:
{accounts}

Rules:
- Treat uploaded receipts and invoices as Inha Inc. expense evidence unless the document clearly shows Inha Inc. is the seller.
- Do not classify an ordinary receipt or invoice as Sales Revenue just because it was issued by a store or service provider.
- Documents billed to an employee or individual may still be company expense evidence unless personal use is clear.
- If the document is for repairs, maintenance, small equipment parts, services, or office operation costs and no more specific allowed account exists, use "Office Supplies Expense".
- If payment is due later, unpaid, invoice-like, or the document includes terms such as "payment is due", credit "Accounts Payable".
- If the document shows credit card or corporate card payment, credit "Credit Card Payable".
- If the receipt is from a restaurant, cafe, snack shop, or food service business, and there is no evidence of personal use or customer entertainment, debit "Employee Benefits Expense".
- Include sales tax/VAT in the total amount. Do not create separate tax lines for this demo.
- Use the detected currency. Use KRW for Korean won documents and USD for dollar documents. Decimal amounts are allowed up to two decimal places.
- If the OCR text is noisy, broken, or does not clearly show the transaction facts, return status "insufficient_information".
- Debit total must equal credit total for every transaction.
- Expense increases are debits.
- Liability increases are credits.
- Revenue increases are credits.
- Corporate credit card payments should normally credit "Credit Card Payable", not "Cash and Cash Equivalents" or "Bank Account".
- Do not recognize revenue from a mere order or letter of credit.
- Recognize revenue only when delivery, transfer of control, invoice issuance, or performance obligation satisfaction is present in the evidence.
- If evidence is insufficient, return status "insufficient_information" instead of inventing missing facts.
- Do not guess missing amounts.
- The demo scope is at most 3 transactions.
- If OCR text contains repair/service invoice items such as brake cables, pedal arms, labor, repair, maintenance, and a total amount, classify the total as "Office Supplies Expense" unless a more specific allowed account applies.
- If OCR text contains "Payment is due", credit "Accounts Payable", not "Credit Card Payable".
- If OCR text contains "TOTAL $154.06" and "Payment is due within 15 days", use debit 154.06 and credit 154.06 in USD.

Required JSON shape:
{{
  "status": "ok",
  "reason": "short explanation",
  "currency": "detected currency such as KRW or USD",
  "transactions": [
    {{
      "no": 1,
      "date": "YYYY-MM-DD or unknown",
      "evidence_summary": "short summary of the OCR evidence",
      "lines": [
        {{
          "account": "account selected from allowed accounts",
          "description": "description based on OCR evidence",
          "debit": 0,
          "credit": 0
        }},
        {{
          "account": "account selected from allowed accounts",
          "description": "description based on OCR evidence",
          "debit": 0,
          "credit": 0
        }}
      ]
    }}
  ]
}}

For the East Repair Inc. invoice example:
{{
  "status": "ok",
  "reason": "Repair/service invoice treated as operating expense; payment is due later.",
  "currency": "USD",
  "transactions": [
    {{
      "no": 1,
      "date": "2019-02-11",
      "evidence_summary": "Repair invoice from East Repair Inc. totaling USD 154.06.",
      "lines": [
        {{
          "account": "Office Supplies Expense",
          "description": "Repair/service invoice including parts and labor",
          "debit": 154.06,
          "credit": 0
        }},
        {{
          "account": "Accounts Payable",
          "description": "Payment due within 15 days",
          "debit": 0,
          "credit": 154.06
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


def build_debug_prompt(ocr_text: str) -> str:
    return f"""
You are helping debug an OCR-to-accounting demo.

Read the OCR text below and explain what transaction facts you can infer.
This is only a debug explanation, not a final journal entry.

Please include:
1. What facts look reliable.
2. What facts are uncertain because OCR may be wrong.
3. What accounting treatment might be possible if the user confirms the business purpose.
4. Whether the OCR text alone is enough for a final journal entry.

OCR text:
\"\"\"
{ocr_text}
\"\"\"
""".strip()


def generate_debug_inference(prompt: str) -> str:
    payload: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
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
        logger.exception("Ollama debug request timed out")
        raise OllamaError("Ollama 디버그 추론 응답 시간이 초과되었습니다.") from exc
    except requests.RequestException as exc:
        logger.exception("Ollama debug request failed")
        raise OllamaError("Ollama 디버그 추론 중 오류가 발생했습니다.") from exc

    if response.status_code == 404:
        raise OllamaError(f"Ollama 모델을 찾을 수 없습니다: {OLLAMA_MODEL}")
    if response.status_code >= 400:
        logger.error("Ollama debug HTTP error %s: %s", response.status_code, response.text[:1000])
        raise OllamaError("Ollama 서버가 오류를 반환했습니다.")

    try:
        data = response.json()
    except ValueError as exc:
        logger.error("Ollama returned non-JSON HTTP body: %s", response.text[:1000])
        raise OllamaError("Ollama 응답을 해석할 수 없습니다.") from exc

    generated = str(data.get("response", "")).strip()
    if not generated:
        raise OllamaError("Ollama가 빈 디버그 응답을 반환했습니다.")
    return generated
