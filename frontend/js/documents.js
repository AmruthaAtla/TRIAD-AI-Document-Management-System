const API_BASE_URL = "/api";

const token = sessionStorage.getItem("access_token");
const storedUser = sessionStorage.getItem("user");

if (!token || !storedUser) {
    window.location.href = "/";
}

let currentUser = {};

try {
    currentUser = JSON.parse(storedUser || "{}");
} catch (error) {
    sessionStorage.clear();
    window.location.href = "/";
}

let currentDocId = null;
let currentDocument = null;


// INITIALIZE PAGE
document.addEventListener("DOMContentLoaded", () => {
    const adminLink = document.getElementById("adminLink");
    if (currentUser.role !== "admin" && adminLink) {
        adminLink.style.display = "none";
    }

    const urlParams = new URLSearchParams(window.location.search);
    currentDocId = urlParams.get("id");

    if (!currentDocId) {
        showError("No document ID specified. Please select a document from the dashboard.");
        return;
    }

    loadDocumentDetails(currentDocId);
});


// LOAD DOCUMENT DETAILS
async function loadDocumentDetails(docId) {
    const loadingState = document.getElementById("loadingState");
    const errorState = document.getElementById("errorState");
    const accessDeniedState = document.getElementById("accessDeniedState");
    const detailsContainer = document.getElementById("documentDetailsContainer");

    loadingState.classList.remove("hidden");
    errorState.classList.add("hidden");
    accessDeniedState.classList.add("hidden");
    detailsContainer.classList.add("hidden");

    try {
        const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(docId)}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            sessionStorage.clear();
            window.location.href = "/";
            return;
        }

        if (response.status === 403) {
            loadingState.classList.add("hidden");
            accessDeniedState.classList.remove("hidden");
            return;
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to load document details.");
        }

        loadingState.classList.add("hidden");
        currentDocument = data.document;
        renderDocumentDetails(currentDocument);

    } catch (error) {
        console.error("Error loading document details:", error);
        showError(error.message);
    }
}


// RENDER DOCUMENT DETAILS
function renderDocumentDetails(doc) {
    const detailsContainer = document.getElementById("documentDetailsContainer");
    const divisionBadge = document.getElementById("divisionBadge");

    document.getElementById("docTitle").textContent = doc.title || doc.filename || "Untitled";
    document.getElementById("docFilename").textContent = doc.filename || "-";
    document.getElementById("docDivision").textContent = doc.division || "-";

    divisionBadge.textContent = doc.division || "Division";
    divisionBadge.classList.remove("hidden");

    const formattedDate = doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString("en-IN", {
        year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
    }) : "-";
    document.getElementById("docUploadedAt").textContent = formattedDate;

    document.getElementById("docUploadedBy").textContent = doc.uploaded_by || "-";
    document.getElementById("docId").textContent = doc.id || currentDocId;

    // Wire Download Button
    const downloadBtn = document.getElementById("downloadBtn");
    downloadBtn.onclick = () => downloadCurrentDocument();

    // Check Delete Permissions (Owner or Admin)
    const deleteBtn = document.getElementById("deleteBtn");
    const isOwner = currentUser.id && doc.uploaded_by && String(currentUser.id) === String(doc.uploaded_by);
    const isAdmin = currentUser.role === "admin";

    if (isOwner || isAdmin) {
        deleteBtn.classList.remove("hidden");
        deleteBtn.onclick = () => openDeleteModal();
    } else {
        deleteBtn.classList.add("hidden");
    }

    // Render Custom Metadata
    renderCustomMetadata(doc.metadata || {});

    // Render OCR Text
    const ocrBox = document.getElementById("ocrTextContent");
    if (doc.ocr_text && doc.ocr_text.trim()) {
        ocrBox.textContent = doc.ocr_text;
    } else {
        ocrBox.textContent = "No OCR text extracted for this document.";
    }

    detailsContainer.classList.remove("hidden");
}


// RENDER METADATA KEY-VALUE PAIRS
function renderCustomMetadata(metadata) {
    const container = document.getElementById("customMetadataContainer");
    const noMetadataMsg = document.getElementById("noMetadataMsg");

    container.innerHTML = "";
    const keys = Object.keys(metadata);

    if (keys.length === 0) {
        noMetadataMsg.classList.remove("hidden");
        return;
    }

    noMetadataMsg.classList.add("hidden");

    keys.forEach(key => {
        const item = document.createElement("div");
        item.className = "border border-slate-200 rounded-lg p-3 bg-slate-50";

        const label = document.createElement("div");
        label.className = "text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1";
        label.textContent = key;

        const val = document.createElement("div");
        val.className = "text-sm font-bold text-slate-800 break-words";
        const rawVal = metadata[key];
        val.textContent = typeof rawVal === "object" ? JSON.stringify(rawVal) : String(rawVal);

        item.appendChild(label);
        item.appendChild(val);
        container.appendChild(item);
    });
}


// DOWNLOAD CURRENT DOCUMENT
async function downloadCurrentDocument() {
    if (!currentDocId) return;

    try {
        const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(currentDocId)}/download`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            sessionStorage.clear();
            window.location.href = "/";
            return;
        }

        if (!response.ok) {
            const result = await response.json().catch(() => ({}));
            throw new Error(result.error || "Download failed.");
        }

        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);

        const filename = currentDocument ? (currentDocument.filename || "document") : "document";

        const link = document.createElement("a");
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();

        URL.revokeObjectURL(downloadUrl);

    } catch (error) {
        console.error("Download error:", error);
        alert(error.message || "Failed to download document.");
    }
}


// SUBMIT ACCESS REQUEST
async function submitAccessRequest(event) {
    event.preventDefault();

    const reasonInput = document.getElementById("accessReason");
    const messageEl = document.getElementById("accessRequestMessage");
    const submitBtn = document.getElementById("submitRequestBtn");
    const reason = reasonInput.value.trim();

    if (!reason) {
        messageEl.className = "text-sm p-3 rounded-lg bg-red-100 text-red-700";
        messageEl.textContent = "Please provide a reason for the access request.";
        messageEl.classList.remove("hidden");
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting...";

    try {
        const response = await fetch(`${API_BASE_URL}/access/request`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                document_id: currentDocId,
                reason: reason
            })
        });

        const data = await response.json();

        if (response.status === 401) {
            sessionStorage.clear();
            window.location.href = "/";
            return;
        }

        if (!response.ok) {
            throw new Error(data.error || "Failed to submit access request.");
        }

        messageEl.className = "text-sm p-3 rounded-lg bg-green-100 text-green-800 font-medium";
        messageEl.textContent = "Access request submitted successfully! Division administrators have been notified.";
        messageEl.classList.remove("hidden");

        reasonInput.disabled = true;
        submitBtn.classList.add("hidden");

    } catch (error) {
        console.error("Access request error:", error);
        messageEl.className = "text-sm p-3 rounded-lg bg-red-100 text-red-700";
        messageEl.textContent = error.message;
        messageEl.classList.remove("hidden");
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit Access Request";
    }
}


// DELETE MODAL CONTROLS
function openDeleteModal() {
    document.getElementById("deleteModal").classList.remove("hidden");
}

function closeDeleteModal() {
    document.getElementById("deleteModal").classList.add("hidden");
}

async function executeDocumentDelete() {
    const confirmBtn = document.getElementById("confirmDeleteBtn");
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Deleting...";

    try {
        const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(currentDocId)}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            sessionStorage.clear();
            window.location.href = "/";
            return;
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to delete document.");
        }

        alert("Document deleted successfully.");
        window.location.href = "/static/pages/dashboard.html";

    } catch (error) {
        console.error("Delete error:", error);
        alert(error.message || "Failed to delete document.");
        confirmBtn.disabled = false;
        confirmBtn.textContent = "Confirm Delete";
        closeDeleteModal();
    }
}


// COPY OCR TEXT
function copyOcrText() {
    const text = document.getElementById("ocrTextContent").textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.getElementById("copyOcrBtn");
        const originalText = btn.textContent;
        btn.textContent = "✅ Copied!";
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error("Copy failed:", err);
    });
}


// SHOW ERROR
function showError(msg) {
    document.getElementById("loadingState").classList.add("hidden");
    document.getElementById("documentDetailsContainer").classList.add("hidden");
    document.getElementById("accessDeniedState").classList.add("hidden");

    const errorState = document.getElementById("errorState");
    document.getElementById("errorMessage").textContent = msg;
    errorState.classList.remove("hidden");
}


// LOGOUT
function logoutUser() {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");
    window.location.href = "/";
}
