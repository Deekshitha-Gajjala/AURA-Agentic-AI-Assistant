import os
import sqlite3
from datetime import datetime


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
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create a SQLite connection with Row access enabled.

    Foreign-key enforcement is enabled for this connection.
    """

    os.makedirs(
        os.path.dirname(DB_PATH),
        exist_ok=True
    )

    connection = sqlite3.connect(
        DB_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# CREATE TABLES
# ============================================================

def create_chat_history_table():
    """
    Create conversation and chat-history tables if they
    do not already exist.

    Also performs lightweight migration for older databases.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # Conversations
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT 'New conversation',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ----------------------------------------------------
        # Chat messages
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                user_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                route TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ----------------------------------------------------
        # Check existing columns
        # ----------------------------------------------------

        cursor.execute(
            "PRAGMA table_info(chat_history)"
        )

        columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        # ----------------------------------------------------
        # Migrate old database
        # ----------------------------------------------------

        if "conversation_id" not in columns:

            cursor.execute(
                """
                ALTER TABLE chat_history
                ADD COLUMN conversation_id INTEGER
                """
            )

        if "user_id" not in columns:

            cursor.execute(
                """
                ALTER TABLE chat_history
                ADD COLUMN user_id INTEGER
                """
            )

        connection.commit()

    finally:

        connection.close()


# ============================================================
# VALIDATE LIMIT
# ============================================================

def _validate_limit(
    limit: int,
    default: int = 20,
    maximum: int = 100
) -> int:
    """
    Prevent invalid or excessively large database queries.
    """

    try:

        limit = int(limit)

    except (
        ValueError,
        TypeError
    ):

        return default

    if limit <= 0:

        return default

    return min(
        limit,
        maximum
    )


# ============================================================
# CREATE NEW CONVERSATION
# ============================================================

def create_conversation(
    user_id: int,
    title: str = "New conversation"
):
    """
    Create a new conversation owned by a user.
    """

    if user_id is None:

        raise ValueError(
            "user_id is required."
        )

    title = (
        str(title).strip()
        if title
        else "New conversation"
    )

    if not title:

        title = "New conversation"

    if len(title) > 100:

        title = title[:100]

    create_chat_history_table()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO conversations
            (
                user_id,
                title
            )
            VALUES (?, ?)
            """,
            (
                user_id,
                title
            )
        )

        conversation_id = cursor.lastrowid

        connection.commit()

        return conversation_id

    finally:

        connection.close()


# ============================================================
# UPDATE CONVERSATION TITLE
# ============================================================

def update_conversation_title(
    conversation_id: int,
    title: str,
    user_id: int = None
):
    """
    Update a conversation title.

    If user_id is provided, ownership is checked.
    """

    if not title:

        title = "New conversation"

    title = str(title).strip()

    if not title:

        title = "New conversation"

    title = title[:100]

    connection = get_connection()

    try:

        cursor = connection.cursor()

        if user_id is None:

            cursor.execute(
                """
                UPDATE conversations
                SET
                    title = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    title,
                    conversation_id
                )
            )

        else:

            cursor.execute(
                """
                UPDATE conversations
                SET
                    title = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    title,
                    conversation_id,
                    user_id
                )
            )

        connection.commit()

        return cursor.rowcount > 0

    finally:

        connection.close()


# ============================================================
# UPDATE CONVERSATION TIME
# ============================================================

def touch_conversation(
    conversation_id: int,
    user_id: int = None
):
    """
    Update the last-used time of a conversation.
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        if user_id is None:

            cursor.execute(
                """
                UPDATE conversations
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    conversation_id,
                )
            )

        else:

            cursor.execute(
                """
                UPDATE conversations
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    conversation_id,
                    user_id
                )
            )

        connection.commit()

        return cursor.rowcount > 0

    finally:

        connection.close()


# ============================================================
# VERIFY CONVERSATION OWNERSHIP
# ============================================================

def conversation_belongs_to_user(
    conversation_id: int,
    user_id: int
) -> bool:
    """
    Check whether a conversation belongs to a user.
    """

    if conversation_id is None or user_id is None:

        return False

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM conversations
            WHERE id = ?
            AND user_id = ?
            """,
            (
                conversation_id,
                user_id
            )
        )

        return cursor.fetchone() is not None

    finally:

        connection.close()


# ============================================================
# SAVE CHAT MESSAGE
# ============================================================

def save_chat(
    question: str,
    answer: str,
    route: str,
    user_id: int = None,
    conversation_id: int = None
):
    """
    Save a question/answer pair.

    If conversation_id is supplied, verify that it belongs
    to the current user before saving.
    """

    if not question:

        raise ValueError(
            "Question cannot be empty."
        )

    if answer is None:

        answer = ""

    question = str(question).strip()
    answer = str(answer)

    route = (
        str(route).strip().upper()
        if route
        else "GENERAL"
    )

    if not question:

        raise ValueError(
            "Question cannot be empty."
        )

    if user_id is None:

        raise ValueError(
            "user_id is required to save chat history."
        )

    create_chat_history_table()

    # --------------------------------------------------------
    # Create a new conversation when necessary
    # --------------------------------------------------------

    if conversation_id is None:

        title = question

        if len(title) > 50:

            title = title[:50] + "..."

        conversation_id = create_conversation(
            user_id=user_id,
            title=title
        )

    else:

        # ----------------------------------------------------
        # SECURITY: verify ownership
        # ----------------------------------------------------

        if not conversation_belongs_to_user(
            conversation_id,
            user_id
        ):

            raise PermissionError(
                "Conversation does not belong to the current user."
            )

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO chat_history
            (
                conversation_id,
                user_id,
                question,
                answer,
                route
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                user_id,
                question,
                answer,
                route
            )
        )

        cursor.execute(
            """
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            AND user_id = ?
            """,
            (
                conversation_id,
                user_id
            )
        )

        connection.commit()

        return conversation_id

    finally:

        connection.close()


# ============================================================
# GET ALL CONVERSATIONS FOR USER
# ============================================================

def get_conversations(
    user_id: int
):
    """
    Return all conversations belonging to a user.
    """

    if user_id is None:

        return []

    create_chat_history_table()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                title,
                created_at,
                updated_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (
                user_id,
            )
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


# ============================================================
# GET ONE CONVERSATION
# ============================================================

def get_conversation(
    conversation_id: int,
    user_id: int
):
    """
    Return a conversation only if it belongs to the user.
    """

    create_chat_history_table()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                title,
                created_at,
                updated_at
            FROM conversations
            WHERE id = ?
            AND user_id = ?
            """,
            (
                conversation_id,
                user_id
            )
        )

        row = cursor.fetchone()

        if row is None:

            return None

        return dict(row)

    finally:

        connection.close()


# ============================================================
# GET MESSAGES FROM ONE CONVERSATION
# ============================================================

def get_conversation_messages(
    conversation_id: int,
    user_id: int
):
    """
    Return messages only from a conversation owned by the user.
    """

    create_chat_history_table()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                conversation_id,
                user_id,
                question,
                answer,
                route,
                created_at
            FROM chat_history
            WHERE conversation_id = ?
            AND user_id = ?
            ORDER BY id ASC
            """,
            (
                conversation_id,
                user_id
            )
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


# ============================================================
# GET USER CHAT HISTORY
# ============================================================

def get_chat_history(
    user_id: int = None,
    limit: int = 20
):
    """
    Return recent chat messages for a user.

    For authenticated AURA usage, user_id should always be
    provided.
    """

    limit = _validate_limit(
        limit,
        default=20,
        maximum=100
    )

    create_chat_history_table()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        if user_id is None:

            cursor.execute(
                """
                SELECT
                    id,
                    conversation_id,
                    user_id,
                    question,
                    answer,
                    route,
                    created_at
                FROM chat_history
                WHERE user_id IS NULL
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    limit,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    id,
                    conversation_id,
                    user_id,
                    question,
                    answer,
                    route,
                    created_at
                FROM chat_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    user_id,
                    limit
                )
            )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


# ============================================================
# GET MEMORY CONTEXT
# ============================================================

def get_memory_context(
    user_id: int = None,
    conversation_id: int = None,
    limit: int = 5
):
    """
    Build conversational context from previous messages.

    If conversation_id is provided, only that conversation
    is used.

    Otherwise, recent conversations/messages for the user
    are used.
    """

    if user_id is None:

        return ""

    limit = _validate_limit(
        limit,
        default=5,
        maximum=20
    )

    create_chat_history_table()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        if conversation_id is not None:

            # ------------------------------------------------
            # Verify conversation ownership
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT id
                FROM conversations
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    conversation_id,
                    user_id
                )
            )

            if cursor.fetchone() is None:

                return ""

            cursor.execute(
                """
                SELECT
                    question,
                    answer
                FROM chat_history
                WHERE conversation_id = ?
                AND user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    conversation_id,
                    user_id,
                    limit
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    question,
                    answer
                FROM chat_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    user_id,
                    limit
                )
            )

        rows = cursor.fetchall()

    finally:

        connection.close()

    if not rows:

        return ""

    # --------------------------------------------------------
    # Convert newest → oldest into oldest → newest
    # --------------------------------------------------------

    rows = list(
        reversed(rows)
    )

    context = []

    for row in rows:

        context.append(
            f"User: {row['question']}\n"
            f"AURA: {row['answer']}"
        )

    return "\n\n".join(
        context
    )


# ============================================================
# DELETE ONE CONVERSATION
# ============================================================

def delete_conversation(
    conversation_id: int,
    user_id: int
):
    """
    Delete one conversation and its messages.

    Ownership is checked before deletion.
    """

    create_chat_history_table()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # Check ownership
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM conversations
            WHERE id = ?
            AND user_id = ?
            """,
            (
                conversation_id,
                user_id
            )
        )

        conversation = cursor.fetchone()

        if conversation is None:

            return False

        # ----------------------------------------------------
        # Delete conversation
        #
        # ON DELETE CASCADE removes its messages.
        # ----------------------------------------------------

        cursor.execute(
            """
            DELETE FROM conversations
            WHERE id = ?
            AND user_id = ?
            """,
            (
                conversation_id,
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:

        connection.close()


# ============================================================
# DELETE ALL USER CONVERSATIONS
# ============================================================

def delete_all_conversations(
    user_id: int
):
    """
    Delete all conversations belonging to a user.

    Their associated chat messages are removed through
    the conversation foreign-key cascade.
    """

    if user_id is None:

        return 0

    create_chat_history_table()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # Get conversation IDs
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM conversations
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        conversation_ids = [
            row["id"]
            for row in cursor.fetchall()
        ]

        # ----------------------------------------------------
        # Delete conversations
        # ----------------------------------------------------

        cursor.execute(
            """
            DELETE FROM conversations
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        # ----------------------------------------------------
        # Remove any orphaned messages belonging to the user.
        #
        # This also protects old databases created before the
        # foreign-key relationship was properly established.
        # ----------------------------------------------------

        cursor.execute(
            """
            DELETE FROM chat_history
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        connection.commit()

        return len(conversation_ids)

    finally:

        connection.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

create_chat_history_table()