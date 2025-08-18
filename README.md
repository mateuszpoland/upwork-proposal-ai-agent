```
aws sagemaker delete-endpoint --endpoint-name rag-worker-endpoint-prod --profile awsomedevs-prd-mateusz
```

```
aws sagemaker create-endpoint \
  --endpoint-name rag-worker-endpoint-prod \
  --endpoint-config-name rag-worker-endpoint-config-prod-1754652110 \
  --region eu-central-1 \
  --profile awsomedevs-prd-mateusz
```