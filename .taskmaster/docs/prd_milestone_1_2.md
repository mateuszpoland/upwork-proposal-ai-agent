# 📄 Product Requirements Document (PRD) - MVP 

## 📌 Project Name:
**Upwork Proposal Agent – MVP Deployment (Milestones 1-3)**

---

## 🎯 MVP Objective

Deploy the existing RAG pipeline implementation (`src/rag_worker/`) to AWS SageMaker with comprehensive manual developer testing and production readiness. The core RAG functionality is **already implemented** - focus is on containerization and AWS deployment.

---

## 📊 Current Implementation Status

### ✅ **Completed Components** (in `src/rag_worker/`)

| File | Purpose | Status |
|------|---------|---------|
| `inference.py` | SageMaker-compatible FastAPI app with `/invocations` endpoint | ✅ Complete |
| `pipeline.py` | RAG orchestration, vector retrieval, LLM inference | ✅ Complete |
| `models.py` | Pydantic data models for job processing | ✅ Complete |
| `payloads.py` | Request/response models | ✅ Complete |
| `prompts.py` | LLM prompts for job analysis | ✅ Complete |
| `node_postprocessors.py` | Keyword boost and re-ranking | ✅ Complete |
| `util.py` | Timing decorators and utilities | ✅ Complete |
| `sample_job.json` | Test data for integration testing | ✅ Available |

### 🔄 **Infrastructure Status**

| Component | File | Status |
|-----------|------|---------|
| SageMaker CDK Stack | `infra/stacks/sagemaker_stack.py` | 🟡 Draft (needs testing) |
| ECR Repository | Manual/CDK | ❌ Not implemented |
| Secrets Management | AWS Secrets Manager | ❌ Not configured |
| Testing Suite | N/A | ❌ Missing |

---

### 🏗️ **Milestone 1: AWS Infrastructure Deployment**

**Goal:** Deploy production-ready infrastructure using CDK

**Implementation References:**
- Complete and test `infra/stacks/sagemaker_stack.py`
- Check the current local Docker deployment, which is operational and is covered in `Dockerfile` and `docker-compose.yaml` 
- Deploy containerized `src/rag_worker/` to SageMaker
- Configure secrets for environment variables used in `inference.py` and `pipeline.py`

**Required Deliverables:**
- [ ] Fix and complete `infra/stacks/sagemaker_stack.py` CDK stack
- [ ] ECR repository creation and Docker image pushing
- [ ] AWS Secrets Manager configuration for:
  - `OPENAI_API_KEY` (used in `pipeline.py:27`)
  - `COHERE_API_KEY` (used in `pipeline.py:28`) 
  - `SUPABASE_URL` (used in `inference.py:84`)
  - `SUPABASE_KEY` (Supabase admin token)
  - `WEBHOOK_URL` (used in `inference.py:30,91`)
  - `BASIC_AUTH_USER/PASS` (used in `inference.py:28-29`)
- [ ] SageMaker endpoint deployment with proper resource allocation
- [ ] The secure configuration for AWS infrastructure that is able to connect to external, managed Supabase service
- [ ] CloudWatch logging and monitoring setup
- [ ] Deployment scripts and environment configurations

### 🚀 **Milestone 2: Production Validation & Go-Live**

**Goal:** Validate production deployment and n8n integration

**Implementation References:**
- Test complete workflow: n8n → `inference.py` → `pipeline.py` → webhook on production (interactively with developer -> mark as done when developer confirms it works correctly)
- Validate latency requirements for `process_job()` function -> interactively with user -> instruct on how to check the latency and document it
- Test webhook callback in `_send_webhook()` function

**Required Deliverables:**
- [ ] Development environment deployment and validation
- [ ] End-to-end workflow testing: n8n → SageMaker → Supabase → webhook (interactive with user)
- [ ] Production secrets configuration in AWS Secrets Manager
- [ ] Production deployment with IAM permissions
- [ ] Production deployment documentation

---

## 🏗️ System Architecture

### Current Implementation Flow

```
n8n POST → /invocations (inference.py:44)
    ↓
JobApplicationRequestModel validation (payloads.py)
    ↓
Async thread: process_job() (inference.py:62)
    ↓
query_rag_pipeline() (pipeline.py)
    ↓
Supabase vector retrieval + LLM inference
    ↓
_send_webhook() to n8n (inference.py:78)
```

### Infrastructure Target

```
ECR Container Image (src/rag_worker/)
    ↓
SageMaker Model (sagemaker_stack.py)
    ↓
SageMaker Endpoint Config (sagemaker_stack.py)
    ↓
SageMaker Endpoint (sagemaker_stack.py)
```

---

## 🔧 Tech Stack (Already Implemented)

| Component | Implementation | File Reference |
|-----------|---------------|----------------|
| **API Framework** | FastAPI | `src/rag_worker/inference.py` |
| **LLM Integration** | OpenAI via LlamaIndex | `src/rag_worker/pipeline.py` |
| **Vector Store** | Supabase pgvector | `src/rag_worker/pipeline.py` |
| **Re-ranking** | Cohere + keyword boost | `src/rag_worker/node_postprocessors.py` |
| **Async Processing** | Threading | `src/rag_worker/inference.py:52` |
| **Authentication** | HTTP Basic Auth | `src/rag_worker/inference.py:32` |

---

## 🚨 Critical Issues to Address

### **CDK Stack Issues** (`infra/stacks/sagemaker_stack.py`)

1. **Line 14:** Missing `()` in `super.__init__` call
2. **Line 46:** Typo "AllTrafic" should be "AllTraffic" 
3. **Line 47:** Instance type `t3.medium` is not valid for SageMaker (use `ml.t3.medium`)
4. **Missing:** Secrets Manager integration
5. **Missing:** ECR repository reference
6. **Missing:** CloudWatch logging configuration
7. **Missing:** VPC and security group configuration

### **Environment Variable Management**

Current code in `src/rag_worker/` expects these environment variables:
- `OPENAI_API_KEY`, `COHERE_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`
- `WEBHOOK_URL`, `BASIC_AUTH_USER`, `BASIC_AUTH_PASS`
- `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL`

**MVP Requirement:** Replace hardcoded `os.getenv()` calls with AWS Secrets Manager integration.

---

## 📋 MVP Success Criteria

### **Milestone 1 Complete When:**
- [ ] CDK stack deploys without errors
- [ ] SageMaker endpoint is accessible and responsive
- [ ] All secrets properly configured in AWS Secrets Manager
- [ ] The request to inference endpoint `/invocations` succeeds, and Sagemaker is able to interact with Supabase and send HTTP calls to n8n webhook addresses

### **Milestone 2 Complete When:**
- [ ] Production deployment handles real n8n requests
- [ ] End-to-end latency meets <120s requirement
- [ ] Monitoring and alerting operational

---

## 🎯 Post-MVP Future Enhancements

**Not included in MVP scope:**
- Horizontal scaling with multiple endpoints
- Redis caching layer  
- Advanced monitoring beyond CloudWatch
- API Gateway integration
- Multi-modal content support
- A/B testing framework

Focus: **Deploy existing code robustly, then enhance.**

