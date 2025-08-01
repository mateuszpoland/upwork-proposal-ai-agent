# 🛠️ Local Dev Environment (Docker + LocalStack)

## ✅ Run local AWS services + database + app

```bash
docker-compose up --build


🧪 Test job ingestion

```
curl -X POST http://localhost:8080/job \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d @src/sample_job.json
```