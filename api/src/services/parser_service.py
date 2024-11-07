from api.src.domain.entities.raw_document import RawDocument
from api.src.ports.parse_to_markdown_port import ParseToMarkdownPort


class ParserService:
    def __init__(self,markdown_adapter:ParseToMarkdownPort,text_adapter):
        self.markdown_adapter = markdown_adapter
        self.text_adapter = text_adapter

    async def parse_to_markdown(self, doc: RawDocument) -> tuple[str, list[str]]:
        return await self.markdown_adapter.parse_to_markdown(doc)