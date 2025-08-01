import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load cleaned fisheries data
df = pd.read_csv("data/cleaned_fisheries_data.csv")

# Categorize species into broader groups
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

df["Category"] = df["Species"].apply(get_category)

# Grouped summary by category
category_summary = df.groupby("Category").agg({
    "Harvest ('000 t)": "sum",
    "Landed Value ($ million)": "sum",
    "Wholesale Value ($ million)": "sum"
}).reset_index()

# Streamlit dashboard layout
st.title("🐟 BC Fisheries Dashboard")
st.markdown("Visualizing harvests, landed and wholesale values from 2021–2023")

# Show raw cleaned data
st.subheader("📊 Cleaned Fisheries Data")
st.dataframe(df)

# Bar chart: Total Harvest by Species
st.subheader("🌊 Total Harvest by Species")
df_sorted = df.sort_values("Harvest ('000 t)", ascending=False)
fig1, ax1 = plt.subplots(figsize=(14, 6))
ax1.bar(df_sorted["Species"], df_sorted["Harvest ('000 t)"])
ax1.set_xlabel("Species")
ax1.set_ylabel("Harvest ('000 t)")
ax1.set_title("Harvest Volume per Species (2021–2023)")
plt.xticks(rotation=90)
st.pyplot(fig1)

# Grouped bar chart: Landed vs. Wholesale Value per Species
st.subheader("💰 Landed vs. Wholesale Value")
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

# Grouped bar chart by Category
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

# Show category summary table
st.subheader("📂 Category Summary Table")
st.dataframe(category_summary.style.format({
    "Harvest ('000 t)": "{:.2f}",
    "Landed Value ($ million)": "${:.2f}M",
    "Wholesale Value ($ million)": "${:.2f}M"
}))
