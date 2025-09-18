"""
AWS S3 Upload MCP Server

A high-performance MCP server for uploading images to AWS S3,
specifically designed for Figma → MCP → HTML workflows.
"""

__version__ = "1.0.0"
__author__ = "AI Agent Development Team"

from .server import main

__all__ = ["main"]
