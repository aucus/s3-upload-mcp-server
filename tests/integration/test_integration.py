"""
Integration tests for S3 Upload MCP Server

These tests require actual AWS credentials and a test bucket.
Run with: pytest tests/integration/ -m aws
"""

import pytest
import os
import tempfile
from pathlib import Path

from s3_upload_mcp.s3_client import S3Client
from s3_upload_mcp.image_processor import ImageProcessor
from s3_upload_mcp.tools import upload_image_to_s3, batch_upload_images, list_s3_buckets
from fastmcp import Context


@pytest.mark.aws
class TestS3Integration:
    """Integration tests with real AWS S3."""
    
    @pytest.fixture(scope="class")
    def aws_credentials(self):
        """Check if AWS credentials are available."""
        if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
            pytest.skip("AWS credentials not available")
        
        return {
            'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
            'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'bucket': os.getenv('S3_BUCKET_NAME', 'test-s3-upload-mcp')
        }
    
    @pytest.fixture(scope="class")
    def s3_client(self, aws_credentials):
        """Create S3 client for integration tests."""
        client = S3Client(
            region=aws_credentials['region'],
            bucket_name=aws_credentials['bucket']
        )
        
        # Test connection
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            connected = loop.run_until_complete(client.test_connection())
            if not connected:
                pytest.skip("Cannot connect to S3 bucket")
        finally:
            loop.close()
        
        return client
    
    @pytest.fixture(scope="class")
    def image_processor(self):
        """Create image processor for integration tests."""
        return ImageProcessor()
    
    @pytest.fixture(scope="class")
    def test_image(self):
        """Create a test image for integration tests."""
        from PIL import Image
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            # Create a simple test image
            img = Image.new('RGB', (200, 200), color='blue')
            img.save(tmp.name)
            yield tmp.name
        
        # Cleanup
        os.unlink(tmp.name)
    
    @pytest.mark.asyncio
    async def test_s3_client_connection(self, s3_client):
        """Test S3 client connection."""
        connected = await s3_client.test_connection()
        assert connected is True
    
    @pytest.mark.asyncio
    async def test_s3_client_upload(self, s3_client, test_image):
        """Test S3 file upload."""
        key = f"integration-test/{Path(test_image).name}"
        
        result = await s3_client.upload_file(
            test_image,
            key,
            metadata={'test': 'integration'}
        )
        
        assert result['success'] is True
        assert 'url' in result
        assert result['key'] == key
        assert result['bucket'] == s3_client.bucket_name
    
    @pytest.mark.asyncio
    async def test_s3_client_list_buckets(self, s3_client):
        """Test S3 bucket listing."""
        buckets = await s3_client.list_buckets()
        
        assert isinstance(buckets, list)
        assert len(buckets) > 0
        assert s3_client.bucket_name in buckets
    
    @pytest.mark.asyncio
    async def test_image_processor_optimization(self, image_processor, test_image):
        """Test image optimization."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            result_path = await image_processor.optimize_image(
                test_image,
                output_path,
                quality=50,
                max_width=100,
                max_height=100
            )
            
            assert os.path.exists(result_path)
            
            # Check if image was resized
            info = image_processor.get_image_info(result_path)
            assert info['width'] <= 100
            assert info['height'] <= 100
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    @pytest.mark.asyncio
    async def test_upload_tool_integration(self, s3_client, image_processor, test_image):
        """Test upload tool with real S3."""
        from s3_upload_mcp.tools import set_global_instances
        set_global_instances(s3_client, image_processor)
        
        # Mock context
        class MockContext:
            async def info(self, msg): print(f"INFO: {msg}")
            async def warning(self, msg): print(f"WARNING: {msg}")
            async def error(self, msg): print(f"ERROR: {msg}")
        
        mock_ctx = MockContext()
        
        result = await upload_image_to_s3(
            test_image,
            s3_client.bucket_name,
            key=f"tool-test/{Path(test_image).name}",
            optimize=True,
            quality=80,
            ctx=mock_ctx
        )
        
        assert result.success is True
        assert result.url is not None
        assert result.bucket == s3_client.bucket_name
    
    @pytest.mark.asyncio
    async def test_batch_upload_tool_integration(self, s3_client, image_processor, test_image):
        """Test batch upload tool with real S3."""
        from s3_upload_mcp.tools import set_global_instances
        set_global_instances(s3_client, image_processor)
        
        # Create multiple test images
        test_images = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=f'_test{i}.png', delete=False) as tmp:
                from PIL import Image
                img = Image.new('RGB', (100, 100), color=f'hsl({i*120}, 50%, 50%)')
                img.save(tmp.name)
                test_images.append(tmp.name)
        
        try:
            # Mock context
            class MockContext:
                async def info(self, msg): print(f"INFO: {msg}")
                async def warning(self, msg): print(f"WARNING: {msg}")
                async def error(self, msg): print(f"ERROR: {msg}")
            
            mock_ctx = MockContext()
            
            result = await batch_upload_images(
                test_images,
                s3_client.bucket_name,
                folder_prefix="batch-test",
                optimize=True,
                quality=80,
                max_concurrent=2,
                ctx=mock_ctx
            )
            
            assert result.success is True
            assert result.total_files == 3
            assert result.successful_uploads == 3
            assert len(result.urls) == 3
            assert len(result.errors) == 0
            
        finally:
            # Cleanup test images
            for img_path in test_images:
                if os.path.exists(img_path):
                    os.unlink(img_path)
    
    @pytest.mark.asyncio
    async def test_list_buckets_tool_integration(self, s3_client):
        """Test list buckets tool with real S3."""
        from s3_upload_mcp.tools import set_global_instances
        set_global_instances(s3_client, None)
        
        # Mock context
        class MockContext:
            async def info(self, msg): print(f"INFO: {msg}")
            async def error(self, msg): print(f"ERROR: {msg}")
        
        mock_ctx = MockContext()
        
        result = await list_s3_buckets(mock_ctx)
        
        assert result.success is True
        assert len(result.buckets) > 0
        assert s3_client.bucket_name in result.buckets
