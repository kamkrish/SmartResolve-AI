import streamlit as st
from google import genai
import os
import json
import pandas as pd
import time


# ========================================================
# PAGE CONFIGURATION
# ========================================================

st.set_page_config(
    page_title="SmartResolve AI",
    page_icon="🤖",
    layout="wide"
)


# ========================================================
# GEMINI API SETUP
# ========================================================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:

    st.error(
        "Gemini API key not found. "
        "Please set GEMINI_API_KEY in Terminal."
    )

    st.stop()


client = genai.Client(api_key=api_key)


# ========================================================
# AI COMPLAINT ANALYSIS
# ========================================================
def analyze_complaint(complaint):

    prompt = f"""
You are an enterprise customer complaint routing system.

Analyze the customer complaint below.

Return ONLY valid JSON.

Use exactly these fields:

{{
    "category": "",
    "department": "",
    "priority": "",
    "sentiment": "",
    "summary": "",
    "recommended_action": "",
    "sla": ""
}}

Allowed categories:

- Delivery
- Product Quality
- Payment
- Refund
- Technical Support
- Account
- Pricing
- Service
- Fraud
- Other

Priority must be exactly one of:

- Low
- Medium
- High
- Critical

Sentiment must be exactly one of:

- Positive
- Neutral
- Negative

Department must be exactly ONE of:

- Logistics
- Finance
- Technical Support
- Customer Support
- Quality
- Sales
- Risk & Compliance
- Operations

Do not create a new department.

SLA must be a realistic response target such as:

- 4 hours
- 24 hours
- 48 hours
- 72 hours

Analyze the complaint carefully.

Customer complaint:

{complaint}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )

        result = response.text

        # Remove markdown formatting if Gemini adds it
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

        # Convert Gemini response to JSON
        result = json.loads(result)


        # ====================================================
        # FORCE CONSISTENT DEPARTMENT ROUTING
        # ====================================================

        department_mapping = {

            "Delivery": "Logistics",

            "Product Quality": "Quality",

            "Payment": "Finance",

            "Refund": "Finance",

            "Technical Support": "Technical Support",

            "Account": "Customer Support",

            "Pricing": "Sales",

            "Service": "Customer Support",

            "Fraud": "Risk & Compliance",

            "Other": "Customer Support"
        }


        result["department"] = department_mapping.get(
            result["category"],
            "Customer Support"
        )


        return result


    except Exception as e:

        # ====================================================
        # SHOW EXACT GEMINI ERROR
        # ====================================================

        st.error("❌ Gemini API Error")

        st.code(
            f"Error Type:\n{type(e).__name__}\n\n"
            f"Exact Error Message:\n{str(e)}",
            language="text"
        )

        # Show the error in the terminal as well
        print("\n================ GEMINI API ERROR ================\n")
        print("Error Type:", type(e).__name__)
        print("Exact Error:", str(e))
        print("\n====================================================\n")

        # Stop execution so the real error is visible
        st.stop()

# ========================================================
# SINGLE COMPLAINT ANALYSIS WITH RETRY
# ========================================================

def analyze_single_complaint(complaint):

    max_retries = 4

    for attempt in range(max_retries):

        try:

            result = analyze_complaint(complaint)

            return {

                "category": result.get(
                    "category",
                    "Other"
                ),

                "department": result.get(
                    "department",
                    "Customer Support"
                ),

                "priority": result.get(
                    "priority",
                    "Medium"
                ),

                "sentiment": result.get(
                    "sentiment",
                    "Neutral"
                ),

                "sla": result.get(
                    "sla",
                    "48 hours"
                ),

                "summary": result.get(
                    "summary",
                    ""
                ),

                "recommended_action": result.get(
                    "recommended_action",
                    ""
                )
            }


        except Exception as e:

            error_message = str(e)


            # Retry temporary Gemini API problems

            if (
                "503" in error_message
                or "429" in error_message
                or "UNAVAILABLE" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            ):

                if attempt < max_retries - 1:

                    wait_time = 5 * (attempt + 1)

                    time.sleep(wait_time)

                else:

                    return {

                        "category": "API Error",

                        "department": "API Error",

                        "priority": "API Error",

                        "sentiment": "API Error",

                        "sla": "API Error",

                        "summary": (
                            "Gemini API temporarily "
                            "unavailable after retries."
                        ),

                        "recommended_action": (
                            "Retry this complaint later."
                        )
                    }


            else:

                return {

                    "category": "Error",

                    "department": "Error",

                    "priority": "Error",

                    "sentiment": "Error",

                    "sla": "Error",

                    "summary": error_message,

                    "recommended_action": (
                        "Check the application."
                    )
                }


# ========================================================
# HEADER
# ========================================================

st.title("🤖 SmartResolve AI")

st.write(
    "AI-powered customer complaint "
    "classification, routing and ticket management."
)


# ========================================================
# TABS
# ========================================================

single_tab, bulk_tab = st.tabs(
    [
        "📝 Single Complaint",
        "📊 Bulk Complaint Analysis"
    ]
)


# ========================================================
# SINGLE COMPLAINT TAB
# ========================================================

with single_tab:

    st.subheader("Analyze Customer Complaint")

    complaint = st.text_area(
        "Enter customer complaint",
        height=150,
        placeholder=(
            "Example: My order was supposed "
            "to arrive three days ago but "
            "I still haven't received it."
        )
    )


    analyze_button = st.button(
        "🔍 Analyze Complaint",
        type="primary"
    )


    if analyze_button:

        if complaint.strip() == "":

            st.warning(
                "Please enter a customer complaint."
            )

        else:

            with st.spinner(
                "AI is analyzing the complaint..."
            ):

                result = analyze_single_complaint(
                    complaint
                )


            st.success(
                "Complaint analyzed successfully!"
            )


            # ============================================
            # TICKET INFORMATION
            # ============================================

            st.subheader("🎫 Generated Ticket")


            col1, col2, col3 = st.columns(3)


            with col1:

                st.metric(
                    "Category",
                    result["category"]
                )


            with col2:

                st.metric(
                    "Department",
                    result["department"]
                )


            with col3:

                st.metric(
                    "Priority",
                    result["priority"]
                )


            col4, col5 = st.columns(2)


            with col4:

                st.metric(
                    "Sentiment",
                    result["sentiment"]
                )


            with col5:

                st.metric(
                    "SLA",
                    result["sla"]
                )


            st.divider()


            st.subheader("📌 Issue Summary")

            st.write(
                result["summary"]
            )


            st.subheader("💡 Recommended Action")

            st.write(
                result["recommended_action"]
            )


            st.subheader("🎫 Ticket Status")

            st.info(
                "Open"
            )


# ========================================================
# BULK COMPLAINT TAB
# ========================================================

with bulk_tab:

    st.subheader(
        "📊 Bulk Complaint Analysis"
    )


    st.write(
        "Upload a CSV containing customer complaints."
    )


    uploaded_file = st.file_uploader(
        "Upload CSV file",
        type=["csv"]
    )


    if uploaded_file is not None:

        df = pd.read_csv(
            uploaded_file
        )


        # ================================================
        # FIND COMPLAINT COLUMN
        # ================================================

        complaint_column = None


        possible_columns = [

            "complaint",

            "Complaint",

            "complaints",

            "customer_complaint",

            "Customer Complaint",

            "issue",

            "Issue"
        ]


        for column in possible_columns:

            if column in df.columns:

                complaint_column = column

                break


        if complaint_column is None:

            st.error(
                "Could not find a complaint column. "
                "Please use a column named 'complaint'."
            )


        else:

            st.success(
                f"Found complaint column: "
                f"'{complaint_column}'"
            )


            # ============================================
            # SHOW UPLOADED DATA
            # ============================================

            st.subheader(
                "📄 Uploaded Complaints"
            )


            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )


            # ============================================
            # ANALYZE BUTTON
            # ============================================

            analyze_bulk = st.button(
                "🚀 Analyze All Complaints",
                type="primary",
                key="bulk_analysis"
            )


            if analyze_bulk:

                results = []


                progress = st.progress(0)

                status_message = st.empty()


                total = len(df)


                for index, row in df.iterrows():

                    complaint_text = str(
                        row[complaint_column]
                    )


                    status_message.write(
                        f"Analyzing complaint "
                        f"{index + 1} of {total}..."
                    )


                    result = analyze_single_complaint(
                        complaint_text
                    )


                    results.append({

                        "Complaint ID":
                            index + 1,

                        "Complaint":
                            complaint_text,

                        "Category":
                            result["category"],

                        "Department":
                            result["department"],

                        "Priority":
                            result["priority"],

                        "Sentiment":
                            result["sentiment"],

                        "SLA":
                            result["sla"],

                        "Summary":
                            result["summary"],

                        "Recommended Action":
                            result[
                                "recommended_action"
                            ],

                        "Status":
                            "Open"
                    })


                    progress.progress(
                        (index + 1) / total
                    )


                    # Small delay between API calls
                    time.sleep(5)


                status_message.success(
                    "✅ All complaints analyzed!"
                )


                results_df = pd.DataFrame(
                    results
                )


                st.session_state[
                    "results_df"
                ] = results_df


# ========================================================
# TICKET DASHBOARD
# ========================================================

if "results_df" in st.session_state:

    results_df = st.session_state[
        "results_df"
    ]


    # ================================================
    # ENSURE STATUS COLUMN EXISTS
    # ================================================

    if "Status" not in results_df.columns:

        results_df["Status"] = "Open"


        st.session_state[
            "results_df"
        ] = results_df


    st.divider()


    st.header(
        "🎫 SmartResolve Ticket Dashboard"
    )


    # ================================================
    # DASHBOARD METRICS
    # ================================================

    total_complaints = len(
        results_df
    )


    high_priority = len(
        results_df[
            results_df["Priority"].isin(
                [
                    "High",
                    "Critical"
                ]
            )
        ]
    )


    critical = len(
        results_df[
            results_df["Priority"] == "Critical"
        ]
    )


    negative = len(
        results_df[
            results_df["Sentiment"] == "Negative"
        ]
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Total Tickets",
            total_complaints
        )


    with col2:

        st.metric(
            "High / Critical",
            high_priority
        )


    with col3:

        st.metric(
            "Critical",
            critical
        )


    with col4:

        st.metric(
            "Negative Sentiment",
            negative
        )


    # ================================================
    # TICKET STATUS METRICS
    # ================================================

    st.subheader(
        "📌 Ticket Status"
    )


    open_tickets = len(
        results_df[
            results_df["Status"] == "Open"
        ]
    )


    in_progress_tickets = len(
        results_df[
            results_df["Status"] == "In Progress"
        ]
    )


    resolved_tickets = len(
        results_df[
            results_df["Status"] == "Resolved"
        ]
    )


    status_col1, status_col2, status_col3 = st.columns(3)


    with status_col1:

        st.metric(
            "🟡 Open",
            open_tickets
        )


    with status_col2:

        st.metric(
            "🔵 In Progress",
            in_progress_tickets
        )


    with status_col3:

        st.metric(
            "🟢 Resolved",
            resolved_tickets
        )


    st.divider()


    # ================================================
    # CRITICAL ESCALATIONS
    # ================================================

    st.subheader(
        "🚨 Critical Escalations"
    )


    critical_df = results_df[
        results_df["Priority"] == "Critical"
    ].copy()


    if len(critical_df) == 0:

        st.success(
            "✅ No critical complaints "
            "requiring immediate escalation."
        )


    else:

        st.error(
            f"⚠️ {len(critical_df)} critical "
            f"complaint(s) require immediate attention."
        )


        critical_df[
            "Escalation Status"
        ] = "🚨 ESCALATE NOW"


        st.dataframe(

            critical_df[
                [
                    "Complaint ID",
                    "Complaint",
                    "Category",
                    "Department",
                    "SLA",
                    "Status",
                    "Escalation Status"
                ]
            ],

            use_container_width=True,

            hide_index=True
        )


    st.divider()


    # ================================================
    # FILTERS
    # ================================================

    st.subheader(
        "🔎 Filter Tickets"
    )


    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)


    with filter_col1:

        category_filter = st.multiselect(

            "Category",

            sorted(
                results_df[
                    "Category"
                ].dropna().unique()
            )
        )


    with filter_col2:

        priority_filter = st.multiselect(

            "Priority",

            sorted(
                results_df[
                    "Priority"
                ].dropna().unique()
            )
        )


    with filter_col3:

        department_filter = st.multiselect(

            "Department",

            sorted(
                results_df[
                    "Department"
                ].dropna().unique()
            )
        )


    with filter_col4:

        status_filter = st.multiselect(

            "Ticket Status",

            [
                "Open",
                "In Progress",
                "Resolved"
            ]
        )


    # ================================================
    # APPLY FILTERS
    # ================================================

    filtered_df = results_df.copy()


    if category_filter:

        filtered_df = filtered_df[
            filtered_df["Category"].isin(
                category_filter
            )
        ]


    if priority_filter:

        filtered_df = filtered_df[
            filtered_df["Priority"].isin(
                priority_filter
            )
        ]


    if department_filter:

        filtered_df = filtered_df[
            filtered_df["Department"].isin(
                department_filter
            )
        ]


    if status_filter:

        filtered_df = filtered_df[
            filtered_df["Status"].isin(
                status_filter
            )
        ]


    # ================================================
    # TICKET MANAGEMENT TABLE
    # ================================================

    st.subheader(
        "🎫 Ticket Management"
    )


    st.caption(
        "Change the status of each ticket "
        "using the dropdown."
    )


    ticket_columns = [

        "Complaint ID",

        "Complaint",

        "Category",

        "Department",

        "Priority",

        "Sentiment",

        "SLA",

        "Status"
    ]


    ticket_df = filtered_df[
        ticket_columns
    ].copy()


    edited_ticket_df = st.data_editor(

        ticket_df,

        column_config={

            "Status":
                st.column_config.SelectboxColumn(

                    "Ticket Status",

                    options=[
                        "Open",
                        "In Progress",
                        "Resolved"
                    ],

                    required=True
                )
        },


        disabled=[

            "Complaint ID",

            "Complaint",

            "Category",

            "Department",

            "Priority",

            "Sentiment",

            "SLA"
        ],


        use_container_width=True,

        hide_index=True,

        key="ticket_status_editor"
    )


    # ================================================
    # SAVE STATUS CHANGES
    # ================================================

    for _, edited_row in edited_ticket_df.iterrows():

        ticket_id = edited_row[
            "Complaint ID"
        ]


        new_status = edited_row[
            "Status"
        ]


        results_df.loc[
            results_df["Complaint ID"] == ticket_id,
            "Status"
        ] = new_status


    st.session_state[
        "results_df"
    ] = results_df


    # ================================================
    # DOWNLOAD RESULTS
    # ================================================

    st.subheader(
        "⬇️ Export Tickets"
    )


    csv_data = results_df.to_csv(
        index=False
    )


    st.download_button(

        label="📥 Download Ticket Data",

        data=csv_data,

        file_name="smartresolve_tickets.csv",

        mime="text/csv"
    )


    # ================================================
    # CHARTS
    # ================================================

    st.divider()

    st.subheader(
        "📊 Ticket Analytics"
    )


    chart_col1, chart_col2 = st.columns(2)


    with chart_col1:

        st.write(
            "Complaints by Category"
        )


        category_counts = (
            results_df["Category"]
            .value_counts()
        )


        st.bar_chart(
            category_counts
        )


    with chart_col2:

        st.write(
            "Tickets by Priority"
        )


        priority_counts = (
            results_df["Priority"]
            .value_counts()
        )


        st.bar_chart(
            priority_counts
        )


    # ================================================
    # STATUS CHART
    # ================================================

    st.write(
        "Tickets by Status"
    )


    status_counts = (
        results_df["Status"]
        .value_counts()
        .reindex(
            [
                "Open",
                "In Progress",
                "Resolved"
            ],
            fill_value=0
        )
    )


    st.bar_chart(
        status_counts
    )