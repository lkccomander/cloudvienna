import pytest
from datetime import date, timedelta

from validation_middleware import (
    ValidationError,
    validate_required,
    validate_email,
    validate_optional_email,
    validate_weight,
    validate_birthday,
)
# NOTE: Disabled below because importing ui.* triggers a DB connection in CI.
# from ui.reports import build_student_filters
# from ui.students import default_newsletter_opt_in

# ---------------------------
# Validation helper tests
# ---------------------------
def test_validate_required_ok():
    validate_required("John", "Name")

def test_validate_required_empty():
    with pytest.raises(ValidationError):
        validate_required("", "Name")

def test_validate_email_ok():
    validate_email("test@example.com")

def test_validate_email_invalid():
    with pytest.raises(ValidationError):
        validate_email("not-an-email")

def test_validate_weight_ok():
    validate_weight("80")

def test_validate_weight_invalid():
    with pytest.raises(ValidationError):
        validate_weight("-5")

def test_validate_birthday_ok():
    validate_birthday(date.today() - timedelta(days=365*20))

def test_validate_birthday_future():
    with pytest.raises(ValidationError):
        validate_birthday(date.today() + timedelta(days=1))


def test_full_student_registration_valid():
    student_data = {
        "name": "Ana Silva",
        "sex": "Female",
        "direction": "Main Street 123",
        "postalcode": "1010",
        "belt": "White",
        "email": "ana.silva@example.com",
        "phone": "+4312345678",
        "phone2": "",
        "weight": "62.5",
        "country": "Austria",
        "taxid": "ATU12345678",
        "birthday": date.today() - timedelta(days=365 * 25),
        "is_minor": False,
        "guardian_name": "",
        "guardian_email": "",
        "guardian_phone": "",
    }

    validate_required(student_data["name"], "Name")
    validate_weight(student_data["weight"])
    validate_birthday(student_data["birthday"])

    if student_data["is_minor"]:
        validate_required(student_data["guardian_name"], "Guardian Name")
        if (
            not student_data["guardian_email"].strip()
            and not student_data["guardian_phone"].strip()
        ):
            raise ValidationError("Guardian email or phone is required")
        validate_optional_email(student_data["guardian_email"])
        validate_optional_email(student_data["email"])
    else:
        validate_email(student_data["email"])

# ---------------------------
# Newsletter defaults
# ---------------------------

# def test_newsletter_default_opt_in():
#     assert default_newsletter_opt_in() is True

# ---------------------------
# Reports filter builder
# ---------------------------

# def test_reports_filters_name_only():
#     where_sql, params = build_student_filters("Ana", None, None, None)
#     assert "s.name ILIKE %s" in where_sql
#     assert params == ["%Ana%"]


# def test_reports_filters_location_none():
#     where_sql, params = build_student_filters("", "NONE", None, None)
#     assert "s.location_id IS NULL" in where_sql
#     assert params == []


# def test_reports_filters_location_specific():
#     where_sql, params = build_student_filters("", 5, None, None)
#     assert "s.location_id = %s" in where_sql
#     assert params == [5]


# def test_reports_filters_consent_and_status():
#     where_sql, params = build_student_filters("", None, True, False)
#     assert "s.newsletter_opt_in = %s" in where_sql
#     assert "s.active = %s" in where_sql
#     assert params == [True, False]
