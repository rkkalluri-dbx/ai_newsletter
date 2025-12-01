#!/usr/bin/env python3
"""Query config.search_terms table using Databricks SDK"""

from databricks.sdk import WorkspaceClient

# Initialize client (uses DEFAULT profile from ~/.databrickscfg)
w = WorkspaceClient(profile="DEFAULT")

# Execute query
query = """
SELECT term, active, category, description
FROM main.config.search_terms
ORDER BY category, term
"""

print("=" * 80)
print("CONFIG.SEARCH_TERMS TABLE CONTENTS")
print("=" * 80)

try:
    # Execute SQL statement using the statement execution API
    statement = w.statement_execution.execute_statement(
        warehouse_id="84823cd491f18a44",  # Serverless Starter Warehouse
        statement=query,
        catalog="main",
        schema="config"
    )

    # Check result
    if statement.result and statement.result.data_array:
        print(f"\nFound {len(statement.result.data_array)} search terms:\n")
        print(f"{'Term':<25} {'Active':<10} {'Category':<15} {'Description':<50}")
        print("-" * 100)

        for row in statement.result.data_array:
            term = row[0] or ""
            active = "✅" if row[1] else "❌"
            category = row[2] or ""
            description = row[3] or ""
            print(f"{term:<25} {active:<10} {category:<15} {description:<50}")

        # Generate query string
        active_terms = [row[0] for row in statement.result.data_array if row[1]]
        if active_terms:
            query_string = " OR ".join(active_terms) + " lang:en -is:retweet"
            print(f"\n{'=' * 80}")
            print("TWITTER QUERY STRING")
            print(f"{'=' * 80}")
            print(f"{query_string}")
            print(f"\nLength: {len(query_string)} characters (Twitter limit: 512)")
    else:
        print("Table exists but contains no data")
        print(f"Statement status: {statement.status.state}")

except Exception as e:
    print(f"Error querying table: {e}")
    print("\nTrying alternative method - listing warehouse IDs...")

    try:
        warehouses = w.warehouses.list()
        print("\nAvailable SQL Warehouses:")
        for wh in warehouses:
            print(f"  - {wh.name} (ID: {wh.id})")
    except Exception as e2:
        print(f"Could not list warehouses: {e2}")

print("=" * 80)
