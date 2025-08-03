#this file is required by SageMaker: https://docs.aws.amazon.com/sagemaker/latest/dg/your-algorithms-inference-code.html
import os
import threading
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .payloads import JobApplicationRequestModel, JobAcceptedResponse
from .pipeline import query_rag_pipeline
from .util import timed

### debugging
if os.getenv("DEBUGPY_ENABLED", "false").lower() == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("✅ debugpy is listening on port 5678 — waiting for debugger to attach...")

app = FastAPI(
    title="Upwork JOB agent inference API",
    description="Retrieves the experience and sales points related to job description that can be used to construct a job application.",
    version="1.0.0")
security = HTTPBasic()

profiling_enabled = os.getenv("ENABLE_PROFILING", "false").lower()
if profiling_enabled == "true":
    from .profiler import PyInstrumentMiddleWare
    app.add_middleware(PyInstrumentMiddleWare)
    print("✅ fastapi-profiler middleware enabled")

BASIC_AUTH_USER = os.getenv('BASIC_AUTH_USER')
BASIC_AUTH_PASS = os.getenv('BASIC_AUTH_PASS')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username == BASIC_AUTH_USER
    password = credentials.password == BASIC_AUTH_PASS
    if not (username and password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    return credentials.username

 # === FastAPI route (SageMaker expects this exact path) ===
@app.post("/invocations", response_model=JobAcceptedResponse, status_code=202)
async def handle_invocation(request: Request):
    try:
        payload = await request.json()
        job = JobApplicationRequestModel(**payload)
        job_id = payload.get('job_id')

        # Start async background job
        threading.Thread(target=process_job, args=(job, job_id)).start()

        return JobAcceptedResponse(job_id=job_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference startup failed: {e}")


# === Long-running RAG logic ===
@timed
def process_job(job: JobApplicationRequestModel, job_id: str):
    try:
        result = query_rag_pipeline(job)

        response = _send_webhook(job_id, result)
        print(f"📡 Webhook sent → status: {response.status_code}")
        if response.status_code != 200:
            print(f"⚠️ Webhook failed: {response.text}")

        print(f"[✓] Webhook success for job {job_id}")

    except Exception as err:
        print(f"[!] Inference failed for job {job_id}: {err}")

import requests

def _send_webhook(job_uuid: str, result: dict) -> Response:
    """Send HTTP webhook back to n8n with job completion status."""
    try:
        payload = {
            "job_id": job_uuid,
            "status": "PROCESSED",
            "result_url": f"{os.environ.get('SUPABASE_URL')}/rest/v1/upwork_jobs?job_uuid=eq.{job_uuid}",
        }

        headers = {
            "Content-Type": "application/json",
        }

        res = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        
        return res

    except Exception as e:
        print("🔥 Failed to send webhook:", str(e))