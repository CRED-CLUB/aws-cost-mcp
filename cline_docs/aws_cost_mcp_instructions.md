# AWS Cost MCP Usage Instructions

## Overview
The aws-cost-mcp server provides tools to analyze AWS cost and usage data through Athena queries. This guide explains how to effectively use these tools for cost analysis.

## Database Information
- Database Name: `athenacurcfn_dp_hourly_cost_report`
- Main Table: `dp_hourly_cost_report`
- Data is partitioned by `year` and `month`

## Available Tools

### 1. athena_run_query
Primary tool for executing cost analysis queries. Example usage:
```python
{
  "query_string": "YOUR_QUERY",
  "database": "athenacurcfn_dp_hourly_cost_report"
}
```

### 2. athena_list_databases
Lists available Athena databases. Requires catalog name:
```python
{
  "catalog_name": "AwsDataCatalog"
}
```

### 3. athena_list_table_metadata
Lists table metadata. Requires both catalog and database names:
```python
{
  "catalog_name": "AwsDataCatalog",
  "database_name": "athenacurcfn_dp_hourly_cost_report"
}
```

## Common Query Patterns

### 1. Finding Costliest Resources
```sql
SELECT 
    line_item_resource_id,
    resource_tags_user_name,
    product_product_name,
    line_item_product_code,
    SUM(CAST(line_item_unblended_cost AS DECIMAL(16,8))) AS total_cost,
    line_item_usage_account_id
FROM 
    dp_hourly_cost_report
WHERE 
    year = '[YEAR]'
    AND month = '[MONTH]'
    AND product_product_name = '[SERVICE_NAME]'
    AND line_item_line_item_type IN ('DiscountedUsage', 'Usage', 'SavingsPlanCoveredUsage')
GROUP BY 
    line_item_resource_id,
    resource_tags_user_name,
    product_product_name,
    line_item_product_code,
    line_item_usage_account_id
ORDER BY 
    total_cost DESC
LIMIT 1
```

### 2. Cost Analysis Best Practices
1. Always include year and month in WHERE clause for partitioned queries
2. Use appropriate line_item_line_item_type filters:
   - 'DiscountedUsage'
   - 'Usage'
   - 'SavingsPlanCoveredUsage'
3. Cast costs to DECIMAL(16,8) for accurate calculations
4. Include relevant resource identifiers and tags in GROUP BY for detailed analysis

## Important Fields

### Resource Identification
- `line_item_resource_id`: Unique identifier for resources
- `resource_tags_user_name`: Resource name tag
- `product_product_name`: AWS service name
- `line_item_product_code`: Service code (e.g., AmazonEC2)

### Cost Fields
- `line_item_unblended_cost`: Cost before discounts
- `line_item_line_item_type`: Type of cost (Usage, DiscountedUsage, etc.)

### Time Fields
- `year`: Partition field for year
- `month`: Partition field for month
- `line_item_usage_start_date`: Timestamp when usage started

## Tips
1. Always verify database and table names first
2. Use appropriate filters to reduce data scanning
3. Include resource tags for better identification
4. Cast cost fields to DECIMAL for accurate calculations
5. Use LIMIT clause for testing queries before running full analysis

## Error Handling
Common errors and solutions:
1. "SCHEMA_NOT_FOUND": Verify database name and use `athena_list_databases`
2. "TABLE_NOT_FOUND": Verify table name within the database
3. "SYNTAX_ERROR": Check SQL syntax and field names

## Example Workflow
1. List databases to confirm names
2. Verify table metadata if needed
3. Run cost analysis query with appropriate filters
4. Process and analyze results

This guide will help you effectively use the aws-cost-mcp server for AWS cost analysis tasks.
