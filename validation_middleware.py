from datetime import date
import re


class ValidationError(Exception):
    """Controlled validation error (business rules)"""
    pass


def validate_required(value, field_name):
    if value is None or str(value).strip() == "":
        raise ValidationError(f"{field_name} is required")


def validate_email(email):
    validate_required(email, "Email")
    pattern = r"^[^@]+@[^@]+\.[^@]+$"
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format")


def validate_optional_email(email):
    if email is None or str(email).strip() == "":
        return
    validate_email(email)


def validate_weight(weight):
    if weight is None or weight == "":
        return
    try:
        w = float(weight)
        if w <= 0 or w > 300:
            raise ValidationError("Weight must be between 1 and 300 kg")
    except ValueError:
        raise ValidationError("Weight must be a number")


def validate_birthday(birthday):
    if birthday is None:
        return
    if birthday > date.today():
        raise ValidationError("Birthday cannot be in the future")
