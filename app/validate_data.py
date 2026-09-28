from pathlib import Path

import pandas as pd


# --------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"


# --------------------------------------------------
# VALIDATION FUNCTIONS
# --------------------------------------------------

def validate_users(df):
    print("\n--- VALIDATING USERS ---")

    # Record count
    print(f"Records: {len(df)}")
    assert len(df) == 50, "Expected 50 users"

    # Unique IDs
    assert df["user_id"].is_unique, "Duplicate user IDs found"

    # Required fields
    required_columns = [
        "user_id",
        "name",
        "department",
        "role",
        "location",
        "employment_type",
        "access_level"
    ]

    for column in required_columns:
        assert df[column].notna().all(), (
            f"Missing values found in {column}"
        )

    print("✓ User validation passed")


def validate_employees(df):
    print("\n--- VALIDATING EMPLOYEES ---")

    print(f"Records: {len(df)}")
    assert len(df) == 50, "Expected 50 employees"

    assert df["employee_id"].is_unique, (
        "Duplicate employee IDs found"
    )

    required_columns = [
        "employee_id",
        "name",
        "department",
        "role",
        "location",
        "employment_type",
        "joining_date"
    ]

    for column in required_columns:
        assert df[column].notna().all(), (
            f"Missing values found in {column}"
        )

    print("✓ Employee validation passed")


def validate_customers(df):
    print("\n--- VALIDATING CUSTOMERS ---")

    print(f"Records: {len(df)}")
    assert len(df) == 2000, "Expected 2000 customers"

    # Customer IDs must be unique
    assert df["customer_id"].is_unique, (
        "Duplicate customer IDs found"
    )

    # Email should be unique
    assert df["email"].is_unique, (
        "Duplicate customer emails found"
    )

    # Account numbers should be unique
    assert df["account_number"].is_unique, (
        "Duplicate account numbers found"
    )

    required_columns = [
        "customer_id",
        "name",
        "email",
        "phone",
        "date_of_birth",
        "address",
        "city",
        "pan_number",
        "account_number",
        "income"
    ]

    for column in required_columns:
        assert df[column].notna().all(), (
            f"Missing values found in {column}"
        )

    # Income should never be negative
    assert (df["income"] >= 0).all(), (
        "Negative income values found"
    )

    print("✓ Customer validation passed")


# --------------------------------------------------
# MAIN VALIDATION WORKFLOW
# --------------------------------------------------

def main():

    print("\n================================")
    print("     AEGIS DATA VALIDATION")
    print("================================")

    # Load datasets
    users = pd.read_csv(
        RAW_DATA_DIR / "users.csv"
    )

    employees = pd.read_csv(
        RAW_DATA_DIR / "employees.csv"
    )

    customers = pd.read_csv(
        RAW_DATA_DIR / "customers.csv"
    )

    # Validate
    validate_users(users)
    validate_employees(employees)
    validate_customers(customers)

    print("\n================================")
    print("✓ ALL DATA VALIDATION PASSED")
    print("================================")


if __name__ == "__main__":
    main()