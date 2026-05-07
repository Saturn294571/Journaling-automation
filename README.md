# Accounting Journal Automation Demo

FastAPI 기반 회계 증빙 이미지 분개 자동화 데모입니다. 사용자가 영수증 또는 거래 증빙 이미지를 업로드하면 OCR로 텍스트를 추출하고, 로컬 Ollama sLLM에 전달해 JSON 분개 초안을 생성한 뒤 SQLite에 저장하고 화면에 표시합니다.

## 주요 기능

- jpg, jpeg, png 이미지 업로드
- 10MB 파일 크기 제한
- 업로드 이미지 미리보기 및 다시 업로드 버튼
- Tesseract OCR 기반 텍스트 추출
- Ollama 로컬 sLLM 호출
- 모델 응답 JSON 파싱 및 계정과목 검증
- 차변/대변 합계 검증
- SQLite 저장
- OCR 텍스트와 분개 결과 테이블 표시
- 한국어 사용자 오류 메시지와 서버 로그

## 설치

Python 3.11 이상을 권장합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

가상환경을 쓰기 어렵다면 사용자 Python 환경에 설치할 수도 있습니다.

```powershell
python -m pip install --user -r requirements.txt
```

## Tesseract OCR 준비

이 프로젝트는 OCR 라이브러리로 `pytesseract`를 사용합니다. Python 패키지 외에 Tesseract 실행 파일이 필요합니다.

Windows에서는 UB Mannheim Tesseract 빌드를 설치한 뒤 설치 경로를 PATH에 추가하세요.

Korean OCR을 쓰려면 `kor.traineddata`가 포함되어 있어야 합니다. OCR 호출 언어는 `kor+eng`입니다.

## Ollama 준비

Ollama를 설치하고 서버를 실행합니다.

```powershell
ollama serve
```

별도 터미널에서 기본 모델을 내려받습니다.

```powershell
ollama pull llama3.1:8b
```

다른 모델을 쓰려면 환경 변수를 지정할 수 있습니다.

```powershell
$env:OLLAMA_MODEL="qwen2.5:7b-instruct"
$env:OLLAMA_BASE_URL="http://localhost:11434"
```

## 실행

```powershell
python -m uvicorn app.main:app --reload
```

브라우저에서 아래 주소를 엽니다.

```text
http://127.0.0.1:8000
```

## 저장 데이터

실행 중 생성되는 데이터는 다음 위치에 저장됩니다.

- 업로드 이미지: `uploads/`
- SQLite DB: `accounting_demo.sqlite3`

DB에는 업로드 파일명, 저장 파일명, OCR 텍스트, Ollama 프롬프트, 모델 원문 응답, 정규화된 JSON, 분개 라인이 저장됩니다.

## GCP 배포 메모

로컬 실행을 우선으로 구성했습니다. GCP에 배포하려면 다음 중 하나를 선택할 수 있습니다.

- GCP VM: Tesseract, Ollama, Python 의존성을 VM에 설치하고 `uvicorn` 또는 `gunicorn`으로 실행
- Cloud Run: FastAPI 앱은 컨테이너화할 수 있지만, Ollama와 Tesseract 런타임 구성이 필요하므로 데모 전 별도 테스트가 필요

현재 프로젝트에는 GCP VM 배포용 설정과 가이드가 포함되어 있습니다.

- 배포 가이드: `deploy/DEPLOY_GCP_VM.md`
- VM 설치 스크립트: `deploy/setup-vm.sh`
- systemd 서비스: `deploy/accounting-demo.service`
- Nginx 설정: `deploy/nginx-accounting-demo.conf`

발표 데모에서는 Cloud Run보다 Compute Engine VM을 권장합니다. OCR, Ollama, SQLite, FastAPI를 한 VM 안에서 관리하는 편이 단순하고 예측 가능하기 때문입니다.

## 알려진 제한사항

- OCR 품질은 이미지 선명도와 Tesseract 언어 데이터에 크게 의존합니다.
- Ollama 모델이 JSON 규칙을 어기면 앱은 결과를 저장하지 않고 오류를 표시합니다.
- 허용 계정과목은 요구사항의 기본 계정 목록으로 제한했습니다.
- 발표 데모 범위에 맞춰 거래는 최대 3개까지 검증합니다.
- 실제 회계 판단을 대체하는 서비스가 아니라 수업 발표용 프로토타입입니다.
