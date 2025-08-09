#!/bin/bash

if [ "$1" = "serve" ]; then
  echo "🚀 Starting inference service..."
  uvicorn src.rag_worker.inference:app --host 0.0.0.0 --port 8080
else
  exec "$@"
fi