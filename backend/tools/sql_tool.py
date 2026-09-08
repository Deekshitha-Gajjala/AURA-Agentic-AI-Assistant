import sqlite3
import os
import re

from llm import ask_llm


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DB_PATH = os.path.join(
    BASE_DIR,
    "database",
    "aura.db"
)


# ============================================================
# TABLES THAT AURA SQL IS ALLOWED TO QUERY
# ============================================================

# These are the application/demo data tables that the SQL
# assistant is allowed to expose to the LLM.
#
# IMPORTANT:
# Authentication, chat history, documents, etc. should NOT
# automatically become available to natural-language SQL.

ALLOWED_TABLES = {
    "customers",
    "employees",
    "sales"
}


# ============================================================
# AUTHENTICATED USER VALIDATION
# ============================================================

def validate_user_id(user_id):
    """
    SQL access is available only to an authenticated AURA user.

    The current demo tables are shared application data and do not
    contain user_id columns, so no artificial row-level filter is
    added to customers/employees/sales.
    """
    if user_id is None:
        raise PermissionError("Authentication is required for SQL queries.")

    try:
        normalized_user_id = int(user_id)
    except (TypeError, ValueError):
        raise PermissionError("Invalid authenticated user.")

    if normalized_user_id <= 0:
        raise PermissionError("Invalid authenticated user.")

    return normalized_user_id


# ============================================================
# GET DATABASE SCHEMA
# ============================================================

def get_schema():

    if not os.path.exists(DB_PATH):
        return ""

    connection = sqlite3.connect(DB_PATH)

    try:

        cursor = connection.cursor()

        tables = cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()

        schema = []

        for table in tables:

            table_name = table[0]

            # Only expose explicitly allowed tables
            if table_name not in ALLOWED_TABLES:
                continue

            columns = cursor.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()

            column_names = [
                column[1]
                for column in columns
            ]

            schema.append(
                f"{table_name}({', '.join(column_names)})"
            )

        return "\n".join(schema)

    finally:

        connection.close()


# ============================================================
# GENERATE SQL FROM NATURAL LANGUAGE
# ============================================================

def generate_sql(question: str):

    question = question.strip()

    if not question:
        raise ValueError(
            "Database question cannot be empty."
        )

    schema = get_schema()

    if not schema:

        raise RuntimeError(
            "No SQL-queryable database tables are available."
        )

    prompt = f"""
You are the SQL query generator for AURA,
an AI database assistant.

DATABASE SCHEMA:

{schema}

USER QUESTION:

{question}

Your task is to convert the user's question
into exactly ONE SQLite SELECT query.

STRICT RULES:

1. Generate ONLY one SELECT query.
2. The query must start with SELECT.
3. Use ONLY the tables and columns present in the schema.
4. Do not invent tables.
5. Do not invent columns.
6. Do not modify the database.
7. Do not use INSERT.
8. Do not use UPDATE.
9. Do not use DELETE.
10. Do not use DROP.
11. Do not use ALTER.
12. Do not use CREATE.
13. Do not use REPLACE.
14. Do not use TRUNCATE.
15. Do not use PRAGMA.
16. Do not use ATTACH.
17. Do not use DETACH.
18. Do not use VACUUM.
19. Do not use transaction statements.
20. Do not use multiple SQL statements.
21. Do not include markdown.
22. Do not include ```sql.
23. Do not include explanations.
24. Return ONLY the SQL query.

The query must be read-only.

Return ONLY the SQL query.
"""

    sql = ask_llm(prompt).strip()

    # --------------------------------------------------------
    # Remove accidental markdown formatting
    # --------------------------------------------------------

    sql = re.sub(
        r"```(?:sql)?",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = sql.replace(
        "```",
        ""
    ).strip()

    return sql


# ============================================================
# NORMALIZE SQL
# ============================================================

def normalize_sql(sql: str):

    if not sql:
        return ""

    sql = sql.strip()

    # Remove leading/trailing markdown code fences
    sql = re.sub(
        r"^```(?:sql)?\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = re.sub(
        r"\s*```$",
        "",
        sql,
        flags=re.IGNORECASE
    )

    return sql.strip()


# ============================================================
# SQL SAFETY CHECK
# ============================================================

def is_safe_sql(sql: str):

    if not sql:
        return False

    normalized = normalize_sql(sql)

    if not normalized:
        return False

    normalized_lower = normalized.lower().strip()

    # --------------------------------------------------------
    # Must begin with SELECT
    # --------------------------------------------------------

    if not re.match(
        r"^select\b",
        normalized_lower
    ):
        return False

    # --------------------------------------------------------
    # Only one SQL statement is allowed
    # --------------------------------------------------------

    # A semicolon is allowed only at the very end.
    sql_without_final_semicolon = normalized_lower.rstrip(";")

    if ";" in sql_without_final_semicolon:
        return False

    # --------------------------------------------------------
    # Block dangerous SQL operations
    # --------------------------------------------------------

    dangerous_patterns = [

        r"\binsert\b",
        r"\bupdate\b",
        r"\bdelete\b",
        r"\bdrop\b",
        r"\balter\b",
        r"\bcreate\b",
        r"\breplace\b",
        r"\btruncate\b",
        r"\bpragma\b",
        r"\battach\b",
        r"\bdetach\b",
        r"\bvacuum\b",
        r"\breindex\b",

        # SQLite transaction/control statements
        r"\bbegin\b",
        r"\bcommit\b",
        r"\brollback\b",
        r"\bsavepoint\b",
        r"\brelease\b",

        # SQLite functions/features that should not be exposed
        r"\breadfile\b",
        r"\bwritefile\b"
    ]

    for pattern in dangerous_patterns:

        if re.search(
            pattern,
            normalized_lower
        ):
            return False

    # --------------------------------------------------------
    # Prevent SQLite comments from hiding SQL
    # --------------------------------------------------------

    if "--" in normalized_lower:
        return False

    if "/*" in normalized_lower:
        return False

    if "*/" in normalized_lower:
        return False

    return True


# ============================================================
# CHECK TABLE ACCESS
# ============================================================

def uses_only_allowed_tables(sql: str):

    """
    Ensures the generated query does not reference
    application-sensitive tables.

    This is an additional layer on top of the LLM prompt.
    """

    normalized = sql.lower()

    # --------------------------------------------------------
    # Find FROM and JOIN table references
    # --------------------------------------------------------

    table_matches = re.findall(
        r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        normalized
    )

    if not table_matches:
        return False

    for table_name in table_matches:

        if table_name not in ALLOWED_TABLES:
            return False

    return True


# ============================================================
# EXECUTE SQL
# ============================================================

def execute_sql(query: str):

    if not os.path.exists(DB_PATH):
        return {
            "success": False,
            "error": "Database is not available."
        }

    connection = None

    try:
        # SQLite URI mode='ro' makes the connection physically read-only.
        # This is an additional protection beyond SQL validation.
        database_uri = f"file:{os.path.abspath(DB_PATH)}?mode=ro"
        connection = sqlite3.connect(
            database_uri,
            uri=True
        )

        cursor = connection.cursor()

        cursor.execute(query)

        results = cursor.fetchall()

        column_names = []

        if cursor.description:
            column_names = [
                description[0]
                for description in cursor.description
            ]

        return {
            "success": True,
            "columns": column_names,
            "results": results
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

    finally:

        if connection is not None:
            connection.close()


# ============================================================
# ANSWER USER USING SQL
# ============================================================

def answer_from_sql(
    question: str,
    user_id: int = None
):

    """
    Converts a natural-language database question
    into a safe read-only SQL query and answers it.

    user_id is accepted so this function remains compatible
    with AURA's authenticated architecture.

    The current SQL demo tables (customers, employees, sales)
    are shared application/demo tables and do not contain
    user ownership fields. Therefore we do not inject a
    fake user_id filter into those queries.
    """

    try:

        # ----------------------------------------------------
        # Validate authenticated user
        # ----------------------------------------------------

        validate_user_id(user_id)

        # ----------------------------------------------------
        # Validate question
        # ----------------------------------------------------

        if not question or not question.strip():

            return {
                "success": False,
                "answer": "Please enter a database question."
            }

        question = question.strip()

        # ----------------------------------------------------
        # Generate SQL
        # ----------------------------------------------------

        sql = generate_sql(
            question
        )

        sql = normalize_sql(
            sql
        )

        print(
            "Generated SQL:",
            sql
        )

        # ----------------------------------------------------
        # Safety check
        # ----------------------------------------------------

        if not is_safe_sql(
            sql
        ):

            return {
                "success": False,
                "answer": (
                    "I couldn't safely execute "
                    "the generated database query."
                ),
                "sql": sql
            }

        # ----------------------------------------------------
        # Allowed-table check
        # ----------------------------------------------------

        if not uses_only_allowed_tables(
            sql
        ):

            return {
                "success": False,
                "answer": (
                    "I couldn't execute this query because "
                    "it references a restricted database table."
                ),
                "sql": sql
            }

        # ----------------------------------------------------
        # Execute query
        # ----------------------------------------------------

        result = execute_sql(
            sql
        )

        if not result["success"]:

            return {
                "success": False,
                "answer": (
                    "I couldn't execute the database query."
                ),
                "sql": sql,
                "error": result["error"]
            }

        # ----------------------------------------------------
        # Handle empty result
        # ----------------------------------------------------

        if not result["results"]:

            return {
                "success": True,
                "answer": (
                    "I couldn't find any matching records "
                    "in the database."
                ),
                "sql": sql,
                "data": result
            }

        # ----------------------------------------------------
        # Convert result into natural language
        # ----------------------------------------------------

        prompt = f"""
You are AURA, an AI database assistant.

USER QUESTION:

{question}

SQL QUERY:

{sql}

DATABASE RESULT:

Columns:
{result["columns"]}

Rows:
{result["results"]}

Answer the user's question using ONLY
the database result above.

RULES:

- Give the direct answer first.
- Keep the answer concise and clear.
- Do not invent information.
- Do not make assumptions beyond the result.
- Do not modify the database.
- If the result contains multiple records,
  summarize them clearly.
- Use a table when it makes the answer easier
  to understand.
- Do not mention internal implementation details
  unless necessary.

Answer naturally.
"""

        answer = ask_llm(
            prompt
        )

        if not answer:

            answer = (
                "The database query completed successfully, "
                "but I couldn't generate a natural-language answer."
            )

        return {
            "success": True,
            "answer": answer.strip(),
            "sql": sql,
            "data": result
        }

    except Exception as e:

        print(
            "SQL tool error:",
            str(e)
        )

        return {
            "success": False,
            "answer": (
                "I couldn't process the database query right now."
            ),
            "error": str(e)
        }