"""
Utility functions for the AWS MCP server.
"""

import os
from datetime import datetime

def get_mcp_server_host() -> str:
    """
    Get the MCP server host from environment variables.
    
    Returns:
        str: The MCP server host.
    """
    return os.getenv("MCP_SERVER_HOST", "127.0.0.1")

def get_mcp_server_port() -> int:
    """
    Get the MCP server port from environment variables.
    
    Returns:
        int: The MCP server port.
    """
    port = os.getenv("MCP_SERVER_PORT", "6543")
    return int(port)

def get_mcp_log_level() -> str:
    """
    Get the MCP log level from environment variables.
    
    Returns:
        str: The MCP log level.
    """
    return os.getenv("MCP_LOG_LEVEL", "INFO")

def filter_none_params(params):
    """Remove None values from a dictionary."""
    return {k: v for k, v in params.items() if v is not None}

def get_athena_database() -> str:
    """
    Get the Athena database name from environment variables.
    
    Returns:
        str: The Athena database name.
    """
    return os.getenv("ATHENA_DATABASE", "your_cur_database")

def get_athena_workgroup() -> str:
    """
    Get the Athena workgroup from environment variables.
    
    Returns:
        str: The Athena workgroup.
    """
    return os.getenv("ATHENA_WORKGROUP", "primary")

def get_athena_output_location() -> str:
    """
    Get the Athena output location from environment variables.
    
    Returns:
        str: The Athena output location.
    """
    return os.getenv("ATHENA_OUTPUT_LOCATION", "s3://your-bucket/athena-results/")

def datetime_serializer(obj):
    """
    Serialize datetime objects to ISO 8601 format.
    
    Args:
        obj: The object to serialize.
        
    Returns:
        str: The ISO 8601 formatted date string.
        
    Raises:
        TypeError: If the object is not serializable.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
