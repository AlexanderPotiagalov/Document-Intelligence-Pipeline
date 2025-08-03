import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Folder with .txt files
pdf_text_folder = "output/pdf_texts"
results = []

# Prompt template
def build_prompt(text):
    return f"""
You are a highly skilled assistant trained to analyze government policy documents.

Your task is to extract key structured information from the following document text. Please return the result as a valid JSON object with the following fields:

- "title": The title or main subject of the document
- "summary": A concise paragraph summarizing the document (2–4 sentences)
- "location": The province, city, or geographic region relevant to the document
- "date": A specific or approximate date (month/year or range) the policy relates to
- "keywords": A list of 3–7 key topics, concepts, or issues from the document
- "species": A list of specific marine animals or fish mentioned in the document (e.g., 'sockeye salmon', 'geoducks')
- "impact": A brief description of the expected or observed impact of the policy

Be factual and concise. Do not invent information. If something is not mentioned, return null or an empty string.

Document text:
{text[:3000]}
"""


# Process each .txt file
for filename in os.listdir(pdf_text_folder):
    if filename.endswith(".txt"):
        path = os.path.join(pdf_text_folder, filename)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        prompt = build_prompt(text)
        print(f"Sending: {filename} to OpenAI...")

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            response_text = response.choices[0].message.content
            parsed = json.loads(response_text)

            parsed["filename"] = filename
            parsed["processed_at"] = datetime.now().isoformat()
            results.append(parsed)
            print(f"Success: {filename}")

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")

# Save results
output_path = "output/gpt_summary.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"All files processed and saved to {output_path}")
