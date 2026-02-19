"""
Utility functions for garbage collection and memory management.
"""

import gc
import os
import tempfile
import shutil
import time
import sys
from typing import List, Dict, Any, Optional, Callable
import logging

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


def cleanup_temp_files(pattern: str = "*") -> int:
    """
    Clean up temporary files matching a pattern.
    
    Args:
        pattern: File pattern to match (default: "*")
        
    Returns:
        Number of files cleaned up
    """
    temp_dir = tempfile.gettempdir()
    cleaned_count = 0
    
    try:
        for filename in os.listdir(temp_dir):
            if pattern == "*" or pattern in filename:
                file_path = os.path.join(temp_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned_count += 1
                except (PermissionError, OSError):
                    # Skip files we can't remove
                    continue
    except (PermissionError, OSError):
        pass
    
    return cleaned_count


def monitor_memory_usage(duration: int = 60, interval: float = 1.0) -> List[Dict[str, Any]]:
    """
    Monitor memory usage over time.
    
    Args:
        duration: Monitoring duration in seconds
        interval: Sampling interval in seconds
        
    Returns:
        List of memory usage samples
    """
    if psutil is None or sys.modules.get('psutil') is None:
        raise ImportError("psutil is required for memory monitoring. Install with: pip install psutil")
    
    process = psutil.Process(psutil.os.getpid())
    samples = []
    start_time = time.time()
    
    while time.time() - start_time < duration:
        memory_info = process.memory_info()
        sample = {
            'timestamp': time.time(),
            'rss': memory_info.rss,
            'vms': memory_info.vms,
            'percent': process.memory_percent(),
            'objects_count': len(gc.get_objects()),
            'gc_counts': gc.get_count()
        }
        samples.append(sample)
        time.sleep(interval)
    
    return samples


def force_garbage_collection(verbose: bool = False) -> Dict[str, int]:
    """
    Force garbage collection on all generations.
    
    Args:
        verbose: If True, print detailed information
        
    Returns:
        Dictionary with collection results per generation
    """
    results = {}
    
    for generation in range(3):
        before_count = len(gc.get_objects())
        collected = gc.collect(generation)
        after_count = len(gc.get_objects())
        
        results[f'gen_{generation}'] = {
            'collected': collected,
            'before_count': before_count,
            'after_count': after_count,
            'net_change': after_count - before_count
        }
        
        if verbose:
            print(f"Generation {generation}: Collected {collected} objects, "
                  f"Net change: {after_count - before_count}")
    
    return results


def find_object_cycles(obj: Any, max_depth: int = 10) -> List[List[Any]]:
    """
    Find reference cycles involving the given object.
    
    Args:
        obj: Object to analyze
        max_depth: Maximum search depth
        
    Returns:
        List of reference cycles found
    """
    cycles = []
    visited = set()
    path = []
    
    def _find_cycles(current_obj, depth):
        if depth > max_depth:
            return
        
        obj_id = id(current_obj)
        if obj_id in visited:
            if current_obj in path:
                # Found a cycle
                cycle_start = path.index(current_obj)
                cycles.append(path[cycle_start:] + [current_obj])
            return
        
        visited.add(obj_id)
        path.append(current_obj)
        
        try:
            referents = gc.get_referents(current_obj)
            for ref in referents:
                _find_cycles(ref, depth + 1)
        except:
            # Skip objects that can't be analyzed
            pass
        
        path.pop()
        visited.remove(obj_id)
    
    _find_cycles(obj, 0)
    return cycles


def get_object_size(obj: Any) -> int:
    """
    Get approximate size of an object in bytes.
    
    Args:
        obj: Object to measure
        
    Returns:
        Approximate size in bytes
    """
    try:
        import sys
        return sys.getsizeof(obj)
    except:
        return 0


def analyze_memory_usage() -> Dict[str, Any]:
    """
    Analyze current memory usage and provide statistics.
    
    Returns:
        Dictionary with memory analysis
    """
    if psutil is None or sys.modules.get('psutil') is None:
        raise ImportError("psutil is required for memory analysis. Install with: pip install psutil")
    
    process = psutil.Process(psutil.os.getpid())
    memory_info = process.memory_info()
    
    # Analyze object types
    all_objects = gc.get_objects()
    type_counts = {}
    for obj in all_objects:
        obj_type = type(obj).__name__
        type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
    
    # Get top 10 most common types
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'timestamp': time.time(),
        'memory': {
            'rss': memory_info.rss,
            'vms': memory_info.vms,
            'percent': process.memory_percent()
        },
        'gc': {
            'enabled': gc.isenabled(),
            'counts': gc.get_count(),
            'threshold': gc.get_threshold(),
            'stats': gc.get_stats()
        },
        'objects': {
            'total_count': len(all_objects),
            'top_types': sorted_types
        }
    }


def set_debug_gc(flags: int = gc.DEBUG_STATS) -> None:
    """
    Set garbage collection debug flags.
    
    Args:
        flags: Debug flags (gc.DEBUG_STATS, gc.DEBUG_LEAK, etc.)
    """
    gc.set_debug(flags)


def clear_gc_debug() -> None:
    """Clear garbage collection debug flags."""
    gc.set_debug(0)


def create_memory_logger(log_file: str = "gc_memory.log") -> logging.Logger:
    """
    Create a logger for memory-related events.
    
    Args:
        log_file: Log file path
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("gc_memory")
    logger.setLevel(logging.INFO)
    
    # Create file handler
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger
