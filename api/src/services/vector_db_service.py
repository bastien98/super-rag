from langchain_core.documents import Document
from ports.vector_db_port import VectorDbPort


class VectorDbService:

    def __init__(self, vectordb_adapter: VectorDbPort):
        self.vectordb_adapter = vectordb_adapter

    async def save_chunks_to_kb(self, chunks: list[str], username: str, kb_name: str, doc_name: str) -> None:
        await self.vectordb_adapter.save_chunks(chunks, username, kb_name, doc_name)

    async def similarity_search(self, query: str, kb_name: str) -> list[Document]:
        return await self.vectordb_adapter.similarity_search(query, kb_name, 10)

    async def similarity_search_with_score(self, query: str, kb_name: str) -> list[tuple[Document, float]]:
        return await self.vectordb_adapter.similarity_search_with_score(query, kb_name, 10)

    async def get_kb_document_count(self, kb_name: str) -> int:
        return self.vectordb_adapter.get_kb_document_count(kb_name)