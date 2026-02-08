"""
Interactive Streamlit Dashboard for Clinical Trial Analysis
Displays results from Parts 2, 3, and 4.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from database import get_connection, init_and_load, DB_PATH
from analysis import get_frequency_table
from statistical_analysis import get_filtered_frequency, run_statistical_tests
from subset_analysis import (
    get_baseline_samples,
    get_samples_per_project,
    get_response_breakdown,
    get_sex_breakdown,
)

st.set_page_config(page_title="Loblaw Bio Clinical Trial Analysis", layout="wide")


@st.cache_resource
def get_db_connection():
    if not os.path.exists(DB_PATH):
        return init_and_load()
    return get_connection()


@st.cache_data
def load_frequency_table():
    conn = get_db_connection()
    return get_frequency_table(conn)


@st.cache_data
def load_filtered_frequency():
    conn = get_db_connection()
    return get_filtered_frequency(conn)


@st.cache_data
def load_stats(df_json):
    df = pd.read_json(df_json)
    return run_statistical_tests(df)


@st.cache_data
def load_baseline_samples():
    conn = get_db_connection()
    return get_baseline_samples(conn)


@st.cache_data
def load_project_breakdown():
    conn = get_db_connection()
    return get_samples_per_project(conn)


@st.cache_data
def load_response_breakdown():
    conn = get_db_connection()
    return get_response_breakdown(conn)


@st.cache_data
def load_sex_breakdown():
    conn = get_db_connection()
    return get_sex_breakdown(conn)


# ── Header ──────────────────────────────────────────────────────────────────
st.title("Loblaw Bio Clinical Trial Dashboard")
st.markdown("Analysis of immune cell populations across clinical trial samples.")

# ── Part 2: Data Overview ───────────────────────────────────────────────────
st.header("Part 2: Cell Population Frequency Overview")

freq_df = load_frequency_table()

col_filter1, col_filter2 = st.columns(2)
with col_filter1:
    sample_search = st.text_input("Filter by sample ID (contains)", key="sample_search")
with col_filter2:
    pop_filter = st.multiselect(
        "Filter by population",
        options=sorted(freq_df["population"].unique()),
        default=sorted(freq_df["population"].unique()),
    )

filtered_freq = freq_df[freq_df["population"].isin(pop_filter)]
if sample_search:
    filtered_freq = filtered_freq[filtered_freq["sample"].str.contains(sample_search)]

st.dataframe(filtered_freq, use_container_width=True, height=400)
st.caption(f"Showing {len(filtered_freq):,} rows ({filtered_freq['sample'].nunique():,} samples)")

# ── Part 3: Statistical Analysis ───────────────────────────────────────────
st.header("Part 3: Responders vs Non-Responders")
st.markdown("**Melanoma** patients treated with **miraclib** (PBMC samples only)")

stat_df = load_filtered_frequency()
stats_results = load_stats(stat_df.to_json())

# Boxplots with Plotly
fig = px.box(
    stat_df,
    x="population",
    y="percentage",
    color="response",
    color_discrete_map={"yes": "#2ecc71", "no": "#e74c3c"},
    labels={
        "population": "Cell Population",
        "percentage": "Relative Frequency (%)",
        "response": "Responder",
    },
    category_orders={
        "population": sorted(stat_df["population"].unique()),
        "response": ["no", "yes"],
    },
)
fig.update_layout(
    title="Cell Population Frequencies: Responders vs Non-Responders",
    boxmode="group",
    height=500,
)
st.plotly_chart(fig, use_container_width=True)

# Stats table
st.subheader("Mann-Whitney U Test Results")

def highlight_significant(row):
    if row["significant (p<0.05)"] == "Yes":
        return ["background-color: #0f7a0d"] * len(row)
    return [""] * len(row)

st.dataframe(
    stats_results.style.apply(highlight_significant, axis=1),
    use_container_width=True,
    hide_index=True,
)

sig_pops = stats_results[stats_results["significant (p<0.05)"] == "Yes"]["population"].tolist()
if sig_pops:
    st.success(f"Significant difference detected in: **{', '.join(sig_pops)}**")
else:
    st.info("No statistically significant differences found at p < 0.05.")

# ── Part 4: Subset Analysis ────────────────────────────────────────────────
st.header("Part 4: Baseline Subset Analysis")
st.markdown("**Melanoma** PBMC samples at baseline (time = 0), treated with **miraclib**")

baseline_df = load_baseline_samples()
project_df = load_project_breakdown()
response_df = load_response_breakdown()
sex_df = load_sex_breakdown()

# Summary metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Samples", f"{len(baseline_df):,}")
m2.metric("Unique Subjects", f"{baseline_df['subject_id'].nunique():,}")
resp_yes = response_df.loc[response_df["response"] == "yes", "subject_count"].values
m3.metric("Responders", int(resp_yes[0]) if len(resp_yes) else 0)
resp_no = response_df.loc[response_df["response"] == "no", "subject_count"].values
m4.metric("Non-Responders", int(resp_no[0]) if len(resp_no) else 0)

# Charts
chart1, chart2, chart3 = st.columns(3)

with chart1:
    fig_proj = px.bar(
        project_df,
        x="project",
        y="sample_count",
        title="Samples per Project",
        labels={"project": "Project", "sample_count": "Sample Count"},
        color="project",
    )
    fig_proj.update_layout(showlegend=False)
    st.plotly_chart(fig_proj, use_container_width=True)

with chart2:
    fig_resp = px.pie(
        response_df,
        names="response",
        values="subject_count",
        title="Responders vs Non-Responders",
        color="response",
        color_discrete_map={"yes": "#2ecc71", "no": "#e74c3c"},
    )
    st.plotly_chart(fig_resp, use_container_width=True)

with chart3:
    fig_sex = px.pie(
        sex_df,
        names="sex",
        values="subject_count",
        title="Sex Distribution",
        color="sex",
        color_discrete_map={"M": "#3498db", "F": "#e91e63"},
    )
    st.plotly_chart(fig_sex, use_container_width=True)

# Raw data explorer
st.subheader("Baseline Samples Explorer")
st.dataframe(baseline_df, use_container_width=True, height=300)
