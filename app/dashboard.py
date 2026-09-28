import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import engine


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AEGIS Security Operations Center",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# CUSTOM STYLE
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #0B0F14;
}

.block-container {
    max-width: 1500px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    letter-spacing: 0.02em;
}

.section-title {
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: #9AA4B2;
    border-bottom: 1px solid #252C36;
    padding-bottom: 0.6rem;
    margin-top: 1.8rem;
    margin-bottom: 1rem;
}

.status {
    display: inline-block;
    padding: 0.35rem 0.7rem;
    border: 1px solid #245C3A;
    color: #55D98A;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
}

.alert-box {
    border: 1px solid #6A2929;
    background-color: #151114;
    padding: 1rem;
}

.info-box {
    border: 1px solid #26384F;
    background-color: #101722;
    padding: 1rem;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATA LOADING FROM POSTGRESQL
# ============================================================

@st.cache_data(ttl=5)
def load_data():

    query = """
        SELECT
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
        ORDER BY timestamp DESC
    """

    with engine.connect() as connection:
        df = pd.read_sql(text(query), connection)

    return df


@st.cache_data(ttl=5)
def load_agent_reports():

    query = """
        SELECT
            id,
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
            created_at
        FROM agent_reports
        ORDER BY created_at DESC
    """

    with engine.connect() as connection:
        reports = pd.read_sql(text(query), connection)

    return reports


df = load_data()
agent_reports = load_agent_reports()


# ============================================================
# DATA PREPARATION
# ============================================================

if not df.empty:

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    alerts = df[
        df["combined_anomaly"] == 1
    ].copy()

else:

    alerts = pd.DataFrame()


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_events = len(df)

total_alerts = len(alerts)

normal_events = total_events - total_alerts

alert_rate = (
    total_alerts / total_events * 100
    if total_events > 0
    else 0
)


# Successful / failed access

successful_access = (
    df["success"]
    .astype(str)
    .str.lower()
    .isin(["true", "1"])
).sum()

failed_access = total_events - successful_access


# Users

users_monitored = (
    df["user_id"].nunique()
    if "user_id" in df.columns
    else 0
)


# Datasets

datasets_monitored = (
    df["dataset_name"].nunique()
    if "dataset_name" in df.columns
    else 0
)


# Records accessed

records_accessed = (
    pd.to_numeric(
        df["records_accessed"],
        errors="coerce"
    )
    .fillna(0)
    .sum()
)


# Users with alerts

users_at_risk = (
    alerts["user_id"].nunique()
    if len(alerts) > 0
    else 0
)


# ============================================================
# DETECTION INTELLIGENCE CALCULATIONS
# ============================================================

# ML detector alerts

ml_alerts = (
    df["ml_anomaly"].sum()
    if "ml_anomaly" in df.columns
    else 0
)


# Behavioral detector alerts

behavioral_alerts = (
    df["behavioral_anomaly"].sum()
    if "behavioral_anomaly" in df.columns
    else 0
)


# Unusual location alerts

location_alerts = (
    alerts["alert_reason"]
    .str.contains(
        "location",
        case=False,
        na=False
    ).sum()
    if "alert_reason" in alerts.columns
    else 0
)


# Unusual device alerts

device_alerts = (
    alerts["alert_reason"]
    .str.contains(
        "device",
        case=False,
        na=False
    ).sum()
    if "alert_reason" in alerts.columns
    else 0
)


# ============================================================
# HEADER
# ============================================================

header_left, header_right = st.columns([4, 1])


with header_left:

    st.title("🛡️ AEGIS")

    st.caption(
        "Agentic AI-powered Security Operations & Compliance Monitoring"
    )


with header_right:

    st.markdown(
        '<div class="status">● MONITORING ACTIVE</div>',
        unsafe_allow_html=True
    )


if len(df) > 0:

    latest_event = df["timestamp"].max()

    if pd.notna(latest_event):

        st.caption(
            f"Latest event processed: "
            f"{latest_event.strftime('%Y-%m-%d %H:%M:%S')}"
        )


# ============================================================
# SECURITY OVERVIEW
# ============================================================

st.markdown(
    '<div class="section-title">SECURITY OVERVIEW</div>',
    unsafe_allow_html=True
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Total Access Events",
        f"{total_events:,}"
    )


with c2:

    st.metric(
        "Security Alerts",
        f"{total_alerts:,}",
        delta=f"{alert_rate:.2f}% of events",
        delta_color="inverse"
    )


with c3:

    st.metric(
        "Normal Events",
        f"{normal_events:,}"
    )


with c4:

    st.metric(
        "Alert Rate",
        f"{alert_rate:.2f}%"
    )


# ============================================================
# OPERATIONAL KPIs
# ============================================================

st.markdown(
    '<div class="section-title">OPERATIONAL KPIs</div>',
    unsafe_allow_html=True
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Users Monitored",
        f"{users_monitored:,}"
    )


with c2:

    st.metric(
        "Datasets Monitored",
        f"{datasets_monitored:,}"
    )


with c3:

    st.metric(
        "Records Accessed",
        f"{records_accessed:,.0f}"
    )


with c4:

    st.metric(
        "Users with Alerts",
        f"{users_at_risk:,}"
    )


# ============================================================
# ACCESS HEALTH
# ============================================================

st.markdown(
    '<div class="section-title">ACCESS HEALTH</div>',
    unsafe_allow_html=True
)


c1, c2, c3 = st.columns(3)


with c1:

    st.metric(
        "Successful Access",
        f"{successful_access:,}"
    )


with c2:

    st.metric(
        "Failed Access",
        f"{failed_access:,}"
    )


with c3:

    failure_rate = (
        failed_access / total_events * 100
        if total_events > 0
        else 0
    )

    st.metric(
        "Failure Rate",
        f"{failure_rate:.2f}%"
    )


# ============================================================
# SECURITY POSTURE
# ============================================================

st.markdown(
    '<div class="section-title">SECURITY POSTURE</div>',
    unsafe_allow_html=True
)


col1, col2 = st.columns(2)


# -------------------------
# Alert trend
# -------------------------

with col1:

    st.subheader("Alert Trend")

    if len(alerts) > 0:

        trend = (
            alerts
            .set_index("timestamp")
            .resample("D")
            .size()
        )

        st.line_chart(
            trend,
            height=300
        )

    else:

        st.info(
            "No alerts available."
        )


# -------------------------
# Alert classification
# -------------------------

with col2:

    st.subheader("Alert Classification")

    if len(alerts) > 0:

        reason_counts = (
            alerts["alert_reason"]
            .value_counts()
        )

        st.bar_chart(
            reason_counts,
            height=300
        )

    else:

        st.info(
            "No alert classifications available."
        )


# ============================================================
# DETECTION INTELLIGENCE
# ============================================================

st.markdown(
    '<div class="section-title">DETECTION INTELLIGENCE</div>',
    unsafe_allow_html=True
)


# Only four metrics are shown here.
# Bulk Access and Failed Access Alerts
# have intentionally been removed.

c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "ML Alerts",
        f"{ml_alerts:,}"
    )


with c2:

    st.metric(
        "Behavioral Alerts",
        f"{behavioral_alerts:,}"
    )


with c3:

    st.metric(
        "Unusual Location",
        f"{location_alerts:,}"
    )


with c4:

    st.metric(
        "Unusual Device",
        f"{device_alerts:,}"
    )


# ============================================================
# USER & DATASET RISK
# ============================================================

st.markdown(
    '<div class="section-title">USER & DATASET RISK</div>',
    unsafe_allow_html=True
)


col1, col2 = st.columns(2)


# -------------------------
# Top users
# -------------------------

with col1:

    st.subheader(
        "Top Users Generating Alerts"
    )

    if len(alerts) > 0:

        top_users = (
            alerts
            .groupby("user_id")
            .size()
            .sort_values(
                ascending=False
            )
            .head(10)
        )

        st.bar_chart(
            top_users,
            height=350
        )

    else:

        st.info(
            "No users with alerts."
        )


# -------------------------
# Targeted datasets
# -------------------------

with col2:

    st.subheader(
        "Most Targeted Datasets"
    )

    if len(alerts) > 0:

        top_datasets = (
            alerts
            .groupby("dataset_name")
            .size()
            .sort_values(
                ascending=False
            )
            .head(10)
        )

        st.bar_chart(
            top_datasets,
            height=350
        )

    else:

        st.info(
            "No targeted datasets."
        )


# ============================================================
# RECENT SECURITY ALERTS
# ============================================================

st.markdown(
    '<div class="section-title">RECENT SECURITY ALERTS</div>',
    unsafe_allow_html=True
)


if len(alerts) > 0:

    display_columns = [
        "user_id",
        "timestamp",
        "dataset_name",
        "action",
        "records_accessed",
        "location",
        "device",
        "alert_reason"
    ]

    display_columns = [
        col
        for col in display_columns
        if col in alerts.columns
    ]

    recent_alerts = (
        alerts
        .sort_values(
            "timestamp",
            ascending=False
        )
        .head(25)
    )

    st.dataframe(
        recent_alerts[display_columns],
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "No security alerts detected."
    )


# ============================================================
# AI SECURITY INVESTIGATION
# ============================================================

st.markdown(
    '<div class="section-title">AI SECURITY INVESTIGATION</div>',
    unsafe_allow_html=True
)


if agent_reports.empty:

    st.info(
        "No AI security investigations are available yet."
    )

else:

    # --------------------------------------------------------
    # Alert selection
    # --------------------------------------------------------

    selected_event = st.selectbox(
        "Select an alert to investigate",
        agent_reports["event_id"].tolist()
    )


    report = agent_reports[
        agent_reports["event_id"] == selected_event
    ].iloc[0]


    # --------------------------------------------------------
    # Investigation summary
    # --------------------------------------------------------

    st.markdown(
        "### Investigation Summary"
    )


    c1, c2, c3, c4 = st.columns(4)


    with c1:

        st.metric(
            "User",
            report["user_id"]
        )


    with c2:

        st.metric(
            "Event ID",
            report["event_id"]
        )


    with c3:

        st.metric(
            "Risk Level",
            report["risk_level"]
        )


    with c4:

        st.metric(
            "Priority",
            report["investigation_priority"]
        )


    # --------------------------------------------------------
    # Security assessment
    # --------------------------------------------------------

    st.markdown(
        "### Security Assessment"
    )


    st.info(
        report["security_assessment"]
    )


    # --------------------------------------------------------
    # Evidence + policies
    # --------------------------------------------------------

    col1, col2 = st.columns(2)


    with col1:

        with st.expander(
            "🔎 Evidence",
            expanded=True
        ):

            for item in report["evidence"]:

                st.markdown(
                    f"• {item}"
                )


    with col2:

        with st.expander(
            "📋 Relevant Policies",
            expanded=True
        ):

            for policy in report["relevant_policies"]:

                st.markdown(
                    f"• {policy}"
                )


    # --------------------------------------------------------
    # Recommended actions
    # --------------------------------------------------------

    with st.expander(
        "🛠️ Recommended Actions",
        expanded=True
    ):

        for index, action in enumerate(
            report["recommended_actions"],
            start=1
        ):

            st.markdown(
                f"**{index}.** {action}"
            )


    # --------------------------------------------------------
    # Additional evidence
    # --------------------------------------------------------

    with st.expander(
        "📂 Additional Evidence Required",
        expanded=False
    ):

        for item in report[
            "additional_evidence_required"
        ]:

            st.markdown(
                f"• {item}"
            )


    # --------------------------------------------------------
    # Escalation
    # --------------------------------------------------------

    st.markdown(
        "### Escalation"
    )


    if report["escalation_required"]:

        st.error(
            "⚠️ Escalation Required"
        )

    else:

        st.success(
            "✓ Escalation Not Required"
        )


# ============================================================
# DETECTION MODEL PERFORMANCE
# ============================================================

st.markdown(
    '<div class="section-title">DETECTION MODEL PERFORMANCE</div>',
    unsafe_allow_html=True
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Precision",
        "100%"
    )
with c2:

    st.metric(
        "Recall",
        "63.0%"
    )
with c3:

    st.metric(
        "F1 Score",
        "77.3%"
    )
with c4:

    st.metric(
        "Combined F1",
        "86.0%"
    )
st.caption(
    "Model performance metrics are based on the AEGIS test dataset; "
    "operational alert metrics above represent monitored access events."
)


# ============================================================
# SYSTEM FOOTER
# ============================================================

st.markdown("---")


st.caption(
    "AEGIS | ML Detection → Behavioral Analysis → RAG Compliance → "
    "Agentic Security Analysis"
)