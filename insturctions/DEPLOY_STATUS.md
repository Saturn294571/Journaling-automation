# Deployment Status

Last verified: 2026-05-13

## GCP Resources

- Project ID: `acct-demo-260511-320`
- VM name: `accounting-demo`
- Zone: `asia-northeast3-a`
- Machine type: `e2-standard-4`
- External URL: `http://34.50.6.101`
- Ollama model: `qwen2.5:3b`

## Service Status

Verified on the VM:

- `accounting-demo`: active
- `nginx`: active
- `ollama`: active
- Tesseract languages installed: `eng`, `kor`, `osd`
- Ollama model installed: `qwen2.5:3b`

## Verification Results

### 1. Front Page

Result: success

The deployed web page returned HTTP 200 from:

```text
http://34.50.6.101
```

### 2. Real Uploaded Image

Result: pipeline success, but evidence insufficient

The server accepted the image, ran OCR, called Ollama, and stored the result. The uploaded image had noisy OCR text, so the model safely returned:

```text
insufficient_information
```

This is acceptable behavior because the app should not invent missing accounting facts.

### 3. Clear Test Receipt

Result: full success

Test image: `test_receipt_clear.png`

The app returned a valid journal result:

| Account | Debit | Credit |
| --- | ---: | ---: |
| Employee Benefits Expense | 5,000 | 0 |
| Credit Card Payable | 0 | 5,000 |

Debit total and credit total matched.

### 4. English Repair Invoice Demo

Result: full success

Test image: `receipt-template-us-classic-white-750px.png`

The deployed app OCR recognized the invoice clearly and returned a valid USD journal result:

| Account | Debit | Credit |
| --- | ---: | ---: |
| Office Supplies Expense | 154.06 | 0 |
| Accounts Payable | 0 | 154.06 |

Debit total and credit total matched.

## Demo Notes

For a reliable classroom demo, use a clear image with large printed text. OCR quality strongly affects the final AI result.

Recommended demo URL:

```text
http://34.50.6.101
```

## Cost Control

Stop the VM when the demo is not needed:

```powershell
gcloud compute instances stop accounting-demo --zone=asia-northeast3-a --project=acct-demo-260511-320
```

Start it again:

```powershell
gcloud compute instances start accounting-demo --zone=asia-northeast3-a --project=acct-demo-260511-320
```

Delete it after the project is finished:

```powershell
gcloud compute instances delete accounting-demo --zone=asia-northeast3-a --project=acct-demo-260511-320
```
