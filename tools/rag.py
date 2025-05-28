from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
import json
from langchain.schema import Document
import dotenv

dotenv.load_dotenv()

llm = init_chat_model("o4-mini", model_provider="openai")

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

with open("data/api_metadata.json", "r", encoding="utf-8") as f:
    api_entries = json.load(f)

docs = []

for entry in api_entries:
    method = entry.get("method")
    endpoint = entry.get("endpoint")
    service = entry.get("service")
    description = entry.get("description")
    body_fields = entry.get("body", [])

    # Skip incomplete entries
    if not all([method, endpoint, service, description]):
        continue

    # Format content
    content = f"""\
    Method: {method}
    Endpoint: {endpoint}
    Service: {service}

    Description:
    {description}

    Body:
    """
    for field in body_fields:
        name = field.get("name", "unknown")
        dtype = field.get("type", "unknown")
        desc = field.get("description", "")
        content += f"- {name} ({dtype}): {desc}\n"
    
    docs.append(Document(page_content=content.strip(), metadata={"endpoint": endpoint}))

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)

vector_store = InMemoryVectorStore.from_documents(
    documents=all_splits,
    embedding=embeddings
)

retriever = vector_store.as_retriever()

retriever_tool = create_retriever_tool(
    retriever,
    "retrieve_api_metadata",
    "Retrieve API metadata based on a query",
)