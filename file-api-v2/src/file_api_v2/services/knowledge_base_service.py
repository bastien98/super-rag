from file_api_v2.domain.entities import Document, RawDocument
from file_api_v2.repositories.user_repository import UserRepository
from file_api_v2.services.bm25_service import Bm25Service
from file_api_v2.services.context_service import ContextService
from file_api_v2.services.file_storage_service import FileStorageService
from file_api_v2.services.location_service import LocalLocationService
from file_api_v2.services.vector_db_service import VectorDbService
from file_api_v2.utils.parser import Parser


class KnowledgeBaseService:
    def __init__(
            self,
            file_storage_service: FileStorageService,
            vector_db_service: VectorDbService,
            user_repo: UserRepository,
            parser: Parser,
            context_service: ContextService,
            local_location_service: LocalLocationService,
            bm25_service: Bm25Service

    ):
        self.file_storage_service = file_storage_service
        self.vector_db_service = vector_db_service
        self.user_repo = user_repo
        self.parser = parser
        self.context_service = context_service
        self.local_location_service = local_location_service
        self.bm25_service = bm25_service

    async def add_document(self, raw_doc: RawDocument, username: str, kb_name: str) -> None:
        self.validate_user_and_kb(username, kb_name)
        self.validate_document_is_pdf(raw_doc)
        self.validate_document_not_exists(username, kb_name, raw_doc.name)

        doc_name = raw_doc.name
        # Calculate file storage locations
        raw_doc_path = self.local_location_service.get_raw_doc_location(username, kb_name, doc_name)
        text_chunks_doc_path = self.local_location_service.get_text_chunks_location(username, kb_name, doc_name)
        md_chunks_doc_path = self.local_location_service.get_md_chunks_doc_location(username, kb_name, doc_name)
        # Save the raw document to file storage
        self.file_storage_service.save_raw_file(raw_doc, raw_doc_path)
        # Parse the byte content to text and return full text and page list
        full_text, text_chunks = self.parser.parse_to_text(raw_doc.content)
        # Parse the byte content to Markdown text and return full text and page list
        full_md_text, md_chunks = await self.parser.parse_to_markdown(raw_doc)
        # Add context to chunks
        ctx_text_chunks = await self.context_service.create_context_chunks(full_text, text_chunks)
        ctx_md_chunks = await self.context_service.create_context_chunks(full_md_text, md_chunks)
        # Save the contextualized chunks to file storage
        self.file_storage_service.save_text_chunks(ctx_text_chunks, text_chunks_doc_path)
        self.file_storage_service.save_md_chunks(ctx_md_chunks, md_chunks_doc_path)
        # Save the md chunks in the vector db
        await self.vector_db_service.save_chunks_to_kb(ctx_text_chunks, username, kb_name, doc_name)
        # Update user state to reflect the change
        document = Document(doc_name, raw_doc.source)
        user = self.user_repo.retrieve_user(username)
        user.add_document_to_knowledge_base(kb_name, document)
        self.user_repo.persist_user(user)
        # Update existing BM25 index
        self.bm25_service.update_bm25_index(user, kb_name)

    # Validation methods
    def validate_user_and_kb(self, username: str, kb_name: str) -> None:
        """Validate that the user and knowledge base exist."""
        user = self.user_repo.retrieve_user(username)
        if not user:
            raise ValueError(f"User {username} does not exist.")

        knowledge_base = user.get_knowledge_base(kb_name)
        if not knowledge_base:
            raise ValueError(f"Knowledge base {kb_name} does not exist for user {username}.")

    def validate_document_is_pdf(self, raw_doc: RawDocument) -> None:
        """Validate that the document is a PDF."""
        if not raw_doc.name.lower().endswith('.pdf'):
            raise ValueError(f"The document {raw_doc.name} is not a PDF file.")

    def validate_document_not_exists(self, username: str, kb_name: str, doc_name: str) -> None:
        """Check if the document already exists in the knowledge base."""
        user = self.user_repo.retrieve_user(username)
        knowledge_base = user.get_knowledge_base(kb_name)
        if knowledge_base and knowledge_base.document_exists(doc_name):
            raise ValueError(f"The document {doc_name} already exists in the knowledge base '{kb_name}'.")
