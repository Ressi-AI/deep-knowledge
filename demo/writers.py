import os
import urllib


def write_md_to_pdf(text: str, filename: str = "") -> str:
    """Converts Markdown text to a PDF file and returns the file path.

    Args:
        text (str): Markdown text to convert.

    Returns:
        str: The encoded file path of the generated PDF.
    """
    os.makedirs("_data/outputs", exist_ok=True)
    file_path = f"_data/outputs/{filename[:60]}.pdf"

    try:
        from md2pdf.core import md2pdf
        md2pdf(file_path,
               md_content=text,
               css_file_path="./demo/pdf_styles.css",
               base_url=None
        )
        print(f"Report written to {file_path}")
    except Exception as e:
        print(f"Error in converting Markdown to PDF: {e}")
        return ""

    encoded_file_path = urllib.parse.quote(file_path)
    return encoded_file_path
