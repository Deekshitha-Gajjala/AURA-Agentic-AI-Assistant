import os
import sqlite3


# ============================================================
# DATABASE PATH
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
# FIND USERS
# ============================================================

def find_users():
    """
    Display registered AURA users.

    This is a local development/debugging utility.
    """

    print("=" * 60)
    print("AURA USER ACCOUNTS")
    print("=" * 60)

    # --------------------------------------------------------
    # Check database exists
    # --------------------------------------------------------

    if not os.path.exists(DB_PATH):

        print()
        print("ERROR:")
        print("AURA database was not found.")
        print()
        print("Expected location:")
        print(DB_PATH)
        print()
        print("=" * 60)

        return

    connection = None

    try:

        # ----------------------------------------------------
        # Connect to database
        # ----------------------------------------------------

        connection = sqlite3.connect(
            DB_PATH
        )

        cursor = connection.cursor()

        # ----------------------------------------------------
        # Read users
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                username,
                email
            FROM users
            ORDER BY id
            """
        )

        users = cursor.fetchall()

        # ----------------------------------------------------
        # Display users
        # ----------------------------------------------------

        if not users:

            print()
            print("No users found.")

        else:

            print()

            for user in users:

                print(
                    f"User ID : {user[0]}"
                )

                print(
                    f"Username: {user[1]}"
                )

                print(
                    f"Email   : {user[2]}"
                )

                print("-" * 60)

    except sqlite3.Error as e:

        print()
        print("DATABASE ERROR:")
        print(str(e))

    except Exception as e:

        print()
        print("ERROR:")
        print(str(e))

    finally:

        if connection is not None:

            connection.close()

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":

    find_users()