import pandas as pd

# load csv
df = pd.read_csv("data/raw_fisheries_data.csv")

# view structure
print(df.head())
print(df.columns)

# clean missing values
df = df.dropna()

# filter by year (2020+)
df = df[df["Year"] >= 2020]

# group by species and sum
species_summary = df.groupby("Species").agg({
    "Harvest ('000 t)": "sum",
    "Landed Value ($ million)": "sum",
    "Wholesale Value ($ million)": "sum"
}).reset_index()

# export cleaned data
species_summary.to_csv("data/cleaned_fisheries_data.csv", index=False)

print("Data cleaned and saved to output/cleaned_summary.csv")