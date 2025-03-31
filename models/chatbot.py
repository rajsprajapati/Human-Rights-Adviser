from models.helper_utils import word_wrap, load_chroma
from pypdf import PdfReader
import os
from openai import OpenAI
from dotenv import load_dotenv


from pypdf import PdfReader
import numpy as np

from langchain_community.document_loaders import PyPDFLoader


# Load environment variables from .env file
load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")
client = OpenAI(api_key=gemini_key)


import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

embedding_function = SentenceTransformerEmbeddingFunction()


reader = PdfReader("./HR_Conventions.pdf")
pdf_texts = [p.extract_text().strip() for p in reader.pages]

# Filter the empty strings
pdf_texts = [text for text in pdf_texts if text]

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    SentenceTransformersTokenTextSplitter,
)

character_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ". ", " ", ""], chunk_size=1000, chunk_overlap=0
)
character_split_texts = character_splitter.split_text("\n\n".join(pdf_texts))

token_splitter = SentenceTransformersTokenTextSplitter(
    chunk_overlap=0, tokens_per_chunk=256
)

token_split_texts = []
for text in character_split_texts:
    token_split_texts += token_splitter.split_text(text)

chroma_client = chromadb.Client()
chroma_collection = chroma_client.get_or_create_collection(
    "Human-Rights", embedding_function=embedding_function
)

# extract the embeddings of the token_split_texts
ids = [str(i) for i in range(len(token_split_texts))]

chroma_collection.add(ids=ids, documents=token_split_texts)

count = chroma_collection.count()

query = "What are the key human rights conventions?"

results = chroma_collection.query(
    query_texts=query, n_results=10, include=["documents", "embeddings"]
)

retrieved_documents = results["documents"][0]

for document in results["documents"][0]:
    print(word_wrap(document))
    print("")

from sentence_transformers import CrossEncoder

cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

pairs = [[query, doc] for doc in retrieved_documents]
scores = cross_encoder.predict(pairs)

print("Scores:")
for score in scores:
    print(score)

print("New Ordering:")
for o in np.argsort(scores)[::-1]:
    print(o + 1)


client = OpenAI(
    api_key=gemini_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Generate the final answer using the Gemini model
def generate_multi_query(query, context, model="gemini-2.0-flash"):

    prompt = f"""
    You are a specialized AI legal expert with deep knowledge of international human rights conventions, treaties, and frameworks. 
    Your task is to provide clear, concise, and fact-based legal responses referencing documents such as:

    - The Universal Declaration of Human Rights (UDHR)
    - International Covenant on Civil and Political Rights (ICCPR)
    - International Covenant on Economic, Social and Cultural Rights (ICESCR)
    - Convention on the Elimination of All Forms of Discrimination Against Women (CEDAW)
    - Convention on the Rights of the Child (CRC)
    - Convention on the Rights of Persons with Disabilities (CRPD)

    Your responsibilities include:

    1. Offering accurate and authoritative answers aligned with international legal standards.
    2. Referring to relevant articles and provisions of international treaties where applicable.
    3. Suggesting appropriate steps that individuals can take when their rights are violated.
    4. Guiding users to relevant institutions such as human rights commissions, ombudsman offices, and international bodies for further assistance.

    If information about a specific query is unavailable, politely indicate that the relevant data was not found in the available context.

    """


    messages = [
        {
            "role": "system",
            "content": prompt,
        },
        {
            "role": "user",
            "content": f"based on the following context:\n\n{context}\n\nAnswer the query: '{query}'",
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    content = response.choices[0].message.content
    content = content.split("\n")
    return content


# multiple queries example 
'''"What protections exist for women under the CEDAW?"
"How does the ICCPR safeguard civil and political rights?"
"What are the key rights guaranteed under the CRPD for persons with disabilities?"
"What recourse is available under international law for victims of human trafficking?"'''

def process_query(query):
    # Main query
        # "What rights are protected under the Convention on the Rights of the Child (CRC)?"
        #'What recourse is available under international law for victims of human trafficking?'

    # print("\nEnter your query related to Human Rights Conventions (or type 'exit' to quit): ")
    # user_query = input()
    original_query = str(query)

    if original_query.lower() == "exit":
        # print("Exiting... Goodbye!")
        return "Exiting... Goodbye!"

    generated_queries = [
        f"What are the legal provisions regarding {original_query}?",
        f"How is {original_query} addressed under international law?",
        f"What actions can be taken if {original_query} is violated?",
    ]

    queries = [original_query] + generated_queries


    # results = chroma_collection.query(
    #     query_texts=queries, n_results=10, include=["documents", "embeddings"]
    # )
    # retrieved_documents = results["documents"]

    # 📝 Retrieve documents from ChromaDB for each query
    retrieved_documents = []  # Reset the documents for each new query
    for query in queries:
        results = chroma_collection.query(
            query_texts=query, n_results=10, include=["documents"]
        )
        retrieved_documents.extend(results["documents"][0])

    # Deduplicate the retrieved documents
    unique_documents = set()
    for documents in retrieved_documents:
        for document in documents:
            unique_documents.add(document)

    unique_documents = list(unique_documents)

    pairs = []
    for doc in unique_documents:
        pairs.append([original_query, doc])

    scores = cross_encoder.predict(pairs)

    print("Scores:")
    for score in scores:
        print(score)

    print("New Ordering:")
    for o in np.argsort(scores)[::-1]:
        print(o)
    # ====
    top_indices = np.argsort(scores)[::-1][:5]
    top_documents = [unique_documents[i] for i in top_indices]

    # Concatenate the top documents into a single context
    context = "\n\n".join(top_documents)

    # Generate the final answer
    try:
        res = generate_multi_query(query=original_query, context=context)
        print("\nFinal Answer:")
        # for line in res:
            # print(line)
        # Write the Markdown text to result.md file
        if isinstance(res, list):
            response = "\n".join(res)
            with open("models/result.md", "w", encoding="utf-8") as file:
                file.write(response)
            return response
    except Exception as e:
        print(f"Error: {e}. Please try again.")


