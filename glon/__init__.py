"""
glon - Python package for garbage collection utilities and memory management.

This package provides tools and utilities for working with Python's garbage collector,
memory profiling, and cleanup operations.
"""

__version__ = "0.1.15"
__author__ = "Tom Sapletta"
__email__ = "tom@example.com"

from .core import GarbageCollector, MemoryProfiler
from .utils import cleanup_temp_files, monitor_memory_usage

__all__ = [
    "GarbageCollector",
    "MemoryProfiler", 
    "cleanup_temp_files",
    "monitor_memory_usage",
]
