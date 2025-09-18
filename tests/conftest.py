"""
Pytest configuration and fixtures for S3 Upload MCP Server tests
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, AsyncMock
from pathlib import Path

# Add src to Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from s3_upload_mcp.s3_client import S3Client
from s3_upload_mcp.image_processor import ImageProcessor


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_image_path(temp_dir):
    """Create a sample image file for testing."""
    # Create a simple test image using PIL
    from PIL import Image
    
    image_path = os.path.join(temp_dir, "test_image.png")
    # Create a simple 100x100 red image
    img = Image.new('RGB', (100, 100), color='red')
    img.save(image_path)
    
    return image_path


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client for testing."""
    client = Mock(spec=S3Client)
    client.region = "us-east-1"
    client.bucket_name = "test-bucket"
    client.test_connection = AsyncMock(return_value=True)
    client.upload_file = AsyncMock(return_value={
        'success': True,
        'url': 'https://test-bucket.s3.us-east-1.amazonaws.com/test-key',
        'key': 'test-key',
        'bucket': 'test-bucket',
        'size': 1024,
        'content_type': 'image/png',
        'metadata': {}
    })
    client.upload_multiple = AsyncMock(return_value=[
        {
            'success': True,
            'url': 'https://test-bucket.s3.us-east-1.amazonaws.com/test-key-1',
            'key': 'test-key-1'
        },
        {
            'success': True,
            'url': 'https://test-bucket.s3.us-east-1.amazonaws.com/test-key-2',
            'key': 'test-key-2'
        }
    ])
    client.list_buckets = AsyncMock(return_value=['test-bucket', 'another-bucket'])
    client.generate_key = Mock(return_value='test-key')
    return client


@pytest.fixture
def mock_image_processor():
    """Create a mock image processor for testing."""
    processor = Mock(spec=ImageProcessor)
    processor.is_supported_format = Mock(return_value=True)
    processor.get_image_info = Mock(return_value={
        'width': 100,
        'height': 100,
        'format': 'PNG',
        'mode': 'RGB',
        'size_bytes': 1024,
        'has_transparency': False
    })
    processor.optimize_image = AsyncMock(return_value='/tmp/optimized_image.png')
    processor.batch_optimize = AsyncMock(return_value=[
        {
            'success': True,
            'file_path': '/tmp/test.png',
            'output_path': '/tmp/optimized_test.png',
            'original_size': 1024,
            'optimized_size': 512
        }
    ])
    processor.get_optimization_stats = Mock(return_value={
        'total_files': 1,
        'successful': 1,
        'failed': 0,
        'total_original_size': 1024,
        'total_optimized_size': 512,
        'compression_ratio': 50.0,
        'space_saved': 512
    })
    processor.normalize_filename = Mock(return_value='test_image.png')
    return processor


@pytest.fixture
def sample_upload_request():
    """Create a sample upload request for testing."""
    return {
        'file_path': '/tmp/test_image.png',
        'bucket_name': 'test-bucket',
        'key': 'test-key',
        'optimize': True,
        'quality': 80
    }


@pytest.fixture
def sample_batch_upload_request():
    """Create a sample batch upload request for testing."""
    return {
        'file_paths': ['/tmp/test1.png', '/tmp/test2.png'],
        'bucket_name': 'test-bucket',
        'folder_prefix': 'images',
        'optimize': True,
        'quality': 80,
        'max_concurrent': 2
    }
