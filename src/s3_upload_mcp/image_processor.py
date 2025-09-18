"""
Image Processing Module for MCP Server

Handles image optimization, format conversion, and file processing.
"""

import os
import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from PIL import Image, ImageOps
import asyncio

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Image processing utilities for the MCP server."""
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.svg'}
    
    # Default optimization settings
    DEFAULT_QUALITY = 80
    DEFAULT_MAX_WIDTH = 1920
    DEFAULT_MAX_HEIGHT = 1080
    
    def __init__(self):
        """Initialize the image processor."""
        logger.info("Image processor initialized")
    
    def is_supported_format(self, file_path: str) -> bool:
        """
        Check if the file format is supported.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            bool: True if format is supported
        """
        extension = Path(file_path).suffix.lower()
        return extension in self.SUPPORTED_FORMATS
    
    def get_image_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic image information.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            dict: Image information including dimensions, format, size
        """
        try:
            with Image.open(file_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': os.path.getsize(file_path),
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
        except Exception as e:
            logger.error(f"Error getting image info for {file_path}: {e}")
            return {}
    
    async def optimize_image(
        self,
        file_path: str,
        output_path: Optional[str] = None,
        quality: int = DEFAULT_QUALITY,
        max_width: int = DEFAULT_MAX_WIDTH,
        max_height: int = DEFAULT_MAX_HEIGHT,
        convert_to_webp: bool = False
    ) -> str:
        """
        Optimize an image file.
        
        Args:
            file_path: Path to the input image
            output_path: Path for the optimized image (auto-generated if None)
            quality: Compression quality (1-100)
            max_width: Maximum width for resizing
            max_height: Maximum height for resizing
            convert_to_webp: Whether to convert to WebP format
            
        Returns:
            str: Path to the optimized image
        """
        try:
            # Generate output path if not provided
            if not output_path:
                input_path = Path(file_path)
                if convert_to_webp:
                    output_path = str(input_path.with_suffix('.webp'))
                else:
                    output_path = str(input_path.with_suffix(f'.optimized{input_path.suffix}'))
            
            # Process image in executor to avoid blocking
            def process_image():
                with Image.open(file_path) as img:
                    # Convert to RGB if necessary (for JPEG/WebP)
                    if convert_to_webp and img.mode in ('RGBA', 'LA'):
                        # Create white background for transparency
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'RGBA':
                            background.paste(img, mask=img.split()[-1])
                        else:
                            background.paste(img)
                        img = background
                    elif convert_to_webp and img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize if necessary
                    img = self._resize_image(img, max_width, max_height)
                    
                    # Optimize
                    img = ImageOps.exif_transpose(img)  # Handle EXIF orientation
                    
                    # Save with optimization
                    save_kwargs = {
                        'optimize': True,
                        'quality': quality
                    }
                    
                    if convert_to_webp:
                        img.save(output_path, 'WEBP', **save_kwargs)
                    else:
                        img.save(output_path, **save_kwargs)
                
                return output_path
            
            # Run in executor
            result_path = await asyncio.get_event_loop().run_in_executor(
                None, process_image
            )
            
            logger.info(f"Optimized image saved to: {result_path}")
            return result_path
            
        except Exception as e:
            logger.error(f"Error optimizing image {file_path}: {e}")
            raise
    
    def _resize_image(self, img: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """
        Resize image while maintaining aspect ratio.
        
        Args:
            img: PIL Image object
            max_width: Maximum width
            max_height: Maximum height
            
        Returns:
            PIL Image object (resized if necessary)
        """
        if img.width <= max_width and img.height <= max_height:
            return img
        
        # Calculate new dimensions maintaining aspect ratio
        ratio = min(max_width / img.width, max_height / img.height)
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def normalize_filename(self, filename: str) -> str:
        """
        Normalize filename for URL safety.
        
        Args:
            filename: Original filename
            
        Returns:
            str: URL-safe filename
        """
        # Remove or replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        safe_filename = "".join(c if c in safe_chars else "_" for c in filename)
        
        # Remove multiple consecutive underscores
        while "__" in safe_filename:
            safe_filename = safe_filename.replace("__", "_")
        
        # Ensure it doesn't start or end with underscore
        safe_filename = safe_filename.strip("_")
        
        # Ensure it has an extension
        if "." not in safe_filename:
            safe_filename += ".jpg"
        
        return safe_filename
    
    async def batch_optimize(
        self,
        file_paths: list[str],
        quality: int = DEFAULT_QUALITY,
        max_width: int = DEFAULT_MAX_WIDTH,
        max_height: int = DEFAULT_MAX_HEIGHT,
        convert_to_webp: bool = False,
        max_concurrent: int = 3
    ) -> list[Dict[str, Any]]:
        """
        Optimize multiple images concurrently.
        
        Args:
            file_paths: List of image file paths
            quality: Compression quality
            max_width: Maximum width
            max_height: Maximum height
            convert_to_webp: Whether to convert to WebP
            max_concurrent: Maximum concurrent operations
            
        Returns:
            List of optimization results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def optimize_single(file_path: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    if not self.is_supported_format(file_path):
                        return {
                            'success': False,
                            'file_path': file_path,
                            'error': f'Unsupported format: {Path(file_path).suffix}'
                        }
                    
                    output_path = await self.optimize_image(
                        file_path,
                        quality=quality,
                        max_width=max_width,
                        max_height=max_height,
                        convert_to_webp=convert_to_webp
                    )
                    
                    return {
                        'success': True,
                        'file_path': file_path,
                        'output_path': output_path,
                        'original_size': os.path.getsize(file_path),
                        'optimized_size': os.path.getsize(output_path)
                    }
                    
                except Exception as e:
                    return {
                        'success': False,
                        'file_path': file_path,
                        'error': str(e)
                    }
        
        # Execute optimizations concurrently
        tasks = [optimize_single(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'file_path': file_paths[i],
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_optimization_stats(self, results: list[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate optimization statistics.
        
        Args:
            results: List of optimization results
            
        Returns:
            dict: Statistics about the optimization process
        """
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        total_original_size = sum(r.get('original_size', 0) for r in successful)
        total_optimized_size = sum(r.get('optimized_size', 0) for r in successful)
        
        compression_ratio = 0
        if total_original_size > 0:
            compression_ratio = (1 - total_optimized_size / total_original_size) * 100
        
        return {
            'total_files': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'total_original_size': total_original_size,
            'total_optimized_size': total_optimized_size,
            'compression_ratio': round(compression_ratio, 2),
            'space_saved': total_original_size - total_optimized_size
        }
