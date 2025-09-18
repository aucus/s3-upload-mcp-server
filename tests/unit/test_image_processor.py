"""
Unit tests for ImageProcessor
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from s3_upload_mcp.image_processor import ImageProcessor


class TestImageProcessor:
    """Test cases for ImageProcessor class."""
    
    def test_init(self):
        """Test ImageProcessor initialization."""
        processor = ImageProcessor()
        assert processor is not None
    
    def test_is_supported_format(self):
        """Test supported format detection."""
        processor = ImageProcessor()
        
        assert processor.is_supported_format("test.png") is True
        assert processor.is_supported_format("test.jpg") is True
        assert processor.is_supported_format("test.jpeg") is True
        assert processor.is_supported_format("test.gif") is True
        assert processor.is_supported_format("test.webp") is True
        assert processor.is_supported_format("test.bmp") is True
        assert processor.is_supported_format("test.tiff") is True
        assert processor.is_supported_format("test.svg") is True
        assert processor.is_supported_format("test.txt") is False
        assert processor.is_supported_format("test.unknown") is False
    
    def test_get_image_info(self, sample_image_path):
        """Test getting image information."""
        processor = ImageProcessor()
        info = processor.get_image_info(sample_image_path)
        
        assert 'width' in info
        assert 'height' in info
        assert 'format' in info
        assert 'mode' in info
        assert 'size_bytes' in info
        assert 'has_transparency' in info
        assert info['width'] == 100
        assert info['height'] == 100
    
    def test_get_image_info_invalid_file(self):
        """Test getting image info for invalid file."""
        processor = ImageProcessor()
        info = processor.get_image_info("nonexistent.png")
        
        assert info == {}
    
    @pytest.mark.asyncio
    async def test_optimize_image(self, sample_image_path, temp_dir):
        """Test image optimization."""
        processor = ImageProcessor()
        output_path = os.path.join(temp_dir, "optimized.png")
        
        result_path = await processor.optimize_image(
            sample_image_path,
            output_path,
            quality=80
        )
        
        assert result_path == output_path
        assert os.path.exists(result_path)
    
    @pytest.mark.asyncio
    async def test_optimize_image_webp_conversion(self, sample_image_path, temp_dir):
        """Test image optimization with WebP conversion."""
        processor = ImageProcessor()
        output_path = os.path.join(temp_dir, "optimized.webp")
        
        result_path = await processor.optimize_image(
            sample_image_path,
            output_path,
            quality=80,
            convert_to_webp=True
        )
        
        assert result_path == output_path
        assert os.path.exists(result_path)
        assert result_path.endswith('.webp')
    
    @pytest.mark.asyncio
    async def test_optimize_image_with_resize(self, sample_image_path, temp_dir):
        """Test image optimization with resizing."""
        processor = ImageProcessor()
        output_path = os.path.join(temp_dir, "resized.png")
        
        result_path = await processor.optimize_image(
            sample_image_path,
            output_path,
            quality=80,
            max_width=50,
            max_height=50
        )
        
        assert result_path == output_path
        assert os.path.exists(result_path)
        
        # Check if image was resized
        info = processor.get_image_info(result_path)
        assert info['width'] <= 50
        assert info['height'] <= 50
    
    def test_normalize_filename(self):
        """Test filename normalization."""
        processor = ImageProcessor()
        
        # Test basic normalization
        assert processor.normalize_filename("test image.png") == "test_image.png"
        assert processor.normalize_filename("test@#$%image.png") == "test_image.png"
        assert processor.normalize_filename("test___image.png") == "test_image.png"
        assert processor.normalize_filename("_test_image_.png") == "test_image_.png"
        
        # Test filename without extension
        result = processor.normalize_filename("test")
        assert result == "test.jpg"
    
    @pytest.mark.asyncio
    async def test_batch_optimize(self, sample_image_path, temp_dir):
        """Test batch image optimization."""
        processor = ImageProcessor()
        
        # Create multiple test images
        image_paths = []
        for i in range(3):
            path = os.path.join(temp_dir, f"test{i}.png")
            # Copy the sample image
            import shutil
            shutil.copy2(sample_image_path, path)
            image_paths.append(path)
        
        results = await processor.batch_optimize(
            image_paths,
            quality=80,
            max_concurrent=2
        )
        
        assert len(results) == 3
        assert all(result['success'] for result in results)
        assert all('output_path' in result for result in results)
    
    @pytest.mark.asyncio
    async def test_batch_optimize_with_errors(self, temp_dir):
        """Test batch optimization with invalid files."""
        processor = ImageProcessor()
        
        # Mix of valid and invalid files
        image_paths = [
            "nonexistent1.png",
            "nonexistent2.png"
        ]
        
        results = await processor.batch_optimize(image_paths)
        
        assert len(results) == 2
        assert all(not result['success'] for result in results)
        assert all('error' in result for result in results)
    
    def test_get_optimization_stats(self):
        """Test optimization statistics calculation."""
        processor = ImageProcessor()
        
        results = [
            {
                'success': True,
                'original_size': 1000,
                'optimized_size': 500
            },
            {
                'success': True,
                'original_size': 2000,
                'optimized_size': 1000
            },
            {
                'success': False,
                'original_size': 500,
                'optimized_size': 0
            }
        ]
        
        stats = processor.get_optimization_stats(results)
        
        assert stats['total_files'] == 3
        assert stats['successful'] == 2
        assert stats['failed'] == 1
        assert stats['total_original_size'] == 3000
        assert stats['total_optimized_size'] == 1500
        assert stats['compression_ratio'] == 50.0
        assert stats['space_saved'] == 1500
