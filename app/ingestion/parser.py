"""
Document Parser Module.
Parses multi-format document text (Markdown, TXT, HTML structure)
and extracts document metadata and structural sections.
"""

import re
from typing import Dict, Any, List

class DocumentParser:
    @staticmethod
    def parse_markdown_or_text(raw_text: str, filename: str = "document.md") -> Dict[str, Any]:
        """Parse raw text/markdown into title, metadata, and sections."""
        lines = raw_text.splitlines()
        title = filename.replace("_", " ").replace(".md", "").replace(".txt", "").title()
        category = "General"
        sections: List[Dict[str, Any]] = []
        current_section = "Overview"
        current_lines = []
        
        # Check frontmatter / header metadata
        for i, line in enumerate(lines):
            line_str = line.strip()
            
            # Detect title # Heading
            if i == 0 and line_str.startswith("# "):
                title = line_str.lstrip("# ").strip()
                continue
                
            # Metadata tag parser e.g. Category: Policy
            if ":" in line_str and i < 10 and not line_str.startswith("#"):
                parts = line_str.split(":", 1)
                key = parts[0].strip().lower()
                val = parts[1].strip()
                if key == "category":
                    category = val
                    continue
                elif key == "title":
                    title = val
                    continue

            # Detect Section Headings (##, ###)
            if line_str.startswith("#") or (line_str.isupper() and len(line_str) > 3 and len(line_str) < 60):
                if current_lines:
                    section_text = "\n".join(current_lines).strip()
                    if section_text:
                        sections.append({
                            "section_title": current_section,
                            "content": section_text
                        })
                    current_lines = []
                current_section = line_str.lstrip("#").strip()
            else:
                current_lines.append(line)
                
        # Flush remaining section
        if current_lines:
            section_text = "\n".join(current_lines).strip()
            if section_text:
                sections.append({
                    "section_title": current_section,
                    "content": section_text
                })
                
        return {
            "title": title,
            "category": category,
            "raw_text": raw_text,
            "sections": sections
        }
