from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from datetime import datetime

class RichLogger:
    def __init__(self):
        self.console = Console()

    def banner(self, host: str, port: int):
        banner_text = Text()
        banner_text.append("Servidor de Chat Modular (TLV)\n", style="bold cyan")
        banner_text.append(f"IP: {host} | Puerto: {port}", style="green")
        
        self.console.print(Panel(banner_text, expand=False, border_style="blue"))

    def info(self, message: str):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[[dim]{time_str}[/]] [[bold blue]INFO[/]] {message}")

    def success(self, message: str):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[[dim]{time_str}[/]] [[bold green]OK[/]] {message}")

    def error(self, message: str):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[[dim]{time_str}[/]] [[bold red]ERROR[/]] {message}")

    def connection(self, addr, status: str):
        style = "green" if "unido" in status.lower() or "conexión" in status.lower() else "red"
        self.info(f"Conexión de [bold yellow]{addr}[/]: [{style}]{status}[/]")

    def file_transfer(self, sender: str, receiver: str, info: str):
        self.console.print(f"[[bold magenta]ARCHIVO[/]] [cyan]{sender}[/] -> [cyan]{receiver}[/]: {info}")

logger = RichLogger()
