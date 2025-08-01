Product Requirements Document – “RAG-for-Job-Proposals”
(a single, self-contained reference for any implementation team: Claude Code, task-master-ai, or human engineers)

1 · Executive summary
We are building a Retrieval-Augmented Generation (RAG) service that ingests the owner’s career knowledge-base, enriches inbound job-postings, retrieves the best matching experience snippets, and emits a JSON payload that an n8n workflow turns into a polished proposal e-mail.
Phase-1 runs in Google Colab + Supabase (pgvector).
Phase-2 re-hosts the same logic on AWS (Lambda + Step Functions + SNS/SQS + Supabase) with Temporal-compatibility in mind.

2 · Goals & success criteria
#	Goal	Metric / Acceptance
G1	Cut manual proposal drafting to near-zero	1-click proposals that need ≤5 % manual edits
G2	≤2 min end-to-end latency per job post	95-th percentile < 120 s
G3	Scalable to 20 jobs/day, burst-safe to 100	Concurrent Lambda invocations auto-scale
G4	Cloud-agnostic RAG core (re-usable in Temporal)	No AWS SDK calls inside business code
G5	Simple ops (no long-lived servers)	Fully serverless & IaC via CDK

3 · Actors & user stories
Actor	Story
Upwork/LinkedIn scraper (future)	“When I detect a new posting I publish it to the job-posts SNS topic.”
n8n	“I push the raw job JSON to SNS, then wait for a webhook with the processed result.”
RAG Worker (Lambda)	“On job message, enrich ➜ retrieve ➜ write result row into Supabase ➜ POST webhook back to n8n.”
n8n (2nd flow)	“On webhook, fetch row, craft final email, optionally open human-approval, then send.”
Human	“If I want to override, I edit the email draft shown in Slack and hit Send.”

4 · Functional requirements
ID	Requirement
F-1	Accept JobApplicationRequestModel JSON (see schema §6.1) via SNS payload.
F-2	JobDataAugmenter must summarise, extract business intent, and output ≤8 vector queries.
F-3	Retrieve top-2 nodes per query from Supabase pgvector; deduplicate by node.id_.
F-4	Apply KeywordBoost post-processor (+0.25 per keyword overlap).
F-5	Persist final record to table processed_job_requests (columns: id, raw_request, augmented_json, created_at).
F-6	POST result JSON to the callback URL contained in the SNS message (callback_url).
F-7	If callback fails (non-200) -> retry via SQS DLQ → Lambda retry (expo back-off 1 min, 4 min, 15 min).
F-8	Expose a Step Functions state-machine for ad-hoc / bulk re-processing.

5 · Non-functional requirements
Runtime: Python 3.11, OpenAI GPT-4o-mini for LLM calls.

Security: All Lambdas run inside private subnets; outbound internet via NAT.

Observability: CloudWatch logs, X-Ray traces, custom metric ProcessingLatency (sns-recv → Supabase write).

Cost ceiling: < $50 / mo at 600 Lambda-minutes, 1 GB storage, 1 M Supabase row reads.

6 · Data contracts
6.1 Inbound – JobApplicationRequestModel (SNS message body)
jsonc
Kopiuj
Edytuj
{
  "job_link": "https://…",
  "job_title": "Hiring Expert n8n Developer …",
  "job_description": "### Summary\nWe run a HubSpot-focused…",
  "skills_keywords": ["n8n", "Make.com", "Automation", "Airtable"],
  "applicant_questions": ["Describe how you would structure …", "…"],
  "additional_agent_instruction": null,
  "callback_url": "https://n8n.cloud/webhook/abcd1234"   // added by n8n
}
6.2 Outbound – QueryAugmentationResult (written to Supabase & POSTed)
jsonc
Kopiuj
Edytuj
{
  "job_summary": "Experienced n8n developer needed…",
  "job_business_problem": "Manual RevOps task orchestration is error-prone…",
  "job_business_outcome": "Autonomous agents will cut task prep time by 80 %…",
  "skillset_required": "n8n, OpenAI, ClickUp API, Slack API, Airtable API",
  "applicant_questions": ["Describe how you would structure…"],
  "retrieval_queries": ["Show projects using n8n + ClickUp API…", "…"],
  "retrieved_nodes": [ { "id": "52c5…", "text": "### CASE_STUDY: HR Automation…" } ],
  "additional_agent_instruction": null
}
7 · High-level architecture
mermaid
Kopiuj
Edytuj
flowchart TD
    subgraph AWS
        A[N8N Webhook\nPOST SNS] --> SNS[Amazon SNS\ntopic: job-posts]
        SNS -->|fan-out| SQS[SQS fifo<br>retry DLQ]
        SQS --> L1[Lambda RAG Worker]
        L1 -->|Augmented JSON| SB[(Supabase\npgvector)]
        L1 --> WC[Outbound HTTPS\ncallback_url]
    end
    WC --> N8N2[n8n Flow #2\nGenerate proposal ➜ send email]
    classDef box fill:#fff,stroke:#333,stroke-width:1px
    class A,SNS,SQS,L1,SB,WC,N8N2 box
Component roles

Component	Responsibility
SNS	Accept lightweight messages; decouples n8n from Lambda back-pressure.
SQS FIFO	Guarantees once-only, ordered delivery; built-in redrive to DLQ on error/retry.
Lambda RAG Worker	Runs rag_pipeline.run_job(). Timeout 90 s, memory 512 MB.
Supabase	Stores vector index (vecs schema) and processed-jobs table.
Outbound HTTPS (Lambda → n8n)	Posts processed JSON; n8n acknowledges with 200.
n8n Flow #2	Fetches Supabase row, applies email template, optional human approval, sends via SMTP.

NAT gateway → outbound IP can be allow-listed if n8n cloud restricts ingress.

8 · Detailed CDK deployment plan
Step	CDK Construct	Notes
1	Vpc with 2 private subnets + 1 NAT	Lower egress cost by sharing NAT across Lambdas.
2	PythonFunction RagWorkerFn	Handler rag_worker/handler.handler, bundling with pip install -r requirements.txt.
3	Topic JobPostsTopic	n8n publishes here.
4	Queue JobPostsQueue (FIFO)	Subscribed to topic; maxReceiveCount=3 → DLQ.
5	SqsEventSource → RagWorkerFn	batch_size=1 for simplicity.
6	Secret / ParameterStore	OpenAI key, Supabase URL/key.
7	SG + Interface Endpoint for secretsmanager + sns if VPC-only.	
8	Step Functions (optional)	Wrap worker for manual re-drives.
9	ApiGateway (optional)	In case we ever need direct HTTP trigger.

9 · Roll-out & migration checklist
✅ Finish Colab prototype → freeze rag_pipeline.py as pure-python.

🗂️ Create src/rag_worker/ package; move pipeline + handler.

🐳 Add Dockerfile or rely on CDK’s Python bundling.

🔑 Store OpenAI & Supabase secrets in AWS Secrets Manager.

🛠️ cdk deploy to dev account – test with sample SNS message.

🔁 Update n8n flow #1 to publish to SNS instead of calling Colab.

⏱️ Validate p95 latency < 120 s; tune Lambda memory if needed.

📈 Add CloudWatch dashboards & alert on DLQ > 0.

🚀 Promote stack to prod account.

📆 (Later) Migrate SQS→Temporal worker by swapping event-source.

Appendix A – Open questions (to answer before prod)
ID	Topic	Decision owner
Q-TLS	Use Supabase’s hosted HTTPS endpoint or VPC Peering?	You / DevOps
Q-IAM	Per-env IAM roles vs. single cross-env?	DevOps
Q-Notify	Telegram alert path (SNS, Slack App, SES)?	You
Q-Human	Where to plug human approvals (n8n Approvals UI vs. Slack modal)?	You


Architecture diagram:


 ┌────────┐            HTTPS (public)            ┌─────────────┐
 │ n8n    │ ───────── trigger ① POST /job …… ──▶ │  API GW     │
 │ cloud  │                                        (REST)
 └──┬─────┘                                         │
    │ EventBridge PutEvents()                       │
    ▼                                               ▼
┌────────────┐   fan-out              ┌─────────────────┐
│ EventBridge│ —────────────────────▶ │  SQS “jobs”     │
│  Bus       │                        │  (FIFO)         │
└────┬───────┘                        └──────┬──────────┘
     │ DLQ (poison)                          │
     ▼                                        ▼
┌────────────────┐                  ② trigger batch (1–10 msgs)
│ Step Functions │  (state-machine)  ────────────────────────────┐
│ “RAG-Pipeline” │   • Map state (1 per msg)                     │
└┬───────────────┘   • waitForTaskToken (optional human)         │
 │                    • Parallel: LlamaParse → Embeddings → RAG  │
 │                    • Save result to Supabase “applications”   │
 │                    • SNS publish “job.done”                   │
 │                    • If human_review flag set ⇒ send link     │
 │                                                            ┌──┴──────────────┐
 │  ③ Lambda “RAG-Worker” (max 15 min)                         │   Supabase      │
 │     - runs retrieval / synthesis                            │   (PGVector)   │
 │     - writes status row & JSON payload                      └─┬──────────────┘
 └───────────────────────────────────────────────────────────────▶│ table: applications
                                                                 │ id | status | result_json
                                                                 └──────────────────────────
                ④ SNS topic “job.done”  ───────► n8n inbound webhook
                                                (3 retries, back-off)


Component rationale
#	Component	Why it fits the constraints
① API Gateway (public)	Gives you a single endpoint to hand out. No need for VPC NAT or static IP-allow lists.	
EventBridge	Decouples ingestion from processing. Native retries (24h) and DLQ. Easy to replay events in Temporal later.	
SQS FIFO “jobs” queue	Guarantees exactly-once delivery to the worker → Step Functions. Handles burst scaling (20/day is trivial).	
② Step Functions (Standard)	< 2 min SLA is easy with direct Lambda, but SFN lets you:
• break the pipeline into >1 Lambda if heavy
• insert waitForTaskToken for future human review without code changes
• emit metrics/alerts per state.	
③ Lambda “RAG-Worker”	Still the cheapest way to run your Python RAG code at low volume. Place it in a private subnet; give it a VPC endpoint for Supabase or set up VPC peering (see previous explanation). Memory ≈ 1 GB → gets 1 vCPU, plenty for 90-sec embedding + LLM calls.	
Supabase/Postgres	Single source of truth. Store: raw request, status, result JSON, error reason.	
④ SNS “job.done”	Fan-out: send to n8n, Slack, e-mail etc. n8n receives via HTTPS webhook—no IP allow-listing needed because outbound traffic from AWS uses NAT IPs that change.	
n8n cloud	Listens to SNS; does proposal formatting + e-mail. If Supabase row not ready → make 3 GETs (/applications/{id}) with exponential back-off; after failure send Telegram alert.