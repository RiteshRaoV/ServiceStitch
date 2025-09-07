# orchestration/project_generator.py
import os
import re
import subprocess
import yaml
from pathlib import Path
from shutil import make_archive

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "generated_projects"
OUTPUT_DIR.mkdir(exist_ok=True)

def load_config(config_file: str):
    with open(config_file, "r") as f:
        return yaml.safe_load(f)

def run_cmd(cmd, cwd=None):
    print(f"[RUN] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)

def sanitize_path(p: str) -> str:
    # remove leading/trailing slashes
    p = p.strip("/")
    if p == "":
        return "root"
    # replace non-alnum with underscore
    return re.sub(r'[^0-9a-zA-Z_]+', "_", p)

def create_project(config_file: str):
    cfg = load_config(config_file)
    project_name = cfg["project_name"]
    apps = cfg.get("apps", [])

    project_dir = OUTPUT_DIR / project_name
    if project_dir.exists():
        raise RuntimeError(f"Project {project_name} already exists. Remove it first or delete the directory.")

    project_dir.mkdir(parents=True, exist_ok=True)
    # 1. Create Django project in project_dir
    run_cmd(["django-admin", "startproject", project_name, str(project_dir)])

    # 2. Create apps using manage.py startapp (cwd=project_dir)
    for app in apps:
        app_name = app["name"]
        run_cmd(["python", "manage.py", "startapp", app_name], cwd=project_dir)
        register_app_in_settings(project_dir, project_name, app_name)
        add_app_urls_and_views(project_dir, app)

    # 3. Add include lines to main urls.py for all apps
    include_apps_in_project_urls(project_dir, project_name, [a["name"] for a in apps])

    # 4. Generate Dockerfile / compose / extras
    generate_requirements(project_dir)
    generate_dockerfile(project_dir)
    generate_composefile(project_dir, project_name)
    generate_dockerignore(project_dir)

    print(f"[OK] Project {project_name} generated at {project_dir}")
    return project_dir

def register_app_in_settings(project_dir: Path, project_name: str, app_name: str):
    settings_file = project_dir / project_name / "settings.py"
    text = settings_file.read_text()

    # find the INSTALLED_APPS block and insert before the closing bracket
    m = re.search(r"INSTALLED_APPS\s*=\s*\[", text)
    if not m:
        raise RuntimeError("Could not find INSTALLED_APPS block in settings.py")

    # find the position of the closing bracket for INSTALLED_APPS (simple approach)
    start = m.end()
    # find the first ']' after start
    end_idx = text.find("]", start)
    if end_idx == -1:
        raise RuntimeError("Malformed INSTALLED_APPS in settings.py")
    insert_at = end_idx
    before = text[:insert_at]
    after = text[insert_at:]
    addition = f'    "{app_name}",\n'
    new_text = before + addition + after
    settings_file.write_text(new_text)
    print(f"[settings] Registered {app_name} in INSTALLED_APPS")

def add_app_urls_and_views(project_dir: Path, app_cfg: dict):
    app_name = app_cfg["name"]
    apis = app_cfg.get("apis", [])
    app_dir = project_dir / app_name

    # ensure views.py exists
    views_file = app_dir / "views.py"
    if not views_file.exists():
        views_file.write_text("from django.http import JsonResponse\nfrom django.views.decorators.csrf import csrf_exempt\n\n")
    views_text = views_file.read_text()

    # Build a map path -> list of methods
    path_map = {}
    for api in apis:
        path = api["path"].lstrip("/")
        method = api.get("method", "GET").upper()
        path_map.setdefault(path, []).append(method)

    # For each unique path create a single view that handles allowed methods
    for path, methods in path_map.items():
        view_name = sanitize_path(path)
        if view_name in views_text:
            continue  # skip if exists

        methods_list = methods  # list like ["GET","POST"]
        # build view function
        func_lines = [
            "\n@csrf_exempt",
            f"def {view_name}(request):",
            f"    \"\"\"Auto-generated mock for path '{path}' supports: {', '.join(methods_list)}\"\"\"",
            "    m = request.method",
        ]
        # provide simple mock responses per method
        for method in methods_list:
            if method == "GET":
                func_lines += [f"    if m == \"GET\":", f"        return JsonResponse({{'message': '{view_name} GET mock', 'data': []}})"]
            elif method == "POST":
                func_lines += [f"    if m == \"POST\":", f"        return JsonResponse({{'message': '{view_name} POST mock'}}, status=201)"]
            elif method == "PUT":
                func_lines += [f"    if m == \"PUT\":", f"        return JsonResponse({{'message': '{view_name} PUT mock'}})"]
            else:
                func_lines += [f"    if m == \"{method}\":", f"        return JsonResponse({{'message': '{view_name} {method} mock'}})"]

        func_lines += [
            "    return JsonResponse({'error': 'Method not allowed'}, status=405)\n"
        ]
        view_code = "\n".join(func_lines)
        views_text += view_code

    views_file.write_text(views_text)
    print(f"[views] Wrote views for {app_name}: {len(path_map)} endpoints")

    # write urls.py
    urls_file = app_dir / "urls.py"
    url_lines = [
        "from django.urls import path",
        "from . import views",
        "",
        "urlpatterns = ["
    ]
    for path in path_map.keys():
        view_name = sanitize_path(path)
        # ensure trailing slash is NOT added by default; user can change later
        url_lines.append(f'    path("{path}", views.{view_name}, name="{view_name}"),')
    url_lines.append("]")
    urls_file.write_text("\n".join(url_lines))
    print(f"[urls] Wrote urls.py for {app_name}")

def include_apps_in_project_urls(project_dir: Path, project_name: str, app_names: list):
    project_urls = project_dir / project_name / "urls.py"
    text = project_urls.read_text()

    # ensure include is imported
    if "include" not in text:
        text = text.replace("from django.urls import path", "from django.urls import path, include")

    # insert include lines inside urlpatterns
    insert_block = ""
    for app in app_names:
        insert_block += f'    path("{app}/", include("{app}.urls")),\n'
    text = text.replace("urlpatterns = [", "urlpatterns = [\n" + insert_block, 1)
    project_urls.write_text(text)
    print(f"[project urls] Included apps in {project_name}/urls.py")

def generate_requirements(project_dir: Path):
    req = "Django>=4.2\n"
    (project_dir / "requirements.txt").write_text(req)
    print("[generate] requirements.txt written")

def generate_dockerfile(project_dir: Path):
    dockerfile = """FROM python:3.11-slim

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
"""
    (project_dir / "Dockerfile").write_text(dockerfile)
    print("[generate] Dockerfile written")

def generate_composefile(project_dir: Path, project_name: str):
    compose = f"""version: '3'
services:
  web:
    build: .
    container_name: {project_name}_web
    ports:
      - "8000:8000"
"""
    (project_dir / "docker-compose.yml").write_text(compose)
    print("[generate] docker-compose.yml written")

def generate_dockerignore(project_dir: Path):
    d = ".venv\n__pycache__\n*.pyc\n*.pyo\n*.pyd\n*.sqlite3\nenv/\nvenv/\n.env\n"
    (project_dir / ".dockerignore").write_text(d)
    print("[generate] .dockerignore written")

def export_zip(project_name: str):
    project_dir = OUTPUT_DIR / project_name
    if not project_dir.exists():
        raise RuntimeError(f"Project {project_name} not found.")
    zip_path = OUTPUT_DIR / f"{project_name}.zip"
    # make_archive creates file without .zip in argument
    make_archive(str(OUTPUT_DIR / project_name), 'zip', project_dir)
    print(f"[ZIP] Created {zip_path}")
    return zip_path
