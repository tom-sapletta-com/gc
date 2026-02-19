"""
Core garbage collection and memory management functionality.
"""

import gc
import sys
import time
from typing import Dict, List, Optional, Any
import weakref


class GarbageCollector:
    """Enhanced garbage collector with monitoring and control features."""
    
    def __init__(self):
        self.stats_history = []
        self.enabled = gc.isenabled()
    
    def enable(self) -> None:
        """Enable garbage collection."""
        gc.enable()
        self.enabled = True
    
    def disable(self) -> None:
        """Disable garbage collection."""
        gc.disable()
        self.enabled = False
    
    def collect(self, generation: int = 2) -> int:
        """
        Force garbage collection for a specific generation.
        
        Args:
            generation: Generation number (0, 1, or 2)
            
        Returns:
            Number of objects collected
        """
        collected = gc.collect()
        self._record_stats()
        return collected
    
    def get_stats(self) -> List[Dict[str, int]]:
        """Get current garbage collection statistics."""
        return gc.get_stats()
    
    def get_count(self) -> tuple:
        """Get current garbage collection counts."""
        return gc.get_count()
    
    def set_threshold(self, threshold: tuple) -> None:
        """Set garbage collection threshold."""
        gc.set_threshold(*threshold)
    
    def get_objects(self) -> List[Any]:
        """Get all objects currently tracked by the garbage collector."""
        return gc.get_objects()
    
    def get_referrers(self, obj: Any) -> List[Any]:
        """Get all objects that refer to the given object."""
        return gc.get_referrers(obj)
    
    def get_referents(self, obj: Any) -> List[Any]:
        """Get all objects referred to by the given object."""
        return gc.get_referents(obj)
    
    def _record_stats(self) -> None:
        """Record current statistics for monitoring."""
        stats = {
            'timestamp': time.time(),
            'counts': self.get_count(),
            'stats': self.get_stats(),
            'objects_count': len(self.get_objects())
        }
        self.stats_history.append(stats)
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of memory usage and garbage collection status."""
        return {
            'enabled': self.enabled,
            'counts': self.get_count(),
            'stats': self.get_stats(),
            'objects_tracked': len(self.get_objects()),
            'threshold': gc.get_threshold()
        }


class MemoryProfiler:
    """Memory profiling and monitoring utilities."""
    
    def __init__(self):
        self.snapshots = []
        self.weak_refs = {}
    
    def take_snapshot(self, label: str = "") -> Dict[str, Any]:
        """
        Take a memory snapshot.
        
        Args:
            label: Optional label for the snapshot
            
        Returns:
            Dictionary containing snapshot data
        """
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            snapshot = {
                'label': label,
                'timestamp': time.time(),
                'rss': memory_info.rss,  # Resident Set Size
                'vms': memory_info.vms,  # Virtual Memory Size
                'objects_count': len(gc.get_objects()),
                'gc_counts': gc.get_count()
            }
        except ImportError:
            # Fallback when psutil is not available
            snapshot = {
                'label': label,
                'timestamp': time.time(),
                'rss': 0,
                'vms': 0,
                'objects_count': len(gc.get_objects()),
                'gc_counts': gc.get_count()
            }
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def track_object(self, obj: Any, label: str = "") -> str:
        """
        Track an object using weak reference.
        
        Args:
            obj: Object to track
            label: Optional label for the object
            
        Returns:
            Tracking ID
        """
        obj_id = str(id(obj))
        try:
            ref = weakref.ref(obj)
            ref_type = 'weak'
        except TypeError:
            ref = obj
            ref_type = 'strong'

        self.weak_refs[obj_id] = {
            'ref': ref,
            'ref_type': ref_type,
            'label': label,
            'type': type(obj).__name__,
            'created': time.time()
        }
        return obj_id
    
    def get_tracked_objects(self) -> Dict[str, Any]:
        """Get information about tracked objects."""
        alive = {}
        for obj_id, info in self.weak_refs.items():
            if info.get('ref_type') == 'weak':
                obj = info['ref']()
            else:
                obj = info.get('ref')
            if obj is not None:
                alive[obj_id] = {
                    'label': info['label'],
                    'type': info['type'],
                    'created': info['created'],
                    'alive': True
                }
            else:
                alive[obj_id] = {
                    'label': info['label'],
                    'type': info['type'],
                    'created': info['created'],
                    'alive': False
                }
        return alive
    
    def compare_snapshots(self, index1: int, index2: int) -> Dict[str, Any]:
        """
        Compare two memory snapshots.
        
        Args:
            index1: Index of first snapshot
            index2: Index of second snapshot
            
        Returns:
            Comparison data
        """
        if index1 >= len(self.snapshots) or index2 >= len(self.snapshots):
            raise IndexError("Snapshot index out of range")
        
        snap1 = self.snapshots[index1]
        snap2 = self.snapshots[index2]
        
        return {
            'time_diff': snap2['timestamp'] - snap1['timestamp'],
            'rss_diff': snap2['rss'] - snap1['rss'],
            'vms_diff': snap2['vms'] - snap1['vms'],
            'objects_diff': snap2['objects_count'] - snap1['objects_count'],
            'label1': snap1.get('label', f'Snapshot {index1}'),
            'label2': snap2.get('label', f'Snapshot {index2}')
        }
    
    def clear_snapshots(self) -> None:
        """Clear all stored snapshots."""
        self.snapshots.clear()
    
    def clear_tracking(self) -> None:
        """Clear all tracked objects."""
        self.weak_refs.clear()
