# glon

Git Clone utility - Clone repositories to organized directory structure.

## Overview

The `glon` package provides a convenient CLI tool for cloning git repositories to an organized directory structure, as well as listing and managing your cloned projects.

## Features

- **Easy Cloning**: Clone git repositories with a single command
- **Clipboard Integration**: Clone directly from clipboard URLs
- **Smart Opening**: Open projects with clipboard auto-detection and auto-cloning
- **Grab from Clipboard**: Grab paths from clipboard (git URLs or local paths)
- **List Projects**: List all cloned projects with time-based filtering
- **Open in IDE**: Open projects directly in PyCharm, VSCode, and other IDEs
- **Organized Structure**: Projects organized by owner/repo structure

## Installation

```bash
pip install glon
```

### Development Installation

```bash
git clone https://github.com/tom-sapletta/glon.git
cd glon
pip install -e ".[dev]"
```

## Quick Start

### Clone a Repository

```bash
# Clone using git URL
glon https://github.com/owner/repo.git

# Or clone from clipboard (copies URL to clipboard first)
glon
```

### Smart Open (Clipboard-Prioritized)

```bash
# Smart open - checks clipboard first, auto-clones if needed
glon open

# Copy a git URL to clipboard, then:
glon open                    # Auto-detects and opens the project
```

### Grab from Clipboard

The `grab` command reads a path from clipboard and processes it:

```bash
# Grab from clipboard - detects if it's a git URL or local path
glon grab

# With options
glon grab --base-path ~/projects
glon grab --dry-run
glon grab --verbose
```

### List Projects

List all cloned projects in your base directory:

```bash
# List all projects
glon list
glon ls

# Filter by time
glon list "last week"
glon list "last month"
glon list "last year"
glon list 30  # last 30 days

# Verbose output with full paths
glon list --verbose
glon ls -v
```

## CLI Commands

### Clone

Clone a git repository to the organized directory structure (default: ~/github):

```bash
glon <git-url>              # Clone from URL
glon clone <git-url>        # Same as above (explicit)
glon --dry-run <url>        # Show what would be done
glon --base-path ~/my-projects <url>  # Custom base path
```

### Grab

Grab a path from clipboard:

```bash
glon grab                   # Read from clipboard and process
glon grab --verbose         # Show detailed output
glon grab --dry-run         # Preview without executing
glon grab --base-path ~/my-projects  # Custom output path
```

### List (or LS)

List all cloned projects:

```bash
glon list                   # List all projects
glon ls                     # Short alias
glon list "last week"       # Projects modified last week
glon list "last month"      # Projects modified last month
glon list "last year"       # Projects modified last year
glon list 30                # Projects modified last 30 days
glon list --verbose         # Show full paths and details
glon ls -v                  # Verbose output
glon list --base-path ~/my-projects  # Custom base path
```

### Open

Open a project in your IDE (PyCharm, VSCode, etc.):

```bash
# Open with clipboard priority - checks clipboard first for git URLs
glon open                    # Auto-detect from clipboard, or show project list

# Open specific project
glon open owner/repo        # Open in PyCharm (default)
glon open owner/repo --ide vscode    # Open in VS Code
glon open /full/path/to/project     # Open with full path
glon open ~/github/owner/repo       # Open with expanded path

# Open with different IDE
glon open --ide vscode              # Open clipboard-detected project in VS Code
glon open --ide idea                # Open in IntelliJ IDEA
glon open --ide webstorm            # Open in WebStorm
glon open --ide goland              # Open in GoLand
glon open --ide rider               # Open in Rider
```

**Clipboard-Prioritized Opening**: When `glon open` is called without arguments, it:
1. First checks clipboard for git URLs (SSH or HTTPS format)
2. If a git URL is found and the project exists locally, opens it immediately
3. If the project doesn't exist, clones it first then opens it
4. If no valid git URL is found, shows the available projects list

## API Reference

### GarbageCollector

Main class for garbage collection control and monitoring.

#### Methods

- `enable()` - Enable garbage collection
- `disable()` - Disable garbage collection
- `collect(generation=2)` - Force garbage collection
- `get_stats()` - Get garbage collection statistics
- `get_memory_summary()` - Get comprehensive memory summary

### MemoryProfiler

Class for memory profiling and object tracking.

#### Methods

- `take_snapshot(label="")` - Take a memory snapshot
- `track_object(obj, label="")` - Track an object with weak reference
- `compare_snapshots(index1, index2)` - Compare two memory snapshots
- `get_tracked_objects()` - Get information about tracked objects

### Utility Functions

- `cleanup_temp_files(pattern="*")` - Clean up temporary files
- `monitor_memory_usage(duration=60, interval=1.0)` - Monitor memory usage
- `force_garbage_collection(verbose=False)` - Force garbage collection on all generations
- `find_object_cycles(obj, max_depth=10)` - Find reference cycles
- `analyze_memory_usage()` - Comprehensive memory analysis

## Requirements

- Python 3.8+
- psutil>=5.8.0

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black glon/
```

### Type Checking

```bash
mypy glon/
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read the CONTRIBUTING.md file for details on our code of conduct and the process for submitting pull requests.

## Changelog

### 0.1.0

- Initial release
- Basic garbage collection control
- Memory profiling capabilities
- Utility functions for memory management

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Author

Created by **Tom Sapletta** - [tom@sapletta.com](mailto:tom@sapletta.com)
