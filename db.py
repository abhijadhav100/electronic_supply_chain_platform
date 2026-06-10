from flask import current_app, g

try:
    import psycopg2
    import psycopg2.extras
except ImportError:  # pragma: no cover
    psycopg2 = None
else:
    psycopg2 = psycopg2


def _connection_settings():
    return {
        "host": current_app.config["DB_HOST"],
        "port": current_app.config["DB_PORT"],
        "user": current_app.config["DB_USER"],
        "password": current_app.config["DB_PASSWORD"],
        "database": current_app.config["DB_NAME"],
    }


def get_db_connection():
    if psycopg2 is None:
        raise RuntimeError(
            "psycopg2 is not installed. Install dependencies from requirements.txt first."
        )

    if "db_connection" not in g:
        try:
            g.db_connection = psycopg2.connect(**_connection_settings())
        except Exception as exc:
            raise RuntimeError(
                f"Unable to connect to PostgreSQL. Check your database settings. Details: {exc}"
            ) from exc
    return g.db_connection


def close_connection(_exception=None):
    connection = g.pop("db_connection", None)
    if connection is not None:
        connection.close()


def fetch_all(query, params=None):
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except Exception as exc:
        raise RuntimeError(f"Database query failed. Details: {exc}") from exc
    finally:
        cursor.close()


def fetch_one(query, params=None):
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    except Exception as exc:
        raise RuntimeError(f"Database query failed. Details: {exc}") from exc
    finally:
        cursor.close()


def execute_query(query, params=None, many=False):
    """
    Execute an INSERT, UPDATE, or DELETE query.

    For INSERT statements, automatically appends RETURNING <primary_key>
    and returns the new row's ID as an integer.
    For UPDATE/DELETE, returns None.
    """
    connection = get_db_connection()
    # Use RealDictCursor so RETURNING results are accessible by column name
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        if many:
            cursor.executemany(query, params or [])
            connection.commit()
            return None

        # Detect INSERT and append RETURNING to get the new primary key
        stripped = query.strip().upper()
        if stripped.startswith("INSERT") and "RETURNING" not in stripped:
            query = query.rstrip().rstrip(";") + " RETURNING *"

        cursor.execute(query, params or ())
        connection.commit()

        # If it was an INSERT with RETURNING, hand back the first PK-like column
        if stripped.startswith("INSERT"):
            row = cursor.fetchone()
            if row:
                # Return the first column value (the primary key)
                return list(row.values())[0]
        return None

    except Exception as exc:
        connection.rollback()
        raise RuntimeError(
            f"Database write failed. Please verify schema and input values. Details: {exc}"
        ) from exc
    finally:
        cursor.close()