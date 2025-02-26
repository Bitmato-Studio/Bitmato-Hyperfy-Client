import os
import sys
import json
import shutil
import subprocess
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

SOURCE_FOLDER = "./core"

def main():
    console.rule("[bold blue]Bitmato - Hyperfy Electron Client - TUI[/bold blue]")
    console.print("Choose an operation:", style="bold green")
    console.print("1) Clone Project (from ./core)\n2) Build Project (electron-builder)\n")

    choice = Prompt.ask("Enter 1 or 2", choices=["1", "2"])
    if choice == "1":
        clone_project_tui()
    else:
        build_project_tui()

def clone_project_tui():
    """
    Clones `./core` → `./<ProjectName>`,
    creates a settings.json, runs `npm install`,
    showing a spinner with Rich while installing.
    """
    console.rule("[bold green]Clone Project[/bold green]")

    # 1) Prompt for project name
    project_name = Prompt.ask("Project Name (also sets `appName`)", default="MyElectronApp").strip()
    # 2) Additional settings
    remote_url = Prompt.ask("remoteUrl", default="https://hyperfy.bitmato.dev").strip()
    window_width = Prompt.ask("Window Width", default="1024").strip()
    window_height = Prompt.ask("Window Height", default="768").strip()
    cache_hours = Prompt.ask("cacheExpirationHours", default="24").strip()

    # Booleans
    is_dev = Confirm.ask("isDeveloper?", default=False)
    start_max = Confirm.ask("startMaximized?", default=False)
    always_on_top = Confirm.ask("alwaysOnTop?", default=False)
    tray_enabled = Confirm.ask("trayEnabled?", default=False)
    disable_cache = Confirm.ask("disableCache?", default=False)
    hardware_accel = Confirm.ask("hardwareAcceleration?", default=True)
    custom_user_agent = Prompt.ask("customUserAgent? (optional)", default="").strip()

    # Validate source
    if not os.path.exists(SOURCE_FOLDER):
        console.print(f"[red]Error: Source '{SOURCE_FOLDER}' does not exist.[/red]")
        sys.exit(1)

    # Destination
    project_dest = os.path.join(".", project_name)
    if os.path.exists(project_dest):
        overwrite = Confirm.ask(f"'{project_dest}' already exists. Overwrite?", default=False)
        if not overwrite:
            console.print("[yellow]Operation canceled.[/yellow]")
            sys.exit(0)
        shutil.rmtree(project_dest)

    # Clone
    console.print(f"[bold cyan]Cloning '{SOURCE_FOLDER}' → '{project_dest}'...[/bold cyan]")
    try:
        shutil.copytree(SOURCE_FOLDER, project_dest)
    except Exception as e:
        console.print(f"[red]Failed to clone folder:\n{e}[/red]")
        sys.exit(1)

    # Create settings.json
    console.print("[bold cyan]Creating settings.json...[/bold cyan]")
    try:
        create_settings_file(
            project_dest, project_name,
            remote_url, window_width, window_height, cache_hours,
            is_dev, start_max, always_on_top, tray_enabled,
            disable_cache, hardware_accel, custom_user_agent
        )
    except Exception as e:
        console.print(f"[red]Failed to create settings.json:\n{e}[/red]")
        sys.exit(1)

    # NPM install with spinner
    console.print("[bold cyan]Running npm install...[/bold cyan]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task_id = progress.add_task("Installing packages...", total=None)
        try:
            subprocess.check_call(["npm", "install"], cwd=project_dest)
        except Exception as e:
            progress.stop_task(task_id)
            console.print(f"[red]npm install failed:\n{e}[/red]")
            sys.exit(1)

    console.print(f"[green]Success![/green] Cloned into '{project_dest}' and installed modules!")

def create_settings_file(
    project_path: str,
    project_name: str,
    remote_url: str,
    win_width: str,
    win_height: str,
    cache_hrs: str,
    is_dev: bool,
    start_max: bool,
    always_top: bool,
    tray_en: bool,
    disable_cache: bool,
    hardware_accel: bool,
    custom_ua: str
):
    """Generates a minimal settings.json file from user inputs."""
    def int_or_default(s: str, default: int):
        try:
            return int(s)
        except:
            return default

    data = {
        "appName": project_name,
        "remoteUrl": remote_url,
        "windowSize": {
            "width": int_or_default(win_width, 1024),
            "height": int_or_default(win_height, 768),
        },
        "cacheExpirationHours": int_or_default(cache_hrs, 24),
        "isDeveloper": is_dev,
        "startMaximized": start_max,
        "alwaysOnTop": always_top,
        "trayEnabled": tray_en,
        "customUserAgent": custom_ua,
        "disableCache": disable_cache,
        "hardwareAcceleration": hardware_accel
    }

    settings_file = os.path.join(project_path, "settings.json")
    package_json = os.path.join(project_path, "package.json")
    with open(settings_file, "w", encoding="utf-8") as sf:
        json.dump(data, sf, indent=4)
        
    with open(package_json, 'r+') as rf:
        current = json.load(rf)
        current['name'] = project_name
        
        rf.seek(0)
        json.dump(current, rf, indent=4)
        rf.truncate()
        
def build_project_tui():
    """
    Runs electron-builder with user-chosen platform & arch in a specified folder,
    showing a spinner in the terminal.
    """
    console.rule("[bold green]Build Project[/bold green]")

    # 1) Ask for the Electron project folder
    project_folder = Prompt.ask("Path to your Electron project folder", default=".")
    if not os.path.exists(project_folder):
        console.print(f"[red]Error: '{project_folder}' does not exist.[/red]")
        sys.exit(1)

    # 2) Choose platform
    console.print("Supported platforms: win32, linux, darwin")
    platform_choice = Prompt.ask("Which platform", default="win32", choices=["win32", "linux", "darwin"])

    # 3) Choose arch
    console.print("Supported archs: x64, arm64, ia32, armv7l")
    arch_choice = Prompt.ask("Which architecture", default="x64", choices=["x64", "arm64", "ia32", "arm7l"])

    # Confirm
    confirm_build = Confirm.ask(
        f"Build for [cyan]{platform_choice}[/cyan] / [cyan]{arch_choice}[/cyan] in '{project_folder}'?",
        default=True
    )
    if not confirm_build:
        console.print("[yellow]Build canceled by user.[/yellow]")
        sys.exit(0)


    # 4) Run electron-builder with a spinner
    cmd = [
        "npx", "electron-builder", 
        f"--{platform_choice}",
        f"--{arch_choice}"
    ]

    console.print(f"[bold green]Building[/bold green] {project_folder} for [cyan]{platform_choice}[/cyan]/[cyan]{arch_choice}[/cyan]...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task_id = progress.add_task("Building with electron-builder...", total=None)

        try:
            subprocess.check_call(cmd, cwd=project_folder)
        except Exception as e:
            progress.stop_task(task_id)
            console.print(f"[red]Build failed:\n{e}[/red]")
            sys.exit(1)

    console.print("[green]Build completed successfully![/green]")
    console.print("Check your dist/ folder (or wherever electron-builder outputs).")

if __name__ == "__main__":
    main()
