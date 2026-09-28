import os
import json
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from sqlalchemy import text

from app.database import engine
from app.rag_retrieval import retrieve_relevant_context


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3.1-flash-lite"


# ============================================================
# GEMINI API WITH RETRY HANDLING
# ============================================================

def generate_with_retry(prompt, max_retries=5):

    last_error = None

    for attempt in range(max_retries):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            return response.text

        except Exception as error:

            last_error = error
            error_text = str(error)

            if "503" in error_text or "UNAVAILABLE" in error_text:

                wait_time = 10 * (2 ** attempt)

                print(
                    f"\nGemini temporarily unavailable. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:

                raise error

    print("\nGemini request failed after multiple retries.")

    raise last_error


# ============================================================
# AGENT 1 — SECURITY DETECTION ANALYST
# ============================================================

def security_detection_agent(alert):
    """
    Agent 1:
    Organizes and summarizes evidence from the completed
    ML and behavioral detection systems.

    This agent does NOT decide whether the event is anomalous.
    """

    evidence = {
        "user_id": str(alert["user_id"]),
        "timestamp": str(alert["timestamp"]),
        "dataset": str(alert["dataset_name"]),
        "action": str(alert["action"]),
        "records_accessed": int(alert["records_accessed"]),
        "source_ip": str(alert["source_ip"]),
        "location": str(alert["location"]),
        "device": str(alert["device"]),
        "success": bool(alert["success"]),
        "ml_anomaly": int(alert["ml_anomaly"]),
        "ml_probability": float(alert["ml_probability"]),
        "behavioral_anomaly": int(alert["behavioral_anomaly"]),
        "combined_anomaly": int(alert["combined_anomaly"]),
        "alert_reason": str(alert["alert_reason"]),
    }

    prompt = f"""
You are Agent 1 of the AEGIS cybersecurity system.

Your role is to organize and summarize evidence from an
already-completed security detection system.

IMPORTANT:
- Do NOT decide whether the alert is anomalous.
- Do NOT change the detector result.
- Do NOT invent facts.
- Clearly distinguish observed evidence from possible explanations.
- Do not claim an attack occurred unless the evidence explicitly proves it.

Detector evidence:

{json.dumps(evidence, indent=2)}

Return a concise security evidence summary containing:

1. Alert status
2. Observed evidence
3. Important anomaly indicators
4. Questions that should be investigated

Return only the analysis.
"""

    response_text = generate_with_retry(prompt)

    return {
        "agent": "Security Detection Agent",
        "evidence": evidence,
        "analysis": response_text
    }


# ============================================================
# AGENT 2 — COMPLIANCE & POLICY ANALYST
# ============================================================

def compliance_policy_agent(alert, security_analysis):
    """
    Agent 2:
    Retrieves relevant organizational policies and regulations
    and explains their relevance to the alert.
    """

    rag_query = f"""
    Security alert involving user {alert["user_id"]}.

    Dataset: {alert["dataset_name"]}.
    Action: {alert["action"]}.
    Records accessed: {alert["records_accessed"]}.
    Location: {alert["location"]}.
    Device: {alert["device"]}.
    Access successful: {alert["success"]}.
    Alert reason: {alert["alert_reason"]}.

    Identify relevant organizational security, access control,
    privacy, incident response, and data protection requirements.
    """

    retrieved_context = retrieve_relevant_context(
        rag_query,
        k=7
    )

    context_text = ""

    for item in retrieved_context:

        context_text += f"""
SOURCE: {item["source"]}
DOCUMENT TYPE: {item["document_type"]}
SCORE: {item["score"]}

CONTENT:
{item["content"]}

--------------------------------------------------
"""

    prompt = f"""
You are Agent 2 of the AEGIS cybersecurity system.

Your role is to perform policy and compliance analysis.

The security detection agent has already analyzed the alert.

You must NOT change the detector result.

Use ONLY the retrieved knowledge below when identifying
organizational policies or regulations.

IMPORTANT:
- Do not invent policy sections.
- Do not invent legal requirements.
- If the retrieved information is insufficient, say so.
- Distinguish organizational policy from regulation.
- Do not claim a legal violation unless the retrieved evidence
  clearly supports that conclusion.
- Do not assume that every retrieved document is a regulation.
- Clearly identify internal AEGIS policies separately from
  external laws or regulations.

SECURITY AGENT ANALYSIS:

{security_analysis}

RETRIEVED KNOWLEDGE:

{context_text}

Identify:

1. Relevant organizational policies
2. Relevant regulatory requirements, if supported
3. Why each requirement is relevant
4. Any compliance information that requires further verification

Return only the analysis.
"""

    response_text = generate_with_retry(prompt)

    return {
        "agent": "Compliance & Policy Agent",
        "retrieved_documents": retrieved_context,
        "analysis": response_text
    }


# ============================================================
# AGENT 3 — SECURITY RESPONSE ANALYST
# ============================================================

def security_response_agent(
    alert,
    security_analysis,
    compliance_analysis
):

    alert_data = {
        "user_id": str(alert["user_id"]),
        "timestamp": str(alert["timestamp"]),
        "dataset": str(alert["dataset_name"]),
        "action": str(alert["action"]),
        "records_accessed": int(alert["records_accessed"]),
        "location": str(alert["location"]),
        "device": str(alert["device"]),
        "success": bool(alert["success"]),
        "ml_anomaly": int(alert["ml_anomaly"]),
        "ml_probability": float(alert["ml_probability"]),
        "behavioral_anomaly": int(alert["behavioral_anomaly"]),
        "combined_anomaly": int(alert["combined_anomaly"]),
        "alert_reason": str(alert["alert_reason"])
    }

    prompt = f"""
You are Agent 3 of the AEGIS cybersecurity system.

Your role is to produce the final security investigation
and response recommendation.

The anomaly detection system has already made the detection
decision.

You receive:

1. Original alert evidence
2. Security analyst findings
3. Compliance and policy analysis

IMPORTANT:
- Do not change the detector result.
- Do not invent facts.
- Do not state that an attack definitely occurred.
- Recommendations must be proportional to the observed evidence.
- Separate immediate investigation actions from possible escalation.
- If evidence is insufficient for a conclusion, explicitly state this.
- Distinguish observed facts from hypotheses.

ORIGINAL ALERT:

{json.dumps(alert_data, indent=2)}

SECURITY ANALYST:

{security_analysis}

COMPLIANCE ANALYST:

{compliance_analysis}

Return ONLY valid JSON.

Use exactly this structure:

{{
  "risk_level": "LOW | MEDIUM | HIGH",
  "investigation_priority": "LOW | MEDIUM | HIGH",
  "security_assessment": "Brief final assessment",
  "evidence": [
    "Observed evidence 1",
    "Observed evidence 2"
  ],
  "relevant_policies": [
    "Policy name 1",
    "Policy name 2"
  ],
  "recommended_actions": [
    "Recommended action 1",
    "Recommended action 2"
  ],
  "additional_evidence_required": [
    "Additional evidence 1",
    "Additional evidence 2"
  ],
  "escalation_required": true
}}

Rules:
- risk_level must be LOW, MEDIUM, or HIGH.
- investigation_priority must be LOW, MEDIUM, or HIGH.
- escalation_required must be true or false.
- Keep evidence limited to facts supported by the alert and analyses.
- Do not invent policy names.
- If no external regulation was retrieved, do not list a regulation.
- Do not claim a legal violation without sufficient evidence.
"""

    response_text = generate_with_retry(prompt)

    # Remove markdown code fences if Gemini adds them
    response_text = response_text.strip()

    if response_text.startswith("```json"):
        response_text = response_text[7:]

    if response_text.startswith("```"):
        response_text = response_text[3:]

    if response_text.endswith("```"):
        response_text = response_text[:-3]

    response_text = response_text.strip()

    try:

        structured_report = json.loads(response_text)

    except json.JSONDecodeError:

        print("\nWarning: Agent 3 did not return valid JSON.")
        print("Raw Agent 3 response:")
        print(response_text)

        structured_report = {
            "risk_level": "UNKNOWN",
            "investigation_priority": "UNKNOWN",
            "security_assessment": response_text,
            "evidence": [],
            "relevant_policies": [],
            "recommended_actions": [],
            "additional_evidence_required": [],
            "escalation_required": False
        }

    return {
        "agent": "Security Response Agent",
        "alert": alert_data,
        "structured_report": structured_report,
        "raw_analysis": response_text
    }


# ============================================================
# MAIN AEGIS AGENT PIPELINE
# ============================================================

def run_agent_pipeline(alert):

    print("\n" + "=" * 60)
    print("AEGIS 3-AGENT SECURITY PIPELINE")
    print("=" * 60)

    print("\n[AGENT 1] SECURITY DETECTION ANALYST")
    print("-" * 60)

    agent_1 = security_detection_agent(alert)

    print(agent_1["analysis"])

    print("\n[AGENT 2] COMPLIANCE & POLICY ANALYST")
    print("-" * 60)

    agent_2 = compliance_policy_agent(
        alert,
        agent_1["analysis"]
    )

    print(agent_2["analysis"])

    print("\n[AGENT 3] SECURITY RESPONSE ANALYST")
    print("-" * 60)

    agent_3 = security_response_agent(
        alert,
        agent_1["analysis"],
        agent_2["analysis"]
    )

    # Add RAG evidence to the final report

    agent_3["structured_report"]["rag_evidence"] = [

        {
            "source": item.get("source"),
            "document_type": item.get("document_type"),
            "score": item.get("score"),
            "content": item.get("content")
        }

        for item in agent_2["retrieved_documents"]
    ]

    print(
        json.dumps(
            agent_3["structured_report"],
            indent=2
        )
    )

    # Save latest individual security report

    output_path = (
        BASE_DIR
        / "data"
        / "processed"
        / "security_report.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            agent_3["structured_report"],
            f,
            indent=2
        )

    print(
        f"\n✓ Security report saved to: "
        f"{output_path}"
    )

    result = {

        "alert": {
            "event_id": int(alert["event_id"]),
            "user_id": str(alert["user_id"]),
            "timestamp": str(alert["timestamp"]),
            "dataset_name": str(alert["dataset_name"]),
            "action": str(alert["action"]),
            "records_accessed": int(alert["records_accessed"]),
            "source_ip": str(alert["source_ip"]),
            "location": str(alert["location"]),
            "device": str(alert["device"]),
            "success": bool(alert["success"]),
            "ml_anomaly": int(alert["ml_anomaly"]),
            "behavioral_anomaly": int(
                alert["behavioral_anomaly"]
            ),
            "combined_anomaly": int(
                alert["combined_anomaly"]
            ),
            "ml_probability": float(
                alert["ml_probability"]
            ),
            "alert_reason": str(
                alert["alert_reason"]
            )
        },

        "agent_1_security_analysis": agent_1,

        "agent_2_compliance_analysis": agent_2,

        "agent_3_response_analysis": agent_3
    }

    print("\n" + "=" * 60)
    print("AEGIS 3-AGENT PIPELINE COMPLETE")
    print("=" * 60)

    return result


# ============================================================
# GET PENDING ALERTS FROM POSTGRESQL
# ============================================================

def get_pending_alerts():

    query = """
        SELECT
            sa.event_id,
            sa.user_id,
            ae.timestamp,
            ae.dataset_name,
            ae.action,
            ae.records_accessed,
            ae.source_ip,
            ae.location,
            ae.device,
            ae.success,
            ae.ml_anomaly,
            ae.ml_probability,
            ae.behavioral_anomaly,
            ae.combined_anomaly,
            ae.alert_reason

        FROM security_alerts sa

        INNER JOIN access_events ae
            ON ae.id = sa.event_id

        WHERE NOT EXISTS (

            SELECT 1

            FROM agent_reports ar

            WHERE ar.event_id = sa.event_id
        )

        ORDER BY sa.event_id ASC
    """

    with engine.connect() as connection:

        df = pd.read_sql(
            text(query),
            connection
        )

    return df


# ============================================================
# SAVE AGENT REPORT TO POSTGRESQL
# ============================================================

def save_agent_report(
    alert,
    agent_result
):

    structured_report = (
        agent_result[
            "agent_3_response_analysis"
        ]["structured_report"]
    )

    query = text("""
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
            escalation_required
        )

        SELECT
            :event_id,
            :user_id,
            :risk_level,
            :investigation_priority,
            :security_assessment,
            CAST(:evidence AS JSONB),
            CAST(:relevant_policies AS JSONB),
            CAST(:recommended_actions AS JSONB),
            CAST(:additional_evidence_required AS JSONB),
            :escalation_required

        WHERE NOT EXISTS (

            SELECT 1

            FROM agent_reports

            WHERE event_id = :event_id
        )
    """)

    parameters = {

        "event_id": int(
            alert["event_id"]
        ),

        "user_id": str(
            alert["user_id"]
        ),

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

        "escalation_required": bool(
            structured_report.get(
                "escalation_required",
                False
            )
        )
    }

    with engine.begin() as connection:

        result = connection.execute(
            query,
            parameters
        )

    return result.rowcount


# ============================================================
# PROCESS ALL PENDING ALERTS
# ============================================================

def process_all_pending_alerts():

    print("\n" + "=" * 70)
    print("AEGIS - MULTI-ALERT AI INVESTIGATION")
    print("=" * 70)

    alerts = get_pending_alerts().head(8)

    print(
        f"\nPending alerts requiring AI investigation: "
        f"{len(alerts)}"
    )

    if alerts.empty:

        print(
            "\n✓ All detected anomalies already "
            "have AI reports."
        )

        return

    successful = 0
    failed = 0

    for position, (_, alert) in enumerate(
        alerts.iterrows(),
        start=1
    ):

        event_id = int(
            alert["event_id"]
        )

        user_id = str(
            alert["user_id"]
        )

        print("\n" + "=" * 70)

        print(
            f"PROCESSING ALERT "
            f"{position}/{len(alerts)}"
        )

        print("=" * 70)

        print(
            f"Event ID : {event_id}"
        )

        print(
            f"User ID  : {user_id}"
        )

        print(
            f"Dataset  : {alert['dataset_name']}"
        )

        print(
            f"Action   : {alert['action']}"
        )

        print(
            f"Reason   : {alert['alert_reason']}"
        )

        try:

            # Run existing 3-agent pipeline

            agent_result = run_agent_pipeline(
                alert.to_dict()
            )

            # Save Agent 3 report

            rows_inserted = save_agent_report(
                alert,
                agent_result
            )

            if rows_inserted == 1:

                successful += 1

                print(
                    f"\n✓ AI report saved "
                    f"for Event ID {event_id}"
                )

            else:

                print(
                    f"\n⚠ Report already existed "
                    f"for Event ID {event_id}"
                )

        except Exception as error:

            failed += 1

            print(
                f"\n✗ Failed for Event ID "
                f"{event_id}"
            )

            print(
                f"Error: {error}"
            )

            print(
                "\nContinuing with the next alert..."
            )

        # Small delay between Gemini requests

        time.sleep(2)

    print("\n" + "=" * 70)
    print(
        "MULTI-ALERT AI INVESTIGATION COMPLETE"
    )
    print("=" * 70)

    print(
        f"Successfully processed : {successful}"
    )

    print(
        f"Failed                 : {failed}"
    )

    with engine.connect() as connection:

        result = connection.execute(
            text(
                "SELECT COUNT(*) FROM agent_reports"
            )
        )

        total_reports = result.scalar()

    print(
        f"Total agent_reports in PostgreSQL: "
        f"{total_reports}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    process_all_pending_alerts()