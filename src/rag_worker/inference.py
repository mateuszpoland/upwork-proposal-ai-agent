#this file is required by SageMaker: https://docs.aws.amazon.com/sagemaker/latest/dg/your-algorithms-inference-code.html
import os
import threading
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.security import HTTPBasic
from .payloads import JobApplicationRequestModel, JobAcceptedResponse
from .pipeline import query_rag_pipeline
from .util import timed
from ..config import config

### debugging
if config.get_bool("DEBUGPY_ENABLED", False):
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("✅ debugpy is listening on port 5678 — waiting for debugger to attach...")

app = FastAPI(
    title="Upwork JOB agent inference API",
    description="Retrieves the experience and sales points related to job description that can be used to construct a job application.",
    version="1.0.0")

from .endpoint_control import router as control_router
app.include_router(control_router)

security = HTTPBasic()

if config.get_bool("ENABLE_PROFILING", False):
    from .profiler import PyInstrumentMiddleWare
    app.add_middleware(PyInstrumentMiddleWare)
    print("✅ fastapi-profiler middleware enabled")

BASIC_AUTH_USER = config.get('BASIC_AUTH_USER')
BASIC_AUTH_PASS = config.get('BASIC_AUTH_PASS')
WEBHOOK_URL = config.get('WEBHOOK_URL')

@app.get("/ping", status_code=200)
def health_check():
    return {"status": "ok"}

 # === FastAPI route (SageMaker expects this exact path) ===
@app.post("/invocations", response_model=JobAcceptedResponse, status_code=202)
async def handle_invocation(request: Request):
    print("🚀 Starting RAG pipeline")
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
            "result_url": f"{config.get('SUPABASE_URL')}/rest/v1/upwork_jobs?job_uuid=eq.{job_uuid}",
        }

        headers = {
            "Content-Type": "application/json",
        }

        res = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        
        return res

    except Exception as e:
        print("🔥 Failed to send webhook:", str(e))