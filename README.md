# AWS S3 Upload MCP Server

A high-performance MCP (Model Context Protocol) server for uploading images to AWS S3, specifically designed for Figma → MCP → HTML workflows.

## 🎯 Features

- **FastMCP Framework**: Built with the high-performance Pythonic MCP library
- **Image Processing**: Automatic optimization, WebP conversion, and compression
- **Batch Upload**: Parallel processing for multiple images
- **AWS S3 Integration**: Secure upload with proper IAM permissions
- **Type Safety**: Full Pydantic model validation
- **Async Support**: Non-blocking operations with asyncio

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- AWS Account with S3 access
- `uv` package manager (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/s3-upload-mcp-server.git
cd s3-upload-mcp-server

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

### Environment Setup

Create a `.env` file in the project root:

```bash
# Copy env.example to .env and update with your values
cp env.example .env

# Edit .env with your AWS credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=your-bucket-name
```

### Running the Server

```bash
# STDIO transport (for Claude Desktop)
uv run fastmcp run src/server.py

# HTTP transport (for web clients)
uv run python -m src.server -- --transport http --port 8000
```

## 🛠️ MCP Tools

### `upload_image_to_s3`
Upload a single image file to S3 and return a public URL.

**Parameters:**
- `file_path` (str): Path to the image file
- `bucket_name` (str): S3 bucket name
- `key` (str, optional): S3 object key (auto-generated if not provided)
- `optimize` (bool): Enable image optimization (default: True)
- `quality` (int): Compression quality 1-100 (default: 80)

**Returns:**
- `success` (bool): Upload success status
- `url` (str): Public URL of uploaded image
- `error` (str): Error message if failed
- `metadata` (dict): Upload metadata

### `batch_upload_images`
Upload multiple images in parallel to S3.

**Parameters:**
- `file_paths` (List[str]): List of image file paths
- `bucket_name` (str): S3 bucket name
- `folder_prefix` (str, optional): S3 folder prefix
- `optimize` (bool): Enable image optimization (default: True)

**Returns:**
- `success` (bool): Overall success status
- `urls` (List[str]): List of public URLs
- `errors` (List[str]): List of error messages
- `total_files` (int): Total number of files
- `successful_uploads` (int): Number of successful uploads

### `list_s3_buckets`
List all accessible S3 buckets.

**Returns:**
- `success` (bool): Operation success status
- `buckets` (List[str]): List of bucket names
- `error` (str): Error message if failed

## 🔧 Claude Desktop Integration

Add to your Claude Desktop configuration:

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

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_tools.py
```

## 📊 Performance

- **Upload Speed**: < 3 seconds for 1MB images
- **Parallel Processing**: Up to 5 files simultaneously
- **Memory Usage**: < 100MB
- **CPU Usage**: < 50% single core

## 🔒 Security

- Environment variable authentication
- IAM role support for EC2/Lambda
- HTTPS/TLS 1.2+ encryption
- S3 server-side encryption
- Least privilege access

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions, please open an issue on GitHub.
