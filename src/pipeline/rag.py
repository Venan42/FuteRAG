from prompts import SYSTEM_PROMPT
import wikipedia
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

wikipedia.set_lang("pt")

class FuteRAG:

    def __init__(self, model_name="llama3.1", number_top_k=10):
        self.model = ChatOllama(model=model_name, temperature=0.1)
        self.embedder = OllamaEmbeddings(model="nomic-embed-text",base_url="http://localhost:11434")
        self.top_k = number_top_k
        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
        self.parser = StrOutputParser()

    def retrieval(self, question: str):
        resultados = wikipedia.search(question, results=self.top_k)
        
        pages = []
        for i, page_title in enumerate(resultados):
            try:
                page_content = wikipedia.page(page_title)
                
                pages.append({
                    "top_result": i + 1,
                    "title": page_title,
                    "summary": page_content.summary,
                    "full_content": page_content.content
                })
            except wikipedia.exceptions.DisambiguationError as e:
                print(f"Ambiguidade encontrada para '{page_title}'. Pulando...")
                continue
            except wikipedia.exceptions.PageError:
                print(f"Página '{page_title}' não encontrada. Pulando...")
                continue
                
        return pages
        
    def embeddings(self, docs):
        self.embedder.embed_documents(docs)

    def rag_chain(self):
        return self.prompt | self.model | self.parser