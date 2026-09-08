import os
import sqlite3
import getpass

from database.auth_db import (
    hash_password,
    verify_password
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.path.join(
    BASE_DIR,
    "database",
    "aura.db"
)


# ============================================================
# PASSWORD CONFIGURATION
# ============================================================

MIN_PASSWORD_LENGTH = 8


# ============================================================
# RESET PASSWORD
# ============================================================

def reset_password():
    """
    Reset the password for an existing AURA user.

    This is a local development/admin utility.
    It is NOT part of the public API.
    """

    print("=" * 60)
    print("AURA PASSWORD RESET")
    print("=" * 60)

    # --------------------------------------------------------
    # Ask for account
    # --------------------------------------------------------

    email = input(
        "\nEnter account email: "
    ).strip()

    if not email:

        print(
            "\nERROR: Email cannot be empty."
        )

        return False

    # --------------------------------------------------------
    # Check database
    # --------------------------------------------------------

    if not os.path.exists(DB_PATH):

        print(
            "\nERROR: AURA database was not found."
        )

        print(
            "\nExpected location:"
        )

        print(DB_PATH)

        return False

    connection = None

    try:

        # ----------------------------------------------------
        # Connect to database
        # ----------------------------------------------------

        connection = sqlite3.connect(
            DB_PATH,
            timeout=30
        )

        cursor = connection.cursor()

        # ----------------------------------------------------
        # Find user
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                username,
                email
            FROM users
            WHERE email = ?
            """,
            (
                email,
            )
        )

        user = cursor.fetchone()

        if not user:

            print(
                "\nERROR: User account not found."
            )

            return False

        user_id = user[0]
        username = user[1]
        account_email = user[2]

        print()
        print("Account found:")
        print(
            "User ID :",
            user_id
        )
        print(
            "Username:",
            username
        )
        print(
            "Email   :",
            account_email
        )

        # ----------------------------------------------------
        # Get new password
        # ----------------------------------------------------

        new_password = getpass.getpass(
            "\nEnter your new password: "
        )

        confirm_password = getpass.getpass(
            "Confirm your new password: "
        )

        # ----------------------------------------------------
        # Validate password
        # ----------------------------------------------------

        if not new_password:

            print(
                "\nERROR: Password cannot be empty."
            )

            return False

        if new_password != confirm_password:

            print(
                "\nERROR: Passwords do not match."
            )

            return False

        if len(new_password) < MIN_PASSWORD_LENGTH:

            print(
                f"\nERROR: Password must contain "
                f"at least {MIN_PASSWORD_LENGTH} characters."
            )

            return False

        # ----------------------------------------------------
        # Generate password hash
        # ----------------------------------------------------

        print(
            "\nCreating password hash using "
            "AURA's authentication system..."
        )

        password_hash = hash_password(
            new_password
        )

        # ----------------------------------------------------
        # Update password
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (
                password_hash,
                user_id
            )
        )

        if cursor.rowcount != 1:

            connection.rollback()

            print(
                "\nERROR: Password update failed."
            )

            return False

        connection.commit()

        # ----------------------------------------------------
        # Verify the new password
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT password_hash
            FROM users
            WHERE id = ?
            """,
            (
                user_id,
            )
        )

        stored_password_row = (
            cursor.fetchone()
        )

        if not stored_password_row:

            print(
                "\nERROR: Could not verify database update."
            )

            return False

        stored_password = (
            stored_password_row[0]
        )

        password_is_valid = verify_password(
            new_password,
            stored_password
        )

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        if password_is_valid:

            print()
            print("=" * 60)
            print("PASSWORD RESET SUCCESSFUL")
            print("=" * 60)

            print()
            print("Account:")
            print(
                "Username:",
                username
            )
            print(
                "Email   :",
                account_email
            )

            print()
            print(
                "Your account was NOT deleted."
            )

            print(
                "Your chat history was NOT deleted."
            )

            print()
            print(
                "The new password is compatible "
                "with AURA's login system."
            )

            return True

        print()
        print("=" * 60)
        print("PASSWORD RESET FAILED")
        print("=" * 60)

        print()
        print(
            "The new password could not be verified."
        )

        return False

    except sqlite3.Error as e:

        if connection is not None:

            connection.rollback()

        print()
        print("DATABASE ERROR:")
        print(str(e))

        return False

    except Exception as e:

        if connection is not None:

            connection.rollback()

        print()
        print("ERROR:")
        print(str(e))

        return False

    finally:

        if connection is not None:

            connection.close()


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":

    success = reset_password()

    if not success:

        raise SystemExit(1)