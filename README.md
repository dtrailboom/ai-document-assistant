\# AI Document Assistant



\*\*A privacy-focused, local AI application for chatting with PDF documents using Retrieval-Augmented Generation (RAG).\*\*



Built with \*\*Python, FastAPI, Ollama, Qwen3 and ChromaDB\*\* — without external AI APIs.



\## Features



\- \*\*Local AI:\*\* Run Qwen3 through Ollama without cloud inference.

\- \*\*PDF Upload:\*\* Upload and automatically index PDF documents.

\- \*\*RAG Search:\*\* Retrieve relevant document passages using vector embeddings.

\- \*\*AI Chat:\*\* Ask questions and receive context-aware answers.

\- \*\*Source References:\*\* Display document names, page numbers and retrieval distances.

\- \*\*Web Interface:\*\* Browser-based chat and PDF upload.

\- \*\*Persistent Storage:\*\* Store document embeddings locally in ChromaDB.



\## Tech Stack



| Component | Technology |

|---|---|

| Language | Python |

| Backend | FastAPI |

| LLM | Qwen3 1.7B |

| Model Runtime | Ollama |

| Embeddings | nomic-embed-text |

| Vector Database | ChromaDB |

| PDF Processing | PyMuPDF |

| Frontend | HTML, CSS, JavaScript |



\## Quick Start



\*\*1. Install dependencies\*\*



```bash

pip install -r requirements.txt

```



\*\*2. Download the AI models\*\*



```bash

ollama pull qwen3:1.7b

ollama pull nomic-embed-text

```



\*\*3. Start the application\*\*



```bash

python -m uvicorn api:app --reload

```



\*\*4. Open the web interface\*\*



http://127.0.0.1:8000



Upload a PDF, wait for indexing, and start asking questions.



\*Prerequisites: Python and Ollama installed, with Ollama running.\*



\## Roadmap



\- \[x] Local LLM integration

\- \[x] Interactive chat and conversation history

\- \[x] PDF extraction and text chunking

\- \[x] RAG with embeddings and vector search

\- \[x] FastAPI backend and web interface

\- \[x] PDF upload with automatic indexing

\- \[ ] Document selection and management

\- \[ ] Improved retrieval and answer quality

\- \[ ] Docker deployment

\- \[ ] Model evaluation and benchmarking



\## Privacy



AI inference, document processing and vector storage run locally. Uploaded PDFs, the vector database and local chat history are excluded from Git.



\*\*Status:\*\* Version 4.4 — Functional local RAG document assistant.



\*An ongoing hands-on project exploring local LLMs, AI engineering and practical RAG applications.\*

