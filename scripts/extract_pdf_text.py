import os
import fitz  # PyMuPDF


def extract_text_from_pdf_filelike(pdf_file, output_dir="output/pdf_texts"):
    os.makedirs(output_dir, exist_ok=True)
    filename = pdf_file.name
    text_path = os.path.join(output_dir, filename.replace(".pdf", ".txt"))

    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        full_text = "".join(page.get_text() for page in doc)

    with open(text_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    return text_path, full_text


def extract_texts_from_folder(input_dir="data/pdfs", output_dir="output/pdf_texts"):
    os.makedirs(output_dir, exist_ok=True)
    extracted = []
    for filename in os.listdir(input_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            text_path = os.path.join(output_dir, filename.replace(".pdf", ".txt"))

            with fitz.open(pdf_path) as doc:
                full_text = "".join(page.get_text() for page in doc)

            with open(text_path, "w", encoding="utf-8") as f:
                f.write(full_text)

            extracted.append((filename, text_path, full_text))
    return extracted