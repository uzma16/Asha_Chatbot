import os
import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document


class RAGService:
    def __init__(self):
        self.vector_store = None
        self._initialize_vector_store()

    def _load_json_files(self):
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_folder = os.path.join(backend_dir, "data")
        print(f"Looking for data in: {data_folder}")

        if not os.path.exists(data_folder):
            raise FileNotFoundError(f"Data folder not found at: {data_folder}")

        documents = []
        for filename in os.listdir(data_folder):
            if filename.endswith(".json"):
                file_path = os.path.join(data_folder, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if not content:
                            print(f"Skipping empty file: {filename}")
                            continue
                        json_data = json.loads(content)
                        if isinstance(json_data, list):
                            for entry in json_data:
                                doc_text = json.dumps(entry, ensure_ascii=False, indent=2)
                                documents.append(Document(page_content=doc_text, metadata={"source": filename}))
                        else:
                            doc_text = json.dumps(json_data, ensure_ascii=False, indent=2)
                            documents.append(Document(page_content=doc_text, metadata={"source": filename}))
                        print(f"Successfully loaded: {filename}")
                except json.JSONDecodeError as e:
                    print(f"Skipping {filename} due to invalid JSON: {e}")
                except Exception as e:
                    print(f"Error processing {filename}: {e}")

        if not documents:
            print("Warning: No valid JSON documents were loaded")
            return None

        return documents

    def _create_vector_store(self, documents):
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = Chroma.from_documents(documents, embeddings, persist_directory="./chroma_db")
        return vector_store

    def _initialize_vector_store(self):
        documents = self._load_json_files()
        if documents:
            self.vector_store = self._create_vector_store(documents)

    def query(self, question: str) -> str:
        """
        Query the vector store. Returns the content of the most relevant document if found, otherwise returns "none".
        """
        if not self.vector_store:
            print("Vector store not initialized or no documents loaded")
            return "none"

        try:
            # Retrieve relevant documents from the vector store
            retriever = self.vector_store.as_retriever(search_kwargs={"k": 1})  # Get only the most relevant document
            retrieved_docs = retriever.invoke(question)

            # If no relevant documents are found, return "none"
            if not retrieved_docs:
                print(f"No relevant documents found for question: {question}")
                return "none"

            # Return the content of the most relevant document
            return retrieved_docs[0].page_content

        except Exception as e:
            print(f"Error querying vector store: {e}")
            return "none"