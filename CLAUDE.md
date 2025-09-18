# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AWS S3 Upload MCP (Model Context Protocol) Server project designed to integrate with the Figma → MCP → HTML → Cursor Rules workflow. The server enables automatic upload of image files extracted from Figma to AWS S3 storage, returning public URLs for immediate use in HTML development.

## Commands

Since this is a Python MCP server project using `uv` package manager:

```bash
# Install dependencies
uv sync

# Run the MCP server
uv run s3-upload-mcp-server

# Run tests (when implemented)
uv run pytest

# Run linting (when configured)
uv run ruff check

# Run type checking (when configured)
uv run mypy src/
```

## Project Architecture

### Core Structure
This MCP server uses the FastMCP framework architecture:

```
src/s3_upload_mcp/
├── server.py          # FastMCP server with tool registration
├── tools.py           # FastMCP tool implementations with decorators
├── image_processor.py # Image optimization and format conversion
└── s3_client.py       # AWS S3 client wrapper with async operations
```

### FastMCP Implementation Pattern
The server leverages FastMCP's decorator-based approach for simplicity:

```python
from fastmcp import FastMCP, Context
from pydantic import BaseModel

mcp = FastMCP("S3 Upload Server")

@mcp.tool
async def upload_image_to_s3(
    file_path: str,
    bucket_name: str,
    key: str = None,
    optimize: bool = True,
    quality: int = 80,
    ctx: Context
) -> dict:
    """Upload image to S3 with automatic optimization"""
    await ctx.info(f"Uploading {file_path} to {bucket_name}")
    # Implementation logic...
```

### Key FastMCP Tools to Implement

1. **upload_image_to_s3** - Single image upload with optimization
   - Uses `@mcp.tool` decorator with automatic type validation
   - Context injection for logging and progress reporting
   - Pydantic response models for structured output

2. **batch_upload_images** - Parallel batch upload processing
   - Async implementation with concurrent file handling
   - Real-time progress updates via Context
   - Structured error reporting for partial failures

3. **list_s3_buckets** - Available S3 bucket enumeration
   - Simple decorator-based implementation
   - Automatic schema generation from function signature

### Technology Stack
- **Language**: Python 3.10+
- **MCP Framework**: `fastmcp` (high-performance Pythonic MCP library)
- **AWS Integration**: `boto3` for S3 operations
- **Image Processing**: `Pillow` (PIL) for optimization and format conversion
- **Type Validation**: `pydantic` (built into FastMCP)
- **Async Operations**: `asyncio` and `aiohttp` for concurrent uploads
- **Package Management**: `uv` (recommended)

### Image Processing Requirements
- **Supported Formats**: PNG, JPG, JPEG, SVG, WebP
- **Auto WebP Conversion**: Optional feature with 80% default quality
- **Optimization**: Resize to max 1920x1080, compress with configurable quality
- **Security**: URL-safe filename normalization

### AWS S3 Integration
- **Authentication**: Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) or IAM roles
- **Permissions Required**: s3:PutObject, s3:PutObjectAcl, s3:GetObject, s3:ListBucket
- **Features**: Multipart upload for files >5MB, metadata tagging, CORS configuration
- **Performance**: Maximum 5 concurrent uploads, target 3 seconds per 1MB image

### Configuration Management
Essential environment variables:
- `AWS_REGION` (default: ap-northeast-2)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET_NAME`

### Error Handling Strategy
- **FastMCP Context**: Built-in logging and error reporting via `ctx.error()`, `ctx.warn()`
- **Retry Logic**: Exponential backoff algorithm for transient failures
- **Circuit Breaker**: Temporary suspension after consecutive failures
- **Graceful Degradation**: Partial success reporting for batch operations
- **Pydantic Validation**: Automatic input/output validation with clear error messages
- **Structured Logging**: FastMCP's integrated logging system with JSON output

### Claude Desktop Integration
The server integrates with Claude Desktop via MCP configuration:

```json
{
  "mcpServers": {
    "s3-upload": {
      "command": "uv",
      "args": ["run", "s3-upload-mcp-server"],
      "env": {
        "AWS_REGION": "ap-northeast-2",
        "S3_BUCKET_NAME": "figma-assets-bucket"
      }
    }
  }
}
```

## Development Guidelines

### Code Style Requirements
- Follow PEP 8 standards
- Mandatory type hints for all functions (FastMCP enforces this)
- Google-style docstrings for tool descriptions
- Async/await pattern for I/O operations
- Use Pydantic models for complex input/output structures
- Leverage FastMCP's `@mcp.tool` decorator pattern

### Performance Constraints
- Memory usage: <100MB
- CPU usage: <50% single core
- Upload target: 3 seconds per 1MB image
- Concurrent uploads: Maximum 5 files

### Security Best Practices
- Never expose AWS credentials in code
- Use environment variables for sensitive configuration
- Implement minimum IAM permissions principle
- Enable S3 server-side encryption
- Use HTTPS/TLS 1.2+ for all transfers

## FastMCP Implementation Guide

### Server Setup Pattern
```python
from fastmcp import FastMCP
from s3_upload_mcp.tools import upload_image_to_s3, batch_upload_images, list_s3_buckets

mcp = FastMCP("S3 Upload Server")

# Register tools
mcp.tool(upload_image_to_s3)
mcp.tool(batch_upload_images)
mcp.tool(list_s3_buckets)

if __name__ == "__main__":
    mcp.run()  # STDIO transport (default)
```

### Response Model Pattern
```python
from pydantic import BaseModel
from typing import Optional, List

class UploadResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None
    metadata: dict

class BatchUploadResponse(BaseModel):
    success: bool
    urls: List[str] = []
    errors: List[str] = []
    total_files: int
    successful_uploads: int
```

### Context Usage Pattern
```python
@mcp.tool
async def upload_image_to_s3(file_path: str, ctx: Context) -> UploadResponse:
    await ctx.info(f"Starting upload: {file_path}")
    try:
        # Upload logic
        await ctx.progress(0.5)  # 50% complete
        result = await upload_to_s3(file_path)
        await ctx.info("Upload completed successfully")
        return UploadResponse(success=True, url=result.url)
    except Exception as e:
        await ctx.error(f"Upload failed: {str(e)}")
        return UploadResponse(success=False, error=str(e))
```

## Important Implementation Notes

This project uses FastMCP framework for simplified MCP server development. Key references:
- PRD.md: Comprehensive product requirements document
- .cursorrules: FastMCP-specific development guidelines and tool specifications

FastMCP advantages for this project:
- **Automatic Schema Generation**: Function signatures become MCP tool schemas
- **Built-in Type Validation**: Pydantic integration prevents runtime type errors
- **Context Integration**: Real-time logging, progress updates, and error reporting
- **Testing Support**: In-memory client for unit testing MCP tools
- **Multiple Transports**: STDIO (default), HTTP, and SSE support