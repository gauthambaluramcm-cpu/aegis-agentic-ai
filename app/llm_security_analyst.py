import os
import pandas as pd
from dotenv import load_dotenv
from google import genai

from app.rag_retrieval import retrieve_relevant_context


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY was not found in the .env file.")


# ============================================================
# CREATE GEMINI CLIENT
# ============================================================

client = genai.Client(api_key=api_key)


# ============================================================
# SECURITY ANALYST
# ============================================================

def analyze_alert(alert, retrieved_context):

    # Combine retrieved RAG documents into one context
    policy_context = ""

    for i, document in enumerate(retrieved_context, start=1):

        policy_context += f"""
--- Retrieved Document {i} ---
Source: {document['source']}
Document Type: {document['document_type']}
Content:
{document['content']}
"""


    prompt = f"""
You are the Security Investigator component of AEGIS,
an AI-based cybersecurity monitoring system.

The AEGIS detection system has already identified the
following activity as suspicious.

IMPORTANT:
- Do NOT determine whether the machine learning detector is correct.
- Treat the detector output as evidence.
- Do NOT invent facts that are not present in the alert.
- Clearly distinguish observed evidence from possible explanations.
- Do not claim that a specific attack occurred unless the evidence supports it.
- Use the retrieved organizational policies as supporting context.
- If the retrieved documents do not provide enough information,
  explicitly say so.

============================================================
SECURITY ALERT
============================================================

User ID: {alert['user_id']}
Timestamp: {alert['timestamp']}
Dataset: {alert['dataset_name']}
Action: {alert['action']}
Records Accessed: {alert['records_accessed']}
Source IP: {alert['source_ip']}
Location: {alert['location']}
Device: {alert['device']}
Access Successful: {alert['success']}

ML Anomaly: {alert['ml_anomaly']}
ML Probability: {alert['ml_probability']}

Unusual Location: {alert['unusual_location']}
Unusual Device: {alert['unusual_device']}
Behavioral Anomaly: {alert['behavioral_anomaly']}

Combined Anomaly: {alert['combined_anomaly']}
Alert Reason: {alert['alert_reason']}

Additional Evidence:
- Unusual Time: {alert['is_unusual_time']}
- Export Action: {alert['is_export']}
- Update Action: {alert['is_update']}
- Failed Access: {alert['is_failed']}
- Records vs User Average: {alert['records_vs_user_average']}
- Bulk Access: {alert['is_bulk_access']}


============================================================
RETRIEVED AEGIS KNOWLEDGE
============================================================

{policy_context}


============================================================
TASK
============================================================

Provide a professional security investigation assessment
using ONLY the alert evidence and retrieved knowledge.

Structure your response as:

1. Why the activity is suspicious
2. Key observed evidence
3. Relevant organizational policies
4. Potential security concerns
5. Recommended investigation actions

When discussing potential security concerns, clearly
identify them as possibilities rather than confirmed attacks.
"""


    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text


# ============================================================
# MAIN
# ============================================================

def main():

    file_path = "data/processed/combined_results.csv"

    df = pd.read_csv(file_path)

    # Select detected anomalies
    alerts = df[df["combined_anomaly"] == 1]

    if alerts.empty:
        print("No suspicious alerts found.")
        return

    # For this test, analyze the first detected alert
    alert = alerts.iloc[0]


    # --------------------------------------------------------
    # CREATE RAG QUERY
    # --------------------------------------------------------

    rag_query = f"""
    Security alert involving user {alert['user_id']}.

    The user accessed the {alert['dataset_name']} dataset
    using a {alert['device']} from {alert['location']}.

    Records accessed: {alert['records_accessed']}.
    Action: {alert['action']}.
    Access successful: {alert['success']}.

    ML anomaly: {alert['ml_anomaly']}.
    Unusual location: {alert['unusual_location']}.
    Unusual device: {alert['unusual_device']}.
    Failed access: {alert['is_failed']}.
    Bulk access: {alert['is_bulk_access']}.

    Alert reason:
    {alert['alert_reason']}

    Identify relevant access control, security monitoring,
    privacy, acceptable use, incident response, and
    data protection requirements.
    """


    print("\n" + "=" * 60)
    print("AEGIS SECURITY ALERT")
    print("=" * 60)

    print(f"\nUser ID       : {alert['user_id']}")
    print(f"Timestamp     : {alert['timestamp']}")
    print(f"Dataset       : {alert['dataset_name']}")
    print(f"Records       : {alert['records_accessed']}")
    print(f"Location      : {alert['location']}")
    print(f"Device        : {alert['device']}")
    print(f"Alert Reason  : {alert['alert_reason']}")


    # --------------------------------------------------------
    # RAG RETRIEVAL
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("RETRIEVING RELEVANT POLICIES")
    print("=" * 60)

    retrieved_context = retrieve_relevant_context(
        rag_query,
        k=5
    )

    for i, document in enumerate(retrieved_context, start=1):

        print(
            f"\n{i}. {document['source']} "
            f"(score: {document['score']:.4f})"
        )


    # --------------------------------------------------------
    # GEMINI ANALYSIS
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("GEMINI SECURITY INVESTIGATION")
    print("=" * 60)

    analysis = analyze_alert(
        alert,
        retrieved_context
    )

    print("\n")
    print(analysis)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()