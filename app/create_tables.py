from sqlalchemy import text

from app.database import engine


def create_tables():

    with engine.begin() as connection:

        # --------------------------------------------------
        # ACCESS EVENTS
        # --------------------------------------------------

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS access_events (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50),
                timestamp TIMESTAMP,
                dataset_name VARCHAR(100),
                action VARCHAR(50),
                records_accessed INTEGER,
                source_ip VARCHAR(100),
                location VARCHAR(100),
                device VARCHAR(100),
                success BOOLEAN,
                ml_anomaly INTEGER,
                ml_probability FLOAT,
                behavioral_anomaly INTEGER,
                combined_anomaly INTEGER,
                alert_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # --------------------------------------------------
        # SECURITY ALERTS
        # --------------------------------------------------

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS security_alerts (
                id SERIAL PRIMARY KEY,
                event_id INTEGER,
                user_id VARCHAR(50),
                timestamp TIMESTAMP,
                dataset_name VARCHAR(100),
                action VARCHAR(50),
                records_accessed INTEGER,
                source_ip VARCHAR(100),
                location VARCHAR(100),
                device VARCHAR(100),
                ml_anomaly INTEGER,
                ml_probability FLOAT,
                behavioral_anomaly INTEGER,
                combined_anomaly INTEGER,
                alert_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # --------------------------------------------------
        # AGENT REPORTS
        # --------------------------------------------------

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_reports (
                id SERIAL PRIMARY KEY,
                event_id INTEGER,
                user_id VARCHAR(50),
                risk_level VARCHAR(20),
                investigation_priority VARCHAR(20),
                security_assessment TEXT,
                evidence JSONB,
                relevant_policies JSONB,
                recommended_actions JSONB,
                additional_evidence_required JSONB,
                escalation_required BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

    print("✓ PostgreSQL tables created successfully")
    print("  - access_events")
    print("  - security_alerts")
    print("  - agent_reports")


if __name__ == "__main__":
    create_tables()