import os
import shutil
import sqlite3
import traceback
import uuid

from dotenv import load_dotenv

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# FASTAPI
# ============================================================

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    Depends,
    HTTPException
)

from fastapi.responses import FileResponse

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel


# ============================================================
# AURA AGENT
# ============================================================

from agent.agent import run_agent


# ============================================================
# TOOLS
# ============================================================

from tools.ocr_tool import answer_from_image
from tools.pdf_tool import (
    process_pdf,
    delete_document_vectorstore
)
from tools.pdf_summary import summarize_pdf
from tools.pdf_quiz import generate_pdf_quiz
from tools.stt_tool import transcribe_audio
from tools.tts_tool import text_to_speech


# ============================================================
# CHAT DATABASE
# ============================================================

from database.memory_db import (
    save_chat,
    get_chat_history,
    create_conversation,
    get_conversations,
    get_conversation,
    get_conversation_messages,
    delete_conversation,
    delete_all_conversations
)


# ============================================================
# AUTH DATABASE
# ============================================================

from database.auth_db import (
    register_user,
    login_user
)


# ============================================================
# JWT AUTHENTICATION
# ============================================================

from auth import (
    create_access_token,
    get_current_user
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AURA - AI Voice Intelligence Assistant",
    description=(
        "AI-powered research assistant with "
        "Agentic AI, RAG, Web Search, YouTube, SQL, "
        "OCR, PDF processing, memory, authentication, "
        "speech-to-text and text-to-speech."
    ),
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origin_regex=(
        r"http://(localhost|127\.0\.0\.1):\d+"
    ),

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

UPLOADS_DIR = os.path.join(
    BASE_DIR,
    "uploads"
)

AUDIO_DIR = os.path.join(
    UPLOADS_DIR,
    "audio"
)

IMAGE_DIR = os.path.join(
    UPLOADS_DIR,
    "images"
)

PDF_DIR = os.path.join(
    UPLOADS_DIR,
    "pdfs"
)

DATABASE_DIR = os.path.join(
    BASE_DIR,
    "database"
)

AURA_DB = os.path.join(
    DATABASE_DIR,
    "aura.db"
)


os.makedirs(
    UPLOADS_DIR,
    exist_ok=True
)

os.makedirs(
    AUDIO_DIR,
    exist_ok=True
)

os.makedirs(
    IMAGE_DIR,
    exist_ok=True
)

os.makedirs(
    PDF_DIR,
    exist_ok=True
)

os.makedirs(
    DATABASE_DIR,
    exist_ok=True
)


# ============================================================
# REQUEST MODELS
# ============================================================

class Question(BaseModel):

    question: str
    document_id: int | None = None
    conversation_id: int | None = None


class ConversationRequest(BaseModel):

    title: str = "New conversation"


class RegisterRequest(BaseModel):

    username: str
    email: str
    password: str


class LoginRequest(BaseModel):

    email: str
    password: str


class SpeechRequest(BaseModel):

    text: str


# ============================================================
# DOCUMENT DATABASE
# ============================================================

def get_document_connection():

    return sqlite3.connect(
        AURA_DB
    )


def create_documents_table():

    connection = get_document_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            filename TEXT NOT NULL,

            stored_filename TEXT NOT NULL,

            file_path TEXT NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()

    connection.close()


# ============================================================
# ADD DOCUMENT
# ============================================================

def add_document(
    user_id: int,
    filename: str,
    stored_filename: str,
    file_path: str
):

    create_documents_table()

    connection = get_document_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO documents
        (
            user_id,
            filename,
            stored_filename,
            file_path
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            filename,
            stored_filename,
            file_path
        )
    )

    document_id = cursor.lastrowid

    connection.commit()

    connection.close()

    return document_id


# ============================================================
# GET USER DOCUMENTS
# ============================================================

def get_user_documents(
    user_id: int
):

    create_documents_table()

    connection = get_document_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            stored_filename,
            file_path,
            created_at
        FROM documents
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (
            user_id,
        )
    )

    rows = cursor.fetchall()

    connection.close()

    documents = []

    for row in rows:

        documents.append(
            {
                "id": row[0],
                "filename": row[1],
                "stored_filename": row[2],
                "file_path": row[3],
                "created_at": row[4]
            }
        )

    return documents


# ============================================================
# GET ONE DOCUMENT
# ============================================================

def get_user_document(
    document_id: int,
    user_id: int
):

    create_documents_table()

    connection = get_document_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            stored_filename,
            file_path,
            created_at
        FROM documents
        WHERE id = ?
        AND user_id = ?
        """,
        (
            document_id,
            user_id
        )
    )

    row = cursor.fetchone()

    connection.close()

    if not row:
        return None

    return {
        "id": row[0],
        "filename": row[1],
        "stored_filename": row[2],
        "file_path": row[3],
        "created_at": row[4]
    }


# ============================================================
# DELETE DOCUMENT RECORD
# ============================================================

def remove_document_record(
    document_id: int,
    user_id: int
):

    create_documents_table()

    connection = get_document_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM documents
        WHERE id = ?
        AND user_id = ?
        """,
        (
            document_id,
            user_id
        )
    )

    deleted = cursor.rowcount

    connection.commit()

    connection.close()

    return deleted > 0


# ============================================================
# DELETE CHAT
# ============================================================

def delete_chat_record(
    chat_id: int,
    user_id: int
):

    connection = sqlite3.connect(
        AURA_DB
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM chat_history
        WHERE id = ?
        AND user_id = ?
        """,
        (
            chat_id,
            user_id
        )
    )

    deleted = cursor.rowcount

    connection.commit()

    connection.close()

    return deleted > 0


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():

    create_documents_table()

    print("")
    print("=" * 60)
    print("AURA BACKEND STARTED")
    print("=" * 60)
    print("Documents database ready.")
    print("=" * 60)
    print("")


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "AURA is running!",
        "status": "online"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# REGISTER
# ============================================================

@app.post("/register")
def register(
    request: RegisterRequest
):

    try:

        result = register_user(
            username=request.username,
            email=request.email,
            password=request.password
        )

        return result

    except Exception as e:

        traceback.print_exc()

        return {
            "success": False,
            "message": str(e)
        }


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
def login(
    request: LoginRequest
):

    try:

        result = login_user(
            email=request.email,
            password=request.password
        )

        if not result["success"]:

            return result

        access_token = create_access_token(
            user_id=result["user_id"],
            username=result["username"]
        )

        return {
            "success": True,

            "user_id":
                result["user_id"],

            "username":
                result["username"],

            "email":
                result["email"],

            "access_token":
                access_token,

            "token_type":
                "bearer",

            "message":
                "Login successful."
        }

    except Exception as e:

        traceback.print_exc()

        return {
            "success": False,
            "message": str(e)
        }


# ============================================================
# ASK AURA
# ============================================================

@app.post("/ask")
def ask(
    question: Question,

    current_user: dict = Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        print("")
        print("=" * 60)
        print("AURA /ASK")
        print("=" * 60)

        print(
            "USER:",
            current_user["username"]
        )

        print(
            "USER ID:",
            user_id
        )

        print(
            "QUESTION:",
            question.question
        )

        print("=" * 60)

        document_filename = None

        if question.document_id is not None:
            document = get_user_document(
                document_id=question.document_id,
                user_id=user_id
            )

            if not document:
                raise HTTPException(
                    status_code=404,
                    detail="Selected document was not found."
                )

            document_filename = document["stored_filename"]

        result = run_agent(
            query=question.question,
            user_id=user_id,
            document_filename=document_filename
        )

        answer = result.get(
            "answer",
            ""
        )

        route = result.get(
            "route",
            "GENERAL"
        )

        if not answer:

            answer = (
                "AURA could not generate "
                "an answer."
            )

        conversation_id = save_chat(
            question=question.question,
            answer=answer,
            route=route,
            user_id=user_id,
            conversation_id=question.conversation_id
        )

        print(
            "ROUTE:",
            route
        )

        print(
            "CHAT SAVED"
        )

        return {
            "success": True,

            "question":
                question.question,

            "user_id":
                user_id,

            "username":
                current_user["username"],

            "route":
                route,

            "conversation_id":
                conversation_id,

            "answer":
                answer
        }

    except Exception as e:

        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "error_type":
                type(e).__name__
        }


# ============================================================
# CHAT HISTORY
# ============================================================

@app.get("/history")
def history(
    current_user: dict = Depends(
        get_current_user
    )
):
    try:
        user_id = current_user["user_id"]

        chats = get_chat_history(
            user_id=user_id,
            limit=50
        )

        return {
            "success": True,
            "user_id": user_id,
            "username": current_user["username"],
            "count": len(chats),
            "history": [
                {
                    "id": chat["id"],
                    "conversation_id": chat["conversation_id"],
                    "user_id": chat["user_id"],
                    "question": chat["question"],
                    "answer": chat["answer"],
                    "route": chat["route"],
                    "created_at": chat["created_at"]
                }
                for chat in chats
            ]
        }

    except Exception as e:
        traceback.print_exc()

        return {
            "success": False,
            "message": str(e)
        }


# ============================================================
# CONVERSATIONS
# ============================================================

@app.post("/conversations")
def create_new_conversation(
    request: ConversationRequest,
    current_user: dict = Depends(
        get_current_user
    )
):
    try:
        conversation_id = create_conversation(
            user_id=current_user["user_id"],
            title=request.title.strip() or "New conversation"
        )

        conversation = get_conversation(
            conversation_id=conversation_id,
            user_id=current_user["user_id"]
        )

        return {
            "success": True,
            "conversation": conversation
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/conversations")
def list_conversations(
    current_user: dict = Depends(
        get_current_user
    )
):
    try:
        conversations = get_conversations(
            user_id=current_user["user_id"]
        )

        return {
            "success": True,
            "count": len(conversations),
            "conversations": conversations
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/conversations/{conversation_id}")
def open_conversation(
    conversation_id: int,
    current_user: dict = Depends(
        get_current_user
    )
):
    try:
        user_id = current_user["user_id"]

        conversation = get_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )

        if conversation:
            messages = get_conversation_messages(
                conversation_id=conversation_id,
                user_id=user_id
            )

            return {
                "success": True,
                "conversation": conversation,
                "messages": messages
            }

        # Backward compatibility for chats saved before the conversations
        # table was introduced.
        legacy = get_chat_history(user_id=user_id, limit=200)
        matching = [
            chat for chat in legacy
            if str(chat.get("conversation_id")) == str(conversation_id)
            or str(chat.get("id")) == str(conversation_id)
        ]

        if not matching:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found."
            )

        return {
            "success": True,
            "conversation": {
                "id": conversation_id,
                "title": matching[0].get("question", "Conversation"),
                "legacy": True
            },
            "messages": matching
        }

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.delete("/conversations/{conversation_id}")
def remove_conversation(
    conversation_id: int,
    current_user: dict = Depends(
        get_current_user
    )
):
    try:
        user_id = current_user["user_id"]

        deleted = delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )

        # Backward compatibility: older AURA chats may exist only in
        # chat_history. Delete every row belonging to that conversation.
        connection = sqlite3.connect(AURA_DB)
        cursor = connection.cursor()

        if deleted:
            deleted_rows = 0
        else:
            cursor.execute(
                """
                DELETE FROM chat_history
                WHERE user_id = ?
                AND conversation_id = ?
                """,
                (user_id, conversation_id)
            )
            deleted_rows = cursor.rowcount

            # Some very old rows may not have a conversation_id and are
            # represented only by their chat-history id.
            if deleted_rows == 0:
                cursor.execute(
                    """
                    DELETE FROM chat_history
                    WHERE user_id = ?
                    AND id = ?
                    """,
                    (user_id, conversation_id)
                )
                deleted_rows = cursor.rowcount

        connection.commit()
        connection.close()

        if not deleted and deleted_rows == 0:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found."
            )

        return {
            "success": True,
            "message": "Conversation deleted.",
            "conversation_id": conversation_id
        }

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.delete("/conversations")
def remove_all_conversations(
    current_user: dict = Depends(
        get_current_user
    )
):
    try:
        delete_all_conversations(
            user_id=current_user["user_id"]
        )

        return {
            "success": True,
            "message": "All conversations deleted."
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# DELETE ONE CHAT
# ============================================================

@app.delete("/history/{chat_id}")
def delete_chat(
    chat_id: int,

    current_user: dict = Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        deleted = delete_chat_record(
            chat_id=chat_id,
            user_id=user_id
        )

        if not deleted:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found."
            )

        return {
            "success": True,

            "message":
                "Conversation deleted.",

            "chat_id":
                chat_id
        }

    except HTTPException:

        raise

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# DELETE ALL CHATS
# ============================================================

@app.delete("/history")
def delete_all_chats(
    current_user: dict = Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        connection = sqlite3.connect(
            AURA_DB
        )

        cursor = connection.cursor()

        delete_all_conversations(
            user_id=user_id
        )

        return {
            "success": True,

            "message":
                "All conversations deleted."
        }

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# ASK IMAGE / OCR
# ============================================================

@app.post("/ask-image")
async def ask_image(
    question: str = Form(...),

    image: UploadFile = File(...),

    conversation_id: int | None = Form(None),

    current_user: dict = Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        original_filename = os.path.basename(
            image.filename
        )

        extension = os.path.splitext(
            original_filename
        )[1]

        stored_filename = (
            str(uuid.uuid4())
            + extension
        )

        image_path = os.path.join(
            IMAGE_DIR,
            stored_filename
        )

        with open(
            image_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                image.file,
                buffer
            )

        answer = answer_from_image(
            question,
            image_path
        )

        if os.path.exists(image_path):
            os.remove(image_path)

        conversation_id = save_chat(
            question=question,
            answer=answer,
            route="OCR",
            user_id=user_id,
            conversation_id=conversation_id
        )

        return {
            "success": True,

            "filename":
                original_filename,

            "user_id":
                user_id,

            "username":
                current_user["username"],

            "question":
                question,

            "route":
                "OCR",

            "conversation_id":
                conversation_id,

            "answer":
                answer
        }

    except Exception as e:

        traceback.print_exc()

        return {
            "success": False,
            "message": str(e)
        }


# ============================================================
# UPLOAD PDF
# ============================================================

@app.post("/upload-pdf")
async def upload_pdf(
    pdf: UploadFile = File(...),

    current_user: dict = Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        original_filename = os.path.basename(
            pdf.filename
        )

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        if not original_filename.lower().endswith(
            ".pdf"
        ):

            return {
                "success": False,

                "message":
                    "Please upload a PDF file."
            }

        # ----------------------------------------------------
        # UNIQUE STORED NAME
        # ----------------------------------------------------

        stored_filename = (
            str(uuid.uuid4())
            + "_"
            + original_filename
        )

        pdf_path = os.path.join(
            PDF_DIR,
            stored_filename
        )

        # ----------------------------------------------------
        # SAVE PDF
        # ----------------------------------------------------

        with open(
            pdf_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                pdf.file,
                buffer
            )

        print("")
        print("=" * 60)
        print("PDF UPLOAD")
        print("=" * 60)

        print(
            "USER:",
            current_user["username"]
        )

        print(
            "ORIGINAL:",
            original_filename
        )

        print(
            "STORED:",
            stored_filename
        )

        # ----------------------------------------------------
        # PROCESS PDF
        # ----------------------------------------------------

        try:
            result = process_pdf(
                pdf_path
            )
        except Exception:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            raise

        if isinstance(result, dict) and result.get("success") is False:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            return result

        # ----------------------------------------------------
        # SAVE DOCUMENT RECORD
        # ----------------------------------------------------

        document_id = add_document(
            user_id=user_id,

            filename=original_filename,

            stored_filename=stored_filename,

            file_path=pdf_path
        )

        print(
            "DOCUMENT ID:",
            document_id
        )

        print("=" * 60)

        return {
            "success": True,

            "document_id":
                document_id,

            "filename":
                original_filename,

            "stored_filename":
                stored_filename,

            "user_id":
                user_id,

            "username":
                current_user["username"],

            "message":
                (
                    f"{original_filename} "
                    "is ready. You can now "
                    "ask questions about this PDF."
                ),

            **result
        }

    except Exception as e:

        traceback.print_exc()

        return {
            "success": False,
            "message": str(e)
        }


# ============================================================
# GET USER DOCUMENTS
# ============================================================

@app.get("/documents")
def documents(
    current_user: dict = Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        docs = get_user_documents(
            user_id=user_id
        )

        return {
            "success": True,

            "user_id":
                user_id,

            "count":
                len(docs),

            "documents":
                docs
        }

    except Exception as e:

        traceback.print_exc()

        return {
            "success": False,
            "message": str(e)
        }


# ============================================================
# DELETE PDF
# ============================================================

@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,

    current_user: dict = Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        document = get_user_document(
            document_id=document_id,
            user_id=user_id
        )

        if not document:

            raise HTTPException(
                status_code=404,

                detail=
                    "Document not found."
            )

        file_path = document[
            "file_path"
        ]

        # ----------------------------------------------------
        # DELETE VECTORSTORE
        # ----------------------------------------------------

        vectorstore_result = delete_document_vectorstore(
            document["stored_filename"]
        )

        # ----------------------------------------------------
        # DELETE PHYSICAL FILE
        # ----------------------------------------------------

        if os.path.exists(
            file_path
        ):

            os.remove(
                file_path
            )

        # ----------------------------------------------------
        # DELETE DATABASE RECORD
        # ----------------------------------------------------

        remove_document_record(
            document_id=document_id,

            user_id=user_id
        )

        return {
            "success": True,

            "message":
                (
                    f"{document['filename']} "
                    "was deleted."
                ),

            "document_id":
                document_id,

            "vectorstore":
                vectorstore_result
        }

    except HTTPException:

        raise

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# SUMMARIZE PDF
# ============================================================

@app.post("/summarize-pdf")
async def summarize_uploaded_pdf(
    pdf: UploadFile = File(...),

    current_user: dict = Depends(
        get_current_user
    )
):

    try:

        filename = os.path.basename(
            pdf.filename
        )

        if not filename.lower().endswith(
            ".pdf"
        ):

            return {
                "success": False,
                "message":
                    "Please upload a PDF file."
            }

        stored_filename = (
            str(uuid.uuid4())
            + "_"
            + filename
        )

        pdf_path = os.path.join(
            PDF_DIR,
            stored_filename
        )

        with open(
            pdf_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                pdf.file,
                buffer
            )

        summary = summarize_pdf(
            pdf_path
        )

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        return {
            "success": True,

            "user_id":
                current_user["user_id"],

            "username":
                current_user["username"],

            "filename":
                filename,

            "summary":
                summary
        }

    except Exception as e:

        traceback.print_exc()

        return {
            "success": False,
            "message": str(e)
        }


# ============================================================
# GENERATE PDF QUIZ
# ============================================================

@app.post("/generate-quiz")
async def generate_quiz(
    pdf: UploadFile = File(...),

    number_of_questions: int = Form(5),

    current_user: dict = Depends(
        get_current_user
    )
):

    try:

        filename = os.path.basename(
            pdf.filename
        )

        if not filename.lower().endswith(
            ".pdf"
        ):

            return {
                "success": False,
                "message":
                    "Please upload a PDF file."
            }

        if number_of_questions < 1:

            return {
                "success": False,

                "message":
                    "Number of questions must be at least 1."
            }

        if number_of_questions > 15:

            return {
                "success": False,

                "message":
                    "Maximum 15 questions are allowed."
            }

        stored_filename = (
            str(uuid.uuid4())
            + "_"
            + filename
        )

        pdf_path = os.path.join(
            PDF_DIR,
            stored_filename
        )

        with open(
            pdf_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                pdf.file,
                buffer
            )

        quiz = generate_pdf_quiz(
            pdf_path=pdf_path,

            number_of_questions=
                number_of_questions
        )

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        return {
            "success": True,

            "user_id":
                current_user["user_id"],

            "username":
                current_user["username"],

            "filename":
                filename,

            "number_of_questions":
                number_of_questions,

            "quiz":
                quiz
        }

    except Exception as e:

        traceback.print_exc()

        return {
            "success": False,
            "message": str(e)
        }


# ============================================================
# SPEECH TO TEXT
# ============================================================

@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),

    current_user: dict = Depends(
        get_current_user
    )
):

    try:

        allowed_extensions = {
            ".wav",
            ".mp3",
            ".m4a",
            ".webm",
            ".ogg",
            ".flac"
        }

        filename = os.path.basename(
            audio.filename
        )

        extension = os.path.splitext(
            filename
        )[1].lower()

        if extension not in allowed_extensions:

            return {
                "success": False,

                "message":
                    (
                        "Unsupported audio format. "
                        "Use WAV, MP3, M4A, WEBM, "
                        "OGG or FLAC."
                    )
            }

        stored_filename = (
            str(uuid.uuid4())
            + extension
        )

        audio_path = os.path.join(
            AUDIO_DIR,
            stored_filename
        )

        with open(
            audio_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                audio.file,
                buffer
            )

        transcript = transcribe_audio(
            audio_path
        )

        if os.path.exists(audio_path):
            os.remove(audio_path)

        return {
            "success": True,

            "user_id":
                current_user["user_id"],

            "username":
                current_user["username"],

            "filename":
                filename,

            "transcript":
                transcript
        }

    except Exception as e:

        traceback.print_exc()

        return {
            "success": False,
            "message": str(e)
        }


# ============================================================
# VOICE ASK
# ============================================================

@app.post("/voice-ask")
async def voice_ask(
    audio: UploadFile = File(...),

    conversation_id: int | None = Form(None),

    current_user: dict = Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        allowed_extensions = {
            ".wav",
            ".mp3",
            ".m4a",
            ".webm",
            ".ogg",
            ".flac"
        }

        filename = os.path.basename(
            audio.filename
        )

        extension = os.path.splitext(
            filename
        )[1].lower()

        if extension not in allowed_extensions:

            return {
                "success": False,

                "message":
                    "Unsupported audio format."
            }

        stored_filename = (
            str(uuid.uuid4())
            + extension
        )

        audio_path = os.path.join(
            AUDIO_DIR,
            stored_filename
        )

        with open(
            audio_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                audio.file,
                buffer
            )

        # ----------------------------------------------------
        # SPEECH TO TEXT
        # ----------------------------------------------------

        transcript = transcribe_audio(
            audio_path
        )

        if not transcript:

            return {
                "success": False,

                "message":
                    "I couldn't understand the audio."
            }

        print(
            "VOICE TRANSCRIPT:",
            transcript
        )

        if os.path.exists(audio_path):
            os.remove(audio_path)

        # ----------------------------------------------------
        # RUN AURA
        # ----------------------------------------------------

        result = run_agent(
            query=transcript,

            user_id=user_id
        )

        answer = result.get(
            "answer",
            ""
        )

        route = result.get(
            "route",
            "GENERAL"
        )

        # ----------------------------------------------------
        # SAVE CHAT
        # ----------------------------------------------------

        conversation_id = save_chat(
            question=transcript,

            answer=answer,

            route=route,

            user_id=user_id,

            conversation_id=conversation_id
        )

        return {
            "success": True,

            "user_id":
                user_id,

            "username":
                current_user["username"],

            "filename":
                filename,

            "transcript":
                transcript,

            "route":
                route,

            "conversation_id":
                conversation_id,

            "answer":
                answer
        }

    except Exception as e:

        traceback.print_exc()

        return {
            "success": False,

            "message":
                str(e),

            "error_type":
                type(e).__name__
        }


# ============================================================
# TEXT TO SPEECH
# ============================================================

@app.post("/speak")
def speak(
    request: SpeechRequest,

    current_user: dict = Depends(
        get_current_user
    )
):

    try:

        text = request.text.strip()

        if not text:

            return {
                "success": False,

                "message":
                    "Text cannot be empty."
            }

        filename = (
            "aura_response_"
            + str(uuid.uuid4())
            + ".wav"
        )

        audio_path = os.path.join(
            AUDIO_DIR,
            filename
        )

        text_to_speech(
            text=text,

            output_path=audio_path
        )

        if not os.path.exists(
            audio_path
        ):

            return {
                "success": False,

                "message":
                    "Audio file was not generated."
            }

        return FileResponse(
            path=audio_path,

            media_type="audio/wav",

            filename="aura-response.wav"
        )

    except Exception as e:

        traceback.print_exc()

        return {
            "success": False,

            "message":
                str(e),

            "error_type":
                type(e).__name__
        }