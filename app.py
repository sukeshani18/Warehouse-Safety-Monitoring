import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
import os

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Warehouse Safety Monitoring",
    page_icon="🏭",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

.main-title {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 5px;
}

.subtitle {
    color: #666;
    font-size: 16px;
    margin-bottom: 25px;
}

.section-title {
    font-size: 22px;
    font-weight: 600;
    margin-top: 30px;
    margin-bottom: 15px;
}

div[data-testid="metric-container"] {
    border: 1px solid #ddd;
    padding: 15px;
    border-radius: 10px;
    background-color: #fafafa;
}

.event-card {
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 18px;
    margin-top: 10px;
    background-color: #fafafa;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    '<div class="main-title">🏭 Warehouse Safety Monitoring Dashboard</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Real-time safety event monitoring using YOLO tracking, restricted-zone detection, '
    'MySQL and Streamlit.'
    '</div>',
    unsafe_allow_html=True
)

# --------------------------------------------------
# PROJECT PATH
# --------------------------------------------------

project_path = r"E:\vs_code\YOLO\Warehouse_Safety_Monitoring"

events_folder = os.path.join(
    project_path,
    "output",
    "events"
)

# --------------------------------------------------
# REFRESH BUTTON
# --------------------------------------------------

refresh_col1, refresh_col2 = st.columns([5, 1])

with refresh_col2:

    if st.button("🔄 Refresh Data"):

        st.rerun()

# --------------------------------------------------
# MYSQL CONNECTION
# --------------------------------------------------

try:

    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1995",
        database="warehouse_safety"
    )

except Exception as e:

    st.error("MySQL connection failed.")
    st.error(e)
    st.stop()

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

query = """
SELECT
    id,
    event_id,
    person_id,
    zone,
    event,
    timestamp,
    frame,
    duration_seconds,
    severity,
    evidence
FROM safety_events
ORDER BY id DESC
"""

df = pd.read_sql(query, connection)

connection.close()

#st.success("MySQL connected successfully.")

# --------------------------------------------------
# FILTERS
# --------------------------------------------------

st.markdown(
    """
    <div style="margin-top: -25px; margin-bottom: 5px;">
        <div class="section-title">🔎 Event Filters</div>
    </div>
    """,
    unsafe_allow_html=True
)

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

# Event filter
event_options = [
    "All",
    "Restricted Zone Entry",
    "Restricted Zone Exit"
]

with filter_col1:

    selected_event = st.selectbox(
        "Event Type",
        event_options
    )

# Severity filter
severity_options = [
    "All",
    "HIGH",
    "MEDIUM",
    "LOW",
    "PENDING"
]

with filter_col2:

    selected_severity = st.selectbox(
        "Severity",
        severity_options
    )

# Person filter
if not df.empty:

    person_options = [
        "All"
    ] + sorted(
        df["person_id"].dropna().unique().tolist()
    )

else:

    person_options = ["All"]

with filter_col3:

    selected_person = st.selectbox(
        "Person ID",
        person_options
    )

# Zone filter
if not df.empty:

    zone_options = [
        "All"
    ] + sorted(
        df["zone"].dropna().unique().tolist()
    )

else:

    zone_options = ["All"]

with filter_col4:

    selected_zone = st.selectbox(
        "Zone",
        zone_options
    )

# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------

filtered_df = df.copy()

if selected_event != "All":

    filtered_df = filtered_df[
        filtered_df["event"] == selected_event
    ]

if selected_severity != "All":

    filtered_df = filtered_df[
        filtered_df["severity"] == selected_severity
    ]

if selected_person != "All":

    filtered_df = filtered_df[
        filtered_df["person_id"] == selected_person
    ]

if selected_zone != "All":

    filtered_df = filtered_df[
        filtered_df["zone"] == selected_zone
    ]

st.caption(
    f"Showing {len(filtered_df)} of {len(df)} total events"
)

# --------------------------------------------------
# KPI SECTION
# --------------------------------------------------

st.markdown(
    '<div class="section-title">📊 Safety Overview</div>',
    unsafe_allow_html=True
)

total_events = len(filtered_df)

entry_count = len(
    filtered_df[
        filtered_df["event"] == "Restricted Zone Entry"
    ]
)

exit_count = len(
    filtered_df[
        filtered_df["event"] == "Restricted Zone Exit"
    ]
)

high_count = len(
    filtered_df[
        filtered_df["severity"] == "HIGH"
    ]
)

medium_count = len(
    filtered_df[
        filtered_df["severity"] == "MEDIUM"
    ]
)

low_count = len(
    filtered_df[
        filtered_df["severity"] == "LOW"
    ]
)

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

with kpi1:
    st.metric(
        "Total Events",
        total_events
    )

with kpi2:
    st.metric(
        "Entries",
        entry_count
    )

with kpi3:
    st.metric(
        "Exits",
        exit_count
    )

with kpi4:
    st.metric(
        "HIGH",
        high_count
    )

with kpi5:
    st.metric(
        "MEDIUM",
        medium_count
    )

with kpi6:
    st.metric(
        "LOW",
        low_count
    )

# --------------------------------------------------
# VISUAL ANALYTICS
# --------------------------------------------------

st.markdown(
    '<div class="section-title">📈 Visual Analytics</div>',
    unsafe_allow_html=True
)

chart_col1, chart_col2 = st.columns(2)

# --------------------------------------------------
# ENTRY VS EXIT
# --------------------------------------------------

with chart_col1:

    event_chart_df = pd.DataFrame({
        "Event Type": [
            "Entry",
            "Exit"
        ],
        "Count": [
            entry_count,
            exit_count
        ]
    })

    fig_event = px.bar(
        event_chart_df,
        x="Event Type",
        y="Count",
        text="Count",
        title="Entry vs Exit Events"
    )

    fig_event.update_traces(
        textposition="outside"
    )

    fig_event.update_layout(
        height=400,
        showlegend=False
    )

    st.plotly_chart(
        fig_event,
        use_container_width=True
    )

# --------------------------------------------------
# SEVERITY DONUT
# --------------------------------------------------

with chart_col2:

    severity_chart_df = pd.DataFrame({
        "Severity": [
            "HIGH",
            "MEDIUM",
            "LOW"
        ],
        "Count": [
            high_count,
            medium_count,
            low_count
        ]
    })

    severity_chart_df = severity_chart_df[
        severity_chart_df["Count"] > 0
    ]

    if not severity_chart_df.empty:

        fig_severity = px.pie(
            severity_chart_df,
            names="Severity",
            values="Count",
            hole=0.55,
            title="Safety Event Severity"
        )

        fig_severity.update_layout(
            height=400
        )

        st.plotly_chart(
            fig_severity,
            use_container_width=True
        )

    else:

        st.info("No severity data available.")

# --------------------------------------------------
# EVENT TIMELINE
# --------------------------------------------------

st.markdown(
    '<div class="section-title">⏱️ Event Timeline</div>',
    unsafe_allow_html=True
)

if not filtered_df.empty:

    timeline_df = filtered_df.copy()

    timeline_df["Time (seconds)"] = (
        pd.to_timedelta(
            timeline_df["timestamp"].astype(str)
        ).dt.total_seconds()
    )

    timeline_df["Event Type"] = timeline_df[
        "event"
    ].replace({
        "Restricted Zone Entry": "Entry",
        "Restricted Zone Exit": "Exit"
    })

    fig_timeline = px.scatter(
        timeline_df,
        x="Time (seconds)",
        y="Event Type",
        color="severity",
        hover_data=[
            "person_id",
            "zone",
            "frame",
            "duration_seconds"
        ],
        title="Safety Events Across Video Timeline"
    )

    fig_timeline.update_layout(
        height=450
    )

    st.plotly_chart(
        fig_timeline,
        use_container_width=True
    )

else:

    st.info("No timeline data available.")

# --------------------------------------------------
# EVENT TABLE
# --------------------------------------------------

st.markdown(
    '<div class="section-title">📋 Safety Event Log</div>',
    unsafe_allow_html=True
)

if not filtered_df.empty:

    display_df = filtered_df[
        [
            "event_id",
            "person_id",
            "zone",
            "event",
            "timestamp",
            "frame",
            "duration_seconds",
            "severity"
        ]
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("No events match the selected filters.")

# --------------------------------------------------
# EVIDENCE VIEWER
# --------------------------------------------------

st.markdown(
    '<div class="section-title">📸 Safety Event Evidence</div>',
    unsafe_allow_html=True
)

if not filtered_df.empty:

    evidence_options = []

    for index, row in filtered_df.iterrows():

        label = (
            f"Event {row['event_id']} | "
            f"Person {row['person_id']} | "
            f"{row['event']} | "
            f"{row['timestamp']}"
        )

        evidence_options.append(
            (label, index)
        )

    selected_evidence = st.selectbox(
        "Select an event to view evidence",
        evidence_options,
        format_func=lambda x: x[0]
    )

    selected_index = selected_evidence[1]

    selected_row = filtered_df.loc[selected_index]

    # --------------------------------------------------
    # EVENT DETAILS
    # --------------------------------------------------

    detail_col1, detail_col2, detail_col3, detail_col4 = st.columns(4)

    with detail_col1:

        st.metric(
            "Event ID",
            selected_row["event_id"]
        )

    with detail_col2:

        st.metric(
            "Person ID",
            selected_row["person_id"]
        )

    with detail_col3:

        st.metric(
            "Severity",
            selected_row["severity"]
        )

    with detail_col4:

        st.metric(
            "Duration",
            f"{selected_row['duration_seconds']} sec"
        )

    st.markdown(
        '<div class="event-card">',
        unsafe_allow_html=True
    )

    st.write(
        "**Zone:**",
        selected_row["zone"]
    )

    st.write(
        "**Event:**",
        selected_row["event"]
    )

    st.write(
        "**Timestamp:**",
        selected_row["timestamp"]
    )

    st.write(
        "**Frame:**",
        selected_row["frame"]
    )

#st.markdown(
   #     '</div>',
   #     unsafe_allow_html=True
   # )

    # --------------------------------------------------
    # EVIDENCE IMAGE
    # --------------------------------------------------

  # --------------------------------------------------
# EVIDENCE IMAGE
# --------------------------------------------------

evidence_filename = selected_row["evidence"]

evidence_path = os.path.join(
    events_folder,
    str(evidence_filename)
)

if os.path.exists(evidence_path):

    st.markdown(
        "<div style='margin-top:15px;'>",
        unsafe_allow_html=True
    )

    st.image(
        evidence_path,
        caption=(
            f"Event {selected_row['event_id']} | "
            f"Person {selected_row['person_id']} | "
            f"{selected_row['event']}"
        ),
        width=800
    )

    st.markdown("</div>", unsafe_allow_html=True)

else:

    st.warning("Evidence image not found:")
    st.code(evidence_path)



# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Warehouse Safety Monitoring System | "
    "YOLO + ByteTrack + MySQL + Streamlit"
)