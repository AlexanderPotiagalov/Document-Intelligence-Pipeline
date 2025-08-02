import os
import fitz  # PyMuPDF

INPUT_DIR = "data/pdfs"
OUTPUT_DIR = "output/pdf_texts"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Loop through all PDF files in the input directory
for filename in os.listdir(INPUT_DIR):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(INPUT_DIR, filename)
        text_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".txt"))

        with fitz.open(pdf_path) as doc:
            full_text = ""
            for page in doc:
                full_text += page.get_text()

        # Save the text output
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        print(f"Extracted text from {filename} → {text_path}")
