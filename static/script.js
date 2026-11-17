const form = document.getElementById("chat-form");
const input = document.getElementById("question");
const chat = document.getElementById("chat");
const sendButton = document.getElementById("send-button");

function addMessage(role, text, sources = []) {
    const message = document.createElement("div");
    message.className = `message ${role}`;

    const heading = document.createElement("strong");
    heading.textContent = role === "user" ? "You" : "Assistant";

    const paragraph = document.createElement("p");
    paragraph.textContent = text;

    message.appendChild(heading);
    message.appendChild(paragraph);

    if (sources.length > 0) {
        const sourceBox = document.createElement("div");
        sourceBox.className = "sources";

        const sourceHeading = document.createElement("strong");
        sourceHeading.textContent = "Retrieved sources:";
        sourceBox.appendChild(sourceHeading);

        for (const source of sources) {
            const line = document.createElement("div");
            line.textContent =
                `${source.document}, page ${source.page} ` +
                `(distance: ${source.distance})`;
            sourceBox.appendChild(line);
        }

        message.appendChild(sourceBox);
    }

    chat.appendChild(message);
    chat.scrollTop = chat.scrollHeight;

    return message;
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = input.value.trim();

    if (!question) return;

    addMessage("user", question);

    input.value = "";
    input.disabled = true;
    sendButton.disabled = true;

    const loadingMessage = addMessage(
        "assistant",
        "Searching documents and generating answer..."
    );

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        loadingMessage.remove();
        addMessage(
            "assistant",
            data.answer,
            data.sources || []
        );

    } catch (error) {
        loadingMessage.remove();
        addMessage(
            "assistant",
            `Error: ${error.message}`
        );
    } finally {
        input.disabled = false;
        sendButton.disabled = false;
        input.focus();
    }
});


// PDF upload

const uploadForm = document.getElementById("upload-form");
const pdfFile = document.getElementById("pdf-file");
const uploadButton = document.getElementById("upload-button");
const uploadStatus = document.getElementById("upload-status");

uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const file = pdfFile.files[0];

    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
        uploadStatus.textContent = "Maximum file size is 10 MB.";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    uploadButton.disabled = true;
    uploadStatus.textContent = "Uploading and indexing PDF...";

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Upload failed."
            );
        }

        uploadStatus.textContent =
            `Success! ${data.filename} indexed ` +
            `(${data.pages} pages, ${data.chunks} chunks).`;

        pdfFile.value = "";

    } catch (error) {
        uploadStatus.textContent =
            `Error: ${error.message}`;
    } finally {
        uploadButton.disabled = false;
    }
});
