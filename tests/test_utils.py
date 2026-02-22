"""
Tests for utility functions.
"""

import pytest
import gc
import tempfile
import os
from unittest.mock import patch, MagicMock
from glon.utils import (
    cleanup_temp_files,
    monitor_memory_usage,
    force_garbage_collection,
    find_object_cycles,
    get_object_size,
    analyze_memory_usage,
    set_debug_gc,
    clear_gc_debug,
    create_memory_logger
)


class TestCleanupTempFiles:
    """Test cases for cleanup_temp_files function."""
    
    def test_cleanup_temp_files(self):
        """Test cleaning up temporary files."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")
        
        # Verify file exists
        assert os.path.exists(temp_path)
        
        # Clean up temp files
        cleaned_count = cleanup_temp_files(os.path.basename(temp_path))
        
        # File should be cleaned up
        assert not os.path.exists(temp_path)
        assert cleaned_count >= 1
    
    def test_cleanup_temp_files_pattern(self):
        """Test cleaning up temporary files with pattern."""
        # Create multiple temporary files with same pattern
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(
                delete=False, 
                prefix=f"test_pattern_{i}_"
            ) as temp_file:
                temp_path = temp_file.name
                temp_file.write(b"test content")
                temp_files.append(temp_path)
        
        # Clean up files with pattern
        cleaned_count = cleanup_temp_files("test_pattern")
        
        # All files should be cleaned up
        for temp_path in temp_files:
            assert not os.path.exists(temp_path)
        
        assert cleaned_count == 3


class TestMonitorMemoryUsage:
    """Test cases for monitor_memory_usage function."""
    
    @patch('glon.utils.psutil')
    def test_monitor_memory_usage(self, mock_psutil):
        """Test memory usage monitoring."""
        # Mock psutil.Process
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1000000, vms=2000000)
        mock_process.memory_percent.return_value = 50.0
        mock_psutil.Process.return_value = mock_process
        mock_psutil.os.getpid.return_value = 1234
        
        # Mock time.sleep to avoid actual delay
        with patch('glon.utils.time.sleep'):
            samples = monitor_memory_usage(duration=2, interval=0.1)
        
        assert len(samples) >= 20  # Should have at least 20 samples
        assert all('timestamp' in sample for sample in samples)
        assert all('rss' in sample for sample in samples)
        assert all('vms' in sample for sample in samples)
        assert all('percent' in sample for sample in samples)


class TestForceGarbageCollection:
    """Test cases for force_garbage_collection function."""
    
    def test_force_garbage_collection(self):
        """Test forcing garbage collection."""
        # Create some objects
        objects = [[] for _ in range(100)]
        
        results = force_garbage_collection()
        
        # Check results structure
        expected_keys = ['gen_0', 'gen_1', 'gen_2']
        for key in expected_keys:
            assert key in results
            assert 'collected' in results[key]
            assert 'before_count' in results[key]
            assert 'after_count' in results[key]
            assert 'net_change' in results[key]
        
        # Check that collected counts are integers
        for key in expected_keys:
            assert isinstance(results[key]['collected'], int)
            assert isinstance(results[key]['before_count'], int)
            assert isinstance(results[key]['after_count'], int)
            assert isinstance(results[key]['net_change'], int)
    
    def test_force_garbage_collection_verbose(self):
        """Test forcing garbage collection with verbose output."""
        with patch('builtins.print') as mock_print:
            force_garbage_collection(verbose=True)
            
            # Check that print was called for each generation
            assert mock_print.call_count == 3


class TestFindObjectCycles:
    """Test cases for find_object_cycles function."""
    
    def test_find_object_cycles_no_cycle(self):
        """Test finding cycles when none exist."""
        obj = [1, 2, 3]
        cycles = find_object_cycles(obj)
        assert cycles == []
    
    def test_find_object_cycles_with_cycle(self):
        """Test finding cycles when they exist."""
        # Create a simple cycle
        a = []
        b = []
        a.append(b)
        b.append(a)
        
        cycles = find_object_cycles(a)
        # Should find at least one cycle
        assert len(cycles) >= 1
        assert all(isinstance(cycle, list) for cycle in cycles)


class TestGetObjectSize:
    """Test cases for get_object_size function."""
    
    def test_get_object_size(self):
        """Test getting object size."""
        obj = [1, 2, 3, 4, 5]
        size = get_object_size(obj)
        assert isinstance(size, int)
        assert size > 0
    
    def test_get_object_size_empty(self):
        """Test getting size of empty object."""
        obj = []
        size = get_object_size(obj)
        assert isinstance(size, int)
        assert size >= 0


class TestAnalyzeMemoryUsage:
    """Test cases for analyze_memory_usage function."""
    
    @patch('glon.utils.psutil')
    def test_analyze_memory_usage(self, mock_psutil):
        """Test memory usage analysis."""
        # Mock psutil.Process
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1000000, vms=2000000)
        mock_process.memory_percent.return_value = 50.0
        mock_psutil.Process.return_value = mock_process
        mock_psutil.os.getpid.return_value = 1234
        
        analysis = analyze_memory_usage()
        
        # Check structure
        required_keys = ['timestamp', 'memory', 'gc', 'objects']
        for key in required_keys:
            assert key in analysis
        
        # Check memory section
        assert 'rss' in analysis['memory']
        assert 'vms' in analysis['memory']
        assert 'percent' in analysis['memory']
        
        # Check gc section
        assert 'enabled' in analysis['gc']
        assert 'counts' in analysis['gc']
        assert 'threshold' in analysis['gc']
        assert 'stats' in analysis['gc']
        
        # Check objects section
        assert 'total_count' in analysis['objects']
        assert 'top_types' in analysis['objects']


class TestDebugFunctions:
    """Test cases for debug functions."""
    
    def test_set_debug_gc(self):
        """Test setting debug flags."""
        set_debug_gc(gc.DEBUG_STATS)
        # Can't easily test the effect, but ensure no exception
        clear_gc_debug()  # Clean up
    
    def test_clear_gc_debug(self):
        """Test clearing debug flags."""
        clear_gc_debug()
        # Ensure no exception


class TestMemoryLogger:
    """Test cases for memory logger creation."""
    
    def test_create_memory_logger(self):
        """Test creating memory logger."""
        logger = create_memory_logger("test_gc_memory.log")
        
        assert logger.name == "gc_memory"
        assert logger.level == 20  # INFO level
        
        # Clean up log file
        if os.path.exists("test_gc_memory.log"):
            os.remove("test_gc_memory.log")
    
    def test_create_memory_logger_default(self):
        """Test creating memory logger with default file."""
        logger = create_memory_logger()
        
        assert logger.name == "gc_memory"
        assert logger.level == 20  # INFO level
        
        # Clean up log file
        if os.path.exists("gc_memory.log"):
            os.remove("gc_memory.log")
