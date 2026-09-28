import json
import pandas as pd
from sqlalchemy import text

from app.database import engine
from app.agents import run_agent_pipeline


def save_agent_report():

    # --------------------------------------------------
    # 1. Get alerts from 5 different users
    # --------------------------------------------------

    query = """
        SELECT DISTINCT ON (user_id)
            id,
            user_id,
            timestamp,
            dataset_name,
            action,
            records_accessed,
            source_ip,
            location,
            device,
            success,
            ml_anomaly,
            ml_probability,
            behavioral_anomaly,
            combined_anomaly,
            alert_reason
        FROM access_events
        WHERE combined_anomaly = 1
          AND NOT EXISTS (
              SELECT 1
              FROM agent_reports ar
              WHERE ar.event_id = access_events.id
          )
        ORDER BY user_id, timestamp
        LIMIT 5
    """

    with engine.connect() as connection:
        df = pd.read_sql(text(query), connection)

    if df.empty:
        print("✗ No new security alerts found.")
        return

    print("=" * 70)
    print("GENERATING AI SECURITY REPORTS")
    print("=" * 70)

    print(f"\n✓ Selected {len(df)} different users for AI investigation\n")

    # --------------------------------------------------
    # 2. Process each alert
    # --------------------------------------------------

    for _, row in df.iterrows():

        alert = row.to_dict()

        event_id = int(alert["id"])
        user_id = alert["user_id"]

        print("\n" + "=" * 70)
        print(f"PROCESSING USER: {user_id}")
        print(f"EVENT ID: {event_id}")
        print("=" * 70)

        # --------------------------------------------------
        # 3. Run the existing 3-agent pipeline
        # --------------------------------------------------

        try:

            run_agent_pipeline(alert)

            print("\n✓ 3-agent investigation completed")

        except Exception as error:

            print(
                f"\n✗ AI investigation failed "
                f"for user {user_id}"
            )
            print(f"Error: {error}")

            # Move to the next user
            continue

        # --------------------------------------------------
        # 4. Read Agent 3 structured report
        # --------------------------------------------------

        report_path = "data/processed/security_report.json"

        try:

            with open(
                report_path,
                "r",
                encoding="utf-8"
            ) as file:

                structured_report = json.load(file)

        except Exception as error:

            print(
                f"\n✗ Could not read security report "
                f"for user {user_id}"
            )
            print(f"Error: {error}")
            continue

        # --------------------------------------------------
        # 5. Check whether report already exists
        # --------------------------------------------------

        with engine.connect() as connection:

            existing = connection.execute(
                text("""
                    SELECT id
                    FROM agent_reports
                    WHERE event_id = :event_id
                    LIMIT 1
                """),
                {"event_id": event_id}
            ).fetchone()

        if existing:

            print(
                f"\n⚠ Agent report already exists "
                f"for event {event_id}. Skipping."
            )

            continue

        # --------------------------------------------------
        # 6. Insert Agent 3 report into PostgreSQL
        # --------------------------------------------------

        insert_query = text("""
            INSERT INTO agent_reports (
                event_id,
                user_id,
                risk_level,
                investigation_priority,
                security_assessment,
                evidence,
                relevant_policies,
                recommended_actions,
                additional_evidence_required,
                escalation_required,
                rag_evidence
            )
            VALUES (
                :event_id,
                :user_id,
                :risk_level,
                :investigation_priority,
                :security_assessment,
                :evidence,
                :relevant_policies,
                :recommended_actions,
                :additional_evidence_required,
                :escalation_required,
                :rag_evidence
            )
        """)

        with engine.begin() as connection:  

            connection.execute(
                insert_query,
                {
                    "event_id": event_id,

                    "user_id": user_id,

                    "risk_level": structured_report.get(
                        "risk_level",
                        "UNKNOWN"
                    ),

                    "investigation_priority": structured_report.get(
                        "investigation_priority",
                        "UNKNOWN"
                    ),

                    "security_assessment": structured_report.get(
                        "security_assessment",
                        ""
                    ),

                    "evidence": json.dumps(
                        structured_report.get(
                            "evidence",
                            []
                        )
                    ),

                    "relevant_policies": json.dumps(
                        structured_report.get(
                            "relevant_policies",
                            []
                        )
                    ),

                    "recommended_actions": json.dumps(
                        structured_report.get(
                            "recommended_actions",
                            []
                        )
                    ),

                    "additional_evidence_required": json.dumps(
                        structured_report.get(
                            "additional_evidence_required",
                            []
                        )
                    ),

                    "escalation_required": structured_report.get(
                        "escalation_required",
                        False
                    ),
                    "rag_evidence": json.dumps(
                        structured_report.get(
                            "rag_evidence",
                            []
                        )
                    )
                    
                }
        )

        # --------------------------------------------------
        # 7. Display result
        # --------------------------------------------------

        print("\n✓ Agent report saved to PostgreSQL")
        print(f"✓ User: {user_id}")
        print(f"✓ Event ID: {event_id}")
        print(
            f"✓ Risk Level: "
            f"{structured_report.get('risk_level')}"
        )
        print(
            f"✓ Investigation Priority: "
            f"{structured_report.get('investigation_priority')}"
        )

    print("\n" + "=" * 70)
    print("✓ MULTIPLE AI REPORTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    save_agent_report()