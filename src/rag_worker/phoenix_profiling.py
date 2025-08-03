from phoenix.otel import register
from openinference.instrumentation import TracerProvider
import os

project_name = os.getenv('')

def get_phoenix_endpoint():
  return os.getenv("PHOENIX_COLLECTOR_ENDPOINT") + '/v1/traces'

def get_tracer():
  tracer_provider = register(
    project_name=project_name,
    endpoint=get_phoenix_endpoint(),
    auto_instrument=True
  )

  tracer = tracer_provider.get_tracer(__name__)

  return tracer