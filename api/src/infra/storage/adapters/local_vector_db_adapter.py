import uuid
from typing import Union
import chromadb
from chromadb import AsyncHttpClient as ChromaClient
from chromadb.errors import InvalidCollectionException
from langchain_chroma import Chroma
import chromadb.utils.embedding_functions as embedding_functions
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings

import config
from ports.vector_db_port import VectorDbPort


class LocalChromaDbAdapter(VectorDbPort):
    def __init__(self, aclient: ChromaClient, model: Union[OpenAIEmbeddings, OllamaEmbeddings]):
        self.aclient = aclient
        self.embedding_function = embedding_functions.create_langchain_embedding(model)

    @staticmethod
    def create(embeddings_model: Union[OpenAIEmbeddings, OllamaEmbeddings]):
        return LocalChromaDbAdapter(
            chromadb.PersistentClient(path=f"{config.PROCESSED_FILE_LOCATION}/vector_db"),
            embeddings_model
        )

    def get_collection_name(self, kb_id: int) -> str:
        return f"knowledge_base_{kb_id}"

    async def save_chunks(self, chunks: list[str], kb_id: int, doc_name: str) -> None:
        collection_name = self.get_collection_name(kb_id)
        try:
            # Try to get the collection if it already exists
            print(f"Attempting to retrieve collection: {collection_name}")
            collection = self.aclient.get_collection(name=collection_name, embedding_function=self.embedding_function)
            print(f"Collection '{collection_name}' retrieved successfully.")
        except InvalidCollectionException:
            # If the collection doesn't exist, create it
            print(f"Collection '{collection_name}' does not exist. Creating a new one.")
            collection = self.aclient.create_collection(name=collection_name,
                                                        embedding_function=self.embedding_function)
            print(f"Collection '{collection_name}' created successfully.")

        chunk_ids = [str(uuid.uuid4()) for _ in chunks]
        metadata = [
            {"filename": doc_name, "chunk_number": chunk_num}  # Metadata with filename and chunk number
            for chunk_num, _ in enumerate(chunks, start=1)
        ]
        collection.add(documents=chunks, ids=chunk_ids, metadatas=metadata)

    async def similarity_search(self, query: str, kb_id: int, k: int) -> list[Document]:
        """ Retrieves a vector store retriever for a given knowledge base and returns the top-k most similar chunks. """
        collection_name = self.get_collection_name(kb_id)
        return Chroma(
            client=self.aclient,
            collection_name=collection_name,
            embedding_function=self.embedding_function,
        ).as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        ).invoke(query)

    async def similarity_search_with_score(self, query: str, kb_id: int, k: int) -> list[tuple[Document, float]]:
        collection_name = self.get_collection_name(kb_id)
        return Chroma(
            client=self.aclient,
            collection_name=collection_name,
            embedding_function=self.embedding_function,
        ).similarity_search_with_score(query=query, k=k)

    def get_kb_document_count(self, kb_id: int) -> int:
        collection_name = self.get_collection_name(kb_id)
        return self.aclient.get_collection(name=collection_name, embedding_function=self.embedding_function).count()
