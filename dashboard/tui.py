# dashboard/tui.py
import subprocess
import threading
import time
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.console import Console

console = Console()

def docker_ps(compose_file="docker-compose.generated.yml"):
    cmd = ["docker", "compose", "-f", compose_file, "ps", "--format", "json"]
    try:
        out = subprocess.check_output(cmd)
        # if the docker CLI doesn't support json on older versions, fall back
        s = out.decode()
        # naive parse: show the raw text
        return s
    except Exception:
        # fallback: use `docker ps`
        try:
            out = subprocess.check_output(["docker", "ps", "--format", "{{.Names}} {{.Status}}"])
            return out.decode()
        except Exception as e:
            return f"error: {e}"

def tail_logs(service_name, compose_file="docker-compose.generated.yml", stop_event=None):
    cmd = ["docker", "compose", "-f", compose_file, "logs", "--no-color", "--tail", "20", service_name]
    try:
        out = subprocess.check_output(cmd)
        return out.decode()
    except Exception as e:
        return f"error: {e}"

def build_table(ps_text: str):
    t = Table(title="Service Status")
    t.add_column("Name / Raw")
    t.add_row(ps_text)
    return t

def run_tui(compose_file="docker-compose.generated.yml"):
    stop = threading.Event()
    def refresh():
        while not stop.is_set():
            time.sleep(2)
    th = threading.Thread(target=refresh, daemon=True)
    th.start()
    with Live(console=console, refresh_per_second=1) as live:
        try:
            while True:
                ps_text = docker_ps(compose_file)
                table = build_table(ps_text)
                logs = tail_logs("mock-user", compose_file)
                live.update(Panel(table))
                console.print(Panel(logs, title="mock-user logs"))
                time.sleep(2)
        except KeyboardInterrupt:
            stop.set()
