import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import tempfile
import os

from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from extract_pdf_text import extract_text_from_pdf_filelike
from analyze_texts_with_gpt import summarize_texts_from_folder, save_summaries
from cross_reference import generate_cross_references, save_cross_references

# === Configuration ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
st.set_page_config(layout="wide")
st.title("🐟 OceanIntel - Fisheries Insight Dashboard")
st.markdown("Analyze PDF policy documents and cross-reference them with fisheries data to extract AI-powered insights and trends.")

# === Upload Section ===
st.header("📤 Upload Your Files")
uploaded_pdf = st.file_uploader("1️⃣ Upload a Policy PDF", type=["pdf"])
uploaded_csv = st.file_uploader("2️⃣ Or Upload Custom Fisheries CSV Data", type=["csv"])

# === Load Fisheries Data ===
if uploaded_csv:
    fisheries_df = pd.read_csv(uploaded_csv)
else:
    fisheries_df = pd.read_csv("data/cleaned_fisheries_data.csv")

# === Analyze PDF and Extract Insights ===
st.divider()
st.header("🧠 GPT-Powered Document Insights")

if uploaded_pdf:
    with tempfile.TemporaryDirectory() as tmp_dir:
        txt_path = extract_text_from_pdf_filelike(uploaded_pdf, tmp_dir)
        summaries = summarize_texts_from_folder(tmp_dir, client)
        save_summaries(summaries, "output/gpt_summary.json")
        gpt_data = summaries
        st.success("✅ Text extracted and summarized using GPT.")
else:
    with open("output/gpt_summary.json", "r", encoding="utf-8") as f:
        gpt_data = json.load(f)

# === Cross-Reference PDF Insights with Fisheries Data ===
cross_ref_results = generate_cross_references(gpt_data, fisheries_df, client)
save_cross_references(cross_ref_results, "output/cross_reference_results.json")

# === Display GPT-Generated Insights ===
for item in cross_ref_results:
    st.markdown(f"### 📄 {item['title']}")
    st.markdown(f"**Matched Species Mentioned:** {', '.join(item['matched_species'])}")
    st.markdown(f"**Impact Statement:** {item.get('impact', '')}")
    st.markdown("**Insight:**")
    st.info(item["gpt_insight"])

# === Fisheries Data Preview ===
st.divider()
st.header("📁 Fisheries Data Preview")
st.markdown("The following table displays the dataset used for analysis. You can optionally upload your own CSV.")
st.dataframe(fisheries_df)

# === Visualizations Section ===
st.divider()
st.header("📊 Fisheries Visual Analytics")

# === Categorize Species ===
category_mapping = {
    "Salmon": ["Chinook Salmon", "Chum Salmon", "Coho Salmon", "Sockeye Salmon", "Pink Salmon", "Pacific Salmon", "Atlantic Salmon"],
    "Groundfish": ["Hake", "Halibut", "Rockfish", "Sablefish", "Pacific Cod", "Pollock", "Arrowtooth Flounders", "Lingcod", "Soles", "Skates", "Tuna", "Other Groundfish"],
    "Shellfish": ["Crabs", "Prawns", "Clams (Excl. Geoduck)", "Geoducks", "Scallops & Other Invertebrates", "Oysters", "Mussels", "Shrimp", "Geoducks & Other Clams"],
    "Invertebrates": ["Sea Cucumbers", "Sea Urchins Green", "Sea Urchins Red", "Other Invertebrates"],
    "Other": ["Other", "Other "]
}

def get_category(species):
    for category, species_list in category_mapping.items():
        if species.strip() in species_list:
            return category
    return "Uncategorized"

fisheries_df["Category"] = fisheries_df["Species"].apply(get_category)

category_summary = fisheries_df.groupby("Category").agg({
    "Harvest ('000 t)": "sum",
    "Landed Value ($ million)": "sum",
    "Wholesale Value ($ million)": "sum"
}).reset_index()

# === Chart 1: Harvest by Species ===
st.subheader("🌊 Total Harvest by Species")
df_sorted = fisheries_df.sort_values("Harvest ('000 t)", ascending=False)
fig1, ax1 = plt.subplots(figsize=(14, 6))
ax1.bar(df_sorted["Species"], df_sorted["Harvest ('000 t)"])
ax1.set_xlabel("Species")
ax1.set_ylabel("Harvest ('000 t)")
ax1.set_title("Harvest Volume per Species (2021–2023)")
plt.xticks(rotation=90)
st.pyplot(fig1)

# === Chart 2: Landed vs. Wholesale Value ===
st.subheader("💰 Landed vs. Wholesale Value by Species")
x = np.arange(len(df_sorted["Species"]))
width = 0.4
fig2, ax2 = plt.subplots(figsize=(14, 6))
ax2.bar(x - width/2, df_sorted["Landed Value ($ million)"], width, label="Landed Value")
ax2.bar(x + width/2, df_sorted["Wholesale Value ($ million)"], width, label="Wholesale Value")
ax2.set_xticks(x)
ax2.set_xticklabels(df_sorted["Species"], rotation=90)
ax2.set_ylabel("Value ($ million)")
ax2.set_title("Landed vs. Wholesale Value by Species")
ax2.legend()
st.pyplot(fig2)

# === Chart 3: Category Comparison ===
st.subheader("📦 Harvest and Value by Category")
x = np.arange(len(category_summary["Category"]))
width = 0.3
fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.bar(x - width, category_summary["Harvest ('000 t)"], width, label="Harvest ('000 t)")
ax3.bar(x, category_summary["Landed Value ($ million)"], width, label="Landed Value ($M)")
ax3.bar(x + width, category_summary["Wholesale Value ($ million)"], width, label="Wholesale Value ($M)")
ax3.set_xticks(x)
ax3.set_xticklabels(category_summary["Category"])
ax3.set_ylabel("Amount")
ax3.set_title("Total Harvest and Value by Category")
ax3.legend()
plt.tight_layout()
st.pyplot(fig3)

# === Table: Category Summary ===
st.subheader("📂 Category Summary Table")
st.dataframe(category_summary.style.format({
    "Harvest ('000 t)": "{:.2f}",
    "Landed Value ($ million)": "${:.2f}M",
    "Wholesale Value ($ million)": "${:.2f}M"
}))
