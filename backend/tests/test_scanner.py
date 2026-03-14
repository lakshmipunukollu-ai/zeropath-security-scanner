"""Tests for scanner engine utilities."""
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from app.scanner.engine import _index_python_files, _chunk_code


def test_index_python_files():
    """Should find .py files and skip excluded directories."""
    tmp = tempfile.mkdtemp()
    try:
        # Create some Python files
        os.makedirs(os.path.join(tmp, "app"))
        with open(os.path.join(tmp, "app", "main.py"), "w") as f:
            f.write("print('hello')")
        with open(os.path.join(tmp, "app", "utils.py"), "w") as f:
            f.write("def helper(): pass")

        # Create files in excluded dirs
        os.makedirs(os.path.join(tmp, "__pycache__"))
        with open(os.path.join(tmp, "__pycache__", "cached.py"), "w") as f:
            f.write("cached")
        os.makedirs(os.path.join(tmp, "venv"))
        with open(os.path.join(tmp, "venv", "lib.py"), "w") as f:
            f.write("lib")
        os.makedirs(os.path.join(tmp, "tests"))
        with open(os.path.join(tmp, "tests", "test_main.py"), "w") as f:
            f.write("test")

        # Create a non-Python file
        with open(os.path.join(tmp, "README.md"), "w") as f:
            f.write("readme")

        files = _index_python_files(tmp)
        paths = [rel for _, rel in files]

        assert "app/main.py" in paths or os.path.join("app", "main.py") in paths
        assert "app/utils.py" in paths or os.path.join("app", "utils.py") in paths

        # Should not contain excluded dirs or non-python files
        for _, rel in files:
            assert "__pycache__" not in rel
            assert "venv" not in rel
            assert not rel.endswith(".md")
    finally:
        shutil.rmtree(tmp)


def test_index_python_files_skip_large_files():
    """Should skip files larger than MAX_FILE_SIZE."""
    tmp = tempfile.mkdtemp()
    try:
        with open(os.path.join(tmp, "small.py"), "w") as f:
            f.write("x = 1")
        with open(os.path.join(tmp, "large.py"), "w") as f:
            f.write("x" * 200_000)  # 200KB > 100KB limit

        files = _index_python_files(tmp)
        paths = [rel for _, rel in files]
        assert "small.py" in paths
        assert "large.py" not in paths
    finally:
        shutil.rmtree(tmp)


def test_chunk_code_small_file():
    """Small file should not be chunked."""
    code = "def hello():\n    print('world')"
    chunks = _chunk_code(code, "test.py")
    assert len(chunks) == 1
    assert chunks[0] == code


def test_chunk_code_large_file():
    """Large file should be split into overlapping chunks."""
    code = "x = 1\n" * 1000  # Much larger than CHUNK_SIZE
    chunks = _chunk_code(code, "test.py")
    assert len(chunks) > 1
    # Chunks should overlap
    for i in range(len(chunks) - 1):
        # End of chunk i should share content with start of chunk i+1
        assert len(chunks[i]) > 0


def test_chunk_code_empty():
    """Empty file should produce one empty chunk."""
    chunks = _chunk_code("", "test.py")
    assert len(chunks) == 1
