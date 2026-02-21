# glon

Python package for garbage collection utilities and memory management.

## Overview

The `glon` package provides comprehensive tools and utilities for working with Python's garbage collector, memory profiling, and cleanup operations. It offers enhanced garbage collection control, memory monitoring, and debugging capabilities.

## Features

- **Enhanced Garbage Collection**: Control and monitor Python's garbage collector with detailed statistics
- **Memory Profiling**: Track memory usage over time and analyze memory patterns
- **Object Tracking**: Monitor specific objects using weak references
- **Reference Cycle Detection**: Find and analyze reference cycles in your code
- **Memory Analysis**: Comprehensive memory usage analysis and reporting
- **Utility Functions**: Common garbage collection and memory management tasks

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

### Basic Garbage Collection Control

```python
from glon import GarbageCollector

# Create a garbage collector instance
gc_manager = GarbageCollector()

# Force garbage collection
collected = gc_manager.collect()
print(f"Collected {collected} objects")

# Get memory summary
summary = gc_manager.get_memory_summary()
print(summary)
```

### Memory Profiling

```python
from glon import MemoryProfiler

# Create a profiler instance
profiler = MemoryProfiler()

# Take a memory snapshot
profiler.take_snapshot("before_operation")

# Your code here...
data = [list(range(1000)) for _ in range(100)]

# Take another snapshot
profiler.take_snapshot("after_operation")

# Compare snapshots
comparison = profiler.compare_snapshots(0, 1)
print(f"Memory change: {comparison['rss_diff']} bytes")
```

### Memory Monitoring

```python
from glon.utils import monitor_memory_usage

# Monitor memory for 60 seconds
samples = monitor_memory_usage(duration=60, interval=1.0)

for sample in samples:
    print(f"Memory: {sample['rss']} bytes, Objects: {sample['objects_count']}")
```

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
