"""
AWS S3 Client for MCP Server

Handles S3 operations including file uploads, URL generation, and bucket management.
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from boto3.s3.transfer import TransferConfig

logger = logging.getLogger(__name__)


class S3Client:
    """AWS S3 client wrapper for MCP server operations."""
    
    def __init__(self, region: str, bucket_name: str):
        """
        Initialize S3 client.
        
        Args:
            region: AWS region name
            bucket_name: S3 bucket name
        """
        self.region = region
        self.bucket_name = bucket_name
        
        # Initialize boto3 client
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            logger.info(f"S3 client initialized for region: {region}, bucket: {bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """
        Test S3 connection and bucket access.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Test bucket access
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully connected to S3 bucket: {self.bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                logger.error(f"S3 connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing S3 connection: {e}")
            return False
    
    async def upload_file(
        self,
        file_path: str,
        key: str,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to S3.
        
        Args:
            file_path: Local file path to upload
            key: S3 object key
            metadata: Optional metadata to attach
            content_type: MIME content type
            
        Returns:
            dict: Upload result with URL and metadata
        """
        try:
            # Prepare metadata
            upload_metadata = {
                'uploaded_at': datetime.now(timezone.utc).isoformat(),
                'original_filename': Path(file_path).name,
                'source': 's3-upload-mcp-server'
            }
            if metadata:
                upload_metadata.update(metadata)
            
            # Determine content type
            if not content_type:
                content_type = self._get_content_type(file_path)
            
            # Configure transfer for large files
            file_size = os.path.getsize(file_path)
            transfer_config = TransferConfig(
                multipart_threshold=5 * 1024 * 1024,  # 5MB
                max_concurrency=10,
                use_threads=True
            )
            
            # Upload file
            extra_args = {
                'Metadata': upload_metadata,
                'ContentType': content_type,
                'ACL': 'public-read'  # Make file publicly accessible
            }
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3_client.upload_file(
                    file_path,
                    self.bucket_name,
                    key,
                    ExtraArgs=extra_args,
                    Config=transfer_config
                )
            )
            
            # Generate public URL
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            
            result = {
                'success': True,
                'url': url,
                'key': key,
                'bucket': self.bucket_name,
                'size': file_size,
                'content_type': content_type,
                'metadata': upload_metadata
            }
            
            logger.info(f"Successfully uploaded {file_path} to S3: {url}")
            return result
            
        except ClientError as e:
            error_msg = f"S3 upload error: {e.response['Error']['Message']}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'key': key
            }
        except Exception as e:
            error_msg = f"Unexpected upload error: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'key': key
            }
    
    async def upload_multiple(
        self,
        files: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Upload multiple files concurrently.
        
        Args:
            files: List of file dictionaries with 'file_path' and 'key'
            max_concurrent: Maximum concurrent uploads
            
        Returns:
            List of upload results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def upload_single(file_info: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.upload_file(
                    file_info['file_path'],
                    file_info['key'],
                    file_info.get('metadata'),
                    file_info.get('content_type')
                )
        
        # Execute uploads concurrently
        tasks = [upload_single(file_info) for file_info in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result),
                    'key': files[i].get('key', 'unknown')
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def list_buckets(self) -> List[str]:
        """
        List all accessible S3 buckets.
        
        Returns:
            List of bucket names
        """
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.s3_client.list_buckets
            )
            buckets = [bucket['Name'] for bucket in response['Buckets']]
            logger.info(f"Found {len(buckets)} accessible buckets")
            return buckets
        except ClientError as e:
            logger.error(f"Error listing buckets: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing buckets: {e}")
            return []
    
    def _get_content_type(self, file_path: str) -> str:
        """
        Determine content type based on file extension.
        
        Args:
            file_path: File path
            
        Returns:
            MIME content type
        """
        extension = Path(file_path).suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.ico': 'image/x-icon'
        }
        return content_types.get(extension, 'application/octet-stream')
    
    def generate_key(self, file_path: str, folder_prefix: Optional[str] = None) -> str:
        """
        Generate S3 key from file path.
        
        Args:
            file_path: Local file path
            folder_prefix: Optional folder prefix
            
        Returns:
            S3 object key
        """
        filename = Path(file_path).name
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        
        # Create URL-safe filename
        safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).rstrip()
        safe_filename = f"{safe_name}_{timestamp}{ext}"
        
        if folder_prefix:
            return f"{folder_prefix.rstrip('/')}/{safe_filename}"
        return safe_filename
