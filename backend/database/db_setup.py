import os
import sqlite3


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE_DIR = os.path.join(
    BASE_DIR,
    "database"
)

DB_PATH = os.path.join(
    DATABASE_DIR,
    "aura.db"
)


# ============================================================
# SAMPLE DATA
# ============================================================

CUSTOMERS = [
    (
        "Rahul Sharma",
        "rahul@example.com",
        "Bangalore",
        45000
    ),
    (
        "Priya Reddy",
        "priya@example.com",
        "Hyderabad",
        62000
    ),
    (
        "Arjun Kumar",
        "arjun@example.com",
        "Chennai",
        38000
    ),
    (
        "Sneha Rao",
        "sneha@example.com",
        "Bangalore",
        71000
    ),
    (
        "Vikram Singh",
        "vikram@example.com",
        "Mumbai",
        29000
    ),
    (
        "Ananya Das",
        "ananya@example.com",
        "Delhi",
        55000
    ),
    (
        "Kiran Patel",
        "kiran@example.com",
        "Pune",
        47000
    ),
    (
        "Meera Nair",
        "meera@example.com",
        "Bangalore",
        83000
    ),
    (
        "Aditya Verma",
        "aditya@example.com",
        "Hyderabad",
        34000
    ),
    (
        "Pooja Iyer",
        "pooja@example.com",
        "Chennai",
        59000
    )
]


EMPLOYEES = [
    (
        "Amit Shah",
        "Sales",
        "Bangalore",
        65000
    ),
    (
        "Neha Kapoor",
        "Marketing",
        "Mumbai",
        72000
    ),
    (
        "Rohan Mehta",
        "Engineering",
        "Hyderabad",
        95000
    ),
    (
        "Divya Rao",
        "Sales",
        "Bangalore",
        68000
    ),
    (
        "Suresh Kumar",
        "Engineering",
        "Chennai",
        88000
    ),
    (
        "Kavya Nair",
        "HR",
        "Pune",
        60000
    )
]


SALES = [
    (
        1,
        "Laptop",
        75000,
        "2026-08-01"
    ),
    (
        2,
        "Monitor",
        25000,
        "2026-08-03"
    ),
    (
        3,
        "Keyboard",
        5000,
        "2026-08-05"
    ),
    (
        4,
        "Laptop",
        80000,
        "2026-08-07"
    ),
    (
        5,
        "Mouse",
        2500,
        "2026-08-10"
    ),
    (
        6,
        "Monitor",
        30000,
        "2026-08-12"
    ),
    (
        7,
        "Laptop",
        70000,
        "2026-08-15"
    ),
    (
        8,
        "Keyboard",
        6000,
        "2026-08-18"
    ),
    (
        9,
        "Mouse",
        3000,
        "2026-08-20"
    ),
    (
        10,
        "Laptop",
        78000,
        "2026-08-22"
    )
]


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create a SQLite database connection.
    """

    os.makedirs(
        DATABASE_DIR,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DB_PATH,
        timeout=30
    )

    # Return rows that can be accessed by column name.
    connection.row_factory = sqlite3.Row

    # Enable foreign-key constraints.
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# CREATE TABLES
# ============================================================

def create_tables(
    connection
):
    """
    Create AURA's demo SQL tables.
    """

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Customers
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            city TEXT,
            total_spent REAL
        )
        """
    )

    # --------------------------------------------------------
    # Employees
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT,
            city TEXT,
            salary REAL
        )
        """
    )

    # --------------------------------------------------------
    # Sales
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            product TEXT,
            amount REAL,
            sale_date TEXT,

            FOREIGN KEY (customer_id)
                REFERENCES customers(id)
        )
        """
    )


# ============================================================
# CHECK WHETHER TABLE HAS DATA
# ============================================================

def table_has_data(
    connection,
    table_name: str
) -> bool:
    """
    Check whether a table already contains rows.

    Only internal, predefined table names should be passed.
    """

    allowed_tables = {
        "customers",
        "employees",
        "sales"
    }

    if table_name not in allowed_tables:

        raise ValueError(
            f"Invalid table name: {table_name}"
        )

    cursor = connection.cursor()

    cursor.execute(
        f"""
        SELECT 1
        FROM {table_name}
        LIMIT 1
        """
    )

    return cursor.fetchone() is not None


# ============================================================
# INSERT SAMPLE CUSTOMERS
# ============================================================

def insert_sample_customers(
    connection
):
    """
    Insert demo customers only if the table is empty.
    """

    if table_has_data(
        connection,
        "customers"
    ):

        return False

    cursor = connection.cursor()

    cursor.executemany(
        """
        INSERT INTO customers
        (
            name,
            email,
            city,
            total_spent
        )
        VALUES (?, ?, ?, ?)
        """,
        CUSTOMERS
    )

    return True


# ============================================================
# INSERT SAMPLE EMPLOYEES
# ============================================================

def insert_sample_employees(
    connection
):
    """
    Insert demo employees only if the table is empty.
    """

    if table_has_data(
        connection,
        "employees"
    ):

        return False

    cursor = connection.cursor()

    cursor.executemany(
        """
        INSERT INTO employees
        (
            name,
            department,
            city,
            salary
        )
        VALUES (?, ?, ?, ?)
        """,
        EMPLOYEES
    )

    return True


# ============================================================
# INSERT SAMPLE SALES
# ============================================================

def insert_sample_sales(
    connection
):
    """
    Insert demo sales only if the table is empty.
    """

    if table_has_data(
        connection,
        "sales"
    ):

        return False

    # --------------------------------------------------------
    # Sales reference customer IDs 1-10.
    # Make sure customers exist first.
    # --------------------------------------------------------

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM customers
        """
    )

    customer_count = cursor.fetchone()[0]

    if customer_count < len(SALES):

        raise RuntimeError(
            "Cannot insert sample sales because "
            "the required customers do not exist."
        )

    cursor.executemany(
        """
        INSERT INTO sales
        (
            customer_id,
            product,
            amount,
            sale_date
        )
        VALUES (?, ?, ?, ?)
        """,
        SALES
    )

    return True


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():
    """
    Create tables and insert demo data if the tables are empty.
    """

    print("=" * 60)
    print("AURA DATABASE INITIALIZATION")
    print("=" * 60)

    print(
        "Database:",
        DB_PATH
    )

    connection = get_connection()

    try:

        # ----------------------------------------------------
        # Create tables
        # ----------------------------------------------------

        create_tables(
            connection
        )

        # ----------------------------------------------------
        # Insert sample data
        # ----------------------------------------------------

        customers_added = (
            insert_sample_customers(
                connection
            )
        )

        employees_added = (
            insert_sample_employees(
                connection
            )
        )

        sales_added = (
            insert_sample_sales(
                connection
            )
        )

        # ----------------------------------------------------
        # Save changes
        # ----------------------------------------------------

        connection.commit()

        print()

        print(
            "Customers:",
            "initialized"
            if customers_added
            else "already populated"
        )

        print(
            "Employees:",
            "initialized"
            if employees_added
            else "already populated"
        )

        print(
            "Sales:",
            "initialized"
            if sales_added
            else "already populated"
        )

        print()
        print(
            "AURA database initialization complete."
        )

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":

    initialize_database()