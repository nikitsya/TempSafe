"""Check the real MySQL connection using the project's .env settings.

Start the configured MySQL server before running this test.
"""

from sqlalchemy import text

from temsafe.database import get_db


def test_database_connection():
    """Confirm that a backend session can execute a query in MySQL."""
    dependency = get_db()
    session = next(dependency)

    try:
        # SELECT 1 checks the connection without changing any stored data.
        result = session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
    finally:
        dependency.close()
