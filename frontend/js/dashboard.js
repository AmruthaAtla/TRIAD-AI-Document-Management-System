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

let allDocuments = [];
let filteredDocuments = [];
let currentPage = 1;
const pageSize = 10;
let isViewAll = false;


// DISPLAY USER INFORMATION
function displayUserInfo() {
    document.getElementById("userName").textContent =
        currentUser.name || "User";

    document.getElementById("userDivision").textContent =
        currentUser.division || "No division assigned";

    document.getElementById("divisionCard").textContent =
        currentUser.division || "-";

    document.getElementById("userRole").textContent =
        currentUser.role || "User";

    const adminLink = document.getElementById("adminLink");

    if (currentUser.role !== "admin" && adminLink) {
        adminLink.style.display = "none";
    }
}


// LOAD DOCUMENTS
async function loadDocuments() {
    const loadingMessage = document.getElementById("loadingMessage");
    const errorMessage = document.getElementById("errorMessage");
    const emptyMessage = document.getElementById("emptyMessage");
    const tableBody = document.getElementById("documentTableBody");

    loadingMessage.textContent = "Loading documents...";
    loadingMessage.style.display = "block";

    errorMessage.classList.add("hidden");
    emptyMessage.classList.add("hidden");
    tableBody.innerHTML = "";

    try {
        const response = await fetch(`${API_BASE_URL}/documents`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const result = await response.json();

        if (response.status === 401) {
            sessionStorage.clear();
            window.location.href = "/";
            return;
        }

        if (!response.ok) {
            throw new Error(result.error || "Unable to load documents.");
        }

        const documents = Array.isArray(result)
            ? result
            : (result.documents || []);

        document.getElementById("totalDocuments").textContent =
            documents.length;

        loadingMessage.style.display = "none";

        documents.sort((a, b) => {
            const dateA = new Date(
                a.uploaded_at || a.created_at || a.createdAt || 0
            );

            const dateB = new Date(
                b.uploaded_at || b.created_at || b.createdAt || 0
            );

            return dateB - dateA;
        });

        allDocuments = documents;
        filteredDocuments = [...allDocuments];
        currentPage = 1;

        const filterInput = document.getElementById("tableFilterInput");
        if (filterInput && filterInput.value.trim()) {
            filterDashboardTable();
        } else {
            renderTable();
        }

    } catch (error) {
        console.error("Dashboard error:", error);

        loadingMessage.style.display = "none";
        errorMessage.textContent = error.message;
        errorMessage.classList.remove("hidden");
    }
}


// RENDER TABLE WITH PAGINATION
function renderTable() {
    const tableBody = document.getElementById("documentTableBody");
    const emptyMessage = document.getElementById("emptyMessage");
    const paginationContainer = document.getElementById("paginationContainer");
    const paginationInfo = document.getElementById("paginationInfo");
    const currentPageIndicator = document.getElementById("currentPageIndicator");
    const prevPageBtn = document.getElementById("prevPageBtn");
    const nextPageBtn = document.getElementById("nextPageBtn");

    tableBody.innerHTML = "";

    if (filteredDocuments.length === 0) {
        emptyMessage.classList.remove("hidden");
        if (paginationContainer) paginationContainer.classList.add("hidden");
        return;
    }

    emptyMessage.classList.add("hidden");
    if (paginationContainer) paginationContainer.classList.remove("hidden");

    let displayedDocs = [];
    let startIdx = 0;
    let endIdx = filteredDocuments.length;

    if (isViewAll) {
        displayedDocs = filteredDocuments;
        if (paginationInfo) {
            paginationInfo.textContent = `Showing all ${filteredDocuments.length} documents`;
        }
        if (currentPageIndicator) currentPageIndicator.textContent = "All";
        if (prevPageBtn) prevPageBtn.disabled = true;
        if (nextPageBtn) nextPageBtn.disabled = true;
    } else {
        const totalPages = Math.ceil(filteredDocuments.length / pageSize) || 1;
        if (currentPage > totalPages) currentPage = totalPages;
        if (currentPage < 1) currentPage = 1;

        startIdx = (currentPage - 1) * pageSize;
        endIdx = Math.min(startIdx + pageSize, filteredDocuments.length);
        displayedDocs = filteredDocuments.slice(startIdx, endIdx);

        if (paginationInfo) {
            paginationInfo.textContent = `Showing ${startIdx + 1} to ${endIdx} of ${filteredDocuments.length} documents`;
        }
        if (currentPageIndicator) {
            currentPageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;
        }
        if (prevPageBtn) prevPageBtn.disabled = currentPage <= 1;
        if (nextPageBtn) nextPageBtn.disabled = currentPage >= totalPages;
    }

    displayedDocs.forEach(doc => {
        const row = document.createElement("tr");
        row.className = "border-b hover:bg-slate-50 transition";

        const title = doc.title || doc.filename || "Untitled";
        const division = doc.division || "-";

        const uploadDate =
            doc.uploaded_at ||
            doc.created_at ||
            doc.createdAt;

        const formattedDate = uploadDate
            ? new Date(uploadDate).toLocaleDateString("en-IN")
            : "-";

        const documentId = doc._id || doc.id;

        const nameCell = document.createElement("td");
        nameCell.className = "py-4 px-3 font-medium text-slate-800";

        if (documentId) {
            const titleLink = document.createElement("a");
            titleLink.href = `/static/pages/document_details.html?id=${encodeURIComponent(documentId)}`;
            titleLink.className = "hover:text-blue-600 hover:underline text-slate-800 font-semibold";
            titleLink.textContent = title;
            nameCell.appendChild(titleLink);
        } else {
            nameCell.textContent = title;
        }

        const divisionCell = document.createElement("td");
        divisionCell.className = "py-4 px-3 text-slate-600";
        divisionCell.textContent = division;

        const dateCell = document.createElement("td");
        dateCell.className = "py-4 px-3 text-slate-600";
        dateCell.textContent = formattedDate;

        const actionCell = document.createElement("td");
        actionCell.className = "py-4 px-3 whitespace-nowrap";

        if (documentId) {
            const viewLink = document.createElement("a");
            viewLink.href = `/static/pages/document_details.html?id=${encodeURIComponent(documentId)}`;
            viewLink.className = "text-slate-600 hover:text-slate-900 font-medium mr-4 text-sm inline-block";
            viewLink.textContent = "Details";

            const downloadButton = document.createElement("button");
            downloadButton.textContent = "Download";
            downloadButton.className = "text-blue-600 hover:text-blue-800 font-medium text-sm";
            downloadButton.addEventListener("click", () => {
                downloadDocument(documentId, doc.filename || "document");
            });

            actionCell.appendChild(viewLink);
            actionCell.appendChild(downloadButton);

            // Document deletion for owner or admin
            const isOwner = currentUser.id && doc.uploaded_by && String(currentUser.id) === String(doc.uploaded_by);
            const isAdmin = currentUser.role === "admin";
            if (isOwner || isAdmin) {
                const deleteButton = document.createElement("button");
                deleteButton.textContent = "Delete";
                deleteButton.className = "text-red-600 hover:text-red-800 font-medium text-sm ml-4";
                deleteButton.addEventListener("click", () => {
                    deleteDocumentFromDashboard(documentId, title);
                });
                actionCell.appendChild(deleteButton);
            }

        } else {
            actionCell.textContent = "-";
        }

        row.appendChild(nameCell);
        row.appendChild(divisionCell);
        row.appendChild(dateCell);
        row.appendChild(actionCell);

        tableBody.appendChild(row);
    });
}


// FILTER TABLE
function filterDashboardTable() {
    const query = document.getElementById("tableFilterInput").value.trim().toLowerCase();

    if (!query) {
        filteredDocuments = [...allDocuments];
    } else {
        filteredDocuments = allDocuments.filter(doc => {
            const title = (doc.title || "").toLowerCase();
            const filename = (doc.filename || "").toLowerCase();
            const division = (doc.division || "").toLowerCase();
            const metaStr = JSON.stringify(doc.metadata || {}).toLowerCase();

            return title.includes(query) ||
                   filename.includes(query) ||
                   division.includes(query) ||
                   metaStr.includes(query);
        });
    }

    currentPage = 1;
    renderTable();
}


// TOGGLE VIEW ALL
function toggleViewAll() {
    isViewAll = !isViewAll;
    const btn = document.getElementById("toggleViewAllBtn");

    if (btn) {
        btn.textContent = isViewAll ? "Show Paginated" : "View All Documents";
    }

    currentPage = 1;
    renderTable();
}


// CHANGE PAGE
function changePage(delta) {
    currentPage += delta;
    renderTable();
}


// DELETE DOCUMENT FROM DASHBOARD
async function deleteDocumentFromDashboard(documentId, title) {
    if (!confirm(`Are you sure you want to delete "${title}"? This action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`, {
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
        await loadDocuments();

    } catch (err) {
        console.error("Delete error:", err);
        alert(err.message || "Failed to delete document.");
    }
}


// DOWNLOAD DOCUMENT
async function downloadDocument(documentId, filename = "document") {
    try {
        const response = await fetch(
            `${API_BASE_URL}/documents/${encodeURIComponent(documentId)}/download`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

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
        alert(error.message);
    }
}


// LOGOUT
function logoutUser() {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");

    window.location.href = "/";
}


// INITIALIZE DASHBOARD
displayUserInfo();
loadDocuments();
