import click
import json
from pathlib import Path
from loguru import logger
import toml
import os
import sys
from typing import Optional, List, Dict, Any

try:
    import click_completion

    click_completion.init()
except ImportError:
    click_completion = None
    print("click-completion är inte installerat. Automatisk komplettering kommer inte att fungera.")

# Konstanten för filnamn
TASK_QUEUE_FILE = "task_queue.json"
GPTME_TOML_FILE = "gptme.toml"
GPTME_CLI_LOG_FILE = "gptme_cli.log"
GPTME_HISTORY_FILE = ".gptme_history"

# Konfigurera loguru med grundläggande inställningar
logger.add(GPTME_CLI_LOG_FILE, rotation="500 MB", level="INFO")

def load_tasks() -> Dict[str, Dict[str, Any]]:
    """Ladda uppgifter från task_queue.json.

    Returns:
        En dictionary där nycklarna är uppgiftsnamn och värdena är uppgiftsdata.
        Returnerar en tom dictionary om filen inte hittas eller är ogiltig JSON.
    """
    try:
        with open(TASK_QUEUE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Filen '{TASK_QUEUE_FILE}' hittades inte. Skapar en ny.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Fel vid avkodning av JSON i '{TASK_QUEUE_FILE}': {e}")
        return {}

def save_tasks(tasks: Dict[str, Dict[str, Any]]) -> None:
    """Spara uppgifter till task_queue.json.

    Args:
        tasks: En dictionary där nycklarna är uppgiftsnamn och värdena är uppgiftsdata.
    """
    try:
        with open(TASK_QUEUE_FILE, "w") as f:
            json.dump(tasks, indent=2)
        logger.info(f"Uppgifter sparade till '{TASK_QUEUE_FILE}'")
    except IOError as e:
        logger.error(f"Fel vid skrivning till '{TASK_QUEUE_FILE}': {e}")
        click.echo(
            click.style(f"Fel: Kunde inte spara uppgifter till '{TASK_QUEUE_FILE}'.", fg="red")
        )

def load_config() -> Dict[str, Dict[str, Any]]:
    """Ladda konfiguration från gptme.toml.

    Returns:
        En dictionary som representerar konfigurationen från gptme.toml.
        Returnerar en tom dictionary om filen inte hittas eller är ogiltig TOML.
    """
    try:
        return toml.load(GPTME_TOML_FILE)
    except FileNotFoundError:
        logger.error(f"Konfigurationsfilen '{GPTME_TOML_FILE}' hittades inte.")
        return {}
    except toml.TomlDecodeError as e:
        logger.error(f"Fel vid avkodning av TOML i '{GPTME_TOML_FILE}': {e}")
        return {}

def append_to_history(command: str) -> None:
    """Lägg till ett kommando i historikfilen.

    Args:
        command: Kommandot som ska läggas till i historiken.
    """
    try:
        with open(GPTME_HISTORY_FILE, "a") as f:
            f.write(command + "\n")
    except IOError as e:
        logger.error(f"Fel vid skrivning till historikfilen '{GPTME_HISTORY_FILE}': {e}")

def load_history() -> List[str]:
    """Ladda kommandohistoriken från filen.

    Returns:
        En lista med tidigare körda kommandon.
        Returnerar en tom lista om historikfilen inte hittas.
    """
    try:
        with open(GPTME_HISTORY_FILE, "r") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return []

# Skapa en Click-grupp för huvudkommandot
@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option()
@click.option(
    "--verbose", "-v", is_flag=True, default=False, help="Visa mer detaljerad information."
)
@click.option(
    "--debug", is_flag=True, default=False, help="Visa debug-information för felsökning."
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, debug: bool):
    """Hantera AI-assisterade utvecklingsuppgifter.

    Använd detta CLI-verktyg för att hantera uppgifter för ditt gptme-system.
    Du kan lägga till, lista, visa status, starta om och ta bort uppgifter.
    Använd '--help' för att se tillgängliga kommandon och deras optioner.
    """
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose
    ctx.obj["DEBUG"] = debug

    if debug:
        logger.remove()
        logger.add(GPTME_CLI_LOG_FILE, rotation="500 MB", level="DEBUG")
        logger.add("stderr", level="DEBUG")
        logger.debug("Debug-läge aktiverat.")
    elif verbose:
        logger.remove()
        logger.add(GPTME_CLI_LOG_FILE, rotation="500 MB", level="INFO")
        logger.add("stderr", level="INFO")
        logger.info("Verbose-läge aktiverat.")

# Lägg till kommandot 'add'
@cli.command()
@click.argument("descriptions", nargs="+")
@click.pass_context
def add(ctx: click.Context, descriptions: List[str]):
    """Lägg till en eller flera nya uppgifter.

    Argument:
        descriptions: En lista med beskrivningar för de nya uppgifterna.

    Exempel:
        gptme add "Skriv enhetstester för modul X" "Dokumentera API-slutpunkt Y"
    """
    tasks = load_tasks()
    for description in descriptions:
        task_name = f"task_{len(tasks) + 1}"
        task_data = {
            "name": task_name,
            "description": description,
            "template_type": "description",
            "priority": 10,
            "status": "pending",
            "context_paths": [],
            "dependencies": [],
            "created_at": "nu",  # Bör ersättas med en faktisk tidsstämpel
            "completed_at": None,
            "outputs": [],
            "metadata": {},
        }
        tasks[task_name] = task_data
        logger.info(f"Lade till uppgift '{task_name}' med beskrivningen: {description}")
        if ctx.obj["VERBOSE"]:
            click.echo(click.style(f"Lade till uppgift '{task_name}'.", fg="green"))
    save_tasks(tasks)
    click.echo(click.style("Uppgifter tillagda!", fg="green", bold=True))

# Lägg till kommandot 'list'
@cli.command()
@click.option("--pending", is_flag=True, help="Visa endast väntande uppgifter.")
@click.option("--in-progress", is_flag=True, help="Visa endast uppgifter som bearbetas.")
@click.option("--completed", is_flag=True, help="Visa endast slutförda uppgifter.")
@click.option("--failed", is_flag=True, help="Visa endast misslyckade uppgifter.")
@click.option(
    "--no-trunc", is_flag=True, help="Visa fullständig beskrivning, trunkera inte."
)
def list(pending: bool, in_progress: bool, completed: bool, failed: bool, no_trunc: bool):
    """Lista uppgifter med möjlighet att filtrera efter status.

    Använd flaggor för att filtrera uppgifter baserat på deras status.
    Om inga flaggor anges visas alla uppgifter.
    """
    tasks = load_tasks()
    filtered_tasks = {}
    if pending:
        filtered_tasks.update(
            {k: v for k, v in tasks.items() if v["status"] == "pending"}
        )
    if in_progress:
        filtered_tasks.update(
            {k: v for k, v in tasks.items() if v["status"] == "in_progress"}
        )
    if completed:
        filtered_tasks.update(
            {k: v for k, v in tasks.items() if v["status"] == "completed"}
        )
    if failed:
        filtered_tasks.update(
            {k: v for k, v in tasks.items() if v["status"] == "failed"}
        )

    if not pending and not in_progress and not completed and not failed:
        filtered_tasks = tasks

    if filtered_tasks:
        click.echo(click.style("Uppgifter:", bold=True))
        for name, task in filtered_tasks.items():
            description = task["description"]
            if not no_trunc and len(description) > 60:
                description = f"{description[:57]}..."
            status_color = {
                "pending": "yellow",
                "in_progress": "blue",
                "completed": "green",
                "failed": "red",
            }.get(task["status"], "white")
            click.echo(
                f"- {click.style(name, bold=True)}: {description} "
                f"({click.style('Status', bold=True)}: {click.style(task['status'], fg=status_color)})"
            )
    else:
        click.echo(click.style("Inga uppgifter hittades med de kriterierna.", fg="yellow"))

# Lägg till kommandot 'status'
@cli.command()
@click.argument("task_name")
def status(task_name: str):
    """Visa detaljerad status för en specifik uppgift.

    Argument:
        task_name: Namnet på uppgiften vars status ska visas.
    """
    tasks = load_tasks()
    task = tasks.get(task_name)
    if task:
        click.echo(click.style(f"Status för uppgift '{task_name}':", bold=True))
        for key, value in task.items():
            click.echo(f"  {click.style(key + ':', bold=True)} {value}")
    else:
        click.echo(click.style(f"Fel: Uppgift '{task_name}' hittades inte.", fg="red"))

# Lägg till kommandot 'start'
@cli.command()
@click.argument("task_name")
def start(task_name: str):
    """Tvinga igång bearbetningen av en specifik uppgift.

    Används för att manuellt sätta statusen till 'pending' om en uppgift har fastnat.

    Argument:
        task_name: Namnet på uppgiften som ska startas om.
    """
    tasks = load_tasks()
    if task_name in tasks:
        if tasks[task_name]["status"] != "pending":
            logger.info(f"Ändrar status för uppgift '{task_name}' till 'pending'.")
            tasks[task_name]["status"] = "pending"
            save_tasks(tasks)
            click.echo(
                click.style(f"Uppgift '{task_name}' har satts till väntande.", fg="yellow")
            )
        else:
            click.echo(
                click.style(f"Uppgift '{task_name}' är redan i vänteläge.", fg="blue")
            )
    else:
        click.echo(click.style(f"Fel: Uppgift '{task_name}' hittades inte.", fg="red"))

# Lägg till kommandot 'remove'
@cli.command()
@click.argument("task_name")
def remove(task_name: str):
    """Ta bort en specifik uppgift.

    Varning: Denna åtgärd kan inte ångras.

    Argument:
        task_name: Namnet på uppgiften som ska tas bort.
    """
    tasks = load_tasks()
    if task_name in tasks:
        if click.confirm(
            click.style(f"Är du säker på att du vill ta bort uppgift '{task_name}'?", fg="yellow")
        ):
            del tasks[task_name]
            save_tasks(tasks)
            click.echo(
                click.style(f"Uppgift '{task_name}' har tagits bort.", fg="green")
            )
            logger.info(f"Uppgift '{task_name}' borttagen.")
    else:
        click.echo(click.style(f"Fel: Uppgift '{task_name}' hittades inte.", fg="red"))

# Skapa en Click-grupp för konfigurationshantering
@cli.group()
def config():
    """Hantera gptme-konfigurationen."""
    pass

# Lägg till subkommandot 'get' under 'config'
@config.command("get")
@click.argument("setting", required=False)
def config_get(setting: Optional[str]):
    """Visa gptme-konfigurationen.

    Visar alla inställningar eller en specifik inställning om den anges.

    Argument:
        setting: Den specifika inställningen att visa (t.ex. 'gptme.default_model').
                 Använd punktnotation för att navigera i sektioner.
    """
    cfg = load_config()
    if setting:
        try:
            value = cfg
            for key in setting.split("."):
                value = value[key]
            click.echo(f"{click.style(setting + ':', bold=True)} {value}")
        except KeyError:
            click.echo(
                click.style(
                    f"Fel: Inställningen '{setting}' hittades inte i konfigurationen.", fg="red"
                )
            )
    else:
        click.echo(click.style("Aktuell konfiguration:", bold=True))
        for section, settings in cfg.items():
            click.echo(f"\n[{click.style(section, bold=True)}")
            for key, value in settings.items():
                click.echo(f"{key} = {value}")

# Lägg till subkommandot 'set' under 'config'
@config.command("set")
@click.argument("setting")
@click.argument("value")
def config_set(setting: str, value: str):
    """Ändra en specifik gptme-konfigurationsinställning.

    Argument:
        setting: Inställningen att ändra (t.ex. 'gptme.default_model').
        value: Det nya värdet för inställningen.
    """
    cfg = load_config()
    try:
        section_keys = setting.split(".")
        if len(section_keys) < 2:
            click.echo(
                click.style(
                    "Fel: Ogiltig inställning. Använd formatet 'sektion.inställning'.", fg="red"
                )
            )
            return

        section = cfg.setdefault(section_keys[0], {})
        setting_key = section_keys[1]
        section[setting_key] = value
        with open(GPTME_TOML_FILE, "w") as f:
            toml.dump(cfg, f)
        click.echo(
            click.style(
                f"Inställningen '{setting}' har ändrats till '{value}'.", fg="green"
            )
        )
        logger.info(f"Konfigurationsinställning '{setting}' ändrad till '{value}'.")
    except (IOError, TypeError) as e:
        logger.error(f"Fel vid ändring av konfigurationen: {e}")
        click.echo(click.style(f"Fel: Kunde inte ändra inställningen: {e}", fg="red"))

# Lägg till kommandot 'gptme_script'
@cli.command()
@click.pass_context
def gptme_script(ctx: click.Context):
    """Kör en serie gptme-kommandon från inklistrad text.

    Klistra in en eller flera gptme-kommandon, en per rad.
    Avsluta inmatningen med en tom rad.
    """
    click.echo(
        click.style(
            "Klistra in gptme-kommandon här, en per rad. Avsluta med en tom rad:",
            fg="yellow",
        )
    )
    commands: List[str] = []
    while True:
        line = input("> ")
        if not line.strip():
            break
        commands.append(line)

    if not commands:
        click.echo(click.style("Inga kommandon att köra.", fg="blue"))
        return

    click.echo(click.style("\nFöljande kommandon kommer att köras:", bold=True))
    for cmd in commands:
        click.echo(f"- {cmd}")

    if not click.confirm(click.style("Vill du fortsätta och köra dessa kommandon?", fg="yellow")):
        click.echo(click.style("Exekvering avbruten.", fg="blue"))
        return

    click.echo(click.style("\nExekverar kommandon:", bold=True))
    for cmd_str in commands:
        try:
            runner = cli.make_context("gptme", args=cmd_str.split())
            with runner:
                cli.invoke(runner)
            append_to_history(cmd_str)  # Lägg till i historiken efter lyckad körning
        except click.NoSuchOption as e:
            click.echo(click.style(f"Fel: Ogiltig flagga i '{cmd_str}': {e}", fg="red"))
        except click.NoSuchCommand as e:
            click.echo(click.style(f"Fel: Okänt kommando: {e}", fg="red"))
        except SystemExit:
            pass
        except Exception as e:
            logger.error(f"Fel vid körning av kommando '{cmd_str}': {e}")
            click.echo(click.style(f"Fel vid körning av '{cmd_str}': {e}", fg="red"))

# Implementera automatisk komplettering
@cli.command()
@click.option(
    "--append/--overwrite",
    default=True,
    help="Lägg till kompletteringskoden eller skriv över den befintliga.",
)
@click.argument(
    "shell",
    type=click_completion.DocumentedChoice(click_completion.shells),
    required=False,
)
def autocomplete(append: bool, shell: Optional[str]):
    """Installera automatisk komplettering för din shell.

    Genererar och installerar skript för automatisk komplettering av gptme-kommandon.
    Stöder bash, zsh och fish.
    """
    if click_completion is None:
        click.echo(
            click.style(
                "Fel: click-completion är inte installerat. Installera det med 'poetry add click-completion'.",
                fg="red",
            )
        )
        return

    extra_env = {"_GPTME_COMPLETE": "bash_source"}
    tcf = click_completion.CompletionItemFormatter()

    output = ""
    shell_to_use = shell or click_completion.get_auto_completion_vars(extra_env=extra_env)[0]
    assert shell_to_use is not None
    actions = click_completion.get_completion_item_help(cli, shell=shell_to_use)

    for action in actions:
        output += f"# {'-' * 78}\n"
        output += str(tcf(action)) + "\n\n"

    comp_vars = click_completion.get_auto_completion_vars(cli_name="gptme")
    if shell_to_use == "fish":
        comp_vars = click_completion.get_auto_completion_vars(cli_name="gptme")
    else:
        comp_vars = click_completion.get_auto_completion_vars(cli_name="gptme")

    if shell_to_use == "bash":
        completion_file = "~/.bashrc"
    elif shell_to_use == "zsh":
        completion_file = "~/.zshrc"
    elif shell_to_use == "fish":
        completion_file = "~/.config/fish/config.fish"
    else:
        click.echo(click.style(f"Varning: Shell '{shell_to_use}' stöds inte automatiskt.", fg="yellow"))
        click.echo("Du kan behöva konfigurera detta manuellt.")
        return

    completion_file = os.path.expanduser(completion_file)

    config = {
        "prog_name": "gptme",
        "complete_var": comp_vars[1],
        "aliases": ["_gptme_completion"],
    }
    try:
        if append:
            click_completion.append_completion_code(completion_file, config)
            click.echo(click.style(f"Automatisk komplettering för {shell_to_use} har lagts till i {completion_file}", fg="green"))
        else:
            click_completion.write_completion_script(completion_file, config)
            click.echo(click.style(f"Automatisk komplettering för {shell_to_use} har skrivits till {completion_file}", fg="green"))
        click.echo(f"Starta om din terminal eller kör 'source {completion_file}' för att aktivera kompletteringen.")
    except IOError as e:
        logger.error(f"Fel vid hantering av kompletteringsfilen '{completion_file}': {e}")
        click.echo(click.style(f"Fel: Kunde inte installera automatisk komplettering.", fg="red"))

# Implementera kommandohistorik
@cli.command()
def history():
    """Visa en lista över tidigare körda kommandon."""
    history = load_history()
    if history:
        click.echo(click.style("Kommandohistorik:", bold=True))
        for i, cmd in enumerate(history, 1):
            click.echo(f"{i}. {cmd}")
    else:
        click.echo(click.style("Ingen kommandohistorik hittades.", fg="blue"))

if __name__ == "__main__":
    cli(obj={})
