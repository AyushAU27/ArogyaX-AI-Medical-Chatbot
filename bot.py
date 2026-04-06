import os
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

print("Waking up the medical assistant...")

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    encode_kwargs={'normalize_embeddings': True},
)

vectorstore = Chroma(
    persist_directory="./chroma_db",
    collection_name="medical_books",
    embedding_function=embedding_model,
)

retriever = vectorstore.as_retriever(search_kwargs={'k': 3})

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2, 
    max_tokens=1024,
)

system_prompt = (
    "You are a highly intelligent and helpful medical AI assistant. "
    "Use the following pieces of retrieved medical context to answer the user's question. "
    "If you don't know the answer based on the context, just say that you don't know. "
    "Do not guess. Keep the answer concise and professional.\n\n"
    "Context:\n{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

#  Build the RAG Chain
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

print("✅ System Ready! Type 'exit' or 'quit' to stop.\n")
print("-" * 50)


while True:
    user_input = input("\n You: ")
    
    if user_input.lower() in ['exit', 'quit']:
        print("Goodbye! Stay healthy.")
        break
        
    if not user_input.strip():
        continue
        
    print("🤖 Bot is thinking...")
    
    # Run the query through the pipeline
    response = rag_chain.invoke({"input": user_input})

    print(f"\n🤖 Bot: {response['answer']}")
    
    print("\n📚 Sources used:")
    for doc in response["context"]:
        book_title = doc.metadata.get('book_title', 'Unknown Source')
        page = doc.metadata.get('page', '?')
        print(f"  - {book_title} (Page {page})")
    
    print("-" * 50)