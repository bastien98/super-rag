from dataclasses import dataclass, field
from typing import List
from file_api_v2.domain.entities.document import Document


@dataclass
class KnowledgeBase:
    kb_name: str
    docs: List[Document] = field(default_factory=list)

    def add_document(self, document: Document) -> None:
        """Adds a new PdfDocument to the knowledge base."""
        self.docs.append(document)
        print(f"Document '{document.doc_name}' added to Knowledge Base '{self.kb_name}'")
