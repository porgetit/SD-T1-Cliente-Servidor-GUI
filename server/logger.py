from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from datetime import datetime

class RichLogger:
    def __init__(self):
        self.console = Console()

    def banner(self, bind_ip: str, port: int, network_ip: str):
        """Imprime el banner del servidor."""
        banner_text = Text()
        banner_text.append("Servidor de Chat Modular (TLV)\n", style="bold cyan")
        banner_text.append(f"Escuchando en: {bind_ip}:{port}\n", style="green")
        banner_text.append(f"IP para clientes remotos: {network_ip}", style="bold yellow")
        
        self.console.print(Panel(banner_text, expand=False, border_style="blue"))

    def info(self, message: str):
        """Imprime un mensaje de información."""
        time_str = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[[dim]{time_str}[/]] [[bold blue]INFO[/]] {message}")

    def success(self, message: str):
        """Imprime un mensaje de éxito."""
        time_str = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[[dim]{time_str}[/]] [[bold green]OK[/]] {message}")

    def error(self, message: str):
        """Imprime un mensaje de error."""
        time_str = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[[dim]{time_str}[/]] [[bold red]ERROR[/]] {message}")

    def connection(self, addr, status: str):
        """Imprime un mensaje de conexión."""
        style = "green" if "unido" in status.lower() or "conexión" in status.lower() else "red"
        self.info(f"Conexión de [bold yellow]{addr}[/]: [{style}]{status}[/]")

    def file_transfer(self, sender: str, receiver: str, info: str):
        """Imprime un mensaje de transferencia de archivo."""
        self.console.print(f"[[bold magenta]ARCHIVO[/]] [cyan]{sender}[/] -> [cyan]{receiver}[/]: {info}")

logger = RichLogger() # Instancia del logger
