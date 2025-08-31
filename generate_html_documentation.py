#!/usr/bin/env python3
"""
HTML Documentation Generator for Face Detection System
Creates an HTML version of the documentation for easy viewing
"""

import os
import markdown
from datetime import datetime

def create_html_documentation():
    """Generate HTML documentation from markdown"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    markdown_file = os.path.join(current_dir, "PROJECT_DOCUMENTATION.md")
    html_file = os.path.join(current_dir, "Face_Detection_System_Documentation.html")
    
    # Read markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert to HTML
    md = markdown.Markdown(extensions=['toc', 'codehilite', 'tables', 'fenced_code'])
    html_body = md.convert(markdown_content)
    
    # Create complete HTML document
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Face Detection System - Complete Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
            margin-top: 30px;
        }}
        h3 {{
            color: #3498db;
            margin-top: 25px;
        }}
        h4 {{
            color: #27ae60;
            margin-top: 20px;
        }}
        h5 {{
            color: #16a085;
            margin-top: 15px;
        }}
        code {{
            background-color: #f1f2f6;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: #e74c3c;
        }}
        pre {{
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 15px 0;
        }}
        pre code {{
            background-color: transparent;
            color: #ecf0f1;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
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
            background-color: #f9f9f9;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 15px 0;
            padding: 10px 20px;
            background-color: #f8f9fa;
        }}
        .toc {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        .toc li {{
            margin: 5px 0;
        }}
        .toc a {{
            text-decoration: none;
            color: #2c3e50;
        }}
        .toc a:hover {{
            color: #3498db;
        }}
        .header-info {{
            background-color: #3498db;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .footer-info {{
            background-color: #34495e;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-top: 30px;
            text-align: center;
        }}
        .emoji {{
            font-size: 1.2em;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 10px;
            border-left: 4px solid #ffc107;
            margin: 15px 0;
        }}
        .success {{
            background-color: #d1f2eb;
            padding: 10px;
            border-left: 4px solid #27ae60;
            margin: 15px 0;
        }}
        .error {{
            background-color: #fadbd8;
            padding: 10px;
            border-left: 4px solid #e74c3c;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-info">
            <h1>📋 Face Detection & Recognition System</h1>
            <p><strong>Complete Project Documentation</strong></p>
            <p>Version 2.0 Enhanced | Generated: {datetime.now().strftime('%B %d, %Y')}</p>
            <p>Django Web Application with Real-time Computer Vision</p>
        </div>
        
        {html_body}
        
        <div class="footer-info">
            <h3>📄 Documentation Complete</h3>
            <p>This HTML documentation provides the same comprehensive information as the PDF version.</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><strong>Files Created:</strong></p>
            <ul style="list-style: none; padding: 0;">
                <li>📄 Face_Detection_System_Complete_Documentation.pdf</li>
                <li>🌐 Face_Detection_System_Documentation.html</li>
                <li>📋 PROJECT_DOCUMENTATION.md</li>
            </ul>
            <p>© 2025 Face Detection System Development Team</p>
        </div>
    </div>
</body>
</html>
    """
    
    # Write HTML file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"✅ HTML documentation created: {html_file}")
    return html_file

if __name__ == "__main__":
    create_html_documentation()
