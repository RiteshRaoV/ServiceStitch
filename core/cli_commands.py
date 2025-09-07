import typer
from orchestration import docker_manager,load_tester

app = typer.Typer(help="Service orchestration commands")

@app.command()
def up(config: str = "services.yaml", rebuild: bool = typer.Option(False, "--rebuild", help="Rebuild images before starting")):
    """
    Spin up services from the given config file.
    """
    typer.echo(f"[UP] Generating docker-compose from {config}...")
    docker_manager.generate_compose(config)
    docker_manager.compose_up(rebuild=rebuild)
    typer.echo("[UP] Services are running!")

@app.command()
def down():
    """
    Tear down running services.
    """
    typer.echo("[DOWN] Stopping services...")
    docker_manager.compose_down()
    typer.echo("[DOWN] Services stopped.")

@app.command()
def generate(config: str):
    """Generate a Django starter project from a YAML config."""
    from orchestration import project_generator
    project_generator.create_project(config)

@app.command()
def export_zip(project: str):
    """Export generated project as a zip file."""
    from orchestration import project_generator
    project_generator.export_zip(project)
@app.command()
def gen_compose(config: str = "services.yaml"):
    """
    Generate compose from services.yaml (parsing expected keys).
    """
    import yaml
    from pathlib import Path
    s = Path(config).read_text()
    cfg = yaml.safe_load(s)
    services = cfg.get("services", {})
    docker_manager.generate_compose(services)

@app.command()
def load(target: str, method: str = "GET", rps: int = 10, duration: int = 10, concurrency: int = 5):
    """
    Basic synthetic load runner.
    """
    typer.echo(f"[load] starting {rps} rps to {target} for {duration}s")
    load_tester.start_sync(target, method, rps, duration, concurrency)