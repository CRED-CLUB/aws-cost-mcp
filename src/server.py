#!/usr/bin/env python3
"""
AWS Cost MCP server implementation focused on querying Cost and Usage Report data through Athena.
"""
import sys
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
from dotenv import load_dotenv

# Add the parent directory to the Python module search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import FastMCP
from src.athena_client import AthenaClient
from src.utils import (
    get_mcp_server_host,
    get_mcp_server_port,
    get_mcp_log_level,
    datetime_serializer,
)

# Configure logging
log_level = get_mcp_log_level()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Athena client
athena_client = AthenaClient()

# Create MCP server
mcp = FastMCP("AWS Cost MCP Server")

def replace_template_variables(content: str) -> str:
    """
    Replace template variables in the content with actual values from environment variables.
    """
    load_dotenv()
    replacements = {
        "${ATHENA_DATABASE}": os.getenv("ATHENA_DATABASE", "your_cur_database"),
        "${ATHENA_TABLE}": os.getenv("ATHENA_TABLE", "your_cur_table"),
        "${ATHENA_WORKGROUP}": os.getenv("ATHENA_WORKGROUP", "primary"),
        "${ATHENA_OUTPUT_BUCKET}": os.getenv("ATHENA_OUTPUT_LOCATION", "s3://your-bucket/athena-results/").rstrip("/").replace("s3://", "")
    }
    
    # Replace all template variables
    for template_var, value in replacements.items():
        content = content.replace(template_var, value)
    
    return content

# Add resources
script_dir = os.path.dirname(os.path.abspath(__file__))
aws_cost_analysis_path = os.path.join(os.path.dirname(script_dir), "resources", "aws-cost-analysis.md")

@mcp.resource(
    uri="file:///aws-cost-analysis",
    name="How to do Cost analysis via AWS Cost and Usage Reports",
    mime_type="text/markdown",
    description="Reference guide for AWS Cost and Usage Reports analysis including database information, common query patterns, and example queries."
)
def get_aws_cost_analysis():
    with open(aws_cost_analysis_path, "r") as f:
        content = f.read()
    return replace_template_variables(content)

@mcp.tool(name="athena_start_query_execution", description="Starts a query execution using Athena.")
def athena_start_query_execution(
    query_string: str,
    database: Optional[str] = None,
    output_location: Optional[str] = None,
    work_group: Optional[str] = None,
    query_execution_context: Optional[Dict[str, str]] = None,
    result_configuration: Optional[Dict[str, Any]] = None,
    execution_parameters: Optional[List[str]] = None
) -> Dict[str, Any]:
    try:
        response = athena_client.start_query_execution(
            query_string=query_string,
            database=database,
            output_location=output_location,
            work_group=work_group,
            query_execution_context=query_execution_context,
            result_configuration=result_configuration,
            execution_parameters=execution_parameters
        )
        return response
    except Exception as e:
        logger.error(f"Error starting query execution: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool(name="athena_get_query_execution", description="Gets information about a single execution of a query.")
def athena_get_query_execution(query_execution_id: str) -> Dict[str, Any]:
    try:
        response = athena_client.get_query_execution(query_execution_id=query_execution_id)
        return response
    except Exception as e:
        logger.error(f"Error getting query execution: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool(name="athena_get_query_results", description="Returns the results of a query execution specified by query execution ID.")
def athena_get_query_results(
    query_execution_id: str,
    next_token: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    try:
        response = athena_client.get_query_results(
            query_execution_id=query_execution_id,
            next_token=next_token,
            max_results=max_results
        )
        return response
    except Exception as e:
        logger.error(f"Error getting query results: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool(name="athena_stop_query_execution", description="Stops a query execution.")
def athena_stop_query_execution(query_execution_id: str) -> Dict[str, Any]:
    try:
        response = athena_client.stop_query_execution(query_execution_id=query_execution_id)
        return response
    except Exception as e:
        logger.error(f"Error stopping query execution: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool(name="athena_list_query_executions", description="Returns a list of query execution IDs.")
def athena_list_query_executions(
    work_group: Optional[str] = None,
    next_token: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    try:
        response = athena_client.list_query_executions(
            work_group=work_group,
            next_token=next_token,
            max_results=max_results
        )
        return response
    except Exception as e:
        logger.error(f"Error listing query executions: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool(name="athena_list_databases", description="Lists the databases in the specified data catalog.")
def athena_list_databases(
    catalog_name: Optional[str] = None,
    next_token: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    try:
        response = athena_client.list_databases(
            catalog_name=catalog_name,
            next_token=next_token,
            max_results=max_results
        )
        return response
    except Exception as e:
        logger.error(f"Error listing databases: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool(name="athena_list_table_metadata", description="Lists the tables in the specified data catalog database.")
def athena_list_table_metadata(
    database_name: str,
    catalog_name: Optional[str] = None,
    expression: Optional[str] = None,
    next_token: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    try:
        response = athena_client.list_table_metadata(
            database_name=database_name,
            catalog_name=catalog_name,
            expression=expression,
            next_token=next_token,
            max_results=max_results
        )
        return response
    except Exception as e:
        logger.error(f"Error listing table metadata: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool(name="athena_run_query", description="Runs a query and optionally waits for its completion.")
def athena_run_query(
    query_string: str,
    database: Optional[str] = None,
    output_location: Optional[str] = None,
    work_group: Optional[str] = None,
    wait_for_completion: bool = True,
    poll_interval: int = 1,
    max_wait_time: int = 300
) -> Dict[str, Any]:
    try:
        
        response = athena_client.run_query(
            query_string=query_string,
            database=database,
            output_location=output_location,
            work_group=work_group,
            wait_for_completion=wait_for_completion,
            poll_interval=poll_interval,
            max_wait_time=max_wait_time
        )
        return response
    except Exception as e:
        logger.error(f"Error running query: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    host = get_mcp_server_host()
    port = get_mcp_server_port()
    load_dotenv()
    logger.info(f"Starting AWS Cost MCP server on {host}:{port}")
    mcp.run()
