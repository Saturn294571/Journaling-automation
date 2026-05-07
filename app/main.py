from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.accounting import JournalValidationError, parse_model_json, validate_and_normalize
from app.database import get_recent_uploads, init_db, save_result
from app.llm import OLLAMA_MODEL, OllamaError, build_prompt, generate_journal
from app.ocr import OcrError, extract_text


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
UPLOAD_DIR.mkdir(exist_ok=True)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(title="Accounting Journal Automation Demo")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.on_event("startup")
def startup() -> None:
    init_db()
    logger.info("Application started with Ollama model=%s", OLLAMA_MODEL)


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "recent_uploads": get_recent_uploads(),
            "ollama_model": OLLAMA_MODEL,
        },
    )


@app.post("/api/process")
async def process_upload(file: UploadFile = File(...)) -> JSONResponse:
    original_filename = file.filename or "uploaded-image"
    extension = Path(original_filename).suffix.lower()
    content_type = file.content_type or ""

    if extension not in ALLOWED_EXTENSIONS or content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="jpg, jpeg, png 이미지 파일만 업로드할 수 있습니다.")

    content = await file.read()
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="빈 파일은 업로드할 수 없습니다.")
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="파일 크기는 10MB 이하만 허용됩니다.")

    stored_filename = f"{uuid4().hex}{extension}"
    stored_path = UPLOAD_DIR / stored_filename
    stored_path.write_bytes(content)
    logger.info("Uploaded file saved: original=%s stored=%s size=%s", original_filename, stored_filename, file_size)

    prompt = ""
    model_response = ""
    try:
        ocr_text = extract_text(stored_path)
        prompt = build_prompt(ocr_text)
        model_response = generate_journal(prompt)
        parsed = parse_model_json(model_response)
        normalized, lines = validate_and_normalize(parsed)
        upload_id = save_result(
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type,
            file_size=file_size,
            ocr_text=ocr_text,
            prompt=prompt,
            model_response=model_response,
            normalized=normalized,
            lines=lines,
        )
    except OcrError as exc:
        logger.warning("OCR failed for %s: %s", stored_filename, exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OllamaError as exc:
        logger.warning("Ollama failed for %s: %s", stored_filename, exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except JournalValidationError as exc:
        logger.warning("Journal validation failed for %s: %s", stored_filename, exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        logger.exception("Database write failed for %s", stored_filename)
        raise HTTPException(status_code=500, detail="SQLite 저장 중 오류가 발생했습니다.") from exc
    except Exception as exc:
        logger.exception("Unexpected processing failure for %s", stored_filename)
        raise HTTPException(status_code=500, detail="처리 중 알 수 없는 오류가 발생했습니다.") from exc

    return JSONResponse(
        {
            "id": upload_id,
            "image_url": f"/uploads/{stored_filename}",
            "original_filename": original_filename,
            "ocr_text": ocr_text,
            "result": normalized,
            "lines": [
                {
                    "no": line.transaction_no,
                    "date": line.transaction_date,
                    "account": line.account,
                    "description": line.description,
                    "debit": line.debit,
                    "credit": line.credit,
                }
                for line in lines
            ],
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
