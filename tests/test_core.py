"""
Tests for core garbage collection functionality.
"""

import pytest
import gc
import time
from glon.core import GarbageCollector, MemoryProfiler


class TestGarbageCollector:
    """Test cases for GarbageCollector class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.gc = GarbageCollector()
    
    def test_initialization(self):
        """Test GarbageCollector initialization."""
        assert self.gc.enabled == gc.isenabled()
        assert isinstance(self.gc.stats_history, list)
    
    def test_enable_disable(self):
        """Test enabling and disabling garbage collection."""
        original_state = gc.isenabled()
        
        self.gc.enable()
        assert gc.isenabled() is True
        assert self.gc.enabled is True
        
        self.gc.disable()
        assert gc.isenabled() is False
        assert self.gc.enabled is False
        
        # Restore original state
        if original_state:
            gc.enable()
    
    def test_collect(self):
        """Test garbage collection."""
        # Create some objects to collect
        objects = [[] for _ in range(100)]
        
        collected = self.gc.collect()
        assert isinstance(collected, int)
        assert collected >= 0
        
        # Check that stats were recorded
        assert len(self.gc.stats_history) > 0
    
    def test_get_stats(self):
        """Test getting garbage collection statistics."""
        stats = self.gc.get_stats()
        assert isinstance(stats, list)
        assert len(stats) == 3  # Three generations
    
    def test_get_count(self):
        """Test getting garbage collection counts."""
        counts = self.gc.get_count()
        assert isinstance(counts, tuple)
        assert len(counts) == 3  # Three generations
    
    def test_set_threshold(self):
        """Test setting garbage collection threshold."""
        original_threshold = gc.get_threshold()
        
        self.gc.set_threshold((700, 10, 10))
        assert gc.get_threshold() == (700, 10, 10)
        
        # Restore original threshold
        gc.set_threshold(*original_threshold)
    
    def test_get_objects(self):
        """Test getting tracked objects."""
        objects = self.gc.get_objects()
        assert isinstance(objects, list)
        assert len(objects) > 0
    
    def test_get_memory_summary(self):
        """Test getting memory summary."""
        summary = self.gc.get_memory_summary()
        
        required_keys = ['enabled', 'counts', 'stats', 'objects_tracked', 'threshold']
        for key in required_keys:
            assert key in summary
        
        assert isinstance(summary['enabled'], bool)
        assert isinstance(summary['counts'], tuple)
        assert isinstance(summary['stats'], list)
        assert isinstance(summary['objects_tracked'], int)
        assert isinstance(summary['threshold'], tuple)


class TestMemoryProfiler:
    """Test cases for MemoryProfiler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.profiler = MemoryProfiler()
    
    def test_initialization(self):
        """Test MemoryProfiler initialization."""
        assert isinstance(self.profiler.snapshots, list)
        assert isinstance(self.profiler.weak_refs, dict)
    
    def test_take_snapshot(self):
        """Test taking memory snapshots."""
        snapshot = self.profiler.take_snapshot("test")
        
        required_keys = ['label', 'timestamp', 'rss', 'vms', 'objects_count', 'gc_counts']
        for key in required_keys:
            assert key in snapshot
        
        assert snapshot['label'] == "test"
        assert isinstance(snapshot['timestamp'], float)
        assert isinstance(snapshot['rss'], int)
        assert isinstance(snapshot['vms'], int)
        assert isinstance(snapshot['objects_count'], int)
        assert isinstance(snapshot['gc_counts'], tuple)
        
        # Check that snapshot was stored
        assert len(self.profiler.snapshots) == 1
    
    def test_track_object(self):
        """Test object tracking."""
        class TestObject:
            pass
        
        test_obj = TestObject()  # Use custom class for weak reference
        tracking_id = self.profiler.track_object(test_obj, "test_object")
        
        assert tracking_id in self.profiler.weak_refs
        assert self.profiler.weak_refs[tracking_id]['label'] == "test_object"
        assert self.profiler.weak_refs[tracking_id]['type'] == "TestObject"
    
    def test_get_tracked_objects(self):
        """Test getting tracked objects information."""
        class TestObject:
            pass
        
        test_obj = TestObject()  # Use custom class for weak reference
        tracking_id = self.profiler.track_object(test_obj, "test_object")
        
        tracked = self.profiler.get_tracked_objects()
        assert tracking_id in tracked
        assert tracked[tracking_id]['alive'] is True
        assert tracked[tracking_id]['label'] == "test_object"
        
        # Delete object and check it's marked as not alive
        del test_obj
        gc.collect()
        
        tracked = self.profiler.get_tracked_objects()
        assert tracking_id in tracked
        assert tracked[tracking_id]['alive'] is False
    
    def test_compare_snapshots(self):
        """Test comparing snapshots."""
        # Take two snapshots
        self.profiler.take_snapshot("before")
        time.sleep(0.1)  # Small delay
        self.profiler.take_snapshot("after")
        
        comparison = self.profiler.compare_snapshots(0, 1)
        
        required_keys = ['time_diff', 'rss_diff', 'vms_diff', 'objects_diff', 'label1', 'label2']
        for key in required_keys:
            assert key in comparison
        
        assert comparison['label1'] == "before"
        assert comparison['label2'] == "after"
        assert comparison['time_diff'] > 0
    
    def test_compare_snapshots_invalid_index(self):
        """Test comparing snapshots with invalid indices."""
        with pytest.raises(IndexError):
            self.profiler.compare_snapshots(0, 1)
    
    def test_clear_snapshots(self):
        """Test clearing snapshots."""
        self.profiler.take_snapshot("test")
        assert len(self.profiler.snapshots) == 1
        
        self.profiler.clear_snapshots()
        assert len(self.profiler.snapshots) == 0
    
    def test_clear_tracking(self):
        """Test clearing tracked objects."""
        class TestObject:
            pass
        
        test_obj = TestObject()  # Use custom class for weak reference
        self.profiler.track_object(test_obj, "test")
        assert len(self.profiler.weak_refs) == 1
        
        self.profiler.clear_tracking()
        assert len(self.profiler.weak_refs) == 0
