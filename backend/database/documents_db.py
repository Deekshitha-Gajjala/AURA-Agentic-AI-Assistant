"""
AURA Document Database Compatibility Layer

IMPORTANT:
The main document management implementation currently lives in
main.py because it also manages:

    - stored_filename
    - physical PDF files
    - user ownership
    - PDF vectorstores

This module is kept for compatibility with any older code that
may still import database.documents_db.

Do not create a second documents schema here.
"""


# ============================================================
# DEPRECATED MODULE
# ============================================================

def create_documents_table():
    """
    Deprecated.

    Document table creation is handled by main.py.
    """
    return None


def add_document(
    user_id: int,
    filename: str,
    file_path: str
):
    """
    Deprecated compatibility function.

    Document creation is handled by main.py.

    Raises:
        RuntimeError: Always, to prevent accidental creation
        of documents through the old schema.
    """

    raise RuntimeError(
        "The legacy document database module is deprecated. "
        "Use the document management functions in main.py."
    )


def get_documents(
    user_id: int
):
    """
    Deprecated compatibility function.

    Document retrieval is handled by main.py.
    """

    raise RuntimeError(
        "The legacy document database module is deprecated. "
        "Use the /documents endpoint in main.py."
    )


def get_document(
    document_id: int,
    user_id: int
):
    """
    Deprecated compatibility function.

    Document retrieval is handled by main.py.
    """

    raise RuntimeError(
        "The legacy document database module is deprecated. "
        "Use the document management functions in main.py."
    )


def delete_document(
    document_id: int,
    user_id: int
):
    """
    Deprecated compatibility function.

    Document deletion is handled by main.py because deletion
    must remove both the physical PDF and its vectorstore.
    """

    raise RuntimeError(
        "The legacy document database module is deprecated. "
        "Use the DELETE /documents/{document_id} endpoint "
        "in main.py."
    )