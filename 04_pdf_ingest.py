# 04_pdf_ingest.py
# PURPOSE: Create a sample movie PDF then parse it
# This covers the PDF parsing requirement of the ingestion layer

import pdfplumber
import pandas as pd
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def create_sample_pdf():
    """
    Creates a PDF file containing movie data.
    This simulates receiving a PDF report from an external source.
    """
    os.makedirs("data/raw", exist_ok=True)
    pdf_path = "data/raw/movie_report.pdf"

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("Movie Analytics Report 2024", styles["Title"]))
    elements.append(Paragraph("Top Grossing Films by Genre", styles["Heading2"]))

    # Table data
    data = [
        ["Title", "Genre", "Year", "Box Office ($M)", "Rating"],
        ["Dune: Part Two", "Science Fiction", "2024", "711", "8.1"],
        ["Inside Out 2", "Animation", "2024", "1698", "7.8"],
        ["Deadpool & Wolverine", "Action", "2024", "1338", "7.7"],
        ["Alien: Romulus", "Horror", "2024", "351", "7.3"],
        ["Twisters", "Action", "2024", "369", "7.2"],
        ["A Quiet Place: Day One", "Horror", "2024", "261", "6.9"],
        ["Kingdom of the Planet of the Apes", "Science Fiction", "2024", "397", "6.8"],
        ["The Substance", "Horror", "2024", "18", "7.4"],
        ["Longlegs", "Thriller", "2024", "73", "6.1"],
        ["Challengers", "Drama", "2024", "53", "7.5"],
        ["The Brutalist", "Drama", "2024", "35", "7.9"],
        ["Conclave", "Thriller", "2024", "42", "7.5"],
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID",       (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    elements.append(Paragraph(" ", styles["Normal"]))
    elements.append(Paragraph("Award Winning Films 2024", styles["Heading2"]))

    data2 = [
        ["Title", "Award", "Director"],
        ["Anora", "Palme d'Or - Cannes", "Sean Baker"],
        ["The Brutalist", "Golden Lion - Venice", "Brady Corbet"],
        ["Emilia Perez", "Best Film - Cannes Jury", "Jacques Audiard"],
        ["A Real Pain", "Best Supporting Actor - Oscar", "Jesse Eisenberg"],
        ["The Substance", "Best Screenplay - Cannes", "Coralie Fargeat"],
    ]

    table2 = Table(data2)
    table2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID",       (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 1), (-1, -1), colors.lightblue),
    ]))

    elements.append(table2)
    doc.build(elements)
    print(f"Created PDF: {pdf_path}")
    return pdf_path

def parse_pdf(pdf_path):
    """
    Opens the PDF and extracts all text and tables from every page.
    """
    print(f"Parsing PDF: {pdf_path}")
    all_text = []
    all_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"  Total pages: {len(pdf.pages)}")

        for i, page in enumerate(pdf.pages):
            # Extract plain text
            text = page.extract_text()
            if text:
                all_text.append({"page": i + 1, "text": text.strip()})

            # Extract tables
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if any(cell for cell in row if cell):
                        all_rows.append({
                            "page": i + 1,
                            "data": " | ".join(str(cell) for cell in row if cell)
                        })

    return all_text, all_rows

def save_pdf_data(all_text, all_rows):
    """Saves extracted PDF content to CSV files."""
    if all_text:
        df_text = pd.DataFrame(all_text)
        path = "data/raw/pdf_text.csv"
        df_text.to_csv(path, index=False)
        print(f"  Saved text:   {path} ({len(df_text)} pages)")

    if all_rows:
        df_rows = pd.DataFrame(all_rows)
        path = "data/raw/pdf_tables.csv"
        df_rows.to_csv(path, index=False)
        print(f"  Saved tables: {path} ({len(df_rows)} rows)")
        return df_rows

def show_preview(all_text):
    print("\n--- PDF content preview ---")
    for item in all_text:
        print(f"\nPage {item['page']}:")
        print(item["text"][:500])
        print("...")

if __name__ == "__main__":
    # Step 1: Create a PDF with movie data
    pdf_path = create_sample_pdf()

    # Step 2: Parse it with pdfplumber
    all_text, all_rows = parse_pdf(pdf_path)

    # Step 3: Save extracted data
    print("\nSaving extracted data...")
    save_pdf_data(all_text, all_rows)

    # Step 4: Preview what we extracted
    show_preview(all_text)

    print("\nPDF parsing complete!")