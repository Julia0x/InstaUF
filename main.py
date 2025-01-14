import time
import os
from datetime import datetime
from colorama import Fore, Style, init
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

init(autoreset=True)
console = Console()

class InstaUF:
    def __init__(self):
        self.client = None
        self.banner = f"""
{Fore.BLUE}╔══════════════════════════════════════════════════╗
║ {Fore.CYAN}██╗███╗   ██╗███████╗████████╗ █████╗ ██╗   ███╗{Fore.BLUE}║
║ {Fore.CYAN}██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║   ██║{Fore.BLUE}║
║ {Fore.CYAN}██║██╔██╗ ██║███████╗   ██║   ███████║██║   ██║{Fore.BLUE}║
║ {Fore.CYAN}██║██║╚██╗██║╚════██║   ██║   ██╔══██║██║   ██║{Fore.BLUE}║
║ {Fore.CYAN}██║██║ ╚████║███████║   ██║   ██║  ██║╚██████╔╝{Fore.BLUE}║
║ {Fore.CYAN}╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ {Fore.BLUE}║
║────────────────────────────────────────────────║
║ {Fore.YELLOW}InstaUF - Instagram Unfollower Tool v3.0       {Fore.BLUE}║
║ {Fore.WHITE}By: Julia0x                                     {Fore.BLUE}║
╚══════════════════════════════════════════════════╝{Style.RESET_ALL}
"""

    def login(self, username: str, password: str) -> bool:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Logging in to Instagram...", total=None)
            
            try:
                self.client = Client()
                try:
                    self.client.load_settings("session.json")
                    progress.update(task, description="[green]Found existing session...")
                except FileNotFoundError:
                    progress.update(task, description="[yellow]No existing session found...")

                self.client.login(username, password)
                self.client.dump_settings("session.json")
                progress.update(task, description="[green]Successfully logged in!")
                return True

            except Exception as e:
                if "challenge_required" in str(e):
                    progress.update(task, description="[yellow]Challenge required...")
                    return self.handle_challenge()
                else:
                    progress.update(task, description=f"[red]Login failed: {str(e)}")
                    return False

    def handle_challenge(self) -> bool:
        try:
            challenge_info = self.client.challenge_resolve(self.client.last_json["challenge"]["api_path"])
            if challenge_info["step_name"] == "email":
                code = console.input("[yellow]Enter the code sent to your email: ")
                self.client.challenge_send_email(code)
            elif challenge_info["step_name"] == "sms":
                code = console.input("[yellow]Enter the code sent to your phone: ")
                self.client.challenge_send_sms(code)
            else:
                console.print("[red]Unsupported challenge type!")
                return False
            return True
        except Exception as e:
            console.print(f"[red]Failed to resolve challenge: {str(e)}")
            return False

    def get_non_followers(self) -> list:
        with Progress() as progress:
            task1 = progress.add_task("[cyan]Getting followers...", total=None)
            task2 = progress.add_task("[cyan]Getting following...", total=None)
            
            try:
                user_id = self.client.user_id
                followers = set(self.client.user_followers(user_id).keys())
                progress.update(task1, description="[green]Got followers list!")
                
                following = set(self.client.user_following(user_id).keys())
                progress.update(task2, description="[green]Got following list!")
                
                return list(following - followers)
            except Exception as e:
                console.print(f"[red]Error getting non-followers: {str(e)}")
                return []

    def display_non_followers(self, non_followers: list):
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim")
        table.add_column("Username", style="cyan")
        table.add_column("Full Name", style="green")
        table.add_column("Posts", justify="right")
        table.add_column("Followers", justify="right")

        for idx, user_id in enumerate(non_followers[:20], 1):
            try:
                user_info = self.client.user_info(user_id)
                table.add_row(
                    str(idx),
                    user_info.username,
                    user_info.full_name,
                    str(user_info.media_count),
                    str(user_info.follower_count)
                )
            except Exception:
                continue

        console.print(table)
        if len(non_followers) > 20:
            console.print(f"\n[yellow]...and {len(non_followers) - 20} more")

    def unfollow_users(self, user_ids: list, delay: int = 15):
        total = len(user_ids)
        with Progress() as progress:
            task = progress.add_task("[red]Unfollowing users...", total=total)
            
            for user_id in user_ids:
                try:
                    user_info = self.client.user_info(user_id)
                    self.client.user_unfollow(user_id)
                    progress.update(task, advance=1, description=f"[green]Unfollowed {user_info.username}")
                    time.sleep(delay)
                except Exception as e:
                    progress.update(task, description=f"[red]Failed to unfollow {user_id}: {str(e)}")
                    if isinstance(e, LoginRequired):
                        break

    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(self.banner)
        
        console.print("\n[cyan]Welcome to InstaUF - Instagram Unfollower Tool![/cyan]")
        console.print("[yellow]Please enter your Instagram credentials:[/yellow]\n")

        username = console.input("[bold cyan]Username: [/bold cyan]")
        password = console.input("[bold cyan]Password: [/bold cyan]", password=True)

        if not self.login(username, password):
            console.print("[red]Failed to log in. Please try again later.")
            return

        while True:
            console.print("\n[bold cyan]Menu Options:[/bold cyan]")
            console.print("1. [green]Find users who don't follow back[/green]")
            console.print("2. [yellow]Unfollow non-followers[/yellow]")
            console.print("3. [red]Exit[/red]\n")

            choice = console.input("[bold cyan]Select an option (1-3): [/bold cyan]")

            if choice == "1":
                non_followers = self.get_non_followers()
                if non_followers:
                    console.print(f"\n[green]Found {len(non_followers)} users who don't follow you back:[/green]")
                    self.display_non_followers(non_followers)
                else:
                    console.print("[yellow]No non-followers found![/yellow]")

            elif choice == "2":
                non_followers = self.get_non_followers()
                if non_followers:
                    confirm = console.input(f"\n[yellow]You are about to unfollow {len(non_followers)} users. Continue? (yes/no): [/yellow]").lower()
                    if confirm == "yes":
                        self.unfollow_users(non_followers)
                        console.print("\n[green]Unfollowing complete![/green]")
                    else:
                        console.print("\n[yellow]Operation cancelled.[/yellow]")
                else:
                    console.print("[yellow]No users to unfollow![/yellow]")

            elif choice == "3":
                console.print("\n[green]Thank you for using InstaUF! Goodbye![/green]")
                break

            else:
                console.print("[red]Invalid option. Please try again.[/red]")

if __name__ == "__main__":
    instauf = InstaUF()
    instauf.run()