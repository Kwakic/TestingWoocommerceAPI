# Optional OpenTelemetry log export

The framework's per-process JSONL files remain the durable test-run logs. This optional Collector reads the files for one run and forwards them to an organization's OTLP/HTTP endpoint. It does not add a Python dependency or change pytest's logging handlers, output, or pass/fail behavior.

## Data flow

```text
pytest workers -> reports/logs/<team>/<environment>/*.jsonl
                         |
                         | optional file collection
                         v
                OpenTelemetry Collector -> company log platform
```

The JSONL files and run manifest remain available as local/CI artifacts. The Collector is an independent service: if it is not started, pytest works as before and no logs are exported.

## Prerequisites

- Docker Compose.
- An OTLP/HTTP endpoint provided by the organization. Set the base URL, for example `https://otel-gateway.example:4318`; do not include `/v1/logs` because the Collector adds that path.
- A pinned OpenTelemetry Collector Contrib image version that supports the `file_log` and `otlp_http` component names used in the sample config (Collector Contrib `0.149.0` or newer).
- The endpoint's required authentication configured using the organization's secret-management approach. The example intentionally contains no credentials.

## Run on Windows PowerShell

Start with a unique run ID and set the endpoint and pinned Collector version. Use the same run ID for pytest and the Collector so only that run's files are forwarded.

```powershell
$env:E2E_RUN_ID = [guid]::NewGuid().ToString("N")
$env:ENABLE_STRUCTURED_LOGS = "true"
$env:OTEL_COLLECTOR_VERSION = "0.164.0"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "https://otel-gateway.example:4318"

docker compose -f docker-compose.otel-logs.yml up -d
pytest tests/ui/tests/shopping/checkout/test_customer_checkout.py::test_customer_can_complete_checkout -v --browser chromium --browser firefox --browser webkit -n 3
docker compose -f docker-compose.otel-logs.yml down
```

Replace the example endpoint with the real endpoint and add its required authentication configuration before using it. CI can set the same environment variables in its job and start this Compose service only for jobs that need central log export.

## Record mapping

- JSONL `timestamp` becomes the OpenTelemetry event timestamp.
- JSONL `level` becomes the OpenTelemetry severity.
- JSONL `message` becomes the log body.
- Other JSONL properties—including `run_id`, `worker_id`, `nodeid`, and `correlation_id`—are retained as log attributes.
- `service.name` and `service.namespace` identify the source as this test automation framework.

The Collector uses persistent file offsets. The test files themselves are mounted read-only and remain the source of truth. If the endpoint is unavailable, pytest still runs; the export problem is reported by the Collector, independently of the test result.
