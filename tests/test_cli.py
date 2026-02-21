"""
Tests for CLI functionality.
"""

import pytest
import subprocess
import tempfile
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from glon.cli import parse_git_url, create_directory_structure, clone_repository


class TestParseGitUrl:
    """Test cases for URL parsing function."""
    
    def test_parse_ssh_url(self):
        """Test parsing SSH git URL."""
        url = "git@github.com:tom-sapletta-com/glon.git"
        result = parse_git_url(url)
        
        assert result == ("tom-sapletta-com", "glon")
    
    def test_parse_https_url_with_git(self):
        """Test parsing HTTPS git URL with .git extension."""
        url = "https://github.com/tom-sapletta-com/glon.git"
        result = parse_git_url(url)
        
        assert result == ("tom-sapletta-com", "glon")
    
    def test_parse_https_url_without_git(self):
        """Test parsing HTTPS git URL without .git extension."""
        url = "https://github.com/tom-sapletta-com/glon"
        result = parse_git_url(url)
        
        assert result == ("tom-sapletta-com", "glon")
    
    def test_parse_invalid_url(self):
        """Test parsing invalid URL."""
        url = "invalid-url"
        result = parse_git_url(url)
        
        assert result is None
    
    def test_parse_different_domain_ssh(self):
        """Test parsing SSH URL with different domain."""
        url = "git@gitlab.com:user/project.git"
        result = parse_git_url(url)
        
        assert result == ("user", "project")
    
    def test_parse_different_domain_https(self):
        """Test parsing HTTPS URL with different domain."""
        url = "https://gitlab.com/user/project.git"
        result = parse_git_url(url)
        
        assert result == ("user", "project")


class TestCreateDirectoryStructure:
    """Test cases for directory structure creation."""
    
    def test_create_directory_default_path(self):
        """Test creating directory with default path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock expanduser to use temp directory
            with patch('os.path.expanduser', return_value=temp_dir):
                target_dir = create_directory_structure("owner", "repo")
                
                expected_path = Path(temp_dir) / "owner" / "repo"
                assert target_dir == expected_path
                assert target_dir.exists()
                assert target_dir.is_dir()
    
    def test_create_directory_custom_path(self):
        """Test creating directory with custom base path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "custom"
            target_dir = create_directory_structure("owner", "repo", str(base_path))
            
            expected_path = base_path / "owner" / "repo"
            assert target_dir == expected_path
            assert target_dir.exists()
            assert target_dir.is_dir()
    
    def test_create_directory_existing(self):
        """Test creating directory when it already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "custom"
            target_dir = create_directory_structure("owner", "repo", str(base_path))
            
            # Create again - should not raise error
            target_dir2 = create_directory_structure("owner", "repo", str(base_path))
            
            assert target_dir == target_dir2
            assert target_dir.exists()


class TestCloneRepository:
    """Test cases for repository cloning."""
    
    @patch('subprocess.run')
    def test_clone_success(self, mock_run):
        """Test successful repository cloning."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Cloning into 'target'...",
            stderr=""
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "target"
            target_dir.mkdir()
            
            url = "https://github.com/owner/repo.git"
            result = clone_repository(url, target_dir)
            
            assert result is True
            mock_run.assert_called_once_with(
                ["git", "clone", url, str(target_dir)],
                capture_output=True,
                text=True,
                check=True
            )
    
    @patch('subprocess.run')
    def test_clone_git_error(self, mock_run):
        """Test repository cloning with git error."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git", stderr="Repository not found"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "target"
            target_dir.mkdir()
            
            url = "https://github.com/owner/repo.git"
            result = clone_repository(url, target_dir)
            
            assert result is False
    
    @patch('subprocess.run')
    def test_clone_git_not_found(self, mock_run):
        """Test repository cloning when git is not found."""
        mock_run.side_effect = FileNotFoundError()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "target"
            target_dir.mkdir()
            
            url = "https://github.com/owner/repo.git"
            result = clone_repository(url, target_dir)
            
            assert result is False
    
    def test_clone_non_empty_directory(self):
        """Test cloning to non-empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "target"
            target_dir.mkdir()
            
            # Create a file in the directory
            (target_dir / "existing_file.txt").write_text("content")
            
            url = "https://github.com/owner/repo.git"
            result = clone_repository(url, target_dir)
            
            assert result is False


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    @patch('glon.cli.clone_repository')
    @patch('glon.cli.create_directory_structure')
    @patch('glon.cli.parse_git_url')
    def test_main_successful_clone(self, mock_parse, mock_create, mock_clone):
        """Test main function with successful clone."""
        mock_parse.return_value = ("owner", "repo")
        mock_create.return_value = Path("/tmp/github/owner/repo")
        mock_clone.return_value = True
        
        with patch('sys.argv', ['glon', 'https://github.com/owner/repo.git']):
            with patch('builtins.print') as mock_print:
                from glon.cli import main
                main()
                
                mock_parse.assert_called_once_with("https://github.com/owner/repo.git")
                mock_create.assert_called_once_with("owner", "repo", None)
                mock_clone.assert_called_once()
                
                # Check success message
                mock_print.assert_any_call("Repository ready at: /tmp/github/owner/repo")
    
    @patch('glon.cli.parse_git_url')
    def test_main_invalid_url(self, mock_parse):
        """Test main function with invalid URL."""
        mock_parse.return_value = None
        
        with patch('sys.argv', ['glon', 'invalid-url']):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print') as mock_print:
                    from glon.cli import main
                    main()
                    
                    mock_exit.assert_not_called()
                    mock_print.assert_any_call("Error: Invalid git URL format: invalid-url")
    
    @patch('glon.cli.clone_repository')
    @patch('glon.cli.create_directory_structure')
    @patch('glon.cli.parse_git_url')
    def test_main_clone_failure(self, mock_parse, mock_create, mock_clone):
        """Test main function with clone failure."""
        mock_parse.return_value = ("owner", "repo")
        mock_create.return_value = Path("/tmp/github/owner/repo")
        mock_clone.return_value = False
        
        with patch('sys.argv', ['glon', 'https://github.com/owner/repo.git']):
            with patch('builtins.print') as mock_print:
                from glon.cli import main
                main()
                
                # Should not print success message on failure
                assert not any("Repository ready at" in str(call) for call in mock_print.call_args_list)
    
    @patch('glon.cli.clone_repository')
    @patch('glon.cli.create_directory_structure')
    @patch('glon.cli.parse_git_url')
    def test_main_dry_run(self, mock_parse, mock_create, mock_clone):
        """Test main function with dry run."""
        mock_parse.return_value = ("owner", "repo")
        mock_create.return_value = Path("/tmp/github/owner/repo")
        
        with patch('sys.argv', ['glon', '--dry-run', 'https://github.com/owner/repo.git']):
            with patch('builtins.print') as mock_print:
                from glon.cli import main
                main()
                
                mock_clone.assert_not_called()
                mock_print.assert_any_call("Would clone https://github.com/owner/repo.git to /tmp/github/owner/repo")
