import json
import subprocess
import yaml
from pathlib import Path

COMPOSE_FILE = Path("docker-compose.generated.yml")

def generate_compose(config_file: str = "services.yaml") -> None:
    """Generate docker-compose file from a YAML config, including mocks."""
    with open(config_file, "r") as f:
        cfg = yaml.safe_load(f)

    services_cfg = cfg.get("services", {})

    compose_dict = {
        "services": {}
    }

    for name, spec in services_cfg.items():
        service_def = {}

        # If service is a mock, build from Dockerfile
        if spec.get("type") == "mock":
            # Use orchestration folder as build context
            service_def["build"] = {
                "context": str(Path(__file__).parent.parent.resolve()),  # project root
                "dockerfile": "orchestration/Dockerfile.mock"
            }

            # Inject endpoints as JSON string
            import json
            endpoints = spec.get("endpoints", [])
            
            # Start with MOCK_ENDPOINTS
            env_vars = [f"MOCK_ENDPOINTS={json.dumps(endpoints)}"]

            # Add NATS subscriptions if any
            nats_subscribe = spec.get("nats_subscribe", [])
            if nats_subscribe:
                env_vars.append(f"NATS_SUBSCRIBE={json.dumps(nats_subscribe)}")

            service_def["environment"] = env_vars
            
            # Map port
            port = spec.get("port", 8000)
            service_def["ports"] = [f"{port}:80"]

        else:
            # Infra services (like nats)
            service_def["image"] = spec["image"]
            if "ports" in spec:
                service_def["ports"] = spec["ports"]
            if "environment" in spec:
                service_def["environment"] = spec["environment"]

        compose_dict["services"][name] = service_def

    # Write the generated docker-compose
    with open(COMPOSE_FILE, "w") as f:
        yaml.dump(compose_dict, f, sort_keys=False)

    print(f"[docker_manager] Generated {COMPOSE_FILE}")



def compose_up(detach: bool = True, rebuild: bool = False) -> None:
    cmd = ["docker", "compose", "-f", str(COMPOSE_FILE), "up"]
    if detach:
        cmd.append("-d")
    if rebuild:
        cmd.append("--build")  # This ensures images are rebuilt
    subprocess.run(cmd, check=True)


def compose_down() -> None:
    """Run docker compose down."""
    cmd = ["docker", "compose", "-f", str(COMPOSE_FILE), "down"]
    subprocess.run(cmd, check=True)
