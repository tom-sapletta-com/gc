"""
CLI interface for glon package - Git Clone utility.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, TypedDict, cast

try:
    import tkinter
except ImportError:  # pragma: no cover - depends on the Python distribution
    tkinter = None  # type: ignore[assignment]

# Try to import argcomplete for tab completion
try:
    import argcomplete
    from argcomplete.completers import ChoicesCompleter as ChoicesCompleter

    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False


DEFAULT_BASE_PATH = "~/github"
MAX_CLIPBOARD_URL_LENGTH = 200
PROJECT_LIST_WIDTH = 80
SELECTION_LIST_WIDTH = 50
IDE_LIST_WIDTH = 40
RECENT_PROJECT_LIMIT = 10
DAYS_PER_MONTH = 30
DAYS_PER_QUARTER = 90
DAYS_PER_HALF_YEAR = 180
DAYS_PER_YEAR = 365

SSH_URL_RE = re.compile(r"git@[^:]+:([^/]+)/([^/]+)\.git$")
HTTPS_URL_RE = re.compile(r"https://[^/]+/([^/]+)/([^/]+)\.git$")
HTTPS_URL_WITHOUT_SUFFIX_RE = re.compile(r"https://[^/]+/([^/]+)/([^/]+)$")
EMBEDDED_URL_RES = (
    re.compile(r"git@[^:\s]+:[^/\s]+/[^\s]+\.git"),
    re.compile(r"https://[^/\s]+/[^/\s]+/[^\s]+\.git"),
    re.compile(r"https://[^/\s]+/[^/\s]+/[^\s]+"),
)

IDE_COMMANDS = {
    "pycharm": "pycharm",
    "idea": "idea",
    "vscode": "code",
    "code": "code",
    "webstorm": "webstorm",
    "goland": "goland",
    "rider": "rider",
}


class ProjectInfo(TypedDict):
    """Filesystem metadata used by project listing and selection."""

    name: str
    path: Path
    mtime: datetime
    owner: str
    repo: str


def _expand_base_path(base_path: Optional[str]) -> Path:
    return Path(os.path.expanduser(base_path or DEFAULT_BASE_PATH))


def get_all_projects(base_path: Optional[str] = None) -> List[str]:
    """Return available projects as sorted ``owner/repo`` names."""
    return sorted(project["name"] for project in get_all_projects_with_time(base_path))


def get_all_projects_with_time(base_path: Optional[str] = None) -> List[ProjectInfo]:
    """Return project directories and their modification times."""
    base_path_obj = _expand_base_path(base_path)
    projects: List[ProjectInfo] = []

    if not base_path_obj.exists():
        return projects

    for owner_dir in base_path_obj.iterdir():
        if not owner_dir.is_dir():
            continue

        for repo_dir in owner_dir.iterdir():
            if not repo_dir.is_dir():
                continue

            try:
                mtime = datetime.fromtimestamp(repo_dir.stat().st_mtime)
            except OSError:
                mtime = datetime.min

            projects.append(
                {
                    "name": f"{owner_dir.name}/{repo_dir.name}",
                    "path": repo_dir,
                    "mtime": mtime,
                    "owner": owner_dir.name,
                    "repo": repo_dir.name,
                }
            )

    return sorted(projects, key=lambda x: x["mtime"], reverse=True)


def _read_clipboard_text() -> Optional[str]:
    if tkinter is not None:
        try:
            root = tkinter.Tk()
            root.withdraw()
            try:
                text = root.clipboard_get()
            finally:
                root.destroy()
            return str(text)
        except Exception:
            pass

    for command in (
        ["wl-paste", "-n"],
        ["xclip", "-o", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--output"],
    ):
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            continue

        text = (result.stdout or "").strip()
        if text:
            return text

    return None


def _extract_git_url_from_text(text: str) -> Optional[str]:
    """Extract the first supported Git URL from arbitrary text."""
    for line in text.strip().splitlines():
        line = line.strip()
        if parse_git_url(line) is not None:
            return line

        for pattern in EMBEDDED_URL_RES:
            match = pattern.search(line)
            if match:
                return match.group(0)

    return None


def _clipboard_url_candidate(
    max_len: int = MAX_CLIPBOARD_URL_LENGTH,
) -> Optional[str]:
    text = _read_clipboard_text()
    if text is None:
        return None

    text = text.strip()
    if not text or len(text) > max_len:
        return None

    if any(ch in text for ch in ("\n", "\r", "\t")):
        return None

    if parse_git_url(text) is None:
        return None

    return text


def parse_git_url(url: str) -> Optional[Tuple[str, str]]:
    """Parse a supported SSH or HTTPS URL into owner and repository names."""
    for pattern in (SSH_URL_RE, HTTPS_URL_RE, HTTPS_URL_WITHOUT_SUFFIX_RE):
        match = pattern.fullmatch(url)
        if match:
            return match.group(1), match.group(2)
    return None


def create_directory_structure(
    owner: str, repo: str, base_path: Optional[str] = None
) -> Path:
    """Create and return the configured ``owner/repo`` directory."""
    target_dir = _expand_base_path(base_path) / owner / repo
    target_dir.mkdir(parents=True, exist_ok=True)

    return target_dir


def clone_repository(url: str, target_dir: Path) -> bool:
    """Clone ``url`` into an empty target directory."""
    try:
        if any(target_dir.iterdir()):
            print(f"Directory {target_dir} is not empty. Skipping clone.")
            return False

        subprocess.run(
            ["git", "clone", url, str(target_dir)],
            capture_output=True,
            text=True,
            check=True,
        )

        print(f"Successfully cloned {url} to {target_dir}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed to clone repository: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Git is not installed or not in PATH")
        return False


def grab_from_clipboard(
    base_path: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Clone a clipboard URL or link/copy a clipboard filesystem path."""
    # Try to read from clipboard
    clipboard_text = _read_clipboard_text()

    if clipboard_text is None:
        print("Error: Clipboard is empty or could not be read.")
        return False

    clipboard_text = clipboard_text.strip()

    if not clipboard_text:
        print("Error: Clipboard is empty.")
        return False

    if verbose:
        print(f"Clipboard content: {clipboard_text}")

    parsed = parse_git_url(clipboard_text)
    if parsed is not None:
        return _grab_git_url(clipboard_text, parsed, base_path, dry_run, verbose)
    return _grab_local_path(clipboard_text, base_path, dry_run, verbose)


def _grab_git_url(
    url: str,
    parsed: Tuple[str, str],
    base_path: Optional[str],
    dry_run: bool,
    verbose: bool,
) -> bool:
    owner, repo = parsed
    if verbose:
        print(f"Detected git URL - Owner: {owner}, Repository: {repo}")

    target_dir = create_directory_structure(owner, repo, base_path)
    if verbose:
        print(f"Target directory: {target_dir}")
    if dry_run:
        print(f"Would clone {url} to {target_dir}")
        return True
    if not clone_repository(url, target_dir):
        return False

    print(f"Repository ready at: {target_dir}")
    return True


def _copy_or_link(source_path: Path, target_dir: Path) -> None:
    if source_path.is_dir():
        link_path = target_dir / source_path.name
        if link_path.exists() or link_path.is_symlink():
            print(f"Symlink already exists at {link_path}")
            return
        link_path.symlink_to(source_path.resolve())
        print(f"Created symlink: {link_path} -> {source_path}")
        return

    shutil.copy2(source_path, target_dir / source_path.name)
    print(f"Copied {source_path} to {target_dir}")


def _grab_local_path(
    clipboard_text: str,
    base_path: Optional[str],
    dry_run: bool,
    verbose: bool,
) -> bool:
    source_path = Path(clipboard_text)
    if not source_path.exists():
        print(f"Error: Path does not exist: {clipboard_text}")
        print("Note: Path must be a valid git URL or existing local directory.")
        return False

    dir_name = source_path.name if source_path.is_dir() else source_path.stem
    if verbose:
        print(f"Detected local path - Name: {dir_name}")

    target_dir = _expand_base_path(base_path) / dir_name
    target_dir.mkdir(parents=True, exist_ok=True)
    if verbose:
        print(f"Target directory: {target_dir}")
    if dry_run:
        print(f"Would copy/symlink {clipboard_text} to {target_dir}")
        return True
    if any(target_dir.iterdir()):
        print(f"Warning: Directory {target_dir} is not empty. Skipping.")
        return False

    try:
        _copy_or_link(source_path, target_dir)
        print(f"Path ready at: {target_dir}")
        return True
    except OSError as error:
        print(f"Error processing path: {error}")
        return False


def parse_time_filter(filter_str: str) -> Optional[datetime]:
    """Convert a supported relative-time label to a cutoff timestamp."""
    filter_str = filter_str.lower().strip()
    now = datetime.now()

    if filter_str in ("today", "last day", "1 day"):
        return now - timedelta(days=1)
    if filter_str in ("last week", "1 week", "week"):
        return now - timedelta(weeks=1)
    if filter_str in ("last month", "1 month", "month"):
        return now - timedelta(days=DAYS_PER_MONTH)
    if filter_str in ("last 3 months", "3 months"):
        return now - timedelta(days=DAYS_PER_QUARTER)
    if filter_str in ("last 6 months", "6 months"):
        return now - timedelta(days=DAYS_PER_HALF_YEAR)
    if filter_str in ("last year", "1 year", "year"):
        return now - timedelta(days=DAYS_PER_YEAR)
    if filter_str in ("all", "everything", "*"):
        return None

    return None


def list_projects(
    base_path: Optional[str] = None,
    time_filter: Optional[str] = None,
    verbose: bool = False,
    limit: Optional[int] = None,
) -> bool:
    """Print projects, optionally filtered by age and result count."""
    base_path_obj = _expand_base_path(base_path)

    if not base_path_obj.exists():
        print(f"Error: Base path does not exist: {base_path_obj}")
        return False

    filter_date = _resolve_filter_date(time_filter)

    projects = [
        project
        for project in get_all_projects_with_time(str(base_path_obj))
        if filter_date is None or project["mtime"] >= filter_date
    ]

    if not projects:
        print(f"No projects found in {base_path_obj}")
        if time_filter:
            print(f"  (No projects modified {time_filter})")
        return True

    total_count = len(projects)
    if limit:
        projects = projects[:limit]

    _print_projects(projects, total_count, base_path_obj, time_filter, verbose, limit)
    return True


def _resolve_filter_date(time_filter: Optional[str]) -> Optional[datetime]:
    if not time_filter:
        return None

    filter_date = parse_time_filter(time_filter)
    if filter_date is not None or time_filter in ("all", "everything", "*"):
        return filter_date

    try:
        return datetime.now() - timedelta(days=int(time_filter))
    except ValueError:
        print(f"Warning: Unknown time filter '{time_filter}', showing all projects")
        return None


def _print_project(project: ProjectInfo, verbose: bool) -> None:
    path = project["path"]
    owner = project["owner"]
    repo = project["repo"]
    date_str = project["mtime"].strftime("%Y-%m-%d %H:%M")
    is_git = (path / ".git").exists()

    if verbose:
        print(f"{owner}/{repo}")
        print(f"  Path: {path}")
        print(f"  Modified: {date_str}")
        print(f"  Git: {'Yes' if is_git else 'No'}")
        print()
        return

    git_marker = "✓" if is_git else "✗"
    print(f"{date_str} {git_marker} {owner}/{repo}")


def _print_projects(
    projects: Sequence[ProjectInfo],
    total_count: int,
    base_path: Path,
    time_filter: Optional[str],
    verbose: bool,
    limit: Optional[int],
) -> None:
    print(f"\nFound {total_count} project(s) in {base_path}")
    if time_filter:
        print(f"Filtered by: {time_filter}")
    if limit:
        print(f"Showing {len(projects)} result(s)")
    print("-" * PROJECT_LIST_WIDTH)

    for project in projects:
        _print_project(project, verbose)


def _resolve_project_path(project_path: str) -> Optional[Path]:
    if "/" in project_path and not os.path.isabs(project_path):
        parts = project_path.split("/")
        if len(parts) == 2:
            owner, repo = parts
            full_path = _expand_base_path(None) / owner / repo
        else:
            print(f"Error: Invalid project path format: {project_path}")
            return None
    else:
        full_path = Path(project_path)

    full_path = Path(os.path.expanduser(str(full_path)))
    if not full_path.exists():
        print(f"Error: Project path does not exist: {full_path}")
        return None
    if not full_path.is_dir():
        print(f"Error: Project path is not a directory: {full_path}")
        return None
    return full_path


def _choose_ide(full_path: Path) -> Optional[str]:
    print(f"\nSelect IDE to open {full_path}:")
    print("-" * IDE_LIST_WIDTH)
    available_ides = list(IDE_COMMANDS)
    for index, ide_name in enumerate(available_ides, 1):
        print(f"  {index}. {ide_name}")
    print("-" * IDE_LIST_WIDTH)

    try:
        choice = input(f"Select IDE (1-{len(available_ides)}): ").strip()
    except EOFError:
        print("No input received. Canceling.")
        return None

    if not choice:
        print("No IDE selected. Canceling.")
        return None

    try:
        index = int(choice) - 1
    except ValueError:
        print(f"Invalid input: {choice}")
        return None

    if 0 <= index < len(available_ides):
        return available_ides[index]

    print(f"Invalid selection: {choice}")
    return None


def open_in_ide(project_path: str, ide: Optional[str] = None) -> bool:
    """Open a project directory in a supported IDE."""
    full_path = _resolve_project_path(project_path)
    if full_path is None:
        return False

    selected_ide = ide or _choose_ide(full_path)
    if selected_ide is None:
        return False

    executable = IDE_COMMANDS.get(selected_ide.lower())
    if executable is None:
        print(f"Error: Unknown IDE: {selected_ide}")
        print(f"Supported IDEs: {', '.join(IDE_COMMANDS)}")
        return False

    command = [executable, str(full_path)]
    try:
        subprocess.Popen(command)
        print(f"Opened {full_path} in {selected_ide}")
        return True
    except FileNotFoundError:
        print(f"Error: {selected_ide} is not installed or not in PATH")
        return False
    except OSError as error:
        print(f"Error opening project: {error}")
        return False


def _parse_ide_option(arguments: Sequence[str]) -> Optional[str]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--ide", choices=list(IDE_COMMANDS))
    options, _ = parser.parse_known_args(arguments)
    return cast(Optional[str], options.ide)


def _format_project_age(mtime: datetime, now: datetime) -> str:
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    age = now - mtime
    if mtime >= today:
        return "today"
    if mtime >= yesterday:
        return "yesterday"
    if age.days < 7:
        return f"{age.days} days ago"
    if age.days < DAYS_PER_MONTH:
        return f"{age.days // 7} weeks ago"
    return f"{age.days // DAYS_PER_MONTH} months ago"


def _print_project_choices(projects: Sequence[ProjectInfo]) -> None:
    now = datetime.now()
    for index, project in enumerate(projects, 1):
        age = _format_project_age(project["mtime"], now)
        print(f"  {index}. {project['name']} ({age})")


def _prompt_for_project(
    projects: Sequence[ProjectInfo],
    prompt: str,
    default_to_first: bool,
) -> Optional[str]:
    try:
        choice = input(prompt).strip()
    except (EOFError, ValueError):
        return projects[0]["name"] if default_to_first else None

    if not choice:
        return projects[0]["name"] if default_to_first else None

    try:
        index = int(choice) - 1
    except ValueError:
        return projects[0]["name"] if default_to_first else None

    if 0 <= index < len(projects):
        return projects[index]["name"]

    if default_to_first:
        print("Invalid selection, using first match.")
        return projects[0]["name"]

    print(f"Invalid selection: {choice}")
    return None


def _clone_clipboard_project(
    git_url: str, all_projects: Sequence[str]
) -> Optional[Path]:
    parsed = parse_git_url(git_url)
    if parsed is None:
        return None

    owner, repo = parsed
    print(f"Detected git URL in clipboard: {git_url}")
    project_path = _expand_base_path(None) / owner / repo
    if project_path.exists():
        print(f"Project already exists at: {project_path}")
        return project_path

    print("Project not found locally. Cloning first...")
    target_dir = create_directory_structure(owner, repo)
    if clone_repository(git_url, target_dir):
        return target_dir

    print("Failed to clone repository. Showing available projects:")
    for project in all_projects:
        print(f"  {project}")
    print("\nUsage: glon open <project>")
    print("Example: glon open tom-sapletta-com/xeen")
    return None


def _open_from_clipboard(arguments: Sequence[str], all_projects: Sequence[str]) -> bool:
    clipboard_content = _read_clipboard_text()
    if not clipboard_content:
        return False

    git_url = _extract_git_url_from_text(clipboard_content)
    if git_url is None:
        return False

    project_path = _clone_clipboard_project(git_url, all_projects)
    if project_path is not None:
        open_in_ide(str(project_path), _parse_ide_option(arguments))
    return True


def _open_recent_project(arguments: Sequence[str]) -> None:
    recent_projects = get_all_projects_with_time()[:RECENT_PROJECT_LIMIT]
    if not recent_projects:
        print("No projects found.")
        return

    print(f"\nRecent projects (last {len(recent_projects)}):")
    print("-" * SELECTION_LIST_WIDTH)
    _print_project_choices(recent_projects)
    print("-" * SELECTION_LIST_WIDTH)

    project = _prompt_for_project(
        recent_projects,
        f"Select project (1-{len(recent_projects)}) or press Enter to cancel: ",
        default_to_first=False,
    )
    if project is None:
        print("Canceled.")
        return
    open_in_ide(project, _parse_ide_option(arguments))


def _select_matching_project(
    project_name: str, projects: Sequence[ProjectInfo]
) -> Optional[str]:
    matches = [
        project
        for project in projects
        if project_name.lower() in project["name"].lower()
    ]
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]["name"]

    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    today_projects = [project for project in matches if project["mtime"] >= today]
    if today_projects:
        most_recent = max(today_projects, key=lambda project: project["mtime"])
        selected = most_recent["name"]
        print(f"Opening most recently modified (today): {selected}")
        return selected

    if any(project["mtime"] >= yesterday for project in matches):
        print(f"Projects matching '{project_name}':")
        print("-" * SELECTION_LIST_WIDTH)
        _print_project_choices(matches)
        print("-" * SELECTION_LIST_WIDTH)
        return _prompt_for_project(
            matches,
            f"Select project (1-{len(matches)}) or press Enter for first: ",
            default_to_first=True,
        )

    return matches[0]["name"]


def _build_open_parser(projects: Sequence[str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Open project in IDE", prog="glon open"
    )
    project_argument = parser.add_argument(
        "project", help="Project path (owner/repo or full path)"
    )
    if ARGCOMPLETE_AVAILABLE and projects:
        setattr(project_argument, "completer", ChoicesCompleter(projects))
    parser.add_argument(
        "--ide",
        choices=list(IDE_COMMANDS),
        help="IDE to use (pycharm, idea, vscode, webstorm, goland, rider)",
    )
    if ARGCOMPLETE_AVAILABLE:
        argcomplete.autocomplete(parser)
    return parser


def _handle_open(arguments: Sequence[str]) -> None:
    all_projects = get_all_projects()
    if not arguments or arguments[0].startswith("-"):
        if not _open_from_clipboard(arguments, all_projects):
            _open_recent_project(arguments)
        return

    project_name = arguments[0]
    candidate_path = Path(project_name)
    if os.path.isabs(project_name) or candidate_path.exists():
        full_path = candidate_path.resolve()
        if full_path.exists() and full_path.is_dir():
            open_in_ide(str(full_path), _parse_ide_option(arguments))
            return

    projects_with_time = get_all_projects_with_time()
    project_to_open = _select_matching_project(project_name, projects_with_time)
    if project_to_open is None:
        print(f"No projects found matching: {project_name}")
        print("\nAvailable projects:")
        for project in all_projects:
            print(f"  {project}")
        return

    options = _build_open_parser(all_projects).parse_args(arguments)
    open_in_ide(project_to_open, options.ide)


def _handle_list(arguments: Sequence[str]) -> None:
    parser = argparse.ArgumentParser(
        description="List all cloned projects", prog="glon list"
    )
    parser.add_argument("--base-path", help="Base path to search (default: ~/github)")
    parser.add_argument(
        "--last",
        choices=["today", "week", "month", "3months", "6months", "year"],
        help="Filter by time: today, week, month, 3months, 6months, year",
    )
    parser.add_argument(
        "filter",
        nargs="*",
        help="Time filter (e.g., 'last month', 'last week', 'today', '30' for days)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output with full paths"
    )
    parser.add_argument("--limit", type=int, help="Limit number of results")
    options = parser.parse_args(arguments)

    time_filter = None
    if options.last:
        time_filter = f"last {options.last}"
    elif options.filter:
        time_filter = " ".join(options.filter)

    list_projects(
        base_path=options.base_path,
        time_filter=time_filter,
        verbose=options.verbose,
        limit=options.limit,
    )


def _handle_grab(arguments: Sequence[str]) -> None:
    parser = argparse.ArgumentParser(
        description="Grab path from clipboard and process it", prog="glon grab"
    )
    parser.add_argument("--base-path", help="Base path for output (default: ~/github)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    options = parser.parse_args(arguments)
    grab_from_clipboard(
        base_path=options.base_path,
        dry_run=options.dry_run,
        verbose=options.verbose,
    )


def _build_clone_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Git Clone utility - Clone repositories to organized directory structure"
        ),
        prog="glon",
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Git repository URL (SSH or HTTPS). If omitted, use the clipboard.",
    )
    parser.add_argument("--base-path", help="Base path for cloning (default: ~/github)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually cloning",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser


def _handle_clone(arguments: Sequence[str]) -> None:
    options = _build_clone_parser().parse_args(arguments)
    url = options.url or _clipboard_url_candidate()
    if url is None:
        print(
            "Error: Missing git URL. Provide URL argument or copy a valid "
            "git URL to clipboard."
        )
        return

    if options.verbose:
        print(f"Parsing URL: {url}")

    parsed = parse_git_url(url)
    if parsed is None:
        print(f"Error: Invalid git URL format: {url}")
        print("Supported formats:")
        print("  SSH: git@github.com:owner/repo.git")
        print("  HTTPS: https://github.com/owner/repo.git")
        return

    owner, repo = parsed
    if options.verbose:
        print(f"Owner: {owner}, Repository: {repo}")

    target_dir = create_directory_structure(owner, repo, options.base_path)
    if options.verbose:
        print(f"Target directory: {target_dir}")

    if options.dry_run:
        print(f"Would clone {url} to {target_dir}")
        return

    if clone_repository(url, target_dir):
        print(f"Repository ready at: {target_dir}")


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Dispatch the requested CLI command."""
    arguments = list(sys.argv[1:] if argv is None else argv)

    if "open" in arguments:
        _handle_open([argument for argument in arguments if argument != "open"])
        return
    if "list" in arguments or "ls" in arguments:
        _handle_list(
            [argument for argument in arguments if argument not in ("list", "ls")]
        )
        return
    if "grab" in arguments:
        _handle_grab([argument for argument in arguments if argument != "grab"])
        return
    if arguments[:1] == ["clone"]:
        arguments = arguments[1:]

    _handle_clone(arguments)


if __name__ == "__main__":
    main()
