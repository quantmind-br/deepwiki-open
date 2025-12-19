"""
HTML exporter for standalone codemap viewing.
"""

import json
import logging
from typing import Optional

from ..models import Codemap

logger = logging.getLogger(__name__)


class HTMLExporter:
    """
    Exports codemaps as standalone HTML files.
    
    The HTML includes embedded Mermaid.js for diagram rendering
    and all necessary CSS/JS for a self-contained view.
    """
    
    HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        :root {{
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --text-primary: #1a1a1a;
            --text-secondary: #666666;
            --accent: #3b82f6;
            --border: #e5e5e5;
        }}
        
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-primary: #1a1a1a;
                --bg-secondary: #2d2d2d;
                --text-primary: #ffffff;
                --text-secondary: #a0a0a0;
                --accent: #60a5fa;
                --border: #404040;
            }}
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }}
        
        h1 {{
            font-size: 1.75rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        
        .meta {{
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}
        
        .layout {{
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 2rem;
        }}
        
        @media (max-width: 1024px) {{
            .layout {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .diagram-container {{
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 1rem;
            overflow: auto;
            min-height: 400px;
        }}
        
        .mermaid {{
            display: flex;
            justify-content: center;
        }}
        
        .trace-guide {{
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 1.5rem;
            max-height: 80vh;
            overflow-y: auto;
        }}
        
        .trace-guide h2 {{
            font-size: 1.25rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
        }}
        
        .trace-guide h3 {{
            font-size: 1rem;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
            color: var(--accent);
        }}
        
        .trace-guide p {{
            margin-bottom: 1rem;
            color: var(--text-secondary);
        }}
        
        .trace-guide code {{
            background: var(--bg-primary);
            padding: 0.125rem 0.375rem;
            border-radius: 4px;
            font-size: 0.875rem;
        }}
        
        .trace-guide pre {{
            background: var(--bg-primary);
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
            margin: 1rem 0;
        }}
        
        .summary {{
            background: var(--accent);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }}
        
        footer {{
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.75rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p class="meta">
                Repository: {repo_url} | 
                Generated: {generated_at} |
                Query: "{query}"
            </p>
        </header>
        
        <div class="layout">
            <div class="diagram-container">
                <div class="mermaid">
{mermaid_code}
                </div>
            </div>
            
            <div class="trace-guide">
                <h2>Trace Guide</h2>
                <div class="summary">
                    <p>{summary}</p>
                </div>
                {trace_sections}
                {conclusion}
            </div>
        </div>
        
        <footer>
            Generated by DeepWiki Codemaps | 
            <a href="{repo_url}" target="_blank">View Repository</a>
        </footer>
    </div>
    
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }},
            securityLevel: 'loose'
        }});
    </script>
</body>
</html>'''
    
    def __init__(self):
        pass
    
    def export(self, codemap: Codemap) -> str:
        """
        Export a codemap as a standalone HTML file.
        
        Args:
            codemap: The complete codemap object
            
        Returns:
            HTML content as string
        """
        # Generate trace sections HTML
        trace_sections = self._render_trace_sections(codemap.trace_guide.sections)
        
        # Generate conclusion if present
        conclusion = ""
        if codemap.trace_guide.conclusion:
            conclusion = f"<h3>Conclusion</h3><p>{self._escape_html(codemap.trace_guide.conclusion)}</p>"
        
        # Format the HTML
        html = self.HTML_TEMPLATE.format(
            title=self._escape_html(codemap.title),
            repo_url=self._escape_html(codemap.repo_url),
            generated_at=codemap.created_at.strftime("%Y-%m-%d %H:%M"),
            query=self._escape_html(codemap.query),
            mermaid_code=codemap.render.mermaid,
            summary=self._escape_html(codemap.trace_guide.summary),
            trace_sections=trace_sections,
            conclusion=conclusion
        )
        
        return html
    
    def _render_trace_sections(self, sections: list) -> str:
        """Render trace guide sections as HTML"""
        html_parts = []
        
        for section in sorted(sections, key=lambda s: s.order):
            section_html = f"""
                <h3>{self._escape_html(section.title)}</h3>
                <div class="section-content">
                    {self._markdown_to_html(section.content)}
                </div>
            """
            html_parts.append(section_html)
        
        return "\n".join(html_parts)
    
    def _markdown_to_html(self, markdown: str) -> str:
        """
        Simple markdown to HTML conversion.
        
        For production, consider using a proper markdown library.
        """
        import re
        
        html = markdown
        
        # Code blocks
        html = re.sub(r'```(\w*)\n(.*?)\n```', r'<pre><code class="language-\1">\2</code></pre>', html, flags=re.DOTALL)
        
        # Inline code
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        
        # Bold
        html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)
        
        # Italic
        html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)
        
        # Line breaks
        html = re.sub(r'\n\n', '</p><p>', html)
        html = f"<p>{html}</p>"
        
        return html
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))
