import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# load cleaned data
df = pd.read_csv("data/cleaned_fisheries_data.csv")

# sort data by harvest in descending order
df_sorted = df.sort_values("Harvest ('000 t)", ascending=False)

# plot total harvest by species
plt.figure(figsize=(14, 6))
plt.bar(df_sorted["Species"], df_sorted["Harvest ('000 t)"], color="teal")
plt.title("Total Harvest by Species (2021–2023)")
plt.xlabel("Species")
plt.ylabel("Harvest ('000 t)")
plt.xticks(rotation=90)  # Rotate species labels to prevent overlap
plt.tight_layout()
plt.savefig("output/harvest_by_species.png")  # Save plot to file
plt.show()

# plot landed vs wholesale value by species
plt.figure(figsize=(14, 6))
x = np.arange(len(df_sorted["Species"])) # Numeric x-axis for spacing
width = 0.4 # Width of each bar

plt.bar(x - width/2, df_sorted["Landed Value ($ million)"], width, label="Landed")
plt.bar(x + width/2, df_sorted["Wholesale Value ($ million)"], width, label="Wholesale")

plt.title("Landed vs. Wholesale Value by Species")
plt.xlabel("Species")
plt.ylabel("Value ($ million)")
plt.xticks(x, df_sorted["Species"], rotation=90)
plt.legend()
plt.tight_layout()
plt.savefig("output/value_by_species.png")
plt.show()