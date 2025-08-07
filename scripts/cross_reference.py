import os
import json
import pandas as pd
import re
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def match_species(gpt_species_list, fisheries_df):
    csv_species = fisheries_df["Species"].tolist()
    csv_species_lower = [s.lower() for s in csv_species]

    matched = set()
    for gpt_species in gpt_species_list:
        gpt_species_lower = gpt_species.lower()
        for sp, sp_lower in zip(csv_species, csv_species_lower):
            if gpt_species_lower in sp_lower or sp_lower in gpt_species_lower:
                matched.add(sp)
    return sorted(matched)


def build_insight_prompt(title, summary, species, impact, matched_species, data_rows):
    harvest_col = "Harvest ('000 t)"
    landed_col = "Landed Value ($ million)"
    table_preview = "\n".join([
        f"- {row['Species']}: Harvest={row[harvest_col]}kT, Landed=${row[landed_col]}M"
        for row in data_rows
    ])

    return f"""
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

Explain what insights this document may be drawing from the data, and what effect the policy could have, using the information above. Write in a professional, insightful tone. Be concise but thoughtful.
"""


def generate_cross_references(gpt_data, fisheries_df, client):
    results = []
    for item in gpt_data:
        extracted_species = item.get("species", [])
        matched_species = match_species(extracted_species, fisheries_df)
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
            insight = f"Error: {e}"

        results.append({
            "filename": item["filename"],
            "title": item["title"],
            "matched_species": matched_species,
            "impact": item.get("impact", ""),
            "gpt_insight": insight,
            "processed_at": datetime.now().isoformat()
        })

    return results


def save_cross_references(results, output_path="output/cross_reference_results.json"):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
