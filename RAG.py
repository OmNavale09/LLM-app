import os
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

import gradio as gr

load_dotenv()

api = os.getenv("GEMINI_API_KEY")

file_path = "./BlockChain.pdf"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

vector_store = Chroma(
    collection_name="BC_store",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",
)
if vector_store._collection.count() == 0: 
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
    )

    all_splits = text_splitter.split_documents(docs)
    vector_store.add_documents(all_splits) 
    print("Documents added to Chroma DB.") 
else: 
    print("Chroma DB already contains documents. Skipping insertion.")

sample_embedding = vector_store.get(
    limit=1,
    include=["embeddings", "documents"]
)

model = init_chat_model(
    "google_genai:gemini-2.5-flash",
    api_key=api,
)


def retrieve_context(query):

    similar_docs = vector_store.similarity_search(
        query,
        k=4
    )

    context = ""

    for doc in similar_docs:
        page = doc.metadata.get("page", "Unknown")
        context += f"Source page: {page + 1 if isinstance(page, int) else page}\n"
        context += f"Content: {doc.page_content}\n\n"

    return context, similar_docs


def ask_about_pdf(user_query):

    context, related_docs = retrieve_context(user_query)

    system_message = f"""You are a helpful chatbot.

Use only the following pieces of context to answer the question. Don't make up any new information:

{context}"""

    messages = [
        {
            "role": "system",
            "content": system_message
        },
        {
            "role": "user",
            "content": user_query
        }
    ]

    response = model.invoke(messages)

    text = f"""Answer: {response.content}
    source_documents: {related_docs}
    context_used: {context}
    """

    result = {
        "answer": response.content,
        "source_documents": related_docs,
        "context_used": context
    }

    print(result)

    return text


result = ask_about_pdf(
    "What is cold wallet "
)

print(result)

demo = gr.Interface(
    fn=ask_about_pdf,
    inputs=[gr.Textbox(lines=5, placeholder="Ask a Question on BC", label="input")],
    outputs=gr.Textbox(lines=10),
    title="DocuChat",
    description="Ask questions on Blockchain"
)
demo.launch()