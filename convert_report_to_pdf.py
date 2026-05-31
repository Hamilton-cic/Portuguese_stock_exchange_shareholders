# -*- coding: utf-8 -*-
"""Convert results/network_report.md to results/network_report.pdf"""

import markdown
from xhtml2pdf import pisa
import io, os

MD_PATH  = "results/network_report.md"
PDF_PATH = "results/network_report.pdf"

with open(MD_PATH, encoding="utf-8") as f:
    md_text = f.read()

# Convert markdown → HTML
md_html = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "toc"],
)

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4;
    margin: 2cm 2cm 2.2cm 2cm;
  }}
  body {{
    font-family: Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    color: #1a1a1a;
    line-height: 1.55;
  }}
  h1 {{
    font-size: 18pt;
    font-weight: bold;
    color: #1a2e5a;
    border-bottom: 2.5px solid #1a2e5a;
    padding-bottom: 6px;
    margin-top: 0;
  }}
  h2 {{
    font-size: 13pt;
    font-weight: bold;
    color: #1a2e5a;
    border-bottom: 1px solid #c8d3e8;
    padding-bottom: 3px;
    margin-top: 18px;
  }}
  h3 {{
    font-size: 11pt;
    font-weight: bold;
    color: #2a4080;
    margin-top: 12px;
    margin-bottom: 4px;
  }}
  h4 {{
    font-size: 10.5pt;
    font-weight: bold;
    color: #2a4080;
    margin-top: 8px;
    margin-bottom: 3px;
  }}
  blockquote {{
    background: #f0f4fb;
    border-left: 4px solid #4472c4;
    margin: 8px 0;
    padding: 6px 12px;
    font-size: 9.5pt;
    color: #444;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 9.5pt;
  }}
  th {{
    background-color: #1a2e5a;
    color: white;
    padding: 6px 8px;
    text-align: left;
    font-weight: bold;
  }}
  td {{
    padding: 5px 8px;
    border-bottom: 1px solid #dde3f0;
  }}
  tr:nth-child(even) td {{
    background-color: #f5f7fc;
  }}
  code {{
    font-family: Courier New, monospace;
    font-size: 9pt;
    background: #f0f0f0;
    padding: 1px 4px;
    border-radius: 3px;
  }}
  pre {{
    background: #f4f4f4;
    border: 1px solid #ddd;
    border-left: 3px solid #4472c4;
    padding: 10px 14px;
    font-family: Courier New, monospace;
    font-size: 9pt;
    overflow: hidden;
    margin: 8px 0;
  }}
  ul, ol {{
    margin: 6px 0;
    padding-left: 20px;
  }}
  li {{
    margin-bottom: 3px;
  }}
  p {{
    margin: 6px 0;
  }}
  hr {{
    border: none;
    border-top: 1px solid #c8d3e8;
    margin: 14px 0;
  }}
  strong {{
    color: #1a2e5a;
  }}
</style>
</head>
<body>
{md_html}
</body>
</html>"""

with open(PDF_PATH, "wb") as pdf_file:
    result = pisa.CreatePDF(
        io.StringIO(html),
        dest=pdf_file,
        encoding="utf-8",
    )

if result.err:
    print(f"ERROR: {result.err}")
else:
    size_kb = os.path.getsize(PDF_PATH) / 1024
    print(f"Saved {PDF_PATH}  ({size_kb:.0f} KB)")
