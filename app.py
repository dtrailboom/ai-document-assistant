from ollama import chat

MODEL = "qwen3:1.7b"

# Store conversation history
messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful AI assistant. "
            "Give clear and concise answers."
        )
    }
]

print("=== AI Document Assistant v2 ===")
print(f"Model: {MODEL}")
print("Commands: exit, history, clear\n")

while True:
    question = input("You: ").strip()

    if question.lower() == "exit":
        print("Goodbye!")
        break

    if question.lower() == "clear":
        messages = messages[:1]
        print("Conversation cleared.\n")
        continue

    if question.lower() == "history":
        for message in messages[1:]:
            print(
                f"{message['role']}: "
                f"{message['content']}"
            )
        print()
        continue

    if not question:
        continue

    # Add user's question to history
    messages.append({
        "role": "user",
        "content": question
    })

    try:
        # Send entire history to Ollama
        response = chat(
            model=MODEL,
            messages=messages,
            think=False
        )

        answer = response.message.content

        # Save AI response to history
        messages.append({
            "role": "assistant",
            "content": answer
        })

        print(f"\nAI: {answer}\n")

    except Exception as error:
        # Remove unanswered question
        messages.pop()
        print(f"Error: {error}\n")
