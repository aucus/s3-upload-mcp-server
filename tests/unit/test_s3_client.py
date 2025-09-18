"""
Unit tests for S3Client
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from s3_upload_mcp.s3_client import S3Client


class TestS3Client:
    """Test cases for S3Client class."""
    
    def test_init_with_credentials(self):
        """Test S3Client initialization with credentials."""
        with patch('boto3.client') as mock_boto:
            client = S3Client(region="us-east-1", bucket_name="test-bucket")
            mock_boto.assert_called_once()
            assert client.region == "us-east-1"
            assert client.bucket_name == "test-bucket"
    
    def test_init_without_credentials(self):
        """Test S3Client initialization without credentials."""
        with patch('boto3.client', side_effect=Exception("No credentials")):
            with pytest.raises(Exception):
                S3Client(region="us-east-1", bucket_name="test-bucket")
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test successful connection test."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.head_bucket = Mock()
            mock_boto.return_value = mock_client
            
            client = S3Client(region="us-east-1", bucket_name="test-bucket")
            result = await client.test_connection()
            
            assert result is True
            mock_client.head_bucket.assert_called_once_with(Bucket="test-bucket")
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test connection test failure."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.head_bucket = Mock(side_effect=Exception("Access denied"))
            mock_boto.return_value = mock_client
            
            client = S3Client(region="us-east-1", bucket_name="test-bucket")
            result = await client.test_connection()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self, temp_dir, sample_image_path):
        """Test successful file upload."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.upload_file = Mock()
            mock_boto.return_value = mock_client
            
            client = S3Client(region="us-east-1", bucket_name="test-bucket")
            
            with patch.object(client, '_get_content_type', return_value='image/png'):
                result = await client.upload_file(
                    sample_image_path,
                    "test-key",
                    metadata={'test': 'value'}
                )
            
            assert result['success'] is True
            assert 'url' in result
            assert result['key'] == "test-key"
            assert result['bucket'] == "test-bucket"
    
    @pytest.mark.asyncio
    async def test_upload_file_failure(self, temp_dir, sample_image_path):
        """Test file upload failure."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.upload_file = Mock(side_effect=Exception("Upload failed"))
            mock_boto.return_value = mock_client
            
            client = S3Client(region="us-east-1", bucket_name="test-bucket")
            
            result = await client.upload_file(sample_image_path, "test-key")
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_upload_multiple(self, temp_dir, sample_image_path):
        """Test multiple file upload."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.upload_file = Mock()
            mock_boto.return_value = mock_client
            
            client = S3Client(region="us-east-1", bucket_name="test-bucket")
            
            files = [
                {'file_path': sample_image_path, 'key': 'key1'},
                {'file_path': sample_image_path, 'key': 'key2'}
            ]
            
            with patch.object(client, '_get_content_type', return_value='image/png'):
                results = await client.upload_multiple(files)
            
            assert len(results) == 2
            assert all(result['success'] for result in results)
    
    @pytest.mark.asyncio
    async def test_list_buckets(self):
        """Test listing S3 buckets."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.list_buckets = Mock(return_value={
                'Buckets': [
                    {'Name': 'bucket1'},
                    {'Name': 'bucket2'}
                ]
            })
            mock_boto.return_value = mock_client
            
            client = S3Client(region="us-east-1", bucket_name="test-bucket")
            buckets = await client.list_buckets()
            
            assert buckets == ['bucket1', 'bucket2']
    
    def test_get_content_type(self):
        """Test content type detection."""
        with patch('boto3.client'):
            client = S3Client(region="us-east-1", bucket_name="test-bucket")
            
            assert client._get_content_type("test.png") == "image/png"
            assert client._get_content_type("test.jpg") == "image/jpeg"
            assert client._get_content_type("test.unknown") == "application/octet-stream"
    
    def test_generate_key(self):
        """Test S3 key generation."""
        with patch('boto3.client'):
            client = S3Client(region="us-east-1", bucket_name="test-bucket")
            
            key = client.generate_key("/path/to/image.png")
            assert key.endswith(".png")
            assert "image" in key
            
            key_with_prefix = client.generate_key("/path/to/image.png", "folder")
            assert key_with_prefix.startswith("folder/")
