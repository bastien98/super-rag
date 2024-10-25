from dataclasses import dataclass
from typing import Optional


@dataclass
class Document:
    doc_id: Optional[int] = None  # doc_id will be generated by the database after persisting
    name: str = '' # The name of the document (e.g., filename with extension)
    source: str = '' # The source of the document
