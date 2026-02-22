"""
CLI interface for glon package - Git Clone utility.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Optional, List
import re
from datetime import datetime, timedelta

# Try to import argcomplete for tab completion
try:
    import argcomplete
    from argcomplete.completers import ChoicesCompleter
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False


def get_all_projects(base_path: Optional[str] = None) -> List[str]:
    """
    Get all available projects in the base path.
    
    Args:
        base_path: Base path to search (default: ~/github)
        
    Returns:
        List of project paths in "owner/repo" format
    """
    if base_path is None:
        base_path = os.path.expanduser("~/github")
    
    base_path_obj = Path(base_path)
    projects = []
    
    if not base_path_obj.exists():
        return projects
    
    for owner_dir in base_path_obj.iterdir():
        if not owner_dir.is_dir():
            continue
        
        for repo_dir in owner_dir.iterdir():
            if not repo_dir.is_dir():
                continue
            
            # Add in "owner/repo" format
            projects.append(f"{owner_dir.name}/{repo_dir.name}")
    
    return sorted(projects)


def _read_clipboard_text() -> Optional[str]:
    try:
        import tkinter

        root = tkinter.Tk()
        root.withdraw()
        try:
            text = root.clipboard_get()
        finally:
            root.destroy()
        return text
    except Exception:
        pass

    for cmd in (
        ["wl-paste", "-n"],
        ["xclip", "-o", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--output"],
    ):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except Exception:
            continue

        text = (result.stdout or "").strip()
        if text:
            return text

    return None


def _clipboard_url_candidate(max_len: int = 200) -> Optional[str]:
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


def parse_git_url(url: str) -> Optional[tuple]:
    """
    Parse git URL and extract owner and repository name.
    
    Args:
        url: Git URL (SSH or HTTPS)
        
    Returns:
        Tuple of (owner, repo) or None if invalid
    """
    # SSH format: git@github.com:owner/repo.git
    ssh_pattern = r'git@[^:]+:([^/]+)/([^/]+)\.git$'
    ssh_match = re.match(ssh_pattern, url)
    if ssh_match:
        return ssh_match.group(1), ssh_match.group(2)
    
    # HTTPS format: https://github.com/owner/repo.git
    https_pattern = r'https://[^/]+/([^/]+)/([^/]+)\.git$'
    https_match = re.match(https_pattern, url)
    if https_match:
        return https_match.group(1), https_match.group(2)
    
    # HTTPS format without .git: https://github.com/owner/repo
    https_pattern_no_git = r'https://[^/]+/([^/]+)/([^/]+)$'
    https_match_no_git = re.match(https_pattern_no_git, url)
    if https_match_no_git:
        return https_match_no_git.group(1), https_match_no_git.group(2)
    
    return None


def create_directory_structure(owner: str, repo: str, base_path: Optional[str] = None) -> Path:
    """
    Create directory structure for the repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        base_path: Base path (defaults to ~/github)
        
    Returns:
        Path to created directory
    """
    if base_path is None:
        base_path = os.path.expanduser("~/github")
    
    target_dir = Path(base_path) / owner / repo
    target_dir.mkdir(parents=True, exist_ok=True)
    
    return target_dir


def clone_repository(url: str, target_dir: Path) -> bool:
    """
    Clone git repository to target directory.
    
    Args:
        url: Git URL to clone
        target_dir: Target directory for cloning
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if directory is empty
        if any(target_dir.iterdir()):
            print(f"Directory {target_dir} is not empty. Skipping clone.")
            return False
        
        # Clone the repository
        result = subprocess.run(
            ["git", "clone", url, str(target_dir)],
            capture_output=True,
            text=True,
            check=True
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


def grab_from_clipboard(base_path: Optional[str] = None, dry_run: bool = False, verbose: bool = False) -> bool:
    """
    Grab path from clipboard and process it.
    
    Reads from clipboard and determines if it's:
    - A git URL → clone it
    - A local path → copy/symlink to organized structure
    
    Args:
        base_path: Base path for cloning (default: ~/github)
        dry_run: Show what would be done without actually doing it
        verbose: Verbose output
        
    Returns:
        True if successful, False otherwise
    """
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
    
    # Check if it's a git URL
    parsed = parse_git_url(clipboard_text)
    if parsed:
        owner, repo = parsed
        if verbose:
            print(f"Detected git URL - Owner: {owner}, Repository: {repo}")
        
        target_dir = create_directory_structure(owner, repo, base_path)
        
        if verbose:
            print(f"Target directory: {target_dir}")
        
        if dry_run:
            print(f"Would clone {clipboard_text} to {target_dir}")
            return True
        
        success = clone_repository(clipboard_text, target_dir)
        
        if success:
            print(f"Repository ready at: {target_dir}")
            return True
        return False
    
    # It's a local path - check if it exists
    source_path = Path(clipboard_text)
    
    if not source_path.exists():
        print(f"Error: Path does not exist: {clipboard_text}")
        print("Note: Path must be a valid git URL or existing local directory.")
        return False
    
    if source_path.is_dir():
        # It's a directory - get the name
        dir_name = source_path.name
    else:
        # It's a file - get the name without extension
        dir_name = source_path.stem
    
    if verbose:
        print(f"Detected local path - Name: {dir_name}")
    
    # Create target directory in base_path
    if base_path is None:
        base_path = os.path.expanduser("~/github")
    
    target_dir = Path(base_path) / dir_name
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if verbose:
        print(f"Target directory: {target_dir}")
    
    if dry_run:
        print(f"Would copy/symlink {clipboard_text} to {target_dir}")
        return True
    
    # Check if target is empty
    if any(target_dir.iterdir()):
        print(f"Warning: Directory {target_dir} is not empty. Skipping.")
        return False
    
    try:
        # Create symlink instead of copying
        if source_path.is_dir():
            # For directories, create a symlink to the source
            link_path = target_dir / source_path.name
            if link_path.exists() or link_path.is_symlink():
                print(f"Symlink already exists at {link_path}")
            else:
                link_path.symlink_to(source_path.resolve())
                print(f"Created symlink: {link_path} -> {source_path}")
        else:
            # For files, copy them
            import shutil
            shutil.copy2(source_path, target_dir / source_path.name)
            print(f"Copied {source_path} to {target_dir}")
        
        print(f"Path ready at: {target_dir}")
        return True
        
    except Exception as e:
        print(f"Error processing path: {e}")
        return False


def parse_time_filter(filter_str: str) -> Optional[datetime]:
    """
    Parse time filter string like 'last month', 'last week', 'today'.
    
    Args:
        filter_str: Time filter string
        
    Returns:
        datetime object or None if invalid
    """
    filter_str = filter_str.lower().strip()
    now = datetime.now()
    
    if filter_str in ("today", "last day", "1 day"):
        return now - timedelta(days=1)
    elif filter_str in ("last week", "1 week", "week"):
        return now - timedelta(weeks=1)
    elif filter_str in ("last month", "1 month", "month"):
        return now - timedelta(days=30)
    elif filter_str in ("last 3 months", "3 months"):
        return now - timedelta(days=90)
    elif filter_str in ("last 6 months", "6 months"):
        return now - timedelta(days=180)
    elif filter_str in ("last year", "1 year", "year"):
        return now - timedelta(days=365)
    elif filter_str in ("all", "everything", "*"):
        return None
    
    return None


def list_projects(base_path: Optional[str] = None, time_filter: Optional[str] = None, verbose: bool = False, limit: Optional[int] = None) -> bool:
    """
    List all projects in the base path.
    
    Args:
        base_path: Base path to search (default: ~/github)
        time_filter: Filter by time (e.g., 'last month', 'last week', 'today')
        verbose: Verbose output
        limit: Limit number of results
        
    Returns:
        True if successful, False otherwise
    """
    if base_path is None:
        base_path = os.path.expanduser("~/github")
    
    base_path_obj = Path(base_path)
    
    if not base_path_obj.exists():
        print(f"Error: Base path does not exist: {base_path}")
        return False
    
    # Parse time filter
    filter_date = None
    if time_filter:
        filter_date = parse_time_filter(time_filter)
        if time_filter and filter_date is None and time_filter not in ("all", "everything", "*"):
            # Check if it's a number (e.g., "30" for 30 days)
            try:
                days = int(time_filter)
                filter_date = now = datetime.now() - timedelta(days=days)
            except ValueError:
                print(f"Warning: Unknown time filter '{time_filter}', showing all projects")
    
    # Collect all projects
    projects = []
    
    for owner_dir in base_path_obj.iterdir():
        if not owner_dir.is_dir():
            continue
        
        for repo_dir in owner_dir.iterdir():
            if not repo_dir.is_dir():
                continue
            
            # Get modification time
            mtime = datetime.fromtimestamp(repo_dir.stat().st_mtime)
            
            # Apply time filter
            if filter_date and mtime < filter_date:
                continue
            
            projects.append({
                "path": repo_dir,
                "owner": owner_dir.name,
                "repo": repo_dir.name,
                "mtime": mtime
            })
    
    if not projects:
        print(f"No projects found in {base_path}")
        if time_filter:
            print(f"  (No projects modified {time_filter})")
        return True
    
    # Sort by modification time (newest first)
    projects.sort(key=lambda x: x["mtime"], reverse=True)
    
    # Apply limit
    total_count = len(projects)
    if limit:
        projects = projects[:limit]
    
    # Print header
    print(f"\nFound {total_count} project(s) in {base_path}")
    if time_filter:
        print(f"Filtered by: {time_filter}")
    if limit:
        print(f"Showing {len(projects)} result(s)")
    print("-" * 80)
    
    # Print projects
    for project in projects:
        path = project["path"]
        owner = project["owner"]
        repo = project["repo"]
        mtime = project["mtime"]
        
        # Format date
        date_str = mtime.strftime("%Y-%m-%d %H:%M")
        
        # Check if it's a git repository
        is_git = (path / ".git").exists()
        
        if verbose:
            print(f"{owner}/{repo}")
            print(f"  Path: {path}")
            print(f"  Modified: {date_str}")
            print(f"  Git: {'Yes' if is_git else 'No'}")
            print()
        else:
            git_marker = "✓" if is_git else "✗"
            print(f"{date_str} {git_marker} {owner}/{repo}")
    
    return True


def open_in_ide(project_path: str, ide: str = "pycharm") -> bool:
    """
    Open a project in an IDE.
    
    Args:
        project_path: Path to project (e.g., "owner/repo" or full path)
        ide: IDE to use (default: pycharm)
        
    Returns:
        True if successful, False otherwise
    """
    # Check if it's in "owner/repo" format
    if "/" in project_path and not os.path.isabs(project_path):
        # It's in owner/repo format, convert to full path
        parts = project_path.split("/")
        if len(parts) == 2:
            owner, repo = parts
            base_path = os.path.expanduser("~/github")
            full_path = Path(base_path) / owner / repo
        else:
            print(f"Error: Invalid project path format: {project_path}")
            return False
    else:
        # It's a full path
        full_path = Path(project_path)
    
    # Expand user path
    full_path = Path(os.path.expanduser(full_path))
    
    # Check if path exists
    if not full_path.exists():
        print(f"Error: Project path does not exist: {full_path}")
        return False
    
    if not full_path.is_dir():
        print(f"Error: Project path is not a directory: {full_path}")
        return False
    
    # Try to open in the IDE
    ide_commands = {
        "pycharm": ["pycharm", str(full_path)],
        "idea": ["idea", str(full_path)],
        "vscode": ["code", str(full_path)],
        "code": ["code", str(full_path)],
        "webstorm": ["webstorm", str(full_path)],
        "goland": ["goland", str(full_path)],
        "rider": ["rider", str(full_path)],
    }
    
    cmd = ide_commands.get(ide.lower())
    if cmd is None:
        print(f"Error: Unknown IDE: {ide}")
        print(f"Supported IDEs: {', '.join(ide_commands.keys())}")
        return False
    
    try:
        subprocess.Popen(cmd)
        print(f"Opened {full_path} in {ide}")
        return True
    except FileNotFoundError:
        print(f"Error: {ide} is not installed or not in PATH")
        return False
    except Exception as e:
        print(f"Error opening project: {e}")
        return False


def main():
    """Main CLI entry point."""
    # Check if open command is being used
    if "open" in sys.argv:
        # Filter out 'open' from sys.argv
        open_args = [arg for arg in sys.argv[1:] if arg != "open"]
        
        parser = argparse.ArgumentParser(
            description="Open project in IDE",
            prog="glon open"
        )
        
        # Get all projects for autocomplete
        all_projects = get_all_projects()
        
        # Add project argument with choices for autocomplete
        project_arg = parser.add_argument(
            "project",
            help="Project path (owner/repo or full path)"
        )
        
        # If argcomplete is available and we have projects, set up autocomplete
        if ARGCOMPLETE_AVAILABLE and all_projects:
            project_arg.completer = ChoicesCompleter(all_projects)
        
        parser.add_argument(
            "--ide",
            default="pycharm",
            choices=["pycharm", "idea", "vscode", "code", "webstorm", "goland", "rider"],
            help="IDE to use (pycharm, idea, vscode, webstorm, goland, rider)"
        )
        
        # If argcomplete is available, activate it
        if ARGCOMPLETE_AVAILABLE:
            argcomplete.autocomplete(parser)
        
        args = parser.parse_args(open_args)
        
        open_in_ide(args.project, args.ide)
        return
    
    # Check if list command is being used (could be "list", "ls", or "glon list", "glon ls")
    if "list" in sys.argv or "ls" in sys.argv:
        # Filter out 'list' or 'ls' from sys.argv for the list parser
        list_args = [arg for arg in sys.argv[1:] if arg not in ("list", "ls")]
        
        # Simple parser for list command
        parser = argparse.ArgumentParser(
            description="List all cloned projects",
            prog="glon list"
        )
        parser.add_argument(
            "--base-path",
            help="Base path to search (default: ~/github)",
            default=None
        )
        parser.add_argument(
            "--last",
            dest="last",
            choices=["today", "week", "month", "3months", "6months", "year"],
            help="Filter by time: today, week, month, 3months, 6months, year"
        )
        parser.add_argument(
            "filter",
            nargs="*",
            default=None,
            help="Time filter (e.g., 'last month', 'last week', 'today', '30' for days)"
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Verbose output with full paths"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of results"
        )
        args = parser.parse_args(list_args)
        
        # Use --last if provided, otherwise use positional filter
        time_filter = None
        if args.last:
            time_filter = f"last {args.last}"
        elif args.filter:
            # Join filter words back together (e.g., "last week" -> "last week")
            time_filter = " ".join(args.filter)
        
        list_projects(
            base_path=args.base_path,
            time_filter=time_filter,
            verbose=args.verbose,
            limit=args.limit
        )
        return
    
    # Check if grab command is being used (could be "grab" or "glon grab")
    if "grab" in sys.argv:
        # Filter out 'grab' from sys.argv for the grab parser
        grab_args = [arg for arg in sys.argv[1:] if arg != "grab"]
        
        # Simple parser for grab command
        parser = argparse.ArgumentParser(
            description="Grab path from clipboard and process it",
            prog="glon grab"
        )
        parser.add_argument(
            "--base-path",
            help="Base path for output (default: ~/github)",
            default=None
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually doing it"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Verbose output"
        )
        args = parser.parse_args(grab_args)
        
        success = grab_from_clipboard(
            base_path=args.base_path,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        return
    
    # Check if clone subcommand is being used
    use_clone_subcommand = len(sys.argv) > 1 and sys.argv[1] == "clone"
    
    # Create main parser with URL as positional argument for backward compatibility
    parser = argparse.ArgumentParser(
        description="Git Clone utility - Clone repositories to organized directory structure",
        prog="glon"
    )
    
    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="Git repository URL (SSH or HTTPS). If omitted, will try to use clipboard."
    )
    
    parser.add_argument(
        "--base-path",
        help="Base path for cloning (default: ~/github)",
        default=None
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually cloning"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # If clone subcommand was used, remove it from args handling
    if use_clone_subcommand:
        # The URL would be in sys.argv[2] if provided
        if args.url is None and len(sys.argv) > 2:
            args.url = sys.argv[2]
    
    if args.url is None:
        args.url = _clipboard_url_candidate()
        if args.url is None:
            print("Error: Missing git URL. Provide URL argument or copy a valid git URL to clipboard.")
            return
    
    # Parse the URL
    if args.verbose:
        print(f"Parsing URL: {args.url}")
    
    parsed = parse_git_url(args.url)
    if not parsed:
        print(f"Error: Invalid git URL format: {args.url}")
        print("Supported formats:")
        print("  SSH: git@github.com:owner/repo.git")
        print("  HTTPS: https://github.com/owner/repo.git")
        return
    
    owner, repo = parsed
    
    if args.verbose:
        print(f"Owner: {owner}, Repository: {repo}")
    
    # Create directory structure
    target_dir = create_directory_structure(owner, repo, args.base_path)
    
    if args.verbose:
        print(f"Target directory: {target_dir}")
    
    if args.dry_run:
        print(f"Would clone {args.url} to {target_dir}")
        return
    
    # Clone the repository
    success = clone_repository(args.url, target_dir)
    
    if not success:
        return
    
    print(f"Repository ready at: {target_dir}")


if __name__ == "__main__":
    main()
