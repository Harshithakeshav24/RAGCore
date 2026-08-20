const API_BASE_URL = "http://127.0.0.1:8000";

console.log("RAGCore frontend loaded");
console.log("API:", API_BASE_URL);


// ============================================================
// DOM ELEMENTS
// ============================================================

const uploadDropzone =
    document.getElementById("uploadDropzone");

const fileInput =
    document.getElementById("fileInput");

const uploadStatus =
    document.getElementById("uploadStatus");

const documentsList =
    document.getElementById("documentsList");

const connectionStatus =
    document.getElementById("connectionStatus");

const questionInput =
    document.getElementById("questionInput");

const askButton =
    document.getElementById("askButton");

const welcomeSection =
    document.getElementById("welcomeSection");

const answerSection =
    document.getElementById("answerSection");

const answerContent =
    document.getElementById("answerContent");

const answerStatus =
    document.getElementById("answerStatus");

const answerLoading =
    document.getElementById("answerLoading");

const sourcesSection =
    document.getElementById("sourcesSection");

const sourcesList =
    document.getElementById("sourcesList");

const characterCount =
    document.getElementById("characterCount");


// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        console.log(
            "DOM loaded"
        );

        checkAPIConnection();

        loadDocuments();

        updateCharacterCount();

    }
);


// ============================================================
// API CONNECTION
// ============================================================

async function checkAPIConnection() {

    console.log(
        "Checking API health..."
    );

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/health`
            );


        console.log(
            "Health response:",
            response.status
        );


        if (!response.ok) {

            throw new Error(
                `Health request failed: ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "Health data:",
            data
        );


        connectionStatus.textContent =
            "Connected";


        connectionStatus.style.color =
            "#56c596";


    } catch (error) {

        console.error(
            "Health check failed:",
            error
        );


        connectionStatus.textContent =
            "Offline";


        connectionStatus.style.color =
            "#e06c75";

    }

}


// ============================================================
// DOCUMENT LIST
// ============================================================

async function loadDocuments() {

    console.log(
        "Loading documents..."
    );


    const url =
        `${API_BASE_URL}/documents`;


    console.log(
        "Documents URL:",
        url
    );


    try {

        const response =
            await fetch(url);


        console.log(
            "Documents response status:",
            response.status
        );


        console.log(
            "Documents response OK:",
            response.ok
        );


        if (!response.ok) {

            const errorText =
                await response.text();


            console.error(
                "Documents API error:",
                errorText
            );


            throw new Error(
                `Documents request failed: ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "Documents data:",
            data
        );


        renderDocuments(
            data.documents
        );


    } catch (error) {

        console.error(
            "LOAD DOCUMENTS FAILED:",
            error
        );


        documentsList.innerHTML = `
            <div class="empty-documents">
                Unable to load documents.
            </div>
        `;

    }

}


// ============================================================
// RENDER DOCUMENTS
// ============================================================

function renderDocuments(
    documents
) {

    console.log(
        "Rendering documents:",
        documents
    );


    if (
        !documents ||
        documents.length === 0
    ) {

        documentsList.innerHTML = `
            <div class="empty-documents">
                No documents loaded.
            </div>
        `;

        return;

    }


    documentsList.innerHTML =
        "";


    documents.forEach(
        document => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "document-card";


            const size =
                formatFileSize(
                    document.size_bytes
                );


            card.innerHTML = `

                <div class="document-icon">
                    📄
                </div>

                <div class="document-info">

                    <div
                        class="document-name"
                        title="${escapeHTML(
                            document.filename
                        )}"
                    >
                        ${escapeHTML(
                            document.filename
                        )}
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
                card.querySelector(
                    ".delete-button"
                );


            deleteButton.addEventListener(
                "click",
                () => {

                    deleteDocument(
                        document.document_id,
                        document.filename
                    );

                }
            );


            documentsList.appendChild(
                card
            );

        }
    );

}


// ============================================================
// FILE UPLOAD
// ============================================================

uploadDropzone.addEventListener(
    "click",
    () => {

        fileInput.click();

    }
);


fileInput.addEventListener(
    "change",
    async () => {

        const file =
            fileInput.files[0];


        if (!file) {

            return;

        }


        await uploadFile(
            file
        );


        fileInput.value =
            "";

    }
);


uploadDropzone.addEventListener(
    "dragover",
    event => {

        event.preventDefault();

        uploadDropzone.classList.add(
            "drag-over"
        );

    }
);


uploadDropzone.addEventListener(
    "dragleave",
    event => {

        event.preventDefault();

        uploadDropzone.classList.remove(
            "drag-over"
        );

    }
);


uploadDropzone.addEventListener(
    "drop",
    async event => {

        event.preventDefault();

        uploadDropzone.classList.remove(
            "drag-over"
        );


        const file =
            event.dataTransfer.files[0];


        if (!file) {

            return;

        }


        await uploadFile(
            file
        );

    }
);


async function uploadFile(
    file
) {

    if (
        !file.name
            .toLowerCase()
            .endsWith(".pdf")
    ) {

        showUploadStatus(
            "Please select a PDF file.",
            true
        );

        return;

    }


    uploadDropzone.classList.add(
        "uploading"
    );


    showUploadStatus(
        "Uploading and processing..."
    );


    try {

        const formData =
            new FormData();


        formData.append(
            "file",
            file
        );


        const response =
            await fetch(
                `${API_BASE_URL}/upload`,
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


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

        console.error(
            "UPLOAD FAILED:",
            error
        );


        showUploadStatus(
            error.message,
            true
        );

    } finally {

        uploadDropzone.classList.remove(
            "uploading"
        );

    }

}


// ============================================================
// DELETE DOCUMENT
// ============================================================

async function deleteDocument(
    documentId,
    filename
) {

    const confirmed =
        confirm(
            `Delete "${filename}"?\n\nThis will also remove its searchable data from RAGCore.`
        );


    if (!confirmed) {

        return;

    }


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/documents/${documentId}`,
                {
                    method: "DELETE"
                }
            );


        const data =
            await response.json();


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

        console.error(
            "DELETE FAILED:",
            error
        );


        showUploadStatus(
            error.message,
            true
        );

    }

}


// ============================================================
// QUESTION
// ============================================================

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


questionInput.addEventListener(
    "input",
    updateCharacterCount
);


function updateCharacterCount() {

    const length =
        questionInput.value.length;


    characterCount.textContent =
        `${length} / 2000`;

}


// ============================================================
// ASK QUESTION
// ============================================================

async function askQuestion() {

    const question =
        questionInput.value.trim();


    if (!question) {

        questionInput.focus();

        return;

    }


    askButton.disabled =
        true;


    askButton.innerHTML = `
        <span>Thinking...</span>
    `;


    answerSection.hidden =
        false;


    welcomeSection.hidden =
        true;


    sourcesSection.hidden =
        true;


    answerContent.textContent =
        "";


    answerContent.classList.remove(
        "error"
    );


    answerLoading.hidden =
        false;


    answerStatus.textContent =
        "Retrieving relevant information";


    try {

        const response =
            await fetch(
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


        const data =
            await response.json();


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

        console.error(
            "QUERY FAILED:",
            error
        );


        showAnswerError(
            error.message
        );

    } finally {

        answerLoading.hidden =
            true;


        askButton.disabled =
            false;


        askButton.innerHTML = `
            <span>Ask</span>
            <span class="ask-arrow">→</span>
        `;

    }

}


// ============================================================
// ERROR DISPLAY
// ============================================================

function showAnswerError(
    message
) {

    answerSection.hidden =
        false;


    welcomeSection.hidden =
        true;


    answerLoading.hidden =
        true;


    sourcesSection.hidden =
        true;


    answerContent.classList.add(
        "error"
    );


    answerContent.textContent =
        `Unable to generate an answer: ${message}`;


    answerStatus.textContent =
        "Request failed";

}


// ============================================================
// SOURCES
// ============================================================

function renderSources(
    sources
) {

    if (
        !sources ||
        sources.length === 0
    ) {

        sourcesSection.hidden =
            true;

        return;

    }


    sourcesList.innerHTML =
        "";


    sources.forEach(
        source => {

            const sourceCard =
                document.createElement(
                    "div"
                );


            sourceCard.className =
                "source-card";


            sourceCard.innerHTML = `
                📄
                <span>
                    ${escapeHTML(
                        source.source
                    )}
                    — Page ${source.page}
                </span>
            `;


            sourcesList.appendChild(
                sourceCard
            );

        }
    );


    sourcesSection.hidden =
        false;

}


// ============================================================
// UPLOAD STATUS
// ============================================================

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


    setTimeout(
        () => {

            uploadStatus.textContent =
                "";

        },
        5000
    );

}


// ============================================================
// FILE SIZE
// ============================================================

function formatFileSize(
    bytes
) {

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


// ============================================================
// HTML SAFETY
// ============================================================

function escapeHTML(
    value
) {

    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}
