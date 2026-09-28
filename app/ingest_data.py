from pathlib import Path

import pandas as pd

from app.database import engine


# --------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"


# --------------------------------------------------
# INGESTION FUNCTION
# --------------------------------------------------

def load_csv_to_postgres(csv_file, table_name):

    file_path = RAW_DATA_DIR / csv_file

    print(f"\nLoading {csv_file}...")

    # Read CSV
    df = pd.read_csv(file_path)

    print(f"Records found: {len(df)}")

    # Load into existing PostgreSQL table
    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False
    )

    print(
        f"✓ {len(df)} records loaded into "
        f"'{table_name}'"
    )


# --------------------------------------------------
# MAIN INGESTION WORKFLOW
# --------------------------------------------------

def main():

    print("\n================================")
    print("     AEGIS DATA INGESTION")
    print("================================")

    ##load_csv_to_postgres("users.csv", "users")

    ##load_csv_to_postgres("employees.csv","employees")

    ##load_csv_to_postgres("customers.csv","customers")

    load_csv_to_postgres("access_logs.csv","access_logs")

    print("\n================================")
    print("✓ DATA INGESTION COMPLETED")
    print("================================")


if __name__ == "__main__":
    main()