import typer
from core import cli_commands

app = typer.Typer(help="Servicestitch CLI - Microservice Simulation Toolkit")

# Register subcommands from core
app.add_typer(cli_commands.app, name="services")

def main():
    app()

if __name__ == "__main__":
    main()
