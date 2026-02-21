"""
CLI interface for glon package - Git Clone utility.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Optional
import re


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


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Git Clone utility - Clone repositories to organized directory structure",
        prog="glon"
    )
    
    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="Git repository URL (SSH or HTTPS). If omitted, glon will try to use clipboard."
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
