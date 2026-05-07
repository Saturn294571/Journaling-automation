# GCP VM Deployment Guide

이 프로젝트는 OCR과 로컬 LLM을 서버에서 돌려야 하므로 Cloud Run보다 Compute Engine VM 배포가 단순합니다. Cloud Run은 컨테이너 시작 시간, 모델 파일 크기, Ollama 프로세스 관리 때문에 발표 데모 직전에는 리스크가 큽니다.

## 권장 구조

```text
User browser
  -> http://VM_EXTERNAL_IP
  -> Nginx :80
  -> FastAPI/Uvicorn :8000
  -> Tesseract OCR
  -> Ollama :11434
  -> SQLite
```

## VM 권장 사양

발표 데모용 권장값:

- OS: Ubuntu 24.04 LTS
- Machine type: `e2-standard-4` 또는 그 이상
- Boot disk: 30GB 이상
- Firewall: HTTP traffic 허용
- Ollama model: 기본 배포 스크립트는 `qwen2.5:3b` 사용

`e2-standard-2`도 작은 모델에서는 가능할 수 있지만, OCR과 Ollama가 함께 돌 때 응답이 느려질 수 있습니다. 안정적인 발표 데모라면 16GB RAM급 VM이 더 편합니다.

참고:

- Google Compute Engine VM 생성 문서: https://docs.cloud.google.com/compute/docs/create-linux-vm-instance
- Google E2 machine type 문서: https://cloud.google.com/compute/docs/general-purpose-machines
- Ollama Linux 설치 문서: https://docs.ollama.com/linux

## 1. 로컬에서 배포 패키지 만들기

PowerShell에서 프로젝트 루트에서 실행합니다.

```powershell
Compress-Archive `
  -Path app,deploy,requirements.txt,README.md `
  -DestinationPath accounting-demo.zip `
  -Force
```

`.venv`, `.deps`, `uploads`, `accounting_demo.sqlite3`는 업로드하지 않습니다.

## 2. GCP VM 생성

Cloud Console에서 만드는 방법이 가장 안전합니다.

1. Compute Engine > VM instances > Create instance
2. OS: Ubuntu 24.04 LTS
3. Machine type: `e2-standard-4`
4. Boot disk: 30GB 이상
5. Firewall: Allow HTTP traffic 체크
6. Create

gcloud CLI를 쓴다면 예시는 아래와 같습니다.

```powershell
gcloud compute instances create accounting-demo `
  --zone=asia-northeast3-a `
  --machine-type=e2-standard-4 `
  --image-family=ubuntu-2404-lts-amd64 `
  --image-project=ubuntu-os-cloud `
  --boot-disk-size=30GB `
  --tags=http-server
```

HTTP 방화벽 규칙이 없다면 추가합니다.

```powershell
gcloud compute firewall-rules create allow-accounting-demo-http `
  --allow=tcp:80 `
  --target-tags=http-server `
  --description="Allow HTTP for accounting demo"
```

## 3. 파일 업로드

```powershell
gcloud compute scp accounting-demo.zip accounting-demo:~/accounting-demo.zip --zone=asia-northeast3-a
```

## 4. VM에서 설치 실행

VM에 SSH 접속합니다.

```powershell
gcloud compute ssh accounting-demo --zone=asia-northeast3-a
```

VM 안에서:

```bash
sudo apt-get update
sudo apt-get install -y unzip
sudo mkdir -p /opt/accounting-demo
sudo unzip -o ~/accounting-demo.zip -d /opt/accounting-demo
cd /opt/accounting-demo
sudo OLLAMA_MODEL=qwen2.5:3b bash deploy/setup-vm.sh
```

더 큰 모델을 쓰려면 VM RAM을 넉넉하게 잡고 모델명을 바꿉니다.

```bash
sudo OLLAMA_MODEL=llama3.1:8b bash deploy/setup-vm.sh
```

## 5. 접속 확인

VM 외부 IP를 확인합니다.

```powershell
gcloud compute instances describe accounting-demo `
  --zone=asia-northeast3-a `
  --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
```

브라우저에서 엽니다.

```text
http://VM_EXTERNAL_IP
```

## 6. 운영 확인 명령

VM 안에서:

```bash
sudo systemctl status accounting-demo --no-pager
sudo journalctl -u accounting-demo -f
sudo systemctl status ollama --no-pager
sudo journalctl -u ollama -f
sudo nginx -t
```

Ollama 모델 확인:

```bash
ollama list
```

앱만 재시작:

```bash
sudo systemctl restart accounting-demo
```

## 7. 발표 전 체크리스트

- `http://VM_EXTERNAL_IP`에서 첫 화면이 뜬다.
- jpg/png 업로드 시 이미지 미리보기가 뜬다.
- OCR 미설치 에러가 더 이상 나오지 않는다.
- Ollama 모델이 없다는 에러가 나오지 않는다.
- 흐린 사진 업로드 시 사용자에게 오류 메시지가 보인다.
- 선명한 테스트 이미지에서 OCR 텍스트가 표시된다.
- 모델 응답이 JSON 검증을 통과한다.
- 차변/대변 합계가 맞는 결과만 저장된다.

## 8. 비용 정리

발표 준비가 끝나면 비용 방지를 위해 VM을 중지하거나 삭제합니다.

```powershell
gcloud compute instances stop accounting-demo --zone=asia-northeast3-a
```

완전히 삭제:

```powershell
gcloud compute instances delete accounting-demo --zone=asia-northeast3-a
```

## 문제 해결

### HTTP 접속이 안 됨

- VM에 외부 IP가 있는지 확인합니다.
- HTTP firewall이 열려 있는지 확인합니다.
- `sudo systemctl status nginx --no-pager`를 확인합니다.

### OCR 에러

```bash
tesseract --list-langs
```

`kor`와 `eng`가 보여야 합니다.

### Ollama 연결 실패

```bash
sudo systemctl status ollama --no-pager
curl http://127.0.0.1:11434/api/tags
```

### 모델 응답이 너무 느림

- `qwen2.5:3b`처럼 작은 모델을 사용합니다.
- VM을 `e2-standard-4` 이상으로 올립니다.
- 발표 전에 같은 테스트 이미지로 한 번 예열합니다.
