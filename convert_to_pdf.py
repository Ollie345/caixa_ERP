#!/usr/bin/env python3
"""
Convert Markdown UAT document to PDF
"""
import subprocess
import sys
import os

def markdown_to_html(md_file):
    """Convert markdown to HTML using Python markdown library or pandoc"""
    html_file = md_file.replace('.md', '.html')
    
    # Try using pandoc first (best quality)
    try:
        result = subprocess.run(
            ['pandoc', md_file, '-o', html_file, '--standalone', '--css', 'style.css'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return html_file
    except FileNotFoundError:
        pass
    
    # Fallback: Use Python markdown library
    try:
        import markdown
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>UAT Document - Caixa ERP</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        h3 {{
            color: #555;
            margin-top: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding-left: 20px;
            color: #666;
        }}
        .toc {{
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        @media print {{
            body {{
                max-width: 100%;
                padding: 10px;
            }}
            h1, h2 {{
                page-break-after: avoid;
            }}
            table {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
{markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'toc'])}
</body>
</html>"""
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file
    except ImportError:
        print("Error: markdown library not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'markdown', '--quiet'])
        # Retry
        import markdown
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>UAT Document - Caixa ERP</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        h3 {{
            color: #555;
            margin-top: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding-left: 20px;
            color: #666;
        }}
        .toc {{
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        @media print {{
            body {{
                max-width: 100%;
                padding: 10px;
            }}
            h1, h2 {{
                page-break-after: avoid;
            }}
            table {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
{markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'toc'])}
</body>
</html>"""
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file

def html_to_pdf(html_file, pdf_file):
    """Convert HTML to PDF using wkhtmltopdf"""
    cmd = [
        'wkhtmltopdf',
        '--page-size', 'A4',
        '--margin-top', '20mm',
        '--margin-bottom', '20mm',
        '--margin-left', '15mm',
        '--margin-right', '15mm',
        '--encoding', 'UTF-8',
        '--enable-local-file-access',
        '--print-media-type',
        html_file,
        pdf_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error converting to PDF: {result.stderr}")
        return False
    return True

def main():
    md_file = '/home/excitepa/odoo18/odoo/caixa_ERP/UAT_DOCUMENT.md'
    pdf_file = '/home/excitepa/odoo18/odoo/caixa_ERP/UAT_DOCUMENT.pdf'
    
    if not os.path.exists(md_file):
        print(f"Error: {md_file} not found")
        sys.exit(1)
    
    print("Converting markdown to HTML...")
    html_file = markdown_to_html(md_file)
    
    if not html_file or not os.path.exists(html_file):
        print("Error: Failed to create HTML file")
        sys.exit(1)
    
    print("Converting HTML to PDF...")
    if html_to_pdf(html_file, pdf_file):
        print(f"✓ PDF created successfully: {pdf_file}")
        # Clean up HTML file
        os.remove(html_file)
        print(f"✓ Temporary HTML file removed")
    else:
        print("Error: Failed to create PDF")
        sys.exit(1)

if __name__ == '__main__':
    main()
