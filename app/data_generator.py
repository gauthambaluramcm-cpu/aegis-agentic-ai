import random
from pathlib import Path
from datetime import date, timedelta

import pandas as pd
from faker import Faker


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

SEED = 42

NUM_USERS = 50
NUM_EMPLOYEES = 50
NUM_CUSTOMERS = 2000

fake = Faker("en_IN")

random.seed(SEED)
Faker.seed(SEED)


# --------------------------------------------------
# OUTPUT DIRECTORY
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# GENERATE USERS
# --------------------------------------------------

def generate_users(num_users=NUM_USERS):

    departments = [
        "Customer Support",
        "Finance",
        "Risk",
        "Operations",
        "IT",
        "Human Resources",
        "Compliance"
    ]

    roles = {
        "Customer Support": [
            "Support Executive",
            "Support Analyst"
        ],
        "Finance": [
            "Finance Analyst",
            "Finance Manager"
        ],
        "Risk": [
            "Risk Analyst",
            "Risk Manager"
        ],
        "Operations": [
            "Operations Analyst",
            "Operations Manager"
        ],
        "IT": [
            "IT Analyst",
            "System Administrator"
        ],
        "Human Resources": [
            "HR Executive",
            "HR Manager"
        ],
        "Compliance": [
            "Compliance Analyst",
            "Compliance Manager"
        ]
    }

    locations = [
        "Bangalore",
        "Mumbai",
        "Delhi",
        "Chennai",
        "Hyderabad",
        "Pune"
    ]

    employment_types = [
        "Full-time",
        "Contract"
    ]

    access_levels = [
        "LOW",
        "MEDIUM",
        "HIGH"
    ]

    users = []

    for i in range(1, num_users + 1):

        user_id = f"U{i:04d}"

        department = random.choice(departments)
        role = random.choice(roles[department])

        # First 5 users will act as managers
        if i <= 5:
            manager_id = None
        else:
            manager_id = f"U{random.randint(1, 5):04d}"

        users.append({
            "user_id": user_id,
            "name": fake.name(),
            "department": department,
            "role": role,
            "manager_id": manager_id,
            "location": random.choice(locations),
            "employment_type": random.choice(employment_types),
            "access_level": random.choice(access_levels)
        })

    return pd.DataFrame(users)


# --------------------------------------------------
# GENERATE EMPLOYEES
# --------------------------------------------------

def generate_employees(users_df):

    employees = []

    start_date = date(2018, 1, 1)
    end_date = date(2025, 12, 31)

    for _, user in users_df.iterrows():

        joining_date = start_date + timedelta(
            days=random.randint(
                0,
                (end_date - start_date).days
            )
        )

        employees.append({
            "employee_id": user["user_id"],
            "name": user["name"],
            "department": user["department"],
            "role": user["role"],
            "manager_id": user["manager_id"],
            "location": user["location"],
            "employment_type": user["employment_type"],
            "joining_date": joining_date
        })

    return pd.DataFrame(employees)


# --------------------------------------------------
# GENERATE CUSTOMERS
# --------------------------------------------------

def generate_customers(num_customers=NUM_CUSTOMERS):

    cities = [
        "Bangalore",
        "Mumbai",
        "Delhi",
        "Chennai",
        "Hyderabad",
        "Pune",
        "Kolkata",
        "Ahmedabad"
    ]

    customers = []

    for i in range(1, num_customers + 1):

        customer_id = f"C{i:06d}"

        customers.append({
            "customer_id": customer_id,
            "name": fake.name(),
            "email": f"customer{i:06d}@novafin.example",
            "phone": fake.msisdn()[:10],
            "date_of_birth": fake.date_of_birth(
                minimum_age=18,
                maximum_age=80
            ),
            "address": fake.address().replace("\n", ", "),
            "city": random.choice(cities),

            # Synthetic identifier.
            # This is NOT a real PAN.
            "pan_number": f"SIMU{i:06d}",

            # Synthetic account number.
            "account_number": f"AC{i:010d}",

            "income": round(
                random.uniform(25000, 500000),
                2
            )
        })

    return pd.DataFrame(customers)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    print("\n=== AEGIS SYNTHETIC DATA GENERATOR ===\n")

    # Generate users
    users_df = generate_users()

    # Generate employees based on users
    employees_df = generate_employees(users_df)

    # Generate customers
    customers_df = generate_customers()

    # Save datasets
    users_df.to_csv(
        RAW_DATA_DIR / "users.csv",
        index=False
    )

    employees_df.to_csv(
        RAW_DATA_DIR / "employees.csv",
        index=False
    )

    customers_df.to_csv(
        RAW_DATA_DIR / "customers.csv",
        index=False
    )

    # Display summary
    print("Data generation completed.\n")

    print(f"Users:      {len(users_df)}")
    print(f"Employees:  {len(employees_df)}")
    print(f"Customers:  {len(customers_df)}")

    print("\nFiles created:")
    print(RAW_DATA_DIR / "users.csv")
    print(RAW_DATA_DIR / "employees.csv")
    print(RAW_DATA_DIR / "customers.csv")

    print("\nSample Users:")
    print(users_df.head())

    print("\nSample Customers:")
    print(customers_df.head())


if __name__ == "__main__":
    main()