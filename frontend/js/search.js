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

// INITIALIZE SEARCH PAGE
document.addEventListener("DOMContentLoaded", () => {
    const adminLink = document.getElementById("adminLink");
    if (currentUser.role !== "admin" && adminLink) {
        adminLink.style.display = "none";
    }

    // Check if query parameter is in URL
    const urlParams = new URLSearchParams(window.location.search);
    const queryParam = urlParams.get("q");
    if (queryParam) {
        document.getElementById("searchQuery").value = queryParam;
        performSearch(queryParam);
    }
});


// HANDLE FORM SUBMIT
function handleSearch(event) {
    event.preventDefault();
    const query = document.getElementById("searchQuery").value.trim();
    if (!query) return;

    // Update browser URL query param without reload
    const newUrl = `${window.location.pathname}?q=${encodeURIComponent(query)}`;
    window.history.pushState({ path: newUrl }, "", newUrl);

    performSearch(query);
}


// PERFORM SEARCH
async function performSearch(query) {
    const initialState = document.getElementById("initialState");
    const loadingState = document.getElementById("loadingState");
    const emptyState = document.getElementById("emptyState");
    const errorMessage = document.getElementById("errorMessage");
    const resultsList = document.getElementById("resultsList");
    const searchSummary = document.getElementById("searchSummary");
    const countBadge = document.getElementById("resultCountBadge");
    const searchButton = document.getElementById("searchButton");

    initialState.classList.add("hidden");
    emptyState.classList.add("hidden");
    errorMessage.classList.add("hidden");
    resultsList.innerHTML = "";

    loadingState.classList.remove("hidden");
    searchButton.disabled = true;
    searchButton.textContent = "Searching...";

    try {
        const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}`, {
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

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Search failed.");
        }

        loadingState.classList.add("hidden");
        searchButton.disabled = false;
        searchButton.textContent = "Search";

        const results = data.results || [];
        const total = data.total !== undefined ? data.total : results.length;

        searchSummary.textContent = `Found ${total} document${total === 1 ? "" : "s"} matching "${query}"`;
        countBadge.textContent = `${total} Result${total === 1 ? "" : "s"}`;
        countBadge.classList.remove("hidden");

        if (results.length === 0) {
            emptyState.classList.remove("hidden");
            return;
        }

        results.forEach(doc => {
            const card = createResultCard(doc);
            resultsList.appendChild(card);
        });

    } catch (error) {
        console.error("Search error:", error);
        loadingState.classList.add("hidden");
        searchButton.disabled = false;
        searchButton.textContent = "Search";

        errorMessage.textContent = error.message || "An error occurred while searching.";
        errorMessage.classList.remove("hidden");
        searchSummary.textContent = "Search could not be completed.";
    }
}


// CREATE RESULT CARD ELEMENT
function createResultCard(doc) {
    const card = document.createElement("div");
    card.className = "border border-slate-200 hover:border-blue-400 rounded-xl p-5 transition bg-white shadow-sm flex flex-col md:flex-row justify-between gap-4 items-start md:items-center";

    const leftCol = document.createElement("div");
    leftCol.className = "flex-1";

    // Title & Filename
    const titleLink = document.createElement("a");
    titleLink.href = `/static/pages/document_details.html?id=${encodeURIComponent(doc.id)}`;
    titleLink.className = "text-lg font-bold text-slate-800 hover:text-blue-600 transition inline-block";
    titleLink.textContent = doc.title || doc.filename || "Untitled Document";

    const filenameText = document.createElement("span");
    filenameText.className = "text-sm text-slate-400 ml-2 font-normal";
    filenameText.textContent = `(${doc.filename})`;

    const titleContainer = document.createElement("div");
    titleContainer.appendChild(titleLink);
    titleContainer.appendChild(filenameText);

    // Metadata details
    const metaInfo = document.createElement("div");
    metaInfo.className = "flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-500 mt-2";

    const divisionSpan = document.createElement("span");
    divisionSpan.innerHTML = `🏢 Division: <strong class="text-slate-700">${escapeHtml(doc.division || "-")}</strong>`;

    const dateSpan = document.createElement("span");
    const formattedDate = doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString("en-IN", {
        year: "numeric", month: "short", day: "numeric"
    }) : "-";
    dateSpan.innerHTML = `📅 Uploaded: <span class="text-slate-700">${formattedDate}</span>`;

    metaInfo.appendChild(divisionSpan);
    metaInfo.appendChild(dateSpan);

    // Matched_in Badges
    const badgeContainer = document.createElement("div");
    badgeContainer.className = "flex flex-wrap items-center gap-2 mt-3";

    const matchedIn = doc.matched_in || [];
    if (matchedIn.length > 0) {
        const matchLabel = document.createElement("span");
        matchLabel.className = "text-xs font-semibold text-slate-400 uppercase tracking-wider";
        matchLabel.textContent = "Matched in:";
        badgeContainer.appendChild(matchLabel);

        matchedIn.forEach(matchType => {
            const badge = document.createElement("span");
            badge.className = getBadgeClass(matchType);
            badge.textContent = getBadgeLabel(matchType);
            badgeContainer.appendChild(badge);
        });
    }

    leftCol.appendChild(titleContainer);
    leftCol.appendChild(metaInfo);
    leftCol.appendChild(badgeContainer);

    // Action buttons
    const rightCol = document.createElement("div");
    rightCol.className = "flex items-center gap-2 w-full md:w-auto justify-end";

    if (doc.has_access === false) {
        const lockBadge = document.createElement("span");
        lockBadge.className = "text-xs bg-amber-100 text-amber-800 font-semibold px-2.5 py-1 rounded-full border border-amber-300";
        lockBadge.textContent = "🔒 Cross-Division (Restricted)";
        badgeContainer.appendChild(lockBadge);

        const requestBtn = document.createElement("a");
        requestBtn.href = `/static/pages/access_requests.html?request_doc_id=${encodeURIComponent(doc.id)}`;
        requestBtn.className = "bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition inline-flex items-center gap-1.5";
        requestBtn.innerHTML = "<span>🔑</span> Request Access";
        rightCol.appendChild(requestBtn);
    } else {
        // View Details button
        const viewButton = document.createElement("a");
        viewButton.href = `/static/pages/document_details.html?id=${encodeURIComponent(doc.id)}`;
        viewButton.className = "bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-semibold px-4 py-2 rounded-lg transition text-center";
        viewButton.textContent = "View Details";

        // Download button
        const downloadButton = document.createElement("button");
        downloadButton.type = "button";
        downloadButton.className = "bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition";
        downloadButton.textContent = "Download";
        downloadButton.addEventListener("click", () => {
            downloadDocument(doc.id, doc.filename || "document");
        });

        rightCol.appendChild(viewButton);
        rightCol.appendChild(downloadButton);
    }

    card.appendChild(leftCol);
    card.appendChild(rightCol);

    return card;
}


// BADGE HELPERS
function getBadgeClass(matchType) {
    switch (matchType) {
        case "ocr_text":
            return "text-xs bg-emerald-100 text-emerald-800 font-medium px-2.5 py-1 rounded-full border border-emerald-300";
        case "metadata":
            return "text-xs bg-purple-100 text-purple-800 font-medium px-2.5 py-1 rounded-full border border-purple-300";
        case "title":
            return "text-xs bg-blue-100 text-blue-800 font-medium px-2.5 py-1 rounded-full border border-blue-300";
        case "filename":
            return "text-xs bg-indigo-100 text-indigo-800 font-medium px-2.5 py-1 rounded-full border border-indigo-300";
        default:
            return "text-xs bg-slate-100 text-slate-700 font-medium px-2.5 py-1 rounded-full border border-slate-300";
    }
}

function getBadgeLabel(matchType) {
    switch (matchType) {
        case "ocr_text":
            return "🔍 OCR Content";
        case "metadata":
            return "🏷️ Custom Metadata";
        case "title":
            return "📌 Document Title";
        case "filename":
            return "📁 Filename";
        default:
            return matchType;
    }
}


// DOWNLOAD DOCUMENT
async function downloadDocument(documentId, filename) {
    try {
        const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentId)}/download`, {
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


// CLEAR SEARCH
function clearSearch() {
    document.getElementById("searchQuery").value = "";
    document.getElementById("resultsList").innerHTML = "";
    document.getElementById("searchSummary").textContent = "Enter a search query above to begin.";
    document.getElementById("resultCountBadge").classList.add("hidden");
    document.getElementById("emptyState").classList.add("hidden");
    document.getElementById("errorMessage").classList.add("hidden");
    document.getElementById("initialState").classList.remove("hidden");

    window.history.pushState({}, "", window.location.pathname);
}


// ESCAPE HTML HELPER
function escapeHtml(string) {
    if (typeof string !== "string") return string;
    return string
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// LOGOUT
function logoutUser() {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");
    window.location.href = "/";
}
