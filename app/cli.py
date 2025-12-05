"""Flask CLI commands."""
import click
from flask import Flask


def register_cli_commands(app: Flask) -> None:
    """Register CLI commands with the Flask app."""

    @app.cli.group()
    def db_seed():
        """Database seeding commands."""
        pass

    @db_seed.command("all")
    def seed_all_cmd():
        """Seed all tables with mock data."""
        from app.seeds.seeder import seed_all
        result = seed_all()
        click.echo(f"Seeding complete: {result}")

    @db_seed.command("vendors")
    def seed_vendors_cmd():
        """Seed vendors table."""
        from app.seeds.seeder import seed_vendors
        vendors = seed_vendors()
        click.echo(f"Seeded {len(vendors)} vendors")

    @db_seed.command("clear")
    @click.confirmation_option(prompt="Are you sure you want to clear all data?")
    def clear_all_cmd():
        """Clear all data from database."""
        from app.seeds.seeder import clear_all
        clear_all()
        click.echo("All data cleared")

    @app.cli.command("init-db")
    def init_db_cmd():
        """Initialize database by creating Delta tables in Unity Catalog.

        Note: Run the SQL scripts in sql/ directory in Databricks SQL Editor first,
        or this command will create the tables using the Databricks SQL Connector.
        """
        from app.database import db
        import os

        sql_dir = os.path.join(os.path.dirname(__file__), '..', 'sql')
        schema_file = os.path.join(sql_dir, '001_create_schema.sql')
        tables_file = os.path.join(sql_dir, '002_create_tables.sql')

        click.echo(f"Creating schema {db.catalog}.{db.schema}...")

        # Read and execute schema creation
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                for statement in f.read().split(';'):
                    stmt = statement.strip()
                    if stmt and not stmt.startswith('--'):
                        try:
                            db.execute_write(stmt)
                        except Exception as e:
                            click.echo(f"Warning: {e}")

        click.echo("Creating Delta tables...")

        # Read and execute table creation
        if os.path.exists(tables_file):
            with open(tables_file, 'r') as f:
                for statement in f.read().split(';'):
                    stmt = statement.strip()
                    if stmt and not stmt.startswith('--'):
                        try:
                            db.execute_write(stmt)
                            click.echo(f"  Created table from statement")
                        except Exception as e:
                            click.echo(f"  Warning: {e}")

        click.echo("Database initialization complete!")

    @app.cli.command("check-db")
    def check_db_cmd():
        """Check database connection and list tables."""
        from app.database import db

        click.echo(f"Checking connection to {db.server_hostname}...")
        click.echo(f"Catalog: {db.catalog}, Schema: {db.schema}")

        try:
            tables = db.execute(f"SHOW TABLES IN {db.catalog}.{db.schema}")
            click.echo(f"\nFound {len(tables)} tables:")
            for table in tables:
                click.echo(f"  - {table.get('tableName', table)}")
        except Exception as e:
            click.echo(f"Error: {e}")
