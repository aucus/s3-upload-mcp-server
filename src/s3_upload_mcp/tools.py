"""
FastMCP Tools for S3 Upload Server

Implements the core MCP tools for image upload and management.
"""

import os
import time
import logging
from typing import Optional, List
from pathlib import Path

from fastmcp import FastMCP, Context
from .models import (
    UploadRequest, UploadResponse, BatchUploadRequest, BatchUploadResponse,
    BucketListResponse, ErrorResponse, ServerInfo
)
from .s3_client import S3Client
from .image_processor import ImageProcessor

logger = logging.getLogger(__name__)

# Global instances (will be initialized by server)
s3_client: Optional[S3Client] = None
image_processor: Optional[ImageProcessor] = None


def set_global_instances(client: S3Client, processor: ImageProcessor) -> None:
    """Set global instances for tools to use."""
    global s3_client, image_processor
    s3_client = client
    image_processor = processor


async def upload_image_to_s3(
    file_path: str,
    bucket_name: str,
    ctx: Context,
    key: Optional[str] = None,
    optimize: bool = True,
    quality: int = 80,
    folder_prefix: Optional[str] = None
) -> UploadResponse:
    """
    Upload a single image file to S3 and return a public URL.
    
    Args:
        file_path: Path to the image file to upload
        bucket_name: S3 bucket name
        key: S3 object key (optional, auto-generated if not provided)
        optimize: Enable image optimization (default: True)
        quality: Compression quality 1-100 (default: 80)
        folder_prefix: S3 folder prefix (optional)
        ctx: FastMCP Context for logging and progress reporting
    
    Returns:
        UploadResponse: Upload result with success status, URL, and metadata
    """
    start_time = time.time()
    
    try:
        await ctx.info(f"Starting upload of {file_path} to bucket {bucket_name}")
        
        # Validate inputs
        if not s3_client:
            raise ValueError("S3 client not initialized")
        if not image_processor:
            raise ValueError("Image processor not initialized")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return UploadResponse(
                success=False,
                error=f"File not found: {file_path}"
            )
        
        # Check if file is a supported image format
        if not image_processor.is_supported_format(file_path):
            return UploadResponse(
                success=False,
                error=f"Unsupported image format: {Path(file_path).suffix}"
            )
        
        # Generate S3 key if not provided
        if not key:
            key = s3_client.generate_key(file_path, folder_prefix)
        
        # Process image if optimization is enabled
        processed_file_path = file_path
        if optimize:
            await ctx.info(f"Optimizing image with quality {quality}")
            try:
                processed_file_path = await image_processor.optimize_image(
                    file_path,
                    quality=quality
                )
                await ctx.info(f"Image optimized and saved to: {processed_file_path}")
            except Exception as e:
                await ctx.warning(f"Image optimization failed, using original: {e}")
                processed_file_path = file_path
        
        # Upload to S3
        await ctx.info(f"Uploading to S3 with key: {key}")
        upload_result = await s3_client.upload_file(
            processed_file_path,
            key,
            metadata={
                'original_file': file_path,
                'optimized': optimize,
                'quality': str(quality)
            }
        )
        
        # Clean up temporary optimized file if different from original
        if processed_file_path != file_path and os.path.exists(processed_file_path):
            try:
                os.remove(processed_file_path)
            except Exception as e:
                await ctx.warning(f"Failed to clean up temporary file: {e}")
        
        processing_time = time.time() - start_time
        
        if upload_result.get('success', False):
            await ctx.info(f"Upload successful: {upload_result['url']}")
            return UploadResponse(
                success=True,
                url=upload_result['url'],
                key=upload_result['key'],
                bucket=upload_result['bucket'],
                size=upload_result['size'],
                content_type=upload_result['content_type'],
                metadata=upload_result['metadata'],
                processing_time=processing_time
            )
        else:
            await ctx.error(f"Upload failed: {upload_result.get('error', 'Unknown error')}")
            return UploadResponse(
                success=False,
                error=upload_result.get('error', 'Upload failed'),
                processing_time=processing_time
            )
            
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Unexpected error during upload: {str(e)}"
        await ctx.error(error_msg)
        logger.error(error_msg, exc_info=True)
        
        return UploadResponse(
            success=False,
            error=error_msg,
            processing_time=processing_time
        )


async def batch_upload_images(
    file_paths: List[str],
    bucket_name: str,
    ctx: Context,
    folder_prefix: Optional[str] = None,
    optimize: bool = True,
    quality: int = 80,
    max_concurrent: int = 5
) -> BatchUploadResponse:
    """
    Upload multiple images in parallel to S3.
    
    Args:
        file_paths: List of image file paths to upload
        bucket_name: S3 bucket name
        folder_prefix: S3 folder prefix (optional)
        optimize: Enable image optimization (default: True)
        quality: Compression quality 1-100 (default: 80)
        max_concurrent: Maximum concurrent uploads (default: 5)
        ctx: FastMCP Context for logging and progress reporting
    
    Returns:
        BatchUploadResponse: Batch upload result with URLs and status
    """
    start_time = time.time()
    
    try:
        await ctx.info(f"Starting batch upload of {len(file_paths)} files to bucket {bucket_name}")
        
        # Validate inputs
        if not s3_client:
            raise ValueError("S3 client not initialized")
        if not image_processor:
            raise ValueError("Image processor not initialized")
        
        # Filter valid files
        valid_files = []
        errors = []
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                errors.append(f"File not found: {file_path}")
                continue
            
            if not image_processor.is_supported_format(file_path):
                errors.append(f"Unsupported format {Path(file_path).suffix}: {file_path}")
                continue
            
            valid_files.append(file_path)
        
        if not valid_files:
            return BatchUploadResponse(
                success=False,
                errors=errors,
                total_files=len(file_paths),
                successful_uploads=0,
                failed_uploads=len(file_paths)
            )
        
        await ctx.info(f"Processing {len(valid_files)} valid files")
        
        # Process images if optimization is enabled
        processed_files = []
        optimization_stats = None
        
        if optimize:
            await ctx.info("Optimizing images...")
            try:
                optimization_results = await image_processor.batch_optimize(
                    valid_files,
                    quality=quality,
                    max_concurrent=max_concurrent
                )
                
                # Update file paths to optimized versions
                for result in optimization_results:
                    if result.get('success', False):
                        processed_files.append(result['output_path'])
                    else:
                        errors.append(f"Optimization failed for {result['file_path']}: {result.get('error', 'Unknown error')}")
                
                optimization_stats = image_processor.get_optimization_stats(optimization_results)
                await ctx.info(f"Optimization complete: {optimization_stats['compression_ratio']:.1f}% compression")
                
            except Exception as e:
                await ctx.warning(f"Batch optimization failed, using original files: {e}")
                processed_files = valid_files
        else:
            processed_files = valid_files
        
        if not processed_files:
            return BatchUploadResponse(
                success=False,
                errors=errors,
                total_files=len(file_paths),
                successful_uploads=0,
                failed_uploads=len(file_paths),
                optimization_stats=optimization_stats
            )
        
        # Prepare upload tasks
        upload_tasks = []
        for i, file_path in enumerate(processed_files):
            key = s3_client.generate_key(file_path, folder_prefix)
            upload_tasks.append({
                'file_path': file_path,
                'key': key,
                'metadata': {
                    'original_file': file_paths[i] if i < len(file_paths) else file_path,
                    'optimized': optimize,
                    'quality': str(quality),
                    'batch_index': str(i)
                }
            })
        
        # Upload files concurrently
        await ctx.info(f"Uploading {len(upload_tasks)} files to S3...")
        upload_results = await s3_client.upload_multiple(
            upload_tasks,
            max_concurrent=max_concurrent
        )
        
        # Process results
        urls = []
        successful_uploads = 0
        detailed_results = []
        
        for i, result in enumerate(upload_results):
            if result.get('success', False):
                urls.append(result['url'])
                successful_uploads += 1
            else:
                errors.append(f"Upload failed for {file_paths[i]}: {result.get('error', 'Unknown error')}")
            
            detailed_results.append({
                'file_path': file_paths[i] if i < len(file_paths) else processed_files[i],
                'success': result.get('success', False),
                'url': result.get('url'),
                'error': result.get('error'),
                'key': result.get('key')
            })
        
        # Clean up temporary optimized files
        if optimize and processed_files != valid_files:
            for processed_file in processed_files:
                if processed_file not in valid_files and os.path.exists(processed_file):
                    try:
                        os.remove(processed_file)
                    except Exception as e:
                        await ctx.warning(f"Failed to clean up temporary file {processed_file}: {e}")
        
        processing_time = time.time() - start_time
        overall_success = successful_uploads > 0
        
        await ctx.info(f"Batch upload complete: {successful_uploads}/{len(file_paths)} successful")
        
        return BatchUploadResponse(
            success=overall_success,
            urls=urls,
            errors=errors,
            total_files=len(file_paths),
            successful_uploads=successful_uploads,
            failed_uploads=len(file_paths) - successful_uploads,
            processing_time=processing_time,
            optimization_stats=optimization_stats,
            results=detailed_results
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Unexpected error during batch upload: {str(e)}"
        await ctx.error(error_msg)
        logger.error(error_msg, exc_info=True)
        
        return BatchUploadResponse(
            success=False,
            errors=[error_msg],
            total_files=len(file_paths),
            successful_uploads=0,
            failed_uploads=len(file_paths),
            processing_time=processing_time
        )


async def list_s3_buckets(ctx: Context) -> BucketListResponse:
    """
    List all accessible S3 buckets.
    
    Args:
        ctx: FastMCP Context for logging
    
    Returns:
        BucketListResponse: List of bucket names and status
    """
    try:
        await ctx.info("Fetching S3 bucket list")
        
        if not s3_client:
            return BucketListResponse(
                success=False,
                error="S3 client not initialized"
            )
        
        buckets = await s3_client.list_buckets()
        
        await ctx.info(f"Found {len(buckets)} accessible buckets")
        
        return BucketListResponse(
            success=True,
            buckets=buckets,
            count=len(buckets)
        )
        
    except Exception as e:
        error_msg = f"Error listing S3 buckets: {str(e)}"
        await ctx.error(error_msg)
        logger.error(error_msg, exc_info=True)
        
        return BucketListResponse(
            success=False,
            error=error_msg
        )


async def get_server_info(ctx: Context) -> ServerInfo:
    """
    Get server information and status.
    
    Args:
        ctx: FastMCP Context for logging
    
    Returns:
        ServerInfo: Server information and capabilities
    """
    try:
        await ctx.info("Fetching server information")
        
        return ServerInfo(
            aws_region=s3_client.region if s3_client else None,
            bucket_name=s3_client.bucket_name if s3_client else None
        )
        
    except Exception as e:
        error_msg = f"Error getting server info: {str(e)}"
        await ctx.error(error_msg)
        logger.error(error_msg, exc_info=True)
        
        return ServerInfo(
            status="error",
            aws_region=None,
            bucket_name=None
        )
