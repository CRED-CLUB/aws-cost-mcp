# AWS Cost MCP Server

An MCP server focused on querying AWS Cost and Usage Report (CUR) data through Amazon Athena. This server provides tools to analyze AWS cost data efficiently through the Model Context Protocol.

## Features

- Query AWS Cost and Usage Report data through Athena
  - More cost-effective than Cost Explorer API (pay only for the queries you run)
  - Access to detailed, raw cost data with granular resource-level insights
  - Access to historical data to do in-depth cost trend analysis
  - No API rate limits or throttling constraints
- Execute and manage Athena queries

## Prerequisites

- Python 3.10+
- AWS credentials configured with access to Athena and CUR
- AWS Cost and Usage Reports set up with Athena integration

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/aws-cost-mcp.git
    cd aws-cost-mcp
    ```

2. Run the setup script:
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

    The setup script will:
    - Create a Python virtual environment
    - Install required dependencies
    - Create a `.env` file from `.env.example`

3. Configure your environment:

    Edit the `.env` file with your settings:
    ```
    # MCP Server Configuration
    MCP_SERVER_HOST=localhost
    MCP_SERVER_PORT=5004
    MCP_LOG_LEVEL=INFO

    # AWS Configuration
    AWS_REGION=us-east-1
    AWS_ACCESS_KEY_ID=your_access_key
    AWS_SECRET_ACCESS_KEY=your_secret_key

    # Athena Configuration (Optional - used as defaults if not provided in queries)
    ATHENA_OUTPUT_LOCATION=s3://your-bucket/athena-results/
    ATHENA_DATABASE=your_cur_database
    ATHENA_TABLE=your_cur_table
    ATHENA_WORKGROUP=primary
    ATHENA_CATALOG=your_cur_catalog(AwsDataCatalog)
    ```

## Connecting to Cline

To connect this MCP server to Cline, you need to update the `cline_mcp_settings.json` file.

Add a configuration like the following to the `mcpServers` section:

```json
{
  "mcpServers": {
    "aws": {
      "command": "absolute_path..../aws-cost-mcp/venv/bin/python",
      "args": [
        "absolute_path..../aws-cost-mcp/src/server.py"
      ],
      "env": {},
      "disabled": false,
      "autoApprove": [],
      "workingDirectory": "absolute_path..../aws-cost-mcp"
    }
  }
}
```

You can configure CLINE with the Custom Instructions available in cline_custom_instructions.txt to receive a detailed cost analysis.

Example query:
```
Using only the configured aws-cost-mcp server's resources and tools, graphically anaylse the ec2 cost trend across jan and feb 2025.
```
Cline response: 

<img width="805" alt="Screenshot 2025-03-24 at 9 33 15 PM" src="https://github.com/user-attachments/assets/1808240d-8404-41a7-8455-598746a02070" />


## Usage

### Running the MCP Server

#### For Development and Testing

Use the MCP CLI's development mode, which provides interactive testing capabilities:

```bash
mcp dev src/server.py
```

#### For Production

Use the MCP CLI's run command:

```bash
mcp run src/server.py
```

By default, the server will use the configuration in the `.env` file:

```
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8080
MCP_LOG_LEVEL=INFO
```


## Documentation

The project documentation is organized in the `cline_docs` directory:

- `projectRoadmap.md`: Project goals, features, and progress tracking
- `currentTask.md`: Current objectives and next steps
- `techStack.md`: Technology choices and architecture decisions
- `codebaseSummary.md`: Project structure and component overview

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.
