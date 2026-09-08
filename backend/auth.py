import os

from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import jwt, JWTError

from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# JWT CONFIGURATION
# ============================================================

SECRET_KEY = os.getenv(
    "AURA_SECRET_KEY"
)

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60

TOKEN_TYPE = "access"


# ============================================================
# VALIDATE SECRET KEY
# ============================================================

if not SECRET_KEY:

    raise ValueError(
        "AURA_SECRET_KEY is missing from .env"
    )

# Prevent accidentally using an extremely weak secret.
if len(SECRET_KEY) < 32:

    raise ValueError(
        "AURA_SECRET_KEY must contain at least 32 characters."
    )


# ============================================================
# BEARER AUTHENTICATION
# ============================================================

security = HTTPBearer(
    auto_error=False
)


# ============================================================
# CREATE ACCESS TOKEN
# ============================================================

def create_access_token(
    user_id: int,
    username: str
):
    """
    Create a JWT access token for an authenticated user.
    """

    if user_id is None:

        raise ValueError(
            "user_id is required to create an access token."
        )

    if not username:

        raise ValueError(
            "username is required to create an access token."
        )

    issued_at = datetime.now(
        timezone.utc
    )

    expires_at = (
        issued_at
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {

        # Subject = authenticated user ID
        "sub": str(user_id),

        # Username for convenience
        "username": username,

        # Token type
        "type": TOKEN_TYPE,

        # Issued-at time
        "iat": issued_at,

        # Expiration time
        "exp": expires_at
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    )
):
    """
    Validate the Bearer JWT and return the authenticated user.
    """

    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid or expired authentication token.",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    # --------------------------------------------------------
    # Missing Authorization header
    # --------------------------------------------------------

    if credentials is None:

        raise credentials_exception

    # --------------------------------------------------------
    # Validate authentication scheme
    # --------------------------------------------------------

    if credentials.scheme.lower() != "bearer":

        raise credentials_exception

    token = credentials.credentials

    if not token:

        raise credentials_exception

    try:

        # ----------------------------------------------------
        # Decode and verify JWT
        # ----------------------------------------------------

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # ----------------------------------------------------
        # Verify token type
        # ----------------------------------------------------

        token_type = payload.get(
            "type"
        )

        if token_type != TOKEN_TYPE:

            raise credentials_exception

        # ----------------------------------------------------
        # Get user ID
        # ----------------------------------------------------

        user_id = payload.get(
            "sub"
        )

        if user_id is None:

            raise credentials_exception

        # ----------------------------------------------------
        # Validate user ID
        # ----------------------------------------------------

        try:

            user_id = int(
                user_id
            )

        except (
            ValueError,
            TypeError
        ):

            raise credentials_exception

        if user_id <= 0:

            raise credentials_exception

        # ----------------------------------------------------
        # Get username
        # ----------------------------------------------------

        username = payload.get(
            "username"
        )

        if not username:

            raise credentials_exception

        # ----------------------------------------------------
        # Return authenticated user
        # ----------------------------------------------------

        return {
            "user_id": user_id,
            "username": username
        }

    except JWTError:

        raise credentials_exception

    except (
        ValueError,
        TypeError
    ):

        raise credentials_exception