import os
import pickle
import hashlib
import shutil

import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# PDFs are stored by main.py in backend/uploads/pdfs.
# Keep the RAG tool on exactly the same directory.
UPLOADS_DIR = os.path.join(
    BASE_DIR,
    "uploads",
    "pdfs"
)

VECTORSTORE_DIR = os.path.join(
    BASE_DIR,
    "vectorstore"
)

DOCUMENT_VECTORSTORE_DIR = os.path.join(
    VECTORSTORE_DIR,
    "documents"
)

os.makedirs(
    UPLOADS_DIR,
    exist_ok=True
)

os.makedirs(
    VECTORSTORE_DIR,
    exist_ok=True
)

os.makedirs(
    DOCUMENT_VECTORSTORE_DIR,
    exist_ok=True
)


# ============================================================
# EMBEDDING MODEL
# ============================================================

MODEL_NAME = "all-MiniLM-L6-v2"

embedding_model = None


def get_embedding_model():
    """Load the embedding model only when an embedding operation is needed."""
    global embedding_model

    if embedding_model is None:
        print("Loading embedding model:", MODEL_NAME)
        embedding_model = SentenceTransformer(MODEL_NAME, device="cpu")

    return embedding_model


# ============================================================
# EXTRACT PDF PAGES
# ============================================================

def extract_pdf_pages(
    pdf_path: str
):
    """
    Extract readable text page-by-page from a PDF.
    """

    if not os.path.exists(pdf_path):

        raise FileNotFoundError(
            f"PDF file not found: {pdf_path}"
        )

    reader = PdfReader(
        pdf_path
    )

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text()

        if text:

            text = text.strip()

            if text:

                pages.append(
                    {
                        "page": page_number,
                        "text": text
                    }
                )

    return pages


# ============================================================
# CREATE CHUNKS
# ============================================================

def create_chunks(
    text: str,
    chunk_size: int = 800,
    overlap: int = 100
):
    """
    Split text into overlapping chunks.
    """

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[
            start:end
        ].strip()

        if chunk:

            chunks.append(
                chunk
            )

        if end >= len(text):
            break

        start = end - overlap

    return chunks


# ============================================================
# DOCUMENT ID
# ============================================================

def get_document_id(
    filename: str
):
    """
    Create a stable hash-based identifier
    from the stored PDF filename.
    """

    return hashlib.md5(
        filename.encode(
            "utf-8"
        )
    ).hexdigest()


# ============================================================
# DOCUMENT VECTORSTORE PATHS
# ============================================================

def get_document_paths(
    filename: str,
    create_directory: bool = True
):
    """
    Return paths for a specific document vectorstore.
    """

    document_id = get_document_id(
        filename
    )

    document_dir = os.path.join(
        DOCUMENT_VECTORSTORE_DIR,
        document_id
    )

    if create_directory:

        os.makedirs(
            document_dir,
            exist_ok=True
        )

    return {
        "directory": document_dir,

        "index": os.path.join(
            document_dir,
            "index.faiss"
        ),

        "chunks": os.path.join(
            document_dir,
            "chunks.pkl"
        ),

        "metadata": os.path.join(
            document_dir,
            "metadata.pkl"
        )
    }


# ============================================================
# RESOLVE PDF FILENAME
# ============================================================

def resolve_pdf_filename(
    filename: str
):
    """
    Resolve either:

        original filename
        OR
        stored UUID-prefixed filename

    Example:

        resume.pdf

    may resolve to:

        4c9..._resume.pdf
    """

    if not filename:
        return None

    filename = os.path.basename(
        filename.strip()
    )

    # --------------------------------------------------------
    # Exact stored filename
    # --------------------------------------------------------

    exact_path = os.path.join(
        UPLOADS_DIR,
        filename
    )

    if os.path.isfile(
        exact_path
    ):

        return filename

    # --------------------------------------------------------
    # Look for UUID-prefixed stored filename
    # --------------------------------------------------------

    suffix = "_" + filename

    matches = []

    try:

        for stored_filename in os.listdir(
            UPLOADS_DIR
        ):

            if not stored_filename.lower().endswith(
                ".pdf"
            ):
                continue

            if stored_filename.endswith(
                suffix
            ):

                matches.append(
                    stored_filename
                )

    except OSError:

        return None

    # --------------------------------------------------------
    # One matching document
    # --------------------------------------------------------

    if len(matches) == 1:

        return matches[0]

    # --------------------------------------------------------
    # Multiple matching documents
    # --------------------------------------------------------

    if len(matches) > 1:

        # Prefer the most recently modified file.
        matches.sort(
            key=lambda name: os.path.getmtime(
                os.path.join(
                    UPLOADS_DIR,
                    name
                )
            ),
            reverse=True
        )

        return matches[0]

    return None


# ============================================================
# BUILD VECTORSTORE FOR ONE PDF
# ============================================================

def build_document_vectorstore(
    pdf_path: str
):
    """
    Build a separate FAISS vectorstore for one PDF.
    """

    if not os.path.exists(
        pdf_path
    ):

        return {
            "success": False,
            "message": (
                f"PDF file not found: {pdf_path}"
            )
        }

    filename = os.path.basename(
        pdf_path
    )

    print(
        "\n======================================"
    )

    print(
        "BUILDING DOCUMENT VECTORSTORE"
    )

    print(
        "PDF:",
        filename
    )

    print(
        "======================================"
    )

    # --------------------------------------------------------
    # Extract pages
    # --------------------------------------------------------

    try:

        pages = extract_pdf_pages(
            pdf_path
        )

    except Exception as e:

        return {
            "success": False,
            "filename": filename,
            "message": (
                f"Could not read PDF: {str(e)}"
            )
        }

    print(
        "Pages with text:",
        len(pages)
    )

    # --------------------------------------------------------
    # Create chunks
    # --------------------------------------------------------

    all_chunks = []

    metadata = []

    for page_data in pages:

        page_number = page_data[
            "page"
        ]

        page_text = page_data[
            "text"
        ]

        chunks = create_chunks(
            page_text
        )

        for chunk in chunks:

            all_chunks.append(
                chunk
            )

            metadata.append(
                {
                    "text": chunk,
                    "source": filename,
                    "page": page_number
                }
            )

    # --------------------------------------------------------
    # Check chunks
    # --------------------------------------------------------

    if not all_chunks:

        return {
            "success": False,
            "filename": filename,
            "message": (
                f"No readable text found "
                f"in {filename}."
            )
        }

    print(
        "Total chunks:",
        len(all_chunks)
    )

    # --------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------

    print(
        "Generating embeddings..."
    )

    try:

        embeddings = get_embedding_model().encode(
            all_chunks,
            convert_to_numpy=True,
            show_progress_bar=True
        )

    except Exception as e:

        return {
            "success": False,
            "filename": filename,
            "message": (
                f"Embedding generation failed: {str(e)}"
            )
        }

    embeddings = embeddings.astype(
        "float32"
    )

    # --------------------------------------------------------
    # Create FAISS index
    # --------------------------------------------------------

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(
        embeddings
    )

    # --------------------------------------------------------
    # Get paths
    # --------------------------------------------------------

    paths = get_document_paths(
        filename,
        create_directory=True
    )

    # --------------------------------------------------------
    # Save FAISS index
    # --------------------------------------------------------

    faiss.write_index(
        index,
        paths["index"]
    )

    # --------------------------------------------------------
    # Save chunks
    # --------------------------------------------------------

    with open(
        paths["chunks"],
        "wb"
    ) as file:

        pickle.dump(
            all_chunks,
            file
        )

    # --------------------------------------------------------
    # Save metadata
    # --------------------------------------------------------

    with open(
        paths["metadata"],
        "wb"
    ) as file:

        pickle.dump(
            metadata,
            file
        )

    print(
        "Document vectorstore created."
    )

    print(
        "FAISS vectors:",
        index.ntotal
    )

    print(
        "Source:",
        filename
    )

    return {
        "success": True,
        "filename": filename,
        "pages": len(pages),
        "chunks": len(all_chunks),
        "vectors": index.ntotal
    }


# ============================================================
# BUILD COMPLETE COMBINED VECTORSTORE
# ============================================================

def build_vectorstore():
    """
    Build:

    1. A separate vectorstore for every PDF.
    2. One combined vectorstore containing all PDFs.

    This function is mainly useful for rebuilding
    the complete RAG index.
    """

    all_chunks = []

    metadata = []

    # --------------------------------------------------------
    # Find PDFs
    # --------------------------------------------------------

    pdf_files = []

    try:

        for filename in os.listdir(
            UPLOADS_DIR
        ):

            if filename.lower().endswith(
                ".pdf"
            ):

                pdf_files.append(
                    os.path.join(
                        UPLOADS_DIR,
                        filename
                    )
                )

    except OSError as e:

        return {
            "success": False,
            "message": (
                f"Could not access uploads directory: {str(e)}"
            )
        }

    if not pdf_files:

        return {
            "success": False,
            "message": (
                "No PDF files found in "
                "the uploads directory."
            )
        }

    print(
        f"\nFound {len(pdf_files)} PDF file(s)."
    )

    # --------------------------------------------------------
    # Process each PDF separately
    # --------------------------------------------------------

    processed_documents = []

    for pdf_path in pdf_files:

        result = build_document_vectorstore(
            pdf_path
        )

        if not result["success"]:

            print(
                "Skipping PDF:",
                os.path.basename(pdf_path),
                "|",
                result.get(
                    "message",
                    "Unknown error"
                )
            )

            continue

        processed_documents.append(
            result
        )

        filename = os.path.basename(
            pdf_path
        )

        # ----------------------------------------------------
        # Extract pages once for combined index
        # ----------------------------------------------------

        try:

            pages = extract_pdf_pages(
                pdf_path
            )

        except Exception as e:

            print(
                "Could not extract pages for combined "
                "vectorstore:",
                filename,
                str(e)
            )

            continue

        for page_data in pages:

            page_number = page_data[
                "page"
            ]

            page_text = page_data[
                "text"
            ]

            chunks = create_chunks(
                page_text
            )

            for chunk in chunks:

                all_chunks.append(
                    chunk
                )

                metadata.append(
                    {
                        "text": chunk,
                        "source": filename,
                        "page": page_number
                    }
                )

    # --------------------------------------------------------
    # Check combined chunks
    # --------------------------------------------------------

    if not all_chunks:

        return {
            "success": False,
            "message": (
                "No readable text chunks "
                "were found."
            )
        }

    print(
        "\n======================================"
    )

    print(
        "BUILDING COMBINED VECTORSTORE"
    )

    print(
        "Total chunks:",
        len(all_chunks)
    )

    print(
        "======================================"
    )

    # --------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------

    try:

        embeddings = get_embedding_model().encode(
            all_chunks,
            convert_to_numpy=True,
            show_progress_bar=True
        )

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Combined embedding generation failed: {str(e)}"
            )
        }

    embeddings = embeddings.astype(
        "float32"
    )

    # --------------------------------------------------------
    # Create FAISS index
    # --------------------------------------------------------

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(
        embeddings
    )

    # --------------------------------------------------------
    # Save combined index
    # --------------------------------------------------------

    index_path = os.path.join(
        VECTORSTORE_DIR,
        "index.faiss"
    )

    faiss.write_index(
        index,
        index_path
    )

    # --------------------------------------------------------
    # Save combined chunks
    # --------------------------------------------------------

    chunks_path = os.path.join(
        VECTORSTORE_DIR,
        "chunks.pkl"
    )

    with open(
        chunks_path,
        "wb"
    ) as file:

        pickle.dump(
            all_chunks,
            file
        )

    # --------------------------------------------------------
    # Save combined metadata
    # --------------------------------------------------------

    metadata_path = os.path.join(
        VECTORSTORE_DIR,
        "metadata.pkl"
    )

    with open(
        metadata_path,
        "wb"
    ) as file:

        pickle.dump(
            metadata,
            file
        )

    print(
        "\nCombined vectorstore successfully created."
    )

    print(
        "FAISS vectors:",
        index.ntotal
    )

    print(
        "Metadata entries:",
        len(metadata)
    )

    return {
        "success": True,
        "pdf_count": len(pdf_files),
        "chunk_count": len(all_chunks),
        "vector_count": index.ntotal,
        "documents": processed_documents,
        "message": (
            "Combined and document-specific "
            "vectorstores created."
        )
    }


# ============================================================
# PROCESS SINGLE PDF
# ============================================================

def process_pdf(
    pdf_path: str
):
    """
    Process one uploaded PDF.

    The PDF is stored in the uploads directory and
    receives its own document-specific FAISS index.

    A complete rebuild is intentionally retained here
    for compatibility with the existing application.
    """

    if not os.path.exists(
        pdf_path
    ):

        return {
            "success": False,
            "message": (
                f"PDF file not found: {pdf_path}"
            )
        }

    # --------------------------------------------------------
    # Build all vectorstores
    # --------------------------------------------------------

    result = build_vectorstore()

    if not result["success"]:

        return result

    filename = os.path.basename(
        pdf_path
    )

    # --------------------------------------------------------
    # Find this PDF's result
    # --------------------------------------------------------

    document_result = None

    for document in result.get(
        "documents",
        []
    ):

        if document.get(
            "filename"
        ) == filename:

            document_result = document

            break

    return {
        "success": True,
        "filename": filename,

        "pdf_count":
            result.get(
                "pdf_count",
                0
            ),

        "chunks":
            document_result.get(
                "chunks",
                0
            )
            if document_result
            else 0,

        "vectors":
            document_result.get(
                "vectors",
                0
            )
            if document_result
            else 0,

        "message": (
            "PDF processed successfully. "
            "A separate vectorstore was created "
            "for this document."
        )
    }


# ============================================================
# SEARCH ONE SPECIFIC DOCUMENT
# ============================================================

def search_document(
    query: str,
    filename: str,
    top_k: int = 5
):
    """
    Search ONLY inside the requested PDF.
    """

    if not query or not query.strip():

        return {
            "success": False,
            "message": "Search query cannot be empty."
        }

    # --------------------------------------------------------
    # Resolve original filename to stored filename
    # --------------------------------------------------------

    resolved_filename = resolve_pdf_filename(
        filename
    )

    if not resolved_filename:

        return {
            "success": False,
            "message": (
                f"PDF not found: {filename}"
            )
        }

    # --------------------------------------------------------
    # Get paths without creating directories
    # --------------------------------------------------------

    paths = get_document_paths(
        resolved_filename,
        create_directory=False
    )

    # --------------------------------------------------------
    # Check vectorstore
    # --------------------------------------------------------

    if not os.path.exists(
        paths["index"]
    ):

        return {
            "success": False,
            "message": (
                f"No vectorstore found "
                f"for {filename}."
            )
        }

    if not os.path.exists(
        paths["metadata"]
    ):

        return {
            "success": False,
            "message": (
                f"No metadata found "
                f"for {filename}."
            )
        }

    # --------------------------------------------------------
    # Load FAISS
    # --------------------------------------------------------

    try:

        index = faiss.read_index(
            paths["index"]
        )

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Could not load vectorstore: {str(e)}"
            )
        }

    if index.ntotal == 0:

        return {
            "success": False,
            "message": (
                f"The vectorstore for {filename} is empty."
            )
        }

    # --------------------------------------------------------
    # Load metadata
    # --------------------------------------------------------

    try:

        with open(
            paths["metadata"],
            "rb"
        ) as file:

            metadata = pickle.load(
                file
            )

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Could not load document metadata: {str(e)}"
            )
        }

    if not metadata:

        return {
            "success": False,
            "message": (
                f"No searchable content found in {filename}."
            )
        }

    # --------------------------------------------------------
    # Embed query
    # --------------------------------------------------------

    try:

        query_embedding = get_embedding_model().encode(
            [query],
            convert_to_numpy=True
        )

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Could not create query embedding: {str(e)}"
            )
        }

    query_embedding = query_embedding.astype(
        "float32"
    )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    actual_k = min(
        max(1, top_k),
        index.ntotal,
        len(metadata)
    )

    distances, indices = index.search(
        query_embedding,
        actual_k
    )

    results = []

    for distance, idx in zip(
        distances[0],
        indices[0]
    ):

        if idx < 0:
            continue

        if idx >= len(metadata):
            continue

        item = metadata[idx]

        results.append(
            {
                "text": item.get(
                    "text",
                    ""
                ),

                "source": item.get(
                    "source",
                    resolved_filename
                ),

                "page": item.get(
                    "page"
                ),

                "distance": float(
                    distance
                )
            }
        )

    return {
        "success": True,
        "query": query,
        "filename": filename,
        "stored_filename": resolved_filename,
        "results": results
    }


# ============================================================
# DELETE DOCUMENT VECTORSTORE
# ============================================================

def delete_document_vectorstore(
    filename: str
):
    """
    Delete the FAISS/vectorstore directory for a PDF.
    """

    resolved_filename = resolve_pdf_filename(
        filename
    )

    # If the physical PDF no longer exists,
    # the caller may already have the stored filename.
    if not resolved_filename:

        resolved_filename = os.path.basename(
            filename
        )

    paths = get_document_paths(
        resolved_filename,
        create_directory=False
    )

    document_dir = paths[
        "directory"
    ]

    if not os.path.exists(
        document_dir
    ):

        return {
            "success": True,
            "message": (
                "No document vectorstore found."
            )
        }

    try:

        shutil.rmtree(
            document_dir
        )

        return {
            "success": True,
            "message": (
                "Document vectorstore deleted successfully."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Could not delete document vectorstore: {str(e)}"
            )
        }


# ============================================================
# GET AVAILABLE DOCUMENTS
# ============================================================

def get_available_documents():

    documents = []

    for filename in os.listdir(
        UPLOADS_DIR
    ):

        if not filename.lower().endswith(
            ".pdf"
        ):

            continue

        paths = get_document_paths(
            filename,
            create_directory=False
        )

        documents.append(
            {
                "filename": filename,

                "ready":
                    os.path.exists(
                        paths["index"]
                    )
            }
        )

    return documents