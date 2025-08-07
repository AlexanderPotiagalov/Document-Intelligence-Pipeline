from pathlib import Path
import os
import sys
import json
import tempfile
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import openai

# Ensure helper modules are discoverable
sys.path.append(os.path.dirname(__file__))

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output"

from extract_pdf_text import extract_text_from_pdf_filelike
from analyze_texts_with_gpt import summarize_texts_from_folder, save_summaries
from cross_reference import generate_cross_references, save_cross_references

# === Configuration ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai

# === Streamlit Application Setup ===
st.set_page_config(
    page_title="OceanIntel Dashboard",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# === Custom Header & Insight Styling ===
st.markdown(
    """
    <style>
    .header-container {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 2rem 1rem; border-radius: 10px; margin-bottom: 2rem;
        color: white; text-align: center;
    }
    .header-container h1 { margin:0; font-size:2.5rem; font-weight:600; }
    .header-container p  { margin:0.5rem 0 0; font-size:1.2rem; opacity:0.9; }

    .insights-section {
        background: #f0f4f8;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    .insight-card {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        border-left: 6px solid #0284c7;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .insight-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 18px rgba(0,0,0,0.15);
    }
    .insight-card h4 { color: #034a6f; margin-bottom:0.5rem; }
    .insight-card p  { color: #1e3a8a; margin:0.5rem 0; }
    .insight-detail {
        background: white;
        border-radius: 6px;
        padding: 1rem;
        font-style: italic;
        color: #334155;
        margin-top: 1rem;
    }
    </style>

    <div class="header-container">
      <h1>🐟 OceanIntel Dashboard BC</h1>
      <p>AI-powered analysis of fisheries data and policy documents for actionable insights</p>
    </div>
    """,
    unsafe_allow_html=True
)

# === Load External CSS ===
st.markdown('<link rel="stylesheet" href="styles.css">', unsafe_allow_html=True)

# === Utilities ===
def load_data(path=None):
    try:
        return pd.read_csv(path) if path else pd.read_csv("data/cleaned_fisheries_data.csv")
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

@st.cache_data
def categorize_species(df, mapping):
    df_copy = df.copy()
    df_copy["Category"] = df_copy["Species"].apply(
        lambda s: next((cat for cat, items in mapping.items() if s in items), "Uncategorized")
    )
    return df_copy

# === Sidebar ===
st.sidebar.header("Dashboard Controls")
enable_insights = st.sidebar.checkbox("Enable AI Document Insights", True)
enable_interactive = st.sidebar.checkbox("Enable Interactive Charts", True)
min_harvest = st.sidebar.slider("Min Harvest (k tons)", 0, 200, 0)
min_value = st.sidebar.slider("Min Value ($M)", 0, 1000, 0)

# === Upload ===
st.markdown('<div class="upload-section">', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    policy_pdf = st.file_uploader("Upload a Policy PDF for AI Analysis", type="pdf")
with col2:
    custom_csv = st.file_uploader("Upload Custom Fisheries CSV", type="csv")
st.markdown('</div>', unsafe_allow_html=True)

# === Load & Filter ===
df = load_data(custom_csv)
if not df.empty:
    df = df[(df["Harvest ('000 t)"] >= min_harvest) & (df["Landed Value ($ million)"] >= min_value)]

# === Metrics ===
if not df.empty:
    metrics = {
        "Total Harvest": (df["Harvest ('000 t)"].sum(), "k tons"),
        "Landed Value": (df["Landed Value ($ million)"].sum(), "M USD"),
        "Wholesale Value": (df["Wholesale Value ($ million)"].sum(), "M USD"),
        "Species Count": (df["Species"].nunique(), "species")
    }
    cols = st.columns(len(metrics))
    for col, (label, (value, unit)) in zip(cols, metrics.items()):
        col.markdown(f"""
        <div class="metric-card">
            <h3>{label}</h3>
            <h2>{value:,.1f} {unit}</h2>
        </div>
        """, unsafe_allow_html=True)

# === AI Insights ===
if enable_insights and (policy_pdf or os.path.exists("output/gpt_summary.json")):
    st.header("AI Document Insights")
    # Wrap in colored section
    if policy_pdf:
        with st.spinner("Analyzing document..."):
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    extract_path = extract_text_from_pdf_filelike(policy_pdf, tmp)
                    summaries = summarize_texts_from_folder(tmp, client)
                    save_summaries(summaries, "output/gpt_summary.json")
                    insights_data = summaries
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                insights_data = []
    else:
        try:
            insights_data = json.load(open("output/gpt_summary.json", encoding="utf-8"))
        except:
            insights_data = []

    # Display cards
    if insights_data:
        try:
            refs = generate_cross_references(insights_data, df, client)
            save_cross_references(refs, "output/cross_reference_results.json")
            for i, item in enumerate(refs, 1):
                st.markdown(f"""
                <div class="insight-card">
                    <h4>Insight {i}: {item.get('title')}</h4>
                    <p><strong>Matched Species:</strong> {', '.join(item.get('matched_species', []))}</p>
                    <p><strong>Impact Statement:</strong> {item.get('impact')}</p>
                    <div class="insight-detail">{item.get('gpt_insight')}</div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Cross-reference failed: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# === Visualizations ===
mapping = {
    "Salmon": ["Chinook Salmon","Chum Salmon","Coho Salmon","Sockeye Salmon","Pink Salmon"],
    "Groundfish": ["Hake","Halibut","Cod","Pollock"],
    "Shellfish": ["Crabs","Oysters","Clams","Mussels"],
    "Invertebrates": ["Sea Urchins","Sea Cucumbers"]
}
if not df.empty:
    df = categorize_species(df, mapping)
    tabs = st.tabs(["Harvest Analysis","Value Analysis","Category Overview","Data Explorer","Harvest Chart","Value Chart",])
    with tabs[0]:
        top15 = df.nlargest(15, "Harvest ('000 t)")
        if enable_interactive:
            fig = px.bar(top15, x="Species", y="Harvest ('000 t)", color="Harvest ('000 t)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(10,4))
            ax.bar(top15["Species"], top15["Harvest ('000 t)"])
            ax.set_xticklabels(top15["Species"], rotation=45, ha='right')
            st.pyplot(fig)
    with tabs[1]:
        fig = px.scatter(df, x="Landed Value ($ million)", y="Wholesale Value ($ million)", size="Harvest ('000 t)", color="Category")
        st.plotly_chart(fig, use_container_width=True)
    with tabs[2]:
        summary = df.groupby("Category").sum(numeric_only=True).reset_index()
        fig = px.pie(summary, values="Harvest ('000 t)", names="Category")
        st.plotly_chart(fig, use_container_width=True)
    with tabs[3]:
        st.dataframe(df)
        st.download_button("Download CSV", df.to_csv(index=False),
                           "data.csv", "text/csv")
    with tabs[4]:
            st.header("Harvest Chart")
            img1 = OUTPUT_DIR / "harvest_by_species.png"
            st.image(str(img1), caption="Harvest by Species", use_container_width=True)
    with tabs[5]:
        st.header("Value Chart")
        img2 = OUTPUT_DIR / "value_by_species.png"
        st.image(str(img2), caption="Value by Species", use_container_width=True)


# === Footer ===
st.markdown("---")
st.markdown(f"<div style='text-align:center;color:#64748b;'>Last updated: {datetime.now():%Y-%m-%d %H:%M}</div>", unsafe_allow_html=True)
