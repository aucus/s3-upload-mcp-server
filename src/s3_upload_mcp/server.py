"""
AWS S3 Upload MCP Server

A high-performance MCP server for uploading images to AWS S3,
specifically designed for Figma → MCP → HTML workflows.
"""

import os
import logging
from typing import Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

from .tools import upload_image_to_s3, batch_upload_images, list_s3_buckets, get_server_info, set_global_instances
from .s3_client import S3Client
from .image_processor import ImageProcessor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("S3 Upload Server")

# Global instances
s3_client: Optional[S3Client] = None
image_processor: Optional[ImageProcessor] = None


def initialize_services() -> None:
    """Initialize S3 client and image processor with environment variables."""
    global s3_client, image_processor
    
    # Get AWS configuration from environment
    aws_region = os.getenv("AWS_REGION", "ap-northeast-2")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    
    if not bucket_name:
        raise ValueError("S3_BUCKET_NAME environment variable is required")
    
    # Initialize services
    s3_client = S3Client(region=aws_region, bucket_name=bucket_name)
    image_processor = ImageProcessor()
    
    # Set global instances for tools
    set_global_instances(s3_client, image_processor)
    
    logger.info(f"S3 Upload Server initialized with region: {aws_region}, bucket: {bucket_name}")




def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Initialize services
        initialize_services()
        
        # Register tools
        mcp.tool(upload_image_to_s3)
        mcp.tool(batch_upload_images)
        mcp.tool(list_s3_buckets)
        mcp.tool(get_server_info)
        
        # Run the server
        logger.info("Starting S3 Upload MCP Server...")
        mcp.run()
        
    except Exception as e:
        logger.error(f"Failed to start S3 Upload MCP Server: {e}")
        raise


if __name__ == "__main__":
    main()
