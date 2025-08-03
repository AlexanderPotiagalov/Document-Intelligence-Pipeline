import os
import json
import pandas as pd
import re
from dotenv import load_dotenv
from datetime import datetime
from openai import OpenAI

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load fisheries data
fisheries_df = pd.read_csv("data/cleaned_fisheries_data.csv")
csv_species = fisheries_df["Species"].tolist()
csv_species_lower = [s.lower() for s in csv_species]

# Load GPT summaries
with open("output/gpt_summary.json", "r", encoding="utf-8") as f:
    gpt_data = json.load(f)

cross_ref_results = []

def expand_species_with_gpt(gpt_species):
    try:
        prompt = f"""
        Given the term '{gpt_species}', list all specific fish or marine species it could refer to in a Canadian fisheries context.
        Include both common types and economically relevant subtypes as used in government reports.
        Output as a JSON array with species names only.
        """
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"GPT expansion error for '{gpt_species}': {e}")
        return []

def match_species(extracted_species):
    matched = set()
    for gpt_species in extracted_species:
        possible_species = [gpt_species]
        if any(keyword in gpt_species.lower() for keyword in ["salmon", "groundfish", "wild", "shellfish"]):
            possible_species.extend(expand_species_with_gpt(gpt_species))

        for spec in possible_species:
            spec_words = set(re.findall(r'\w+', spec.lower()))
            for csv_sp, csv_sp_lower in zip(csv_species, csv_species_lower):
                csv_words = set(re.findall(r'\w+', csv_sp_lower))
                if spec_words & csv_words:
                    matched.add(csv_sp)

    return sorted(matched)

def build_insight_prompt(title, summary, species, impact, matched_species, data_rows):
    harvest_col = "Harvest ('000 t)"
    landed_col = "Landed Value ($ million)"

    table_preview = "\n".join([
        f"- {row['Species']}: Harvest={row[harvest_col]}kT, Landed=${row[landed_col]}M"
        for row in data_rows
    ])

    prompt = f"""
You are a government policy analyst AI. Your task is to analyze the relationship between the following policy document and real-world fisheries data.

### Document Information:
Title: {title}
Summary: {summary}
Mentioned Species: {', '.join(species)}
Impact: {impact}

### Matched Species in Fisheries Data:
{', '.join(matched_species)}

### Related Data:
{table_preview}

Explain what insights this document may be drawing from the data, and what effect the policy could have, using the information above.
Use professional policy analysis terms (e.g., ecological yield, economic contribution, sustainability index, biodiversity impact).
Include rough estimations or context where helpful (e.g., "Sockeye Salmon contributed over $485M in landed value").
Write in a concise, analytical, and insightful tone.
"""
    return prompt

# Process each summary
for item in gpt_data:
    extracted_species = item.get("species", [])
    matched_species = match_species(extracted_species)

    data_rows = fisheries_df[fisheries_df["Species"].isin(matched_species)].to_dict("records")

    prompt = build_insight_prompt(
        item["title"],
        item["summary"],
        extracted_species,
        item.get("impact", ""),
        matched_species,
        data_rows
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        insight = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"GPT insight error: {e}")
        insight = "Unable to generate insight due to an error."

    cross_ref_results.append({
        "filename": item["filename"],
        "title": item["title"],
        "matched_species": matched_species,
        "impact": item.get("impact", ""),
        "gpt_insight": insight,
        "processed_at": datetime.now().isoformat()
    })

# Save results
output_path = "output/cross_reference_results.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(cross_ref_results, f, indent=2, ensure_ascii=False)

print(f"Cross-referencing complete! Results saved to {output_path}")
