#!/usr/bin/env python3
"""
PDF Documentation Generator for Face Detection System
Converts the markdown documentation to a professional PDF format
"""

import os
import sys
import markdown
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import re

class PDFDocumentationGenerator:
    def __init__(self, markdown_file, output_file):
        self.markdown_file = markdown_file
        self.output_file = output_file
        self.doc = SimpleDocTemplate(output_file, pagesize=A4,
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)
        self.styles = getSampleStyleSheet()
        self.story = []
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Create custom styles for the PDF"""
        # Title style
        if 'CustomTitle' not in self.styles:
            self.styles.add(ParagraphStyle(name='CustomTitle',
                                         parent=self.styles['Title'],
                                         fontSize=24,
                                         spaceAfter=30,
                                         textColor=colors.darkblue,
                                         alignment=TA_CENTER))
        
        # Subtitle style
        if 'Subtitle' not in self.styles:
            self.styles.add(ParagraphStyle(name='Subtitle',
                                         parent=self.styles['Heading1'],
                                         fontSize=16,
                                         spaceAfter=20,
                                         textColor=colors.darkblue,
                                         alignment=TA_CENTER))
        
        # Section header style
        if 'SectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(name='SectionHeader',
                                         parent=self.styles['Heading1'],
                                         fontSize=18,
                                         spaceBefore=20,
                                         spaceAfter=15,
                                         textColor=colors.darkblue,
                                         leftIndent=0))
        
        # Subsection header style
        if 'SubsectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(name='SubsectionHeader',
                                         parent=self.styles['Heading2'],
                                         fontSize=14,
                                         spaceBefore=15,
                                         spaceAfter=10,
                                         textColor=colors.blue,
                                         leftIndent=20))
        
        # Code style
        if 'CustomCode' not in self.styles:
            self.styles.add(ParagraphStyle(name='CustomCode',
                                         parent=self.styles['Normal'],
                                         fontName='Courier',
                                         fontSize=10,
                                         leftIndent=20,
                                         backgroundColor=colors.lightgrey,
                                         borderColor=colors.grey,
                                         borderWidth=1))
        
        # Table style
        if 'TableHeader' not in self.styles:
            self.styles.add(ParagraphStyle(name='TableHeader',
                                         parent=self.styles['Normal'],
                                         fontSize=12,
                                         textColor=colors.white,
                                         alignment=TA_CENTER))

    def create_cover_page(self):
        """Create the cover page"""
        # Main title
        title = Paragraph("📋 Face Detection & Recognition System", self.styles['CustomTitle'])
        self.story.append(title)
        self.story.append(Spacer(1, 50))
        
        # Subtitle
        subtitle = Paragraph("Complete Project Documentation", self.styles['Subtitle'])
        self.story.append(subtitle)
        self.story.append(Spacer(1, 30))
        
        # Version info
        version_info = [
            "Version: 2.0 Enhanced",
            f"Generated: {datetime.now().strftime('%B %d, %Y')}",
            "Project Type: Django Web Application with Computer Vision",
            "Technologies: Python, Django, OpenCV, face_recognition"
        ]
        
        for info in version_info:
            p = Paragraph(info, self.styles['Normal'])
            p.alignment = TA_CENTER
            self.story.append(p)
            self.story.append(Spacer(1, 12))
        
        self.story.append(Spacer(1, 100))
        
        # Description
        description = """
        This comprehensive documentation covers all aspects of the Face Detection & Recognition System,
        including installation, configuration, usage, troubleshooting, and development guidelines.
        The system combines real-time computer vision with web-based administration for complete
        security and monitoring solutions.
        """
        desc_para = Paragraph(description, self.styles['Normal'])
        desc_para.alignment = TA_JUSTIFY
        self.story.append(desc_para)
        
        self.story.append(PageBreak())

    def parse_markdown_content(self):
        """Parse the markdown content and convert to PDF elements"""
        with open(self.markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        current_section = ""
        in_code_block = False
        code_content = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines in some contexts
            if not line and not in_code_block:
                self.story.append(Spacer(1, 6))
                continue
            
            # Handle code blocks
            if line.startswith('```'):
                if in_code_block:
                    # End of code block
                    if code_content:
                        code_text = '\n'.join(code_content)
                        code_para = Paragraph(f"<pre>{code_text}</pre>", self.styles['CustomCode'])
                        self.story.append(code_para)
                        self.story.append(Spacer(1, 12))
                    code_content = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
                continue
            
            if in_code_block:
                code_content.append(line)
                continue
            
            # Handle headers
            if line.startswith('# '):
                # Main title (skip, already handled in cover)
                if '📋' in line:
                    continue
                header_text = line[2:].strip()
                self.story.append(Paragraph(header_text, self.styles['SectionHeader']))
                self.story.append(Spacer(1, 12))
                current_section = header_text
            
            elif line.startswith('## '):
                header_text = line[3:].strip()
                self.story.append(Paragraph(header_text, self.styles['SectionHeader']))
                self.story.append(Spacer(1, 12))
            
            elif line.startswith('### '):
                header_text = line[4:].strip()
                self.story.append(Paragraph(header_text, self.styles['SubsectionHeader']))
                self.story.append(Spacer(1, 8))
            
            elif line.startswith('#### '):
                header_text = line[5:].strip()
                style = ParagraphStyle(name='H4', parent=self.styles['Heading3'],
                                     fontSize=12, spaceBefore=10, spaceAfter=6,
                                     textColor=colors.darkgreen, leftIndent=30)
                self.story.append(Paragraph(header_text, style))
                self.story.append(Spacer(1, 6))
            
            elif line.startswith('##### '):
                header_text = line[6:].strip()
                style = ParagraphStyle(name='H5', parent=self.styles['Heading3'],
                                     fontSize=11, spaceBefore=8, spaceAfter=4,
                                     textColor=colors.green, leftIndent=40)
                self.story.append(Paragraph(header_text, style))
                self.story.append(Spacer(1, 4))
            
            # Handle bullet points
            elif line.startswith('- ') or line.startswith('* '):
                bullet_text = line[2:].strip()
                bullet_para = Paragraph(f"• {bullet_text}", self.styles['Normal'])
                bullet_para.leftIndent = 30
                self.story.append(bullet_para)
                self.story.append(Spacer(1, 4))
            
            # Handle numbered lists
            elif re.match(r'^\d+\. ', line):
                list_text = re.sub(r'^\d+\. ', '', line)
                list_para = Paragraph(list_text, self.styles['Normal'])
                list_para.leftIndent = 30
                self.story.append(list_para)
                self.story.append(Spacer(1, 4))
            
            # Handle tables (basic support)
            elif '|' in line and line.count('|') >= 2:
                # Simple table handling
                self.handle_table_line(line)
            
            # Handle horizontal rules
            elif line.startswith('---'):
                self.story.append(Spacer(1, 20))
                # Add a horizontal line
                from reportlab.platypus import HRFlowable
                hr = HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.grey)
                self.story.append(hr)
                self.story.append(Spacer(1, 20))
            
            # Handle regular paragraphs
            elif line:
                # Clean up markdown formatting
                clean_line = self.clean_markdown_formatting(line)
                if clean_line.strip():
                    para = Paragraph(clean_line, self.styles['Normal'])
                    self.story.append(para)
                    self.story.append(Spacer(1, 6))

    def clean_markdown_formatting(self, text):
        """Clean markdown formatting for PDF"""
        # Replace markdown bold with HTML bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
        
        # Replace markdown italic with HTML italic
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
        
        # Replace markdown code with HTML code
        text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
        
        # Remove markdown links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Clean up any remaining markdown
        text = text.replace('**', '').replace('__', '')
        
        return text

    def handle_table_line(self, line):
        """Basic table line handling"""
        # This is a simplified table handler
        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
        if cells:
            table_text = " | ".join(cells)
            table_para = Paragraph(table_text, self.styles['Normal'])
            table_para.leftIndent = 20
            self.story.append(table_para)
            self.story.append(Spacer(1, 4))

    def create_table_of_contents(self):
        """Create a table of contents"""
        toc_title = Paragraph("📑 Table of Contents", self.styles['SectionHeader'])
        self.story.append(toc_title)
        self.story.append(Spacer(1, 20))
        
        toc_items = [
            "1. Project Overview",
            "2. System Architecture", 
            "3. Features & Capabilities",
            "4. File Structure & Descriptions",
            "5. Technical Specifications",
            "6. Installation & Setup",
            "7. User Guide",
            "8. API Documentation",
            "9. Database Schema",
            "10. Configuration Settings",
            "11. Troubleshooting Guide",
            "12. Development & Maintenance"
        ]
        
        for item in toc_items:
            toc_para = Paragraph(item, self.styles['Normal'])
            toc_para.leftIndent = 20
            self.story.append(toc_para)
            self.story.append(Spacer(1, 8))
        
        self.story.append(PageBreak())

    def generate_pdf(self):
        """Generate the complete PDF"""
        print("🔄 Generating PDF documentation...")
        
        # Create cover page
        self.create_cover_page()
        
        # Create table of contents
        self.create_table_of_contents()
        
        # Parse and add main content
        self.parse_markdown_content()
        
        # Add footer information
        footer_info = [
            "",
            "---",
            "",
            "📄 End of Documentation",
            "",
            "This document contains complete information about the Face Detection & Recognition System.",
            "For updates and additional information, please refer to the project repository.",
            "",
            f"Document generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            "Total pages: Approximately 50+ pages when printed",
            "",
            "© 2025 Face Detection System Development Team"
        ]
        
        for info in footer_info:
            if info == "---":
                self.story.append(Spacer(1, 20))
                from reportlab.platypus import HRFlowable
                hr = HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.grey)
                self.story.append(hr)
                self.story.append(Spacer(1, 20))
            elif info:
                para = Paragraph(info, self.styles['Normal'])
                para.alignment = TA_CENTER
                self.story.append(para)
                self.story.append(Spacer(1, 6))
            else:
                self.story.append(Spacer(1, 12))
        
        # Build the PDF
        self.doc.build(self.story)
        print(f"✅ PDF documentation generated successfully: {self.output_file}")

def main():
    """Main function to generate PDF documentation"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    markdown_file = os.path.join(current_dir, "PROJECT_DOCUMENTATION.md")
    output_file = os.path.join(current_dir, "Face_Detection_System_Complete_Documentation.pdf")
    
    if not os.path.exists(markdown_file):
        print(f"❌ Error: Markdown file not found: {markdown_file}")
        return False
    
    try:
        generator = PDFDocumentationGenerator(markdown_file, output_file)
        generator.generate_pdf()
        
        print(f"\n📋 Documentation Summary:")
        print(f"   📁 Source: {os.path.basename(markdown_file)}")
        print(f"   📄 Output: {os.path.basename(output_file)}")
        print(f"   📊 Size: {os.path.getsize(output_file) / 1024:.1f} KB")
        print(f"   📅 Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating PDF: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
