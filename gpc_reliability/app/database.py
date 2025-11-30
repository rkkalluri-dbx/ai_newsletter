"""Databricks SQL Connector for Delta Lake tables in Unity Catalog."""
import os
import threading
from contextlib import contextmanager
from typing import Any, Generator, Optional

from databricks import sql
from databricks.sql.client import Connection, Cursor
from flask import g, has_app_context


def get_databricks_token() -> Optional[str]:
    """Get Databricks access token from environment or SDK credentials.

    In Databricks Apps, uses the app's service principal credentials.
    Locally, uses DATABRICKS_TOKEN env var or databricks CLI config.
    """
    # First check for explicit token
    token = os.environ.get("DATABRICKS_TOKEN")
    if token:
        return token

    # In Databricks Apps, try to get token from SDK's default credentials
    try:
        from databricks.sdk import WorkspaceClient
        from databricks.sdk.config import Config

        # This will use the app's service principal in Databricks Apps
        config = Config()
        w = WorkspaceClient(config=config)
        # Get the token from the config's authentication
        if hasattr(config, 'token') and config.token:
            return config.token
        # Try to get token via oauth
        if config.authenticate:
            headers = config.authenticate()
            if 'Authorization' in headers:
                auth_header = headers['Authorization']
                if auth_header.startswith('Bearer '):
                    return auth_header[7:]
    except Exception as e:
        print(f"Could not get token from SDK: {e}")

    return None


class DatabricksDB:
    """Database connection manager for Databricks SQL Warehouse.

    Uses per-request connections via Flask's g object to handle concurrent requests.
    Falls back to a thread-local connection for non-Flask contexts (CLI scripts).
    """

    def __init__(self, app=None):
        self.app = app
        self._local = threading.local()  # Thread-local storage for non-Flask contexts
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with Flask app configuration."""
        self.app = app
        # Register teardown to close per-request connections
        app.teardown_appcontext(self.teardown)

    @property
    def server_hostname(self) -> str:
        """Get Databricks server hostname."""
        return os.environ.get(
            "DATABRICKS_SERVER_HOSTNAME",
            self.app.config.get("DATABRICKS_SERVER_HOSTNAME", "")
        )

    @property
    def http_path(self) -> str:
        """Get SQL Warehouse HTTP path."""
        return os.environ.get(
            "DATABRICKS_HTTP_PATH",
            self.app.config.get("DATABRICKS_HTTP_PATH", "")
        )

    @property
    def access_token(self) -> Optional[str]:
        """Get Databricks access token."""
        # Check environment variable first
        token = os.environ.get(
            "DATABRICKS_TOKEN",
            self.app.config.get("DATABRICKS_TOKEN") if self.app else None
        )
        if token:
            return token

        # Try to get from SDK (for Databricks Apps)
        return get_databricks_token()

    @property
    def catalog(self) -> str:
        """Get Unity Catalog name."""
        return os.environ.get(
            "DATABRICKS_CATALOG",
            self.app.config.get("DATABRICKS_CATALOG", "main")
        )

    @property
    def schema(self) -> str:
        """Get Unity Catalog schema name."""
        return os.environ.get(
            "DATABRICKS_SCHEMA",
            self.app.config.get("DATABRICKS_SCHEMA", "gpc_reliability")
        )

    def _create_connection(self) -> Connection:
        """Create a new database connection."""
        token = self.access_token

        connect_args = {
            "server_hostname": self.server_hostname,
            "http_path": self.http_path,
            "catalog": self.catalog,
            "schema": self.schema,
        }

        if token:
            connect_args["access_token"] = token
        else:
            # Use credentials_provider for Databricks Apps environment
            try:
                from databricks.sdk.config import Config
                config = Config()
                connect_args["credentials_provider"] = config.authenticate
            except Exception as e:
                print(f"Warning: Could not set up credentials provider: {e}")
                # Fall back to letting the connector handle auth
                pass

        return sql.connect(**connect_args)

    def _get_connection_storage(self):
        """Get the appropriate storage for the connection (Flask g or thread-local)."""
        if has_app_context():
            return g
        return self._local

    def get_connection(self) -> Connection:
        """Get or create database connection.

        Uses Flask's g object for per-request isolation in web contexts,
        or thread-local storage for CLI/scripts.
        """
        storage = self._get_connection_storage()
        conn = getattr(storage, 'db_connection', None)

        if conn is None:
            conn = self._create_connection()
            storage.db_connection = conn

        return conn

    def _reset_connection(self):
        """Reset the database connection."""
        storage = self._get_connection_storage()
        conn = getattr(storage, 'db_connection', None)

        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            storage.db_connection = None

    def _get_fresh_cursor(self) -> Cursor:
        """Get a fresh cursor, creating new connection if needed."""
        try:
            conn = self.get_connection()
            # Try to create cursor - this will fail if connection is stale
            cursor = conn.cursor()
            return cursor
        except Exception as e:
            error_msg = str(e).lower()
            if 'closed' in error_msg or 'invalid' in error_msg or 'session' in error_msg:
                print(f"Stale connection detected, creating fresh connection: {e}")
                self._reset_connection()
                conn = self.get_connection()
                return conn.cursor()
            raise

    @contextmanager
    def cursor(self) -> Generator[Cursor, None, None]:
        """Context manager for database cursor with automatic reconnection."""
        cursor = self._get_fresh_cursor()
        try:
            yield cursor
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    def execute(self, query: str, params: Optional[tuple] = None, _retry: bool = True) -> list[dict]:
        """Execute a query and return results as list of dicts.

        Automatically retries once on connection errors.
        """
        try:
            with self.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                return []
        except Exception as e:
            error_msg = str(e).lower()
            # Check for connection-related errors
            if _retry and ('closed' in error_msg or 'invalid' in error_msg or 'session' in error_msg):
                print(f"Connection error detected, reconnecting: {e}")
                self._reset_connection()
                return self.execute(query, params, _retry=False)
            raise

    def execute_many(self, query: str, params_list: list[tuple], _retry: bool = True) -> None:
        """Execute a query with multiple parameter sets.

        Automatically retries once on connection errors.
        """
        try:
            with self.cursor() as cursor:
                for params in params_list:
                    cursor.execute(query, params)
        except Exception as e:
            error_msg = str(e).lower()
            if _retry and ('closed' in error_msg or 'invalid' in error_msg or 'session' in error_msg):
                print(f"Connection error detected, reconnecting: {e}")
                self._reset_connection()
                return self.execute_many(query, params_list, _retry=False)
            raise

    def execute_write(self, query: str, params: Optional[tuple] = None, _retry: bool = True) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows.

        Automatically retries once on connection errors.
        """
        try:
            with self.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount if cursor.rowcount else 0
        except Exception as e:
            error_msg = str(e).lower()
            if _retry and ('closed' in error_msg or 'invalid' in error_msg or 'session' in error_msg):
                print(f"Connection error detected, reconnecting: {e}")
                self._reset_connection()
                return self.execute_write(query, params, _retry=False)
            raise

    def teardown(self, exception=None):
        """Close connection on app context teardown."""
        # Close Flask g connection if it exists
        if has_app_context():
            conn = getattr(g, 'db_connection', None)
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
                g.db_connection = None

    def table_name(self, table: str) -> str:
        """Get fully qualified table name."""
        return f"{self.catalog}.{self.schema}.{table}"


# Global database instance
db = DatabricksDB()
