"""
Unit tests for MCP Tools
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastmcp import Context

from s3_upload_mcp.tools import (
    upload_image_to_s3, batch_upload_images, list_s3_buckets, get_server_info,
    set_global_instances
)
from s3_upload_mcp.models import UploadResponse, BatchUploadResponse, BucketListResponse


class TestMCPTools:
    """Test cases for MCP tools."""
    
    @pytest.fixture(autouse=True)
    def setup_tools(self, mock_s3_client, mock_image_processor):
        """Set up global instances for tools."""
        set_global_instances(mock_s3_client, mock_image_processor)
    
    @pytest.mark.asyncio
    async def test_upload_image_to_s3_success(self, sample_image_path, mock_s3_client, mock_image_processor):
        """Test successful single image upload."""
        # Mock file existence
        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=1024):
                # Mock context
                mock_ctx = Mock(spec=Context)
                mock_ctx.info = AsyncMock()
                mock_ctx.warning = AsyncMock()
                mock_ctx.error = AsyncMock()
                
                result = await upload_image_to_s3(
                    sample_image_path,
                    "test-bucket",
                    key="test-key",
                    optimize=True,
                    quality=80,
                    ctx=mock_ctx
                )
                
                assert isinstance(result, UploadResponse)
                assert result.success is True
                assert result.url is not None
                assert result.key == "test-key"
                assert result.bucket == "test-bucket"
                
                # Verify context calls
                mock_ctx.info.assert_called()
                mock_s3_client.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_image_to_s3_file_not_found(self, mock_s3_client, mock_image_processor):
        """Test upload with non-existent file."""
        with patch('os.path.exists', return_value=False):
            mock_ctx = Mock(spec=Context)
            mock_ctx.info = AsyncMock()
            mock_ctx.error = AsyncMock()
            
            result = await upload_image_to_s3(
                "nonexistent.png",
                "test-bucket",
                ctx=mock_ctx
            )
            
            assert isinstance(result, UploadResponse)
            assert result.success is False
            assert "File not found" in result.error
    
    @pytest.mark.asyncio
    async def test_upload_image_to_s3_unsupported_format(self, sample_image_path, mock_s3_client, mock_image_processor):
        """Test upload with unsupported format."""
        mock_image_processor.is_supported_format.return_value = False
        
        with patch('os.path.exists', return_value=True):
            mock_ctx = Mock(spec=Context)
            mock_ctx.info = AsyncMock()
            mock_ctx.error = AsyncMock()
            
            result = await upload_image_to_s3(
                sample_image_path,
                "test-bucket",
                ctx=mock_ctx
            )
            
            assert isinstance(result, UploadResponse)
            assert result.success is False
            assert "Unsupported image format" in result.error
    
    @pytest.mark.asyncio
    async def test_upload_image_to_s3_optimization_failure(self, sample_image_path, mock_s3_client, mock_image_processor):
        """Test upload with optimization failure."""
        mock_image_processor.optimize_image.side_effect = Exception("Optimization failed")
        
        with patch('os.path.exists', return_value=True):
            mock_ctx = Mock(spec=Context)
            mock_ctx.info = AsyncMock()
            mock_ctx.warning = AsyncMock()
            mock_ctx.error = AsyncMock()
            
            result = await upload_image_to_s3(
                sample_image_path,
                "test-bucket",
                optimize=True,
                ctx=mock_ctx
            )
            
            assert isinstance(result, UploadResponse)
            assert result.success is True  # Should fallback to original file
            mock_ctx.warning.assert_called()
    
    @pytest.mark.asyncio
    async def test_batch_upload_images_success(self, mock_s3_client, mock_image_processor):
        """Test successful batch upload."""
        file_paths = ["test1.png", "test2.png"]
        
        with patch('os.path.exists', return_value=True):
            mock_ctx = Mock(spec=Context)
            mock_ctx.info = AsyncMock()
            mock_ctx.warning = AsyncMock()
            mock_ctx.error = AsyncMock()
            
            result = await batch_upload_images(
                file_paths,
                "test-bucket",
                folder_prefix="images",
                optimize=True,
                quality=80,
                max_concurrent=2,
                ctx=mock_ctx
            )
            
            assert isinstance(result, BatchUploadResponse)
            assert result.success is True
            assert result.total_files == 2
            assert result.successful_uploads == 2
            assert len(result.urls) == 2
            assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_batch_upload_images_with_errors(self, mock_s3_client, mock_image_processor):
        """Test batch upload with some failures."""
        file_paths = ["test1.png", "nonexistent.png", "test3.png"]
        
        def mock_exists(path):
            return path != "nonexistent.png"
        
        # Mock upload_multiple to return results for 2 files (excluding nonexistent)
        mock_s3_client.upload_multiple.return_value = [
            {
                'success': True,
                'url': 'https://test-bucket.s3.us-east-1.amazonaws.com/test-key-1',
                'key': 'test-key-1'
            },
            {
                'success': True,
                'url': 'https://test-bucket.s3.us-east-1.amazonaws.com/test-key-3',
                'key': 'test-key-3'
            }
        ]
        
        with patch('os.path.exists', side_effect=mock_exists):
            mock_ctx = Mock(spec=Context)
            mock_ctx.info = AsyncMock()
            mock_ctx.warning = AsyncMock()
            mock_ctx.error = AsyncMock()
            
            result = await batch_upload_images(
                file_paths,
                "test-bucket",
                ctx=mock_ctx
            )
            
            assert isinstance(result, BatchUploadResponse)
            assert result.success is True  # Partial success
            assert result.total_files == 3
            assert result.successful_uploads == 2
            assert result.failed_uploads == 1
            assert len(result.errors) == 1
            assert "File not found" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_batch_upload_images_no_valid_files(self, mock_s3_client, mock_image_processor):
        """Test batch upload with no valid files."""
        file_paths = ["nonexistent1.png", "nonexistent2.png"]
        
        with patch('os.path.exists', return_value=False):
            mock_ctx = Mock(spec=Context)
            mock_ctx.info = AsyncMock()
            mock_ctx.warning = AsyncMock()
            mock_ctx.error = AsyncMock()
            
            result = await batch_upload_images(
                file_paths,
                "test-bucket",
                ctx=mock_ctx
            )
            
            assert isinstance(result, BatchUploadResponse)
            assert result.success is False
            assert result.total_files == 2
            assert result.successful_uploads == 0
            assert result.failed_uploads == 2
            assert len(result.errors) == 2
    
    @pytest.mark.asyncio
    async def test_list_s3_buckets_success(self, mock_s3_client):
        """Test successful bucket listing."""
        mock_ctx = Mock(spec=Context)
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        result = await list_s3_buckets(mock_ctx)
        
        assert isinstance(result, BucketListResponse)
        assert result.success is True
        assert len(result.buckets) == 2
        assert result.count == 2
        assert "test-bucket" in result.buckets
    
    @pytest.mark.asyncio
    async def test_list_s3_buckets_failure(self, mock_s3_client):
        """Test bucket listing failure."""
        mock_s3_client.list_buckets.side_effect = Exception("AWS error")
        
        mock_ctx = Mock(spec=Context)
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        result = await list_s3_buckets(mock_ctx)
        
        assert isinstance(result, BucketListResponse)
        assert result.success is False
        assert "AWS error" in result.error
    
    @pytest.mark.asyncio
    async def test_get_server_info_success(self, mock_s3_client):
        """Test successful server info retrieval."""
        mock_ctx = Mock(spec=Context)
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        result = await get_server_info(mock_ctx)
        
        assert result.name == "S3 Upload MCP Server"
        assert result.version == "1.0.0"
        assert result.status == "running"
        assert result.aws_region == "us-east-1"
        assert result.bucket_name == "test-bucket"
    
    @pytest.mark.asyncio
    async def test_get_server_info_failure(self):
        """Test server info retrieval with no client."""
        # Clear global instances
        set_global_instances(None, None)
        
        mock_ctx = Mock(spec=Context)
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        result = await get_server_info(mock_ctx)
        
        assert result.status == "running"  # Default status
        assert result.aws_region is None
        assert result.bucket_name is None
