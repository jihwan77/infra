from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import subprocess, os, json
from pathlib import Path
import re
from datetime import datetime, timedelta, timezone

app = FastAPI(title="Terraform Runner - Local State")

BASE_CVE_DIR = Path("/opt/terraform-runner/terraform/cve_templates")
VALID = re.compile(r"^[A-Za-z0-9_\-]+$")

# ---------------------------
# 요청 모델
# ---------------------------
class CreateRequest(BaseModel):
    uuid: str
    cveId: str
    userId: str

class DestroyRequest(BaseModel):
    uuid: str
    cveId: str
    userId: str

# ---------------------------
# 유효성 체크
# ---------------------------
def validate(name: str):
    if not VALID.match(name):
        raise HTTPException(status_code=400, detail=f"Invalid name: {name}")


# ---------------------------
# Terraform 실행 함수
# ---------------------------
def run_cmd(cmd: list, cwd: Path):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[Terraform Error] {proc.stderr}")
        raise HTTPException(status_code=500, detail=proc.stderr)

    print(f"[Terraform OK] {' '.join(cmd)}")
    return proc.stdout.strip()


# ---------------------------
# CREATE API
# ---------------------------
@app.post("/api/labs/create")
def create(req: CreateRequest):
    validate(req.cveId)
    validate(req.uuid)

    cve_path = BASE_CVE_DIR / req.cveId
    if not cve_path.exists():
        raise HTTPException(status_code=404, detail="CVE folder not found")

    state_dir = cve_path / "states"
    state_dir.mkdir(exist_ok=True)
    state_file = state_dir / f"{req.uuid}.tfstate"

    # init
    run_cmd(["terraform", "init", "-input=false", "-no-color"], cve_path)

    # apply
    run_cmd([
        "terraform", "apply", "-auto-approve", "-input=false", "-no-color",
        f"-state={state_file}",
        f"-var=uuid={req.uuid}",
        f"-var=cve_id={req.cveId}",
        f"-var=user_id={req.userId}"
    ], cve_path)

    # output
    output_raw = run_cmd(["terraform", "output", "-json", f"-state={state_file}"], cve_path)
    try:
        outputs = json.loads(output_raw)
    except:
        outputs = {"raw": output_raw}

    # KST timestamp
    kst = timezone(timedelta(hours=9))
    created_time = datetime.now(kst).isoformat()

    return {
        "status": "success",
        "uuid": req.uuid,
        "cveId": req.cveId,
        "tfstate_path": str(state_file),
        "created_time": created_time,
        "outputs": outputs
    }


# ---------------------------
# DESTROY 비동기 실행 함수
# ---------------------------
def run_destroy_async(req: DestroyRequest, cve_path: Path, state_file: Path):
    """백그라운드에서 실행되는 destroy 작업"""
    try:
        print(f"[Destroy] Async destroy start for {req.uuid}")

        run_cmd(["terraform", "init", "-input=false", "-no-color"], cve_path)

        run_cmd([
            "terraform", "destroy", "-auto-approve", "-input=false", "-no-color",
            f"-state={state_file}",
            f"-var=uuid={req.uuid}",
            f"-var=cve_id={req.cveId}",
            f"-var=user_id={req.userId}"
        ], cve_path)

        # destroy 성공 후 tfstate 삭제
        if state_file.exists():
            os.remove(state_file)
            print(f"[Destroy] State file removed: {state_file}")

        print(f"[Destroy] Async destroy complete for {req.uuid}")

    except Exception as e:
        print(f"[Destroy Error] {e}")


# ---------------------------
# DESTROY API - 즉시 응답
# ---------------------------
@app.post("/api/labs/destroy")
def destroy(req: DestroyRequest, background_tasks: BackgroundTasks):
    validate(req.cveId)
    validate(req.uuid)

    cve_path = BASE_CVE_DIR / req.cveId
    state_file = cve_path / "states" / f"{req.uuid}.tfstate"

    if not state_file.exists():
        raise HTTPException(status_code=404, detail="State file not found")

    # destroy를 백그라운드에서 실행
    background_tasks.add_task(run_destroy_async, req, cve_path, state_file)

    # 응답 즉시 반환
    kst = timezone(timedelta(hours=9))
    request_time = datetime.now(kst).isoformat()

    return {
        "status": "destroy-started",
        "uuid": req.uuid,
        "cveId": req.cveId,
        "request_time": request_time
    }


# ---------------------------
# 헬스체크
# ---------------------------
@app.get("/health")
def health():
    return {"ok": True}
