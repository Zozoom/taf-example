# TAF Example

**Test Automation Framework** – a web-based dashboard for managing and running Robot Framework tests, with a sample API test suite.

## Summary

This project provides a complete example for API test automation with Robot Framework. It includes:

- **taf-ms** – A FastAPI dashboard where you can:
  - Run tests immediately or on a schedule (daily, weekly, custom)
  - Choose predefined suites, filter by tags, or upload custom `.robot` files
  - View run history, status (running/passed/failed), and duration
  - Open HTML reports and download them
  - Track results per environment (local, staging)

- **robot-tests** – A Robot Framework suite with smoke tests against httpbin-style APIs (status checks, POST, headers, query params, delayed responses). Configurable per environment via YAML.

You can use the Docker stack to get the full dashboard plus PostgreSQL, or run the Robot tests manually from the command line without Docker.

---

## Structure

- **taf-ms** – Dashboard (scheduling, history, reports)
- **robot-tests** – Robot Framework smoke tests vs httpbin

---

## Option 1: Docker

From the project root:

```bash
cd taf-ms
docker-compose up --build
```

- Dashboard: http://localhost:8000  
- PostgreSQL: localhost:5432

---

## Option 2: Run Robot Framework Manually (no Docker)

If you prefer not to use Docker, run the Robot tests directly from CMD/PowerShell:

### Prerequisites

- Python 3.11+
- Install dependencies:

```bash
pip install robotframework robotframework-requests requests PyYAML
```

### Run Tests

```bash
cd robot-tests
python runner/run_tests.py --env local
```

Or against staging (https://httpbin.org):

```bash
python runner/run_tests.py --env stg
```

**Options:**
- `--env` – Config name (local, stg, dev). Uses `config/<env>.yaml`.
- `--include` – Tag filter, e.g. `--include smoke`
- `--base-url` – Override base URL, e.g. `--base-url https://httpbin.org`

### Local env

For `--env local`, httpbin must be reachable at `http://localhost:8080`. Either:

- Run httpbin via Docker: `docker run -p 8080:80 kennethreitz/httpbin`
- Or point to another httpbin instance with `--base-url`

For `--env stg`, no local services are needed; tests hit https://httpbin.org.

### Output

Results go to `robot-tests/artifacts/robot/runs/<timestamp>/` (report.html, log.html, output.xml).
