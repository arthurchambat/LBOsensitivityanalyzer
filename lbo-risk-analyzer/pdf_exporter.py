"""
PDF Export System for IC Reports
Converts markdown + charts to professional PDF.
"""
import markdown2
from weasyprint import HTML, CSS
from typing import Dict, Optional
from datetime import datetime
import os
import tempfile


class PDFExporter:
    """
    Exports IC reports to PDF with embedded charts.
    """
    
    # CSS styling for professional look
    PDF_CSS = """
    @page {
        size: A4;
        margin: 2cm 2.5cm;
        
        @top-center {
            content: "Investment Committee Report";
            font-size: 10pt;
            color: #666;
        }
        
        @bottom-right {
            content: "Page " counter(page) " of " counter(pages);
            font-size: 9pt;
            color: #666;
        }
    }
    
    body {
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #2c3e50;
        background: white;
    }
    
    h1 {
        color: #1a1a1a;
        font-size: 24pt;
        font-weight: bold;
        margin-top: 30pt;
        margin-bottom: 15pt;
        border-bottom: 3px solid #00d4ff;
        padding-bottom: 10pt;
        page-break-after: avoid;
    }
    
    h2 {
        color: #2c3e50;
        font-size: 18pt;
        font-weight: bold;
        margin-top: 25pt;
        margin-bottom: 12pt;
        page-break-after: avoid;
    }
    
    h3 {
        color: #34495e;
        font-size: 14pt;
        font-weight: bold;
        margin-top: 15pt;
        margin-bottom: 8pt;
        page-break-after: avoid;
    }
    
    p {
        margin-bottom: 10pt;
        text-align: justify;
    }
    
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 15pt 0;
        font-size: 10pt;
        page-break-inside: avoid;
    }
    
    th {
        background-color: #00d4ff;
        color: white;
        font-weight: bold;
        padding: 8pt;
        text-align: left;
        border: 1px solid #ddd;
    }
    
    td {
        padding: 6pt 8pt;
        border: 1px solid #ddd;
    }
    
    tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    ul, ol {
        margin: 10pt 0;
        padding-left: 25pt;
    }
    
    li {
        margin-bottom: 5pt;
    }
    
    strong {
        font-weight: bold;
        color: #1a1a1a;
    }
    
    em {
        font-style: italic;
    }
    
    code {
        background-color: #f4f4f4;
        padding: 2pt 4pt;
        border-radius: 3pt;
        font-family: 'Courier New', monospace;
        font-size: 9pt;
    }
    
    pre {
        background-color: #f4f4f4;
        padding: 10pt;
        border-radius: 5pt;
        overflow-x: auto;
        font-family: 'Courier New', monospace;
        font-size: 9pt;
        line-height: 1.4;
    }
    
    blockquote {
        border-left: 4px solid #00d4ff;
        margin: 15pt 0;
        padding: 10pt 15pt;
        background-color: #f8f9fa;
        font-style: italic;
    }
    
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 15pt auto;
        page-break-inside: avoid;
    }
    
    .cover-page {
        text-align: center;
        padding-top: 100pt;
        page-break-after: always;
    }
    
    .cover-title {
        font-size: 32pt;
        font-weight: bold;
        color: #1a1a1a;
        margin-bottom: 20pt;
    }
    
    .cover-company {
        font-size: 24pt;
        color: #00d4ff;
        margin-bottom: 15pt;
    }
    
    .cover-date {
        font-size: 12pt;
        color: #7f8c8d;
        margin-top: 30pt;
    }
    
    .metric-box {
        background-color: #f8f9fa;
        border-left: 4px solid #00d4ff;
        padding: 10pt 15pt;
        margin: 10pt 0;
        page-break-inside: avoid;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10pt 15pt;
        margin: 10pt 0;
        page-break-inside: avoid;
    }
    
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 10pt 15pt;
        margin: 10pt 0;
        page-break-inside: avoid;
    }
    
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20pt;
        border-radius: 10pt;
        margin: 20pt 0;
        text-align: center;
        page-break-inside: avoid;
    }
    
    .score-value {
        font-size: 48pt;
        font-weight: bold;
        margin: 10pt 0;
    }
    
    hr {
        border: none;
        border-top: 2px solid #e0e0e0;
        margin: 20pt 0;
    }
    """
    
    def __init__(self):
        """Initialize PDF exporter."""
        pass
    
    def _create_cover_page(self, company_name: str, date: str = None) -> str:
        """
        Create cover page HTML.
        
        Args:
            company_name: Name of target company
            date: Report date (defaults to today)
            
        Returns:
            HTML string for cover page
        """
        if date is None:
            date = datetime.now().strftime("%B %d, %Y")
        
        return f"""
        <div class="cover-page">
            <div class="cover-title">Investment Committee Report</div>
            <div class="cover-company">{company_name}</div>
            <hr style="width: 50%; margin: 30pt auto;">
            <div class="cover-date">{date}</div>
        </div>
        """
    
    def _embed_charts(self, markdown_content: str, charts: Dict[str, str]) -> str:
        """
        Embed base64 charts into markdown.
        
        Args:
            markdown_content: Markdown text
            charts: Dictionary of chart_name -> base64_image
            
        Returns:
            Markdown with embedded images
        """
        # Replace chart placeholders with embedded images
        for chart_name, base64_img in charts.items():
            placeholder = f"{{{{chart:{chart_name}}}}}"
            img_tag = f'<img src="data:image/png;base64,{base64_img}" alt="{chart_name}" style="max-width:100%; height:auto;"/>'
            markdown_content = markdown_content.replace(placeholder, img_tag)
        
        return markdown_content
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        """
        Convert markdown to HTML.
        
        Args:
            markdown_content: Markdown text
            
        Returns:
            HTML string
        """
        # Configure markdown2 with extras
        extras = [
            'tables',
            'fenced-code-blocks',
            'break-on-newline',
            'cuddled-lists',
            'header-ids'
        ]
        
        html_body = markdown2.markdown(markdown_content, extras=extras)
        
        return html_body
    
    def export_to_pdf(
        self,
        markdown_content: str,
        output_path: str,
        company_name: str = "Target Company",
        charts: Optional[Dict[str, str]] = None,
        add_cover: bool = True
    ) -> bool:
        """
        Export markdown report to PDF.
        
        Args:
            markdown_content: Markdown formatted report
            output_path: Path to save PDF file
            company_name: Company name for cover page
            charts: Dictionary of chart base64 images
            add_cover: Whether to add cover page
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Embed charts if provided
            if charts:
                markdown_content = self._embed_charts(markdown_content, charts)
            
            # Convert markdown to HTML
            html_body = self._markdown_to_html(markdown_content)
            
            # Build complete HTML document
            html_parts = ['<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>']
            
            # Add cover page
            if add_cover:
                html_parts.append(self._create_cover_page(company_name))
            
            # Add main content
            html_parts.append(html_body)
            html_parts.append('</body></html>')
            
            full_html = ''.join(html_parts)
            
            # Convert to PDF using WeasyPrint
            HTML(string=full_html).write_pdf(
                output_path,
                stylesheets=[CSS(string=self.PDF_CSS)]
            )
            
            return True
            
        except Exception as e:
            print(f"PDF export error: {e}")
            return False
    
    def export_to_pdf_bytes(
        self,
        markdown_content: str,
        company_name: str = "Target Company",
        charts: Optional[Dict[str, str]] = None,
        add_cover: bool = True
    ) -> bytes:
        """
        Export markdown report to PDF bytes (for download button).
        
        Args:
            markdown_content: Markdown formatted report
            company_name: Company name for cover page
            charts: Dictionary of chart base64 images
            add_cover: Whether to add cover page
            
        Returns:
            PDF file as bytes
        """
        # Embed charts if provided
        if charts:
            markdown_content = self._embed_charts(markdown_content, charts)
        
        # Convert markdown to HTML
        html_body = self._markdown_to_html(markdown_content)
        
        # Build complete HTML document
        html_parts = ['<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>']
        
        # Add cover page
        if add_cover:
            html_parts.append(self._create_cover_page(company_name))
        
        # Add main content
        html_parts.append(html_body)
        html_parts.append('</body></html>')
        
        full_html = ''.join(html_parts)
        
        # Convert to PDF bytes
        pdf_bytes = HTML(string=full_html).write_pdf(
            stylesheets=[CSS(string=self.PDF_CSS)]
        )
        
        return pdf_bytes
