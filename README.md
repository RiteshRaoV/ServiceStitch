
# **ServiceStitch**

ServiceStitch is a lightweight **microservices orchestration and mocking framework** designed for local development and testing. It allows developers to spin up **mock services, infra, and NATS pub/sub communication** dynamically from a YAML configuration. It also includes a **Django code generator** to bootstrap apps quickly.

---

## **Table of Contents**

1. [Features](#features)
2. [MVP Implementation](#mvp-implementation)
3. [Planned Features](#planned-features)
4. [Getting Started](#getting-started)
5. [CLI Commands](#cli-commands)
6. [Service Configuration (YAML)](#service-configuration-yaml)
7. [Docker & Mock Service Architecture](#docker--mock-service-architecture)
8. [Django Generator](#django-generator)

---

## **Features**

* Dynamic service orchestration using **YAML config**
* Supports **mock services** with HTTP endpoints and optional delays/faults
* Supports **NATS pub/sub integration** for cross-service events
* Automatically generates **docker-compose.yml** from YAML
* CLI interface to spin up/down services and rebuild images
* Optional **Django app generator** for rapid scaffolding of projects
* Future: plugin system, metrics collection, logging aggregator

---

## **MVP Implementation**

Today’s MVP includes:

1. **Mock Services**

   * HTTP endpoints defined in YAML with optional `delay` and `failure_rate`.
   * Example: Payments service `/charge` endpoint.

2. **NATS Pub/Sub Integration**

   * Services can **publish events** to NATS when certain endpoints are hit.
   * Other services can **subscribe to these events** and trigger local endpoints.
   * Example: Payments service publishes `"payments.completed"` → Notifier service triggers `/notify`.

3. **Dynamic Docker Compose Generation**

   * Generates `docker-compose.generated.yml` based on YAML config.
   * Handles **build for mocks** and **pull for infra**.
   * Ports, environment variables, and NATS subscriptions are automatically injected.

---


### Planned Features

* **Downstream API mocking & stubs**: Define mock endpoints for testing interactions between services.
* **Synthetic load & latency simulation**: Inject latency or simulate service failures for realistic testing.
* **Fault injection**: Configure endpoints to randomly fail to test resiliency.
* **TUI Dashboard**: Visualize service health, logs, network latency, and route mapping in real-time.
* **NATS Pub/Sub Enhancements**: Persistent connections and automatic routing of events between services.
* **Plugin system**: Extend mock services with custom logic or behavior.
* **Analytics & logging**: Central collection of metrics, logs, and event flows.
* **OpenAPI / API Schema Generation**: Auto-document mock APIs for easier integration.

---

## **Getting Started**

### **Requirements**

* Docker & Docker Compose
* Python 3.11+
* `poetry` or `pip` to install dependencies

```bash
# Install dependencies
pip install -r requirements.txt
```

### **Running Services**

```bash
# Spin up services
python manage.py cli up --rebuild

# Shut down services
python manage.py cli down
```

* `--rebuild` ensures the latest mock service code is built.

---

## **CLI Commands**

| Command            | Description                                |
| ------------------ | ------------------------------------------ |
| `cli up`           | Generate docker-compose and start services |
| `cli down`         | Stop and remove services                   |
| `cli up --rebuild` | Rebuild mock images and start services     |

---

## **Service Configuration (YAML)**

Example `services.yaml`:

```yaml
services:
  nats:
    type: infra
    image: nats:2.10-alpine
    ports:
      - "4222:4222"
      - "8222:8222"

  auth:
    type: mock
    port: 8001
    endpoints:
      - path: /signup
        method: POST
        response: {"id": 1, "name": "testuser"}
      - path: /login
        method: POST
        response: {"status": "ok", "token": "abc123"}

  payments:
    type: mock
    port: 8002
    endpoints:
      - path: /charge
        method: POST
        response: {"status": "processed", "transaction_id": "tx123"}
        nats_publish:
          - subject: "payments.completed"
            data: {"transaction_id": "{{transaction_id}}"}

  notifier:
    type: mock
    port: 8004
    endpoints:
      - path: /notify
        method: POST
        response: {"status": "notification sent"}
    nats_subscribe:
      - subject: "payments.completed"
        action: POST /notify
```

* **`MOCK_ENDPOINTS`**: Defines HTTP endpoints for the mock.
* **`nats_publish`**: Events published to NATS after hitting endpoint.
* **`nats_subscribe`**: Subscribe to NATS events and trigger local endpoints.

---

## **Docker & Mock Service Architecture**

* **Mock Services**:

  * Run **FastAPI** with dynamic routes injected from env (`MOCK_ENDPOINTS`).
  * Handle delays, simulated failures, and NATS publishing.

* **NATS Integration**:

  * Publisher service connects to NATS, sends messages.
  * Subscriber service connects at startup, subscribes, and triggers HTTP actions.

* **Infra Services**: Pulled from Docker Hub (e.g., `nats:2.10-alpine`).

* **Docker Workflow**:

  1. `generate_compose()` reads YAML → builds docker-compose dict.
  2. Writes `docker-compose.generated.yml`.
  3. `compose_up()` runs `docker compose up -d`.
  4. Mock services start and read endpoints/NATS subscriptions from environment.

---

## **Django Generator Features**

* **Generate Django Project**:

  * Automatically scaffold apps with models, views, serializers, and URLs.
  * Preconfigured **REST API endpoints** for rapid testing.
  * Optional **mock service integration** for testing API calls.

* Example Usage:
    * **Load the service configuration to `project.yaml`**:
        This allows you to define the project structure, apps, and APIs in a single YAML file. 
        The configuration is then used to scaffold the Django project and integrate with ServiceStitch mocks.

```yaml
project_name: myapp
apps:
  - name: core
    apis:
      - path: /projects
        method: GET
      - path: /projects
        method: POST
      - path: /projects
        method: PUT

  - name: custom_auth
    apis:
      - path: /login
        method: POST
      - path: /signup
        method: POST

  - name: analytics
    apis: []

```

```bash
python manage.py generate
```
* Can integrate with **ServiceStitch mocks** for development.

* Creates:

  * Project skeleton (`myproject/`)
  * App directories (`auth/`, `payments/`)
  * Prebuilt serializers, models, URLs (Planned)

* Can integrate with **ServiceStitch mocks** for development (Planned).

---

## **Development Notes**

* Modify `services.yaml` to add/remove mocks.
* Changes to mock code require `--rebuild` to reflect in Docker.
* NATS subscriber must connect at startup to receive events.
* Load  service configuration to `project.yaml`: This allows you to define the project structure, apps, and APIs in a single YAML file. The configuration is then used to scaffold the Django project and integrate with ServiceStitch mocks.

---
