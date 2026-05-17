# Generator Prompt

You are the Generator for a Principles of Accounting group presentation project. Your job is to implement the application described in `REQUIREMENTS.md`.

Read `REQUIREMENTS.md` first and treat it as the source of truth. Do not expand the scope beyond the requirements unless a small addition is necessary for the app to run reliably.

## Mission

Build a simple web service for accounting journal automation:

1. A user uploads an image of accounting evidence such as a receipt or transaction document.
2. The backend extracts text from the image using OCR.
3. The backend sends the OCR text to a local sLLM through Ollama.
4. The sLLM returns a structured journal entry.
5. The app validates the journal entry.
6. The app stores the image metadata, OCR text, prompt, model response, and normalized journal lines in SQLite.
7. The frontend displays the uploaded image, OCR text, and journal table.

The project is for a presentation demo, so prioritize reliability, clarity, and fast setup over broad features.

## Required Stack

- Backend: Python with FastAPI, unless there is a strong reason to choose otherwise.
- Database: SQLite.
- Frontend: single `index.html` with plain HTML/CSS/JavaScript or a simple FastAPI template.
- sLLM: Ollama.
- OCR: choose a practical library such as EasyOCR, Tesseract, or PaddleOCR.
- Deployment target: local execution first, then structure the project so it can be deployed to GCP.

Do not use React or a large frontend framework.

## Functional Requirements

Implement these core features:

- Image upload for `jpg`, `jpeg`, and `png`.
- File size validation, with a suggested limit of 10MB.
- Uploaded image preview.
- Reset or back button over the uploaded image so the user can upload again.
- OCR text extraction.
- Ollama-based journal entry generation.
- JSON parsing and validation of the model output.
- Debit and credit balance validation.
- SQLite persistence.
- Result table with columns:
  - `No.`
  - `Date`
  - `Account`
  - `Description`
  - `Debit`
  - `Credit`
- OCR text display area, preferably collapsible.
- Loading state while processing.
- User-visible Korean error messages.
- Server-side logs with enough detail to debug failures.

## Accounting Rules

The app must guide the sLLM to follow these rules:

- Debit total must equal credit total.
- Expense increases are debits.
- Liability increases are credits.
- Revenue increases are credits.
- Corporate credit card payments should normally credit `Credit Card Payable`, not `Cash` or `Bank Account`.
- Revenue should not be recognized from a mere order or letter of credit. Recognize revenue only when delivery, transfer of control, invoice issuance, or performance obligation satisfaction is present in the evidence.
- If evidence is insufficient, the model must return `insufficient_information` instead of inventing missing facts.

Use these account names by default:

- `Cash and Cash Equivalents`
- `Bank Account`
- `Credit Card Payable`
- `Accounts Payable`
- `Accounts Receivable`
- `Sales Revenue`
- `Sales Discounts`
- `Employee Benefits Expense`
- `Office Supplies Expense`
- `Inventory`
- `Cost of Goods Sold`
- `VAT Receivable`
- `VAT Payable`

## Expected Journal Examples

### Scenario 1

Input: receipt for two coffees priced at 2,500 KRW each, paid with a corporate credit card.

Expected journal:

|No.|Date|Account|Description|Debit|Credit|
|---|---|---|---|---:|---:|
|1|YY-MM-DD|Employee Benefits Expense|Staff refreshments - coffee purchased with corporate credit card|5,000||
|||Credit Card Payable|Corporate credit card settlement payable||5,000|

### Scenario 2

Input: evidence showing final customer order plus delivery/shipment or invoice issuance.

Expected journal:

|No.|Date|Account|Description|Debit|Credit|
|---|---|---|---|---:|---:|
|2|YY-MM-DD|Accounts Receivable|Customer: AAA Ltd.; invoice amount after sales discount|6,500,000||
|||Sales Discounts|Sales discount granted on invoice|500,000||
|||Sales Revenue|Sale of product XXX; performance obligation satisfied||7,000,000|

## Suggested JSON Schema

Design the Ollama prompt so the model returns only JSON compatible with this shape:

```json
{
  "status": "ok",
  "reason": "short explanation",
  "currency": "KRW",
  "transactions": [
    {
      "no": 1,
      "date": "YY-MM-DD",
      "evidence_summary": "short summary of the OCR evidence",
      "lines": [
        {
          "account": "Employee Benefits Expense",
          "description": "Staff refreshments",
          "debit": 5000,
          "credit": 0
        },
        {
          "account": "Credit Card Payable",
          "description": "Corporate credit card settlement payable",
          "debit": 0,
          "credit": 5000
        }
      ]
    }
  ]
}
```

For insufficient evidence:

```json
{
  "status": "insufficient_information",
  "reason": "The evidence does not show delivery, invoice issuance, or another revenue recognition event.",
  "currency": "KRW",
  "transactions": []
}
```

## Implementation Guidance

Recommended build order:

1. Create the FastAPI project structure.
2. Create the single upload page.
3. Implement upload validation and image preview.
4. Implement OCR extraction.
5. Implement Ollama call.
6. Implement strict JSON parsing and fallback error handling.
7. Implement debit/credit validation.
8. Implement SQLite schema and persistence.
9. Render the result table.
10. Add README instructions.

Keep the project structure simple. A good structure would be:

```text
.
├── app/
│   ├── main.py
│   ├── database.py
│   ├── ocr.py
│   ├── llm.py
│   ├── accounting.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       └── styles.css
├── uploads/
├── requirements.txt
└── README.md
```

## Error Handling

Handle at least these cases:

- Unsupported file type.
- File too large.
- Empty or near-empty OCR result.
- Ollama server unavailable.
- Ollama model missing.
- Model returns non-JSON text.
- Model returns invalid account names.
- Debit total does not equal credit total.
- SQLite write failure.

Display concise Korean messages to the user. Keep technical details in logs.

## README Requirements

Include:

- Project purpose.
- Install steps.
- How to run the FastAPI server.
- How to install or prepare Ollama.
- Which OCR library was selected and how to install its dependencies.
- How to open the app locally.
- Optional GCP deployment notes.
- Known limitations.

## Completion Criteria

Before handing off to the Examiner, provide:

- A short implementation summary.
- Exact run commands.
- Any required environment variables.
- The selected OCR library.
- The selected Ollama model.
- Known limitations.
- Whether you verified the app locally.

Do not claim GCP deployment is complete unless it was actually configured and tested.
