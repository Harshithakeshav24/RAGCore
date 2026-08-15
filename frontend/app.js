const API_BASE_URL = "http://127.0.0.1:8000";


// =========================
// DOM ELEMENTS
// =========================

const uploadButton = document.getElementById("uploadButton");
const fileInput = document.getElementById("fileInput");
const uploadStatus = document.getElementById("uploadStatus");

const documentsList = document.getElementById("documentsList");
const connectionStatus = document.getElementById("connectionStatus");

const questionInput = document.getElementById("questionInput");
const askButton = document.getElementById("askButton");

const welcomeSection = document.getElementById("welcomeSection");
const answerSection = document.getElementById("answerSection");

const answerContent = document.getElementById("answerContent");
const answerStatus = document.getElementById("answerStatus");

const sourcesSection = document.getElementById("sourcesSection");
const sourcesList = document.getElementById("sourcesList");


// =========================
// INITIALIZATION
// =========================

document.addEventListener("DOMContentLoaded", () => {

    checkAPIConnection();

    loadDocuments();

});


// =========================
// API CONNECTION
// =========================

async function checkAPIConnection() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/health`
        );

        if (!response.ok) {
            throw new Error("API unavailable");
        }

        connectionStatus.textContent = "Connected";

        connectionStatus.style.color = "#56c596";

    } catch (error) {

        connectionStatus.textContent = "Offline";

        connectionStatus.style.color = "#e06c75";

    }

}


// =========================
// DOCUMENT LIST
// =========================

async function loadDocuments() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/documents`
        );

        if (!response.ok) {
            throw new Error("Failed to load documents");
        }

        const data = await response.json();

        renderDocuments(data.documents);

    } catch (error) {

        documentsList.innerHTML = `
            <div class="empty-documents">
                Unable to load documents.
            </div>
        `;

    }

}


function renderDocuments(documents) {

    if (!documents || documents.length === 0) {

        documentsList.innerHTML = `
            <div class="empty-documents">
                No documents loaded.
            </div>
        `;

        return;

    }


    documentsList.innerHTML = "";


    documents.forEach(document => {

        const card = document.createElement("div");

        card.className = "document-card";


        const size = formatFileSize(
            document.size_bytes
        );


        card.innerHTML = `

            <div class="document-icon">
                📄
            </div>

            <div class="document-info">

                <div
                    class="document-name"
                    title="${escapeHTML(document.filename)}"
                >
                    ${escapeHTML(document.filename)}
                </div>

                <div class="document-size">
                    ${size}
                </div>

            </div>

            <button
                class="delete-button"
                title="Delete document"
            >
                🗑
            </button>

        `;


        const deleteButton =
            card.querySelector(".delete-button");


        deleteButton.addEventListener(
            "click",
            () => deleteDocument(
                document.document_id,
                document.filename
            )
        );


        documentsList.appendChild(card);

    });

}


// =========================
// UPLOAD DOCUMENT
// =========================

uploadButton.addEventListener(
    "click",
    () => {

        fileInput.click();

    }
);


fileInput.addEventListener(
    "change",
    async () => {

        const file = fileInput.files[0];

        if (!file) {
            return;
        }


        if (!file.name.toLowerCase().endsWith(".pdf")) {

            showUploadStatus(
                "Please select a PDF file.",
                true
            );

            fileInput.value = "";

            return;

        }


        uploadButton.disabled = true;

        uploadStatus.textContent =
            "Uploading and processing...";


        try {

            const formData = new FormData();

            formData.append(
                "file",
                file
            );


            const response = await fetch(
                `${API_BASE_URL}/upload`,
                {
                    method: "POST",
                    body: formData
                }
            );


            const data = await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Upload failed."
                );

            }


            showUploadStatus(
                `${file.name} uploaded successfully.`
            );


            await loadDocuments();


        } catch (error) {

            showUploadStatus(
                error.message,
                true
            );

        } finally {

            uploadButton.disabled = false;

            fileInput.value = "";

        }

    }
);


// =========================
// DELETE DOCUMENT
// =========================

async function deleteDocument(
    documentId,
    filename
) {

    const confirmed = confirm(
        `Delete "${filename}"?\n\nThis will also remove its searchable data from RAGCore.`
    );


    if (!confirmed) {
        return;
    }


    try {

        const response = await fetch(
            `${API_BASE_URL}/documents/${documentId}`,
            {
                method: "DELETE"
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to delete document."
            );

        }


        await loadDocuments();


        showUploadStatus(
            `${filename} deleted successfully.`
        );


    } catch (error) {

        showUploadStatus(
            error.message,
            true
        );

    }

}


// =========================
// ASK QUESTION
// =========================

askButton.addEventListener(
    "click",
    askQuestion
);


questionInput.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            askQuestion();

        }

    }
);


async function askQuestion() {

    const question =
        questionInput.value.trim();


    if (!question) {

        questionInput.focus();

        return;

    }


    askButton.disabled = true;

    askButton.innerHTML =
        "Thinking...";


    answerSection.hidden = false;

    welcomeSection.hidden = true;

    sourcesSection.hidden = true;


    answerContent.textContent =
        "Searching your documents...";


    answerStatus.textContent =
        "Retrieving relevant information";


    try {

        const response = await fetch(
            `${API_BASE_URL}/query`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    question: question
                })

            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Question failed."
            );

        }


        answerContent.textContent =
            data.answer ||
            "No answer was returned.";


        answerStatus.textContent =
            "Grounded response";


        renderSources(
            data.sources
        );


    } catch (error) {

        answerContent.textContent =
            `Unable to generate an answer: ${error.message}`;


        answerStatus.textContent =
            "Request failed";

    } finally {

        askButton.disabled = false;

        askButton.innerHTML =
            `Ask <span>→</span>`;

    }

}


// =========================
// SOURCES
// =========================

function renderSources(sources) {

    if (
        !sources ||
        sources.length === 0
    ) {

        sourcesSection.hidden = true;

        return;

    }


    sourcesList.innerHTML = "";


    sources.forEach(source => {

        const sourceCard =
            document.createElement("div");


        sourceCard.className =
            "source-card";


        sourceCard.innerHTML = `
            📄
            <span>
                ${escapeHTML(source.source)}
                — Page ${source.page}
            </span>
        `;


        sourcesList.appendChild(
            sourceCard
        );

    });


    sourcesSection.hidden = false;

}


// =========================
// HELPERS
// =========================

function showUploadStatus(
    message,
    isError = false
) {

    uploadStatus.textContent =
        message;

    uploadStatus.style.color =
        isError
            ? "#e06c75"
            : "#56c596";


    setTimeout(() => {

        uploadStatus.textContent = "";

    }, 5000);

}


function formatFileSize(bytes) {

    if (!bytes) {
        return "0 KB";
    }


    const kilobytes =
        bytes / 1024;


    if (kilobytes < 1024) {

        return `${kilobytes.toFixed(1)} KB`;

    }


    const megabytes =
        kilobytes / 1024;


    return `${megabytes.toFixed(1)} MB`;

}


function escapeHTML(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}
