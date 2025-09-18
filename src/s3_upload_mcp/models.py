"""
Pydantic Models for S3 Upload MCP Server

Defines data models for type safety and validation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class UploadRequest(BaseModel):
    """Request model for single image upload."""
    file_path: str = Field(..., description="Path to the image file to upload")
    bucket_name: str = Field(..., description="S3 bucket name")
    key: Optional[str] = Field(None, description="S3 object key (auto-generated if not provided)")
    optimize: bool = Field(True, description="Enable image optimization")
    quality: int = Field(80, ge=1, le=100, description="Compression quality (1-100)")
    folder_prefix: Optional[str] = Field(None, description="S3 folder prefix")
    
    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v):
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()
    
    @field_validator('bucket_name')
    @classmethod
    def validate_bucket_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Bucket name cannot be empty")
        return v.strip()


class UploadResponse(BaseModel):
    """Response model for single image upload."""
    success: bool = Field(..., description="Upload success status")
    url: Optional[str] = Field(None, description="Public URL of uploaded image")
    key: Optional[str] = Field(None, description="S3 object key")
    bucket: Optional[str] = Field(None, description="S3 bucket name")
    size: Optional[int] = Field(None, description="File size in bytes")
    content_type: Optional[str] = Field(None, description="MIME content type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Upload metadata")
    error: Optional[str] = Field(None, description="Error message if upload failed")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class BatchUploadRequest(BaseModel):
    """Request model for batch image upload."""
    file_paths: List[str] = Field(..., min_length=1, description="List of image file paths to upload")
    bucket_name: str = Field(..., description="S3 bucket name")
    folder_prefix: Optional[str] = Field(None, description="S3 folder prefix")
    optimize: bool = Field(True, description="Enable image optimization")
    quality: int = Field(80, ge=1, le=100, description="Compression quality (1-100)")
    max_concurrent: int = Field(5, ge=1, le=10, description="Maximum concurrent uploads")
    
    @field_validator('file_paths')
    @classmethod
    def validate_file_paths(cls, v):
        if not v:
            raise ValueError("File paths list cannot be empty")
        for path in v:
            if not path or not path.strip():
                raise ValueError("File path cannot be empty")
        return [path.strip() for path in v]
    
    @field_validator('bucket_name')
    @classmethod
    def validate_bucket_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Bucket name cannot be empty")
        return v.strip()


class BatchUploadResponse(BaseModel):
    """Response model for batch image upload."""
    success: bool = Field(..., description="Overall success status")
    urls: List[str] = Field(default_factory=list, description="List of public URLs")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    total_files: int = Field(..., description="Total number of files processed")
    successful_uploads: int = Field(..., description="Number of successful uploads")
    failed_uploads: int = Field(..., description="Number of failed uploads")
    processing_time: Optional[float] = Field(None, description="Total processing time in seconds")
    optimization_stats: Optional[Dict[str, Any]] = Field(None, description="Image optimization statistics")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed results for each file")


class BucketListResponse(BaseModel):
    """Response model for S3 bucket list."""
    success: bool = Field(..., description="Operation success status")
    buckets: List[str] = Field(default_factory=list, description="List of bucket names")
    count: int = Field(0, description="Number of accessible buckets")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class ImageInfo(BaseModel):
    """Model for image information."""
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    format: str = Field(..., description="Image format")
    mode: str = Field(..., description="Image color mode")
    size_bytes: int = Field(..., description="File size in bytes")
    has_transparency: bool = Field(False, description="Whether image has transparency")


class OptimizationStats(BaseModel):
    """Model for optimization statistics."""
    total_files: int = Field(..., description="Total number of files processed")
    successful: int = Field(..., description="Number of successful optimizations")
    failed: int = Field(..., description="Number of failed optimizations")
    total_original_size: int = Field(..., description="Total original size in bytes")
    total_optimized_size: int = Field(..., description="Total optimized size in bytes")
    compression_ratio: float = Field(..., description="Compression ratio percentage")
    space_saved: int = Field(..., description="Space saved in bytes")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ServerInfo(BaseModel):
    """Server information model."""
    name: str = Field("S3 Upload MCP Server", description="Server name")
    version: str = Field("1.0.0", description="Server version")
    status: str = Field("running", description="Server status")
    aws_region: Optional[str] = Field(None, description="AWS region")
    bucket_name: Optional[str] = Field(None, description="Default S3 bucket")
    supported_formats: List[str] = Field(
        default_factory=lambda: ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.svg'],
        description="Supported image formats"
    )
    max_file_size: int = Field(100 * 1024 * 1024, description="Maximum file size in bytes (100MB)")
    max_concurrent_uploads: int = Field(5, description="Maximum concurrent uploads")
