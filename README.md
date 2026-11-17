\# AI Document Assistant



A privacy-focused, locally running AI assistant built with Python, Ollama, and Qwen3.



\## Project Overview



This project explores local Large Language Models (LLMs) and their integration into practical applications.



The goal is to develop an AI-powered document assistant capable of answering questions about uploaded documents using Retrieval-Augmented Generation (RAG).



All AI inference runs locally through Ollama.



\## Current Features



\- Local LLM inference using Ollama

\- Qwen3 1.7B integration

\- Interactive Python chat

\- Conversation history

\- Persistent chat history using JSON

\- Clear and history commands

\- No cloud AI API required



\## Technologies



\- Python

\- Ollama

\- Qwen3

\- JSON

\- Git and GitHub



\## Installation



1\. Install Python and Ollama.

2\. Download the model:



&#x20;  ollama pull qwen3:1.7b



3\. Install Python dependencies:



&#x20;  pip install -r requirements.txt



4\. Start the application:



&#x20;  python app.py



\## Roadmap



\- \[x] Local LLM integration

\- \[x] Interactive chat

\- \[x] Conversation history

\- \[x] Persistent JSON storage

\- \[ ] PDF document processing

\- \[ ] RAG with embeddings and vector search

\- \[ ] FastAPI backend

\- \[ ] Web interface

\- \[ ] Docker deployment

\- \[ ] Model evaluation and benchmarking



\## Privacy



The assistant runs locally using Ollama.



Conversation history is stored locally in

chat\_history.json and excluded from Git.



\## Project Status



Version 2.1 - Local AI chat with persistent memory.



This is an ongoing educational project focused on

Generative AI, local LLM deployment, and RAG.



