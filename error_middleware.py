import logging
from tkinter import messagebox
from psycopg2.errors import (
    UniqueViolation,
    ForeignKeyViolation,
    NotNullViolation,
    CheckViolation,
    IntegrityError,
)

# ---------- Logging ----------
logging.basicConfig(
    filename="app.log",
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def handle_db_error(exc, context=""):
    """
    Central DB error handler:
    - Logs technical info
    - Shows user-friendly message
    """

    constraint = getattr(exc.diag, "constraint_name", None)

    logging.error(
        "DB ERROR | context=%s | type=%s | constraint=%s | msg=%s",
        context,
        type(exc).__name__,
        constraint,
        str(exc)
    )

    # -------- User-friendly messages --------
    if isinstance(exc, UniqueViolation):
        if constraint == "t_students_email_key":
            messagebox.showerror(
                "Duplicate email",
                "There is already a student registered with this email."
            )
        else:
            messagebox.showerror(
                "Duplicate value",
                "This record already exists."
            )

    elif isinstance(exc, ForeignKeyViolation):
        messagebox.showerror(
            "Invalid reference",
            "This record is linked to other data and cannot be modified."
        )

    elif isinstance(exc, NotNullViolation):
        messagebox.showerror(
            "Missing data",
            "Some required fields are missing."
        )

    elif isinstance(exc, CheckViolation):
        messagebox.showerror(
            "Invalid data",
            "One or more fields contain invalid values."
        )

    elif isinstance(exc, IntegrityError):
        messagebox.showerror(
            "Database integrity error",
            "The operation violates database rules."
        )

    else:
        messagebox.showerror(
            "Unexpected error",
            "An unexpected database error occurred."
        )
