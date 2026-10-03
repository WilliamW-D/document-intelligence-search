"""
Semantic Chunking Engine.
Splits document section texts into sliding window chunks with overlap,
preserves section context, computes character offsets, and calculates MD5 hashes for deduplication.
"""

import hashlib
from typing import List, Dict, Any
from app.config import settings

class SemanticChunker:
    def __init__(self, chunk_size: int = settings.DEFAULT_CHUNK_SIZE, overlap: int = settings.DEFAULT_CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, parsed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process parsed document sections into semantic chunks."""
        chunks: List[Dict[str, Any]] = []
        global_char_offset = 0
        chunk_index = 0

        for section in parsed_doc.get("sections", []):
            section_title = section.get("section_title", "General")
            content = section.get("content", "")
            
            if not content:
                continue

            # Sliding window over section text
            start = 0
            content_len = len(content)
            
            while start < content_len:
                end = min(start + self.chunk_size, content_len)
                
                # Adjust end to nearest space/sentence boundary if possible
                if end < content_len and " " in content[start:end]:
                    last_space = content[start:end].rfind(" ")
                    if last_space > self.chunk_size // 2:
                        end = start + last_space
                        
                chunk_text = content[start:end].strip()
                
                if chunk_text:
                    # MD5 Chunk Hash for Deduplication
                    chunk_hash = hashlib.md5(f"{section_title}:{chunk_text}".encode("utf-8")).hexdigest()
                    
                    start_char = global_char_offset + start
                    end_char = global_char_offset + end
                    
                    chunks.append({
                        "chunk_index": chunk_index,
                        "chunk_hash": chunk_hash,
                        "section_title": section_title,
                        "content": chunk_text,
                        "start_char": start_char,
                        "end_char": end_char
                    })
                    chunk_index += 1

                # Move window with overlap
                start = end - self.overlap if (end - self.overlap) > start else end

            global_char_offset += content_len + 2  # newline separation buffer

        return chunks
