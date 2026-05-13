from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps


logger = logging.getLogger(__name__)


class OcrError(RuntimeError):
    pass


def extract_text(image_path: Path) -> str:
    try:
        import pytesseract
    except ImportError as exc:
        raise OcrError("OCR 라이브러리(pytesseract)가 설치되어 있지 않습니다.") from exc

    try:
        with Image.open(image_path) as image:
            image = _prepare_for_receipt_ocr(image)
            config = "--oem 3 --psm 6 -c preserve_interword_spaces=1"
            text = pytesseract.image_to_string(image, lang="kor+eng", config=config)
    except pytesseract.TesseractNotFoundError as exc:
        logger.exception("Tesseract executable not found")
        raise OcrError("Tesseract OCR 실행 파일을 찾을 수 없습니다. 설치 후 PATH를 확인해 주세요.") from exc
    except pytesseract.TesseractError as exc:
        logger.exception("Tesseract OCR failed")
        raise OcrError("OCR 처리 중 오류가 발생했습니다.") from exc
    except Exception as exc:
        logger.exception("Image OCR failed")
        raise OcrError("이미지를 읽거나 OCR을 수행할 수 없습니다.") from exc

    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if len(cleaned) < 5:
        raise OcrError("OCR 결과가 너무 적습니다. 더 선명한 영수증 또는 거래 증빙 이미지를 업로드해 주세요.")
    return cleaned


def _prepare_for_receipt_ocr(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")

    width, height = image.size
    shortest_side = min(width, height)
    if shortest_side < 1400:
        scale = 1400 / shortest_side
        new_size = (int(width * scale), int(height * scale))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.SHARPEN)
    image = image.point(lambda pixel: 255 if pixel > 175 else 0)
    return image
