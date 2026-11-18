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
            body: JSON.stringify({
    		question,
    		document: documentSelect.value || null
	    })
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
	await loadDocuments();

    } catch (error) {
        uploadStatus.textContent =
            `Error: ${error.message}`;
    } finally {
        uploadButton.disabled = false;
    }
});


//
// Version 4.5 - Document Selection
//

const documentSelect = document.getElementById("document-select");
const documentList = document.getElementById("document-list");
const managementStatus = document.getElementById("management-status");

// Load indexed PDF documents from FastAPI
async function loadDocuments() {
    try {
        const response = await fetch("/documents");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Remember selected document
        const selectedDocument = documentSelect.value;

        // Clear existing options
        documentSelect.innerHTML = "";

        // Default option: all documents
        const allOption = document.createElement("option");
        allOption.value = "";
        allOption.textContent = "All documents";
        documentSelect.appendChild(allOption);

        // Add indexed PDFs
        for (const filename of data.documents) {
            const option = document.createElement("option");

            option.value = filename;
            option.textContent = filename;

            documentSelect.appendChild(option);
        }

        // Restore previous selection
        const documentExists = Array.from(
            documentSelect.options
        ).some(option => option.value === selectedDocument);

        if (documentExists) {
            documentSelect.value = selectedDocument;
        }

	
        // Version 4.6 - Display document management list

        documentList.replaceChildren();

        if (data.documents.length === 0) {
            const emptyMessage = document.createElement("p");
            emptyMessage.textContent = "No documents indexed yet.";
            documentList.appendChild(emptyMessage);
        }

        for (const filename of data.documents) {
            const row = document.createElement("div");
            row.className = "document-row";

            const name = document.createElement("span");
            name.className = "document-name";
            name.textContent = filename;

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className = "delete-button";
            deleteButton.textContent = "Delete";

            deleteButton.addEventListener("click", () => {
                deleteDocument(filename);
            });

            row.appendChild(name);
            row.appendChild(deleteButton);

            documentList.appendChild(row);
        }

    } catch (error) {
        console.error("Could not load documents:", error);
        managementStatus.textContent =
            `Could not refresh documents: ${error.message}`;
        throw error;
    }
}

// Load document list when page opens
loadDocuments();


//
// Version 4.6 - Delete Document
//

async function deleteDocument(filename) {
    const confirmed = window.confirm(
        `Are you sure you want to delete "${filename}"?\n\n` +
        "This will permanently remove the PDF and its indexed chunks."
    );

    if (!confirmed) {
        return;
    }

    managementStatus.textContent = `Deleting ${filename}...`;

    // Disable delete buttons during deletion
    const deleteButtons = document.querySelectorAll(".delete-button");

    deleteButtons.forEach(button => {
        button.disabled = true;
    });

    try {
        const response = await fetch(
            `/documents/${encodeURIComponent(filename)}`,
            {
                method: "DELETE"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || `HTTP ${response.status}`
            );
        }

        managementStatus.textContent =
            `Successfully deleted ${data.filename} ` +
            `(${data.deleted_chunks} chunks removed).`;

        // Refresh document selection and management list
        await loadDocuments();

    } catch (error) {
        managementStatus.textContent =
            `Error: ${error.message}`;

    } finally {
        document.querySelectorAll(".delete-button").forEach(button => {
            button.disabled = false;
        });
    }
}


