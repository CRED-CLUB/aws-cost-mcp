# AWS Cost Analysis using AWS Cost and Usage Reports Reference Guide

## Initial Setup and Verification

### Database and Table Verification
Before running any queries, always verify the correct database and table names:

 **Verify Table Access**:
```sql
-- Simple test query to verify table access
SELECT COUNT(1) as record_count
FROM ${ATHENA_TABLE}
WHERE year = '${YEAR}' 
  AND month = '${MONTH}'
LIMIT 1;
```

## Database and Table Information

- **Database Name**: `${ATHENA_DATABASE}`
- **Table Name**: `${ATHENA_TABLE}`

## Common Query Patterns

### Basic Cost Query Structure
```sql
SELECT
    [resource identifiers],
    [time period],
    SUM(CAST(line_item_unblended_cost AS DECIMAL(16,8))) AS total_cost
FROM
    ${ATHENA_TABLE}
WHERE
    year = '${YEAR}'
    AND month = '${MONTH}'
    [additional filters]
GROUP BY
    [resource identifiers],
    [time period]
ORDER BY
    total_cost DESC
LIMIT ${RESULT_LIMIT}
```

## Important Columns

### Time Period Columns
- `year` - Year of the cost data (e.g., '2024', '2025')
- `month` - Month of the cost data (e.g., '1', '2', '12')
- `line_item_usage_start_date` - Timestamp when usage started

### Resource Identification Columns
- `line_item_resource_id` - Unique identifier for the resource (e.g., EC2 instance ID, NAT Gateway ID)
- `product_product_name` - AWS service name (e.g., 'Amazon Elastic Compute Cloud', 'Amazon CloudFront')
- `line_item_product_code` - Short code for the AWS service (e.g., 'AmazonEC2', 'AmazonRDS')
- `line_item_usage_account_id` - AWS account ID where the resource is deployed
- `bill_payer_account_id` - AWS account ID that pays for the resource

### Resource Tag Columns
- `resource_tags_user_Name` - The "Name" tag of the resource
- `resource_tags_user_pod` - The "pod" tag of the resource (e.g., 'sre')
- `resource_tags_user_[TagName]` - Other user-defined tags

### Cost and Usage Columns
- `line_item_unblended_cost` - The cost of the line item (before discounts)
- `line_item_usage_amount` - The amount of usage
- `line_item_usage_type` - The type of usage (e.g., 'DataTransfer-Out-Bytes', 'Requests')
- `line_item_line_item_type` - The type of line item (e.g., 'Usage', 'DiscountedUsage', 'SavingsPlanCoveredUsage')

## Example Queries

### 1. Compare Costs Between Time Periods for EC2-Other Services
```sql
-- Compare EC2-other costs between two months
WITH period1_costs AS (
    SELECT 
        line_item_usage_type, 
        SUM(CAST(line_item_unblended_cost AS DECIMAL(16,8))) as period1_cost 
    FROM 
        ${ATHENA_TABLE}
    WHERE 
        year = '${YEAR}' 
        AND month = '${MONTH1}' 
        AND product_product_name LIKE '%${SERVICE_NAME}%' 
        AND line_item_line_item_type IN (${LINE_ITEM_TYPES})
        AND line_item_resource_id NOT LIKE '${RESOURCE_PREFIX}%'
    GROUP BY 
        line_item_usage_type
), 
period2_costs AS (
    SELECT 
        line_item_usage_type, 
        SUM(CAST(line_item_unblended_cost AS DECIMAL(16,8))) as period2_cost 
    FROM 
        ${ATHENA_TABLE}
    WHERE 
        year = '${YEAR}' 
        AND month = '${MONTH2}' 
        AND product_product_name LIKE '%${SERVICE_NAME}%' 
        AND line_item_line_item_type IN (${LINE_ITEM_TYPES})
        AND line_item_resource_id NOT LIKE '${RESOURCE_PREFIX}%'
    GROUP BY 
        line_item_usage_type
) 
SELECT 
    COALESCE(p2.line_item_usage_type, p1.line_item_usage_type) as usage_type, 
    COALESCE(p1.period1_cost, 0) as period1_cost, 
    COALESCE(p2.period2_cost, 0) as period2_cost, 
    COALESCE(p2.period2_cost, 0) - COALESCE(p1.period1_cost, 0) as cost_increase, 
    CASE 
        WHEN COALESCE(p1.period1_cost, 0) > 0 
        THEN ((COALESCE(p2.period2_cost, 0) - COALESCE(p1.period1_cost, 0)) / COALESCE(p1.period1_cost, 0) * 100) 
        ELSE NULL 
    END as percentage_increase 
FROM 
    period2_costs p2 
FULL OUTER JOIN 
    period1_costs p1 
ON 
    p2.line_item_usage_type = p1.line_item_usage_type 
ORDER BY 
    cost_increase DESC
LIMIT ${RESULT_LIMIT};
```

### 2. Identify New Resources Contributing to Cost Increases
```sql
-- Find new resources that weren't present in the previous period
WITH period1_resources AS (
    SELECT DISTINCT line_item_resource_id 
    FROM ${ATHENA_TABLE}
    WHERE 
        year = '${YEAR}' 
        AND month = '${MONTH1}' 
        AND product_product_name LIKE '%${SERVICE_NAME}%' 
        AND line_item_usage_type = '${USAGE_TYPE}'
), 
period2_resources AS (
    SELECT DISTINCT line_item_resource_id 
    FROM ${ATHENA_TABLE}
    WHERE 
        year = '${YEAR}' 
        AND month = '${MONTH2}' 
        AND product_product_name LIKE '%${SERVICE_NAME}%' 
        AND line_item_usage_type = '${USAGE_TYPE}'
), 
new_resources AS (
    SELECT p2.line_item_resource_id 
    FROM period2_resources p2 
    LEFT JOIN period1_resources p1 
    ON p2.line_item_resource_id = p1.line_item_resource_id 
    WHERE p1.line_item_resource_id IS NULL
), 
resource_costs AS (
    SELECT 
        nr.line_item_resource_id, 
        resource_tags_user_Name, 
        SUM(CAST(line_item_unblended_cost AS DECIMAL(16,8))) as cost 
    FROM 
        ${ATHENA_TABLE}
    JOIN 
        new_resources nr 
    ON 
        ${ATHENA_TABLE}.line_item_resource_id = nr.line_item_resource_id 
    WHERE 
        year = '${YEAR}' 
        AND month = '${MONTH2}' 
        AND line_item_usage_type = '${USAGE_TYPE}' 
    GROUP BY 
        nr.line_item_resource_id, 
        resource_tags_user_Name
) 
SELECT * FROM resource_costs 
ORDER BY cost DESC 
LIMIT ${RESULT_LIMIT};
```

### 3. Analyze Cost Increases by Resource Tags
```sql
-- Analyze cost increases with resource tags between two periods
WITH period1_costs AS (
    SELECT 
        line_item_resource_id, 
        resource_tags_user_Name, 
        resource_tags_user_pod,
        SUM(CAST(line_item_unblended_cost AS DECIMAL(16,8))) as period1_cost 
    FROM 
        ${ATHENA_TABLE}
    WHERE 
        year = '${YEAR}' 
        AND month = '${MONTH1}' 
        AND product_product_name LIKE '%${SERVICE_NAME}%' 
        AND line_item_usage_type = '${USAGE_TYPE}' 
    GROUP BY 
        line_item_resource_id, 
        resource_tags_user_Name,
        resource_tags_user_pod
), 
period2_costs AS (
    SELECT 
        line_item_resource_id, 
        resource_tags_user_Name, 
        resource_tags_user_pod,
        SUM(CAST(line_item_unblended_cost AS DECIMAL(16,8))) as period2_cost 
    FROM 
        ${ATHENA_TABLE}
    WHERE 
        year = '${YEAR}' 
        AND month = '${MONTH2}' 
        AND product_product_name LIKE '%${SERVICE_NAME}%' 
        AND line_item_usage_type = '${USAGE_TYPE}' 
    GROUP BY 
        line_item_resource_id, 
        resource_tags_user_Name,
        resource_tags_user_pod
) 
SELECT 
    COALESCE(p1.line_item_resource_id, p2.line_item_resource_id) as resource_id, 
    COALESCE(p1.resource_tags_user_Name, p2.resource_tags_user_Name) as resource_name, 
    COALESCE(p1.resource_tags_user_pod, p2.resource_tags_user_pod) as pod,
    COALESCE(p1.period1_cost, 0) as period1_cost, 
    COALESCE(p2.period2_cost, 0) as period2_cost, 
    COALESCE(p2.period2_cost, 0) - COALESCE(p1.period1_cost, 0) as cost_increase, 
    CASE 
        WHEN COALESCE(p1.period1_cost, 0) > 0 
        THEN ((COALESCE(p2.period2_cost, 0) - COALESCE(p1.period1_cost, 0)) / COALESCE(p1.period1_cost, 0) * 100) 
        ELSE NULL 
    END as percentage_increase 
FROM 
    period1_costs p1 
FULL OUTER JOIN 
    period2_costs p2 
ON 
    p1.line_item_resource_id = p2.line_item_resource_id 
ORDER BY 
    cost_increase DESC 
LIMIT ${RESULT_LIMIT};
```

### 4. Find Highest Costing Resource
```sql
SELECT
    line_item_resource_id,
    resource_tags_user_Name,
    product_instance_type,
    SUM(CAST(line_item_unblended_cost AS DECIMAL(16,8))) AS total_cost
FROM
    ${ATHENA_TABLE}
WHERE
    year = '${YEAR}'
    AND month = '${MONTH}'
    AND product_product_name = '${SERVICE_NAME}'
    AND line_item_resource_id LIKE '${RESOURCE_PREFIX}%'
GROUP BY
    line_item_resource_id,
    resource_tags_user_Name,
    product_instance_type
ORDER BY
    total_cost DESC
LIMIT ${RESULT_LIMIT};
```

## Managing Query Performance and Result Size

### Checking and Limiting Result Size

To prevent excessive resource usage and timeout issues, always implement strategies to limit both the amount of data scanned and the size of the result set:

```sql
-- First run a COUNT query to check potential result size
SELECT COUNT(*) AS potential_result_count
FROM ${ATHENA_TABLE}
WHERE
    year = '${YEAR}'
    AND month = '${MONTH}'
    AND line_item_product_code = '${PRODUCT_CODE}';
```

If the count is too large (e.g., over 10,000 rows), consider:
1. Adding more specific filters
2. Aggregating at a higher level
3. Sampling the data
4. Breaking the query into smaller time periods

### Sampling Data for Large Datasets

When dealing with very large datasets, consider using sampling techniques:

```sql
-- Sample approximately ${SAMPLE_PERCENTAGE}% of data using a hash function
SELECT
    line_item_resource_id,
    SUM(CAST(line_item_unblended_cost AS DECIMAL(16,8))) AS total_cost
FROM
    ${ATHENA_TABLE}
WHERE
    year = '${YEAR}'
    AND month = '${MONTH}'
    -- Use hash of resource ID for consistent sampling
    AND MOD(CAST(ABS(HASH(line_item_resource_id)) AS BIGINT), ${SAMPLE_DENOMINATOR}) = 0
GROUP BY
    line_item_resource_id
ORDER BY
    total_cost DESC
LIMIT ${RESULT_LIMIT};
```

### Using Partitioning Efficiently

Athena uses partitioning to improve query performance. Always include partition columns in your WHERE clause:

```sql
-- Good: Uses partition columns
SELECT * FROM ${ATHENA_TABLE}
WHERE year = '${YEAR}' AND month = '${MONTH}';

-- Better: Uses partition columns and additional filters
SELECT * FROM ${ATHENA_TABLE}
WHERE year = '${YEAR}' AND month = '${MONTH}' 
AND line_item_product_code = '${PRODUCT_CODE}';

-- Avoid: Doesn't use partition columns efficiently
SELECT * FROM ${ATHENA_TABLE}
WHERE line_item_usage_start_date BETWEEN '${START_DATE}' AND '${END_DATE}';
```

## Tips for Cost Analysis

### General Best Practices

1. **Filter by Time Period**: Always include year and month filters to limit the data scanned and improve query performance. Consider narrowing to specific days if analyzing high-volume services.

### Analyzing Cost Increases Between Time Periods

1. **Start with High-Level Comparison**:
   - First compare total costs by usage type to identify the major contributors to cost increases
   - Use COALESCE and FULL OUTER JOIN to handle resources that may exist in only one time period
   - Calculate both absolute cost difference and percentage increase

2. **Identify New Resources**:
   - Use LEFT JOIN between current and previous period to find new resources
   - Check resource tags to understand which team/service owns new resources
   - Look for patterns in resource names or tags that might indicate systematic changes

3. **Analyze Resource-Level Changes**:
   - For resources present in both periods, analyze usage pattern changes
   - Pay special attention to resources with large percentage increases
   - Group resources by tags (e.g., pod, service) to identify team-level patterns

4. **Deep Dive into Specific Services**:
   - For services like EBS, analyze different cost components separately (e.g., storage vs IOPS)
   - Consider the relationship between different metrics (e.g., increased IOPS often correlates with increased volume size)
   - Look for configuration changes that might explain cost increases

5. **Document Findings with Context**:
   - Include resource names and tags in your analysis
   - Calculate both absolute and percentage changes
   - Group related resources together (e.g., all volumes belonging to the same service)
   - Note any relevant system changes or deployments during the period

6. **Common Cost Increase Patterns**:
   - New resources being provisioned
   - Configuration changes to existing resources
   - Increased usage of existing resources
   - Changes in pricing or billing structure
   - Resource tagging changes affecting cost allocation

### Other Best Practices

1. **Use Specific Filters**: Apply as many specific filters as possible (account IDs, service names, resource IDs) to reduce the amount of data processed.

2. **Check Result Size First**: Run a COUNT query before executing complex aggregations to estimate result size and adjust your query if needed.

3. **Implement Result Limits**: Always use LIMIT in your queries, typically between 10-100 rows depending on your needs.

4. **Group by Resource Identifiers**: Group by resource IDs, account IDs, and other relevant identifiers to get costs per resource.

5. **Use CASE Statements for Cost Breakdowns**: Use CASE statements to categorize costs by usage type or other criteria.

6. **Cast Costs to DECIMAL**: Always cast line_item_unblended_cost to DECIMAL(16,8) for accurate calculations.

7. **Filter by Line Item Type**: Include `line_item_line_item_type IN (${LINE_ITEM_TYPES})` to exclude refunds, credits, and taxes.

8. **Use Resource Tags**: Leverage resource tags like `resource_tags_user_Name` and `resource_tags_user_pod` to filter and group resources.

10. **Consider Data Sampling**: For exploratory analysis of very large datasets, use sampling techniques to get representative results without processing all data.

11. **Monitor Query Runtime**: If a query runs for more than ${MAX_QUERY_RUNTIME_MINUTES} minutes, consider canceling it and refining your filters.
