import subprocess
import sys
import os
import requests
import json
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
import threading
from tzlocal import get_localzone

# Function to check if a package is installed
def is_package_installed(package):
    try:
        subprocess.check_output([sys.executable, '-m', 'pip', 'show', package])
        return True
    except subprocess.CalledProcessError:
        return False

# Function to install a package
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required packages if not installed
def setup():
    packages = [
        "requests",
        "rich",
        "tzlocal"
    ]
    
    for package in packages:
        if not is_package_installed(package):
            print(f"Installing {package}...")
            install_package(package)
        else:
            print(f"{package} is already installed.")

    if os.name == 'nt':
        subprocess.call('cls', shell=True)
    else:
        subprocess.call('clear', shell=True)

# Global variables
SETTINGS_FILE = 'settings.json'
LAST_SEARCH_FILE = 'last_search.json'
console = Console()

# Function to load settings from JSON file
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as file:
            return json.load(file)
    return {}

# Function to save settings to JSON file
def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as file:
        json.dump(settings, file)

# Function to get GitHub token from user input or settings file
def get_github_token():
    settings = load_settings()
    if 'GITHUB_TOKEN' in settings:
        return settings['GITHUB_TOKEN']
    token = Prompt.ask("Enter your GitHub token")
    settings['GITHUB_TOKEN'] = token
    save_settings(settings)
    return token

# Function to load last search time from JSON file
def load_last_search_time():
    if os.path.exists(LAST_SEARCH_FILE):
        with open(LAST_SEARCH_FILE, 'r') as file:
            data = json.load(file)
            return datetime.fromisoformat(data['last_search_time'])
    return None

# Function to save last search time to JSON file
def save_last_search_time(time):
    with open(LAST_SEARCH_FILE, 'w') as file:
        json.dump({'last_search_time': time.isoformat()}, file)

# Function to handle existing last search file
def handle_existing_last_search_file():
    if os.path.exists(LAST_SEARCH_FILE):
        console.print("[bold yellow]Last search file already exists. This may prevent finding new CVEs.[/bold yellow]")
        action = Prompt.ask("Do you want to delete or rename the last search file? (delete/rename/continue)", default="continue")
        if action == "delete":
            os.remove(LAST_SEARCH_FILE)
            console.print("[bold green]Last search file deleted.[/bold green]")
        elif action == "rename":
            new_name = Prompt.ask("Enter new name for the last search file")
            os.rename(LAST_SEARCH_FILE, new_name)
            console.print(f"[bold green]Last search file renamed to {new_name}.[/bold green]")
        else:
            console.print("[bold yellow]Continuing with the existing last search file.[/bold yellow]")

# Function to clone repository using git
def clone_repository(repo_url, repo_name):
    try:
        subprocess.run(["git", "clone", repo_url, repo_name], check=True)
        console.print(f"[bold green]Successfully cloned {repo_name}[/bold green]")
    except subprocess.CalledProcessError:
        console.print(f"[bold red]Failed to clone {repo_name}[/bold red]")

# Function to fetch repositories from GitHub API
def fetch_repositories(url, headers, repos):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = response.json()
            for repo in results['items']:
                repos.append(repo)
        else:
            console.print(f"[bold red]Failed to fetch data from GitHub API. Status code: {response.status_code}[/bold red]")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]An error occurred: {str(e)}[/bold red]")

# Function to search for new CVEs
def search_new_cves():
    github_token = get_github_token()
    timezone = str(get_localzone())
    headers = {'Authorization': f'token {github_token}'}
    
    last_search_time = load_last_search_time() or datetime.now() - timedelta(days=1)
    query = f'CVE created:>{last_search_time.strftime("%Y-%m-%dT%H:%M:%SZ")}'
    url = f'https://api.github.com/search/repositories?q={query}&per_page=10'

    repos = []
    threads = []
    for page in range(1, 6):  # Fetching up to 50 repositories (5 pages, 10 per page)
        paginated_url = f'{url}&page={page}'
        thread = threading.Thread(target=fetch_repositories, args=(paginated_url, headers, repos))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    if repos:
        table = Table(title="New CVEs Found", show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=5)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("URL", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Created At", style="yellow", no_wrap=True)

        for idx, repo in enumerate(repos, start=1):
            table.add_row(str(idx), repo['name'], repo['html_url'], repo['description'] or 'No description', repo['created_at'])

        console.print(table)

        while True:
            repo_index = Prompt.ask("Enter the number of the repository to clone (or 'exit' to quit)", default="exit")
            if repo_index.lower() == 'exit':
                break
            try:
                repo_index = int(repo_index) - 1
                if 0 <= repo_index < len(repos):
                    repo = repos[repo_index]
                    clone_repository(repo['html_url'], repo['name'])
                else:
                    console.print("[bold red]Invalid number. Please try again.[/bold red]")
            except ValueError:
                console.print("[bold red]Invalid input. Please enter a number or 'exit'.[/bold red]")
    else:
        console.print("[bold red]No new CVEs found.[/bold red]")

    save_last_search_time(datetime.now())

# Function to search for a specific CVE
def search_specific_cve(cve_id):
    github_token = get_github_token()
    headers = {'Authorization': f'token {github_token}'}
    url = f'https://api.github.com/search/repositories?q={cve_id}'

    repos = []
    fetch_repositories(url, headers, repos)

    if repos:
        table = Table(title=f"Repositories for {cve_id}", show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=5)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("URL", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Created At", style="yellow", no_wrap=True)

        for idx, repo in enumerate(repos, start=1):
            table.add_row(str(idx), repo['name'], repo['html_url'], repo['description'] or 'No description', repo['created_at'])

        console.print(table)

        while True:
            repo_index = Prompt.ask("Enter the number of the repository to clone (or 'exit' to quit)", default="exit")
            if repo_index.lower() == 'exit':
                break
            try:
                repo_index = int(repo_index) - 1
                if 0 <= repo_index < len(repos):
                    repo = repos[repo_index]
                    clone_repository(repo['html_url'], repo['name'])
                else:
                    console.print("[bold red]Invalid number. Please try again.[/bold red]")
            except ValueError:
                console.print("[bold red]Invalid input. Please enter a number or 'exit'.[/bold red]")
    else:
        console.print(f"[bold red]No repositories found for {cve_id}.[/bold red]")

# Function to search CVEs based on a specific date
def search_cves_by_date():
    while True:
        try:
            search_date_str = Prompt.ask("Enter the search date (YYYY-MM-DD) or 'exit' to cancel", default="exit")
            if search_date_str.lower() == 'exit':
                return
            search_date = datetime.strptime(search_date_str, "%Y-%m-%d")
            break
        except ValueError:
            console.print("[bold red]Invalid date format. Please enter date in YYYY-MM-DD format.[/bold red]")

    github_token = get_github_token()
    timezone = str(get_localzone())
    headers = {'Authorization': f'token {github_token}'}
    
    query = f'CVE created:{search_date.strftime("%Y-%m-%d")}'
    url = f'https://api.github.com/search/repositories?q={query}&per_page=10'

    repos = []
    fetch_repositories(url, headers, repos)

    if repos:
        table = Table(title=f"CVEs created on {search_date.strftime('%Y-%m-%d')}", show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=5)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("URL", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Created At", style="yellow", no_wrap=True)

        for idx, repo in enumerate(repos, start=1):
            table.add_row(str(idx), repo['name'], repo['html_url'], repo['description'] or 'No description', repo['created_at'])

        console.print(table)

        while True:
            repo_index = Prompt.ask("Enter the number of the repository to clone (or 'exit' to quit)", default="exit")
            if repo_index.lower() == 'exit':
                break
            try:
                repo_index = int(repo_index) - 1
                if 0 <= repo_index < len(repos):
                    repo = repos[repo_index]
                    clone_repository(repo['html_url'], repo['name'])
                else:
                    console.print("[bold red]Invalid number. Please try again.[/bold red]")
            except ValueError:
                console.print("[bold red]Invalid input. Please enter a number or 'exit'.[bold red]")
    else:
        console.print(f"[bold red]No new CVEs found on {search_date.strftime('%Y-%m-%d')}.[/bold red]")

# Function to search repositories by keyword
def search_repos_by_keyword():
    github_token = get_github_token()
    headers = {'Authorization': f'token {github_token}'}
    keyword = Prompt.ask("Enter keyword(s) to search for repositories")
    url = f'https://api.github.com/search/repositories?q={keyword}&per_page=10'

    repos = []
    threads = []
    for page in range(1, 6):  # Fetching up to 50 repositories (5 pages, 10 per page)
        paginated_url = f'{url}&page={page}'
        thread = threading.Thread(target=fetch_repositories, args=(paginated_url, headers, repos))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    if repos:
        table = Table(title=f"Repositories for keyword(s): {keyword}", show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=5)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("URL", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Created At", style="yellow", no_wrap=True)

        for idx, repo in enumerate(repos, start=1):
            table.add_row(str(idx), repo['name'], repo['html_url'], repo['description'] or 'No description', repo['created_at'])

        console.print(table)

        while True:
            repo_index = Prompt.ask("Enter the number of the repository to clone (or 'exit' to quit)", default="exit")
            if repo_index.lower() == 'exit':
                break
            try:
                repo_index = int(repo_index) - 1
                if 0 <= repo_index < len(repos):
                    repo = repos[repo_index]
                    clone_repository(repo['html_url'], repo['name'])
                else:
                    console.print("[bold red]Invalid number. Please try again.[/bold red]")
            except ValueError:
                console.print("[bold red]Invalid input. Please enter a number or 'exit'.[/bold red]")
    else:
        console.print(f"[bold red]No repositories found for keyword(s): {keyword}.[/bold red]")

# Function to handle user input and actions
def main():
    setup()
    handle_existing_last_search_file()

    while True:
        menu = Panel.fit("""
[bold cyan]What would you like to do?[/bold cyan]
1. Search for a specific CVE
2. Search for new CVEs
3. Search for CVEs by specific date
4. Search repositories by keyword
5. Help
6. Exit
""", title="Menu", border_style="green")

        console.print(menu)

        try:
            choice = Prompt.ask("Choose an option", choices=[str(i) for i in range(1, 7)], default="1")
            if choice == "1":
                search_specific_cve(Prompt.ask("Enter CVE ID to search for"))
            elif choice == "2":
                search_new_cves()
            elif choice == "3":
                search_cves_by_date()
            elif choice == "4":
                search_repos_by_keyword()
            elif choice == "5":
                console.print("""
[bold cyan]Help - Available Commands[/bold cyan]
1. Search for a specific CVE by entering its ID.
2. Search for new CVEs created since the last search.
3. Search for CVEs created on a specific date.
4. Search for repositories using keywords.
5. Exit the program.
""")
            elif choice == "6":
                break
        except ValueError:
            console.print("[bold red]Invalid input. Please enter a number from 1 to 6.[/bold red]")

if __name__ == "__main__":
    main()
