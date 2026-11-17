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

let currentTab = "incoming";


// INITIALIZE PAGE
document.addEventListener("DOMContentLoaded", () => {
    const adminLink = document.getElementById("adminLink");
    if (currentUser.role !== "admin" && adminLink) {
        adminLink.style.display = "none";
    }

    // Check if docId was passed via URL to prefill request modal
    const urlParams = new URLSearchParams(window.location.search);
    const prefillDocId = urlParams.get("request_doc_id");
    if (prefillDocId) {
        openNewRequestModal();
        document.getElementById("modalDocId").value = prefillDocId;
    }

    loadRequests();
});


// TAB SWITCHING
function switchTab(tab) {
    currentTab = tab;

    const tabIncoming = document.getElementById("tabIncoming");
    const tabOutgoing = document.getElementById("tabOutgoing");
    const incomingSection = document.getElementById("incomingSection");
    const outgoingSection = document.getElementById("outgoingSection");

    if (tab === "incoming") {
        tabIncoming.className = "pb-3 px-4 font-bold border-b-2 border-blue-600 text-blue-600 transition flex items-center gap-2";
        tabOutgoing.className = "pb-3 px-4 font-bold border-b-2 border-transparent text-slate-500 hover:text-slate-800 transition flex items-center gap-2";
        incomingSection.classList.remove("hidden");
        outgoingSection.classList.add("hidden");
    } else {
        tabOutgoing.className = "pb-3 px-4 font-bold border-b-2 border-blue-600 text-blue-600 transition flex items-center gap-2";
        tabIncoming.className = "pb-3 px-4 font-bold border-b-2 border-transparent text-slate-500 hover:text-slate-800 transition flex items-center gap-2";
        outgoingSection.classList.remove("hidden");
        incomingSection.classList.add("hidden");
    }

    loadRequests();
}


// LOAD REQUESTS
async function loadRequests() {
    const loadingEl = document.getElementById("loadingRequests");
    const errorEl = document.getElementById("requestsError");

    loadingEl.classList.remove("hidden");
    errorEl.classList.add("hidden");

    try {
        if (currentTab === "incoming") {
            await loadIncomingRequests();
        } else {
            await loadOutgoingRequests();
        }
    } catch (err) {
        console.error("Error loading requests:", err);
        errorEl.textContent = err.message || "Failed to load requests.";
        errorEl.classList.remove("hidden");
    } finally {
        loadingEl.classList.add("hidden");
    }
}


// LOAD INCOMING REQUESTS
async function loadIncomingRequests() {
    const listEl = document.getElementById("incomingList");
    const emptyEl = document.getElementById("incomingEmpty");
    const badgeEl = document.getElementById("incomingBadge");
    const sectionEl = document.getElementById("incomingSection");

    listEl.innerHTML = "";
    emptyEl.classList.add("hidden");

    const response = await fetch(`${API_BASE_URL}/access/requests?type=incoming`, {
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
        throw new Error(data.error || "Failed to load incoming requests.");
    }

    const requests = data.requests || [];
    badgeEl.textContent = requests.length;
    badgeEl.classList.remove("hidden");

    if (requests.length === 0) {
        emptyEl.classList.remove("hidden");
        sectionEl.classList.remove("hidden");
        return;
    }

    requests.forEach(req => {
        const card = createIncomingRequestCard(req);
        listEl.appendChild(card);
    });

    sectionEl.classList.remove("hidden");
}


// CREATE INCOMING REQUEST CARD
function createIncomingRequestCard(req) {
    const card = document.createElement("div");
    card.id = `req_card_${req.request_id}`;
    card.className = "bg-white rounded-xl shadow-sm p-6 border border-slate-200 transition hover:border-blue-300";

    const header = document.createElement("div");
    header.className = "flex flex-col sm:flex-row justify-between sm:items-start gap-4 mb-4 pb-4 border-b border-slate-100";

    const titleDiv = document.createElement("div");
    const title = document.createElement("h4");
    title.className = "text-xl font-bold text-slate-800 break-words";
    title.textContent = req.document_title || "Untitled Document";

    const docIdSpan = document.createElement("p");
    docIdSpan.className = "text-xs font-mono text-slate-400 mt-1";
    docIdSpan.textContent = `Document ID: ${req.document_id}`;

    titleDiv.appendChild(title);
    titleDiv.appendChild(docIdSpan);

    const requesterBadge = document.createElement("div");
    requesterBadge.className = "text-sm bg-blue-50 text-blue-800 px-3 py-1.5 rounded-lg border border-blue-200";
    requesterBadge.innerHTML = `Requested by: <strong>${escapeHtml(req.requester_name || "User")}</strong> (${escapeHtml(req.requester_division || "Division")})`;

    header.appendChild(titleDiv);
    header.appendChild(requesterBadge);

    // Reason block
    const reasonDiv = document.createElement("div");
    reasonDiv.className = "bg-slate-50 rounded-lg p-4 mb-4 text-sm";
    reasonDiv.innerHTML = `
        <span class="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Stated Reason:</span>
        <p class="text-slate-700 italic">"${escapeHtml(req.reason || "No reason provided.")}"</p>
    `;

    // Footer with timestamp and action buttons
    const footer = document.createElement("div");
    footer.className = "flex flex-col sm:flex-row justify-between sm:items-center gap-4 text-sm";

    const formattedDate = req.requested_at ? new Date(req.requested_at).toLocaleDateString("en-IN", {
        year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
    }) : "-";
    const dateSpan = document.createElement("span");
    dateSpan.className = "text-slate-400";
    dateSpan.textContent = `Received: ${formattedDate}`;

    const buttonGroup = document.createElement("div");
    buttonGroup.className = "flex items-center gap-3";

    const approveBtn = document.createElement("button");
    approveBtn.className = "bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded-lg transition text-sm inline-flex items-center gap-1.5";
    approveBtn.innerHTML = `<span>✓</span> Approve Access`;
    approveBtn.onclick = () => reviewRequest(req.request_id, "approved");

    const rejectBtn = document.createElement("button");
    rejectBtn.className = "bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 font-semibold px-4 py-2 rounded-lg transition text-sm inline-flex items-center gap-1.5";
    rejectBtn.innerHTML = `<span>✕</span> Reject`;
    rejectBtn.onclick = () => reviewRequest(req.request_id, "rejected");

    buttonGroup.appendChild(rejectBtn);
    buttonGroup.appendChild(approveBtn);

    footer.appendChild(dateSpan);
    footer.appendChild(buttonGroup);

    card.appendChild(header);
    card.appendChild(reasonDiv);
    card.appendChild(footer);

    return card;
}


// LOAD OUTGOING REQUESTS
async function loadOutgoingRequests() {
    const listEl = document.getElementById("outgoingList");
    const emptyEl = document.getElementById("outgoingEmpty");
    const badgeEl = document.getElementById("outgoingBadge");
    const sectionEl = document.getElementById("outgoingSection");

    listEl.innerHTML = "";
    emptyEl.classList.add("hidden");

    const response = await fetch(`${API_BASE_URL}/access/requests?type=outgoing`, {
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
        throw new Error(data.error || "Failed to load outgoing requests.");
    }

    const requests = data.requests || [];
    badgeEl.textContent = requests.length;
    badgeEl.classList.remove("hidden");

    if (requests.length === 0) {
        emptyEl.classList.remove("hidden");
        sectionEl.classList.remove("hidden");
        return;
    }

    requests.forEach(req => {
        const card = createOutgoingRequestCard(req);
        listEl.appendChild(card);
    });

    sectionEl.classList.remove("hidden");
}


// CREATE OUTGOING REQUEST CARD
function createOutgoingRequestCard(req) {
    const card = document.createElement("div");
    card.className = "bg-white rounded-xl shadow-sm p-6 border border-slate-200 transition";

    const header = document.createElement("div");
    header.className = "flex flex-col sm:flex-row justify-between sm:items-start gap-4 mb-4 pb-4 border-b border-slate-100";

    const titleDiv = document.createElement("div");
    const title = document.createElement("h4");
    title.className = "text-xl font-bold text-slate-800 break-words";
    title.textContent = req.document_title || "Untitled Document";

    const docIdSpan = document.createElement("p");
    docIdSpan.className = "text-xs font-mono text-slate-400 mt-1";
    docIdSpan.textContent = `Document ID: ${req.document_id} | Target Division: ${req.document_division || "-"}`;

    titleDiv.appendChild(title);
    titleDiv.appendChild(docIdSpan);

    const statusBadge = document.createElement("span");
    statusBadge.className = getStatusBadgeClass(req.status);
    statusBadge.textContent = getStatusBadgeLabel(req.status);

    header.appendChild(titleDiv);
    header.appendChild(statusBadge);

    // Reason
    const reasonDiv = document.createElement("div");
    reasonDiv.className = "bg-slate-50 rounded-lg p-4 mb-4 text-sm";
    reasonDiv.innerHTML = `
        <span class="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Your Stated Reason:</span>
        <p class="text-slate-700 italic">"${escapeHtml(req.reason || "No reason provided.")}"</p>
    `;

    // Footer with timestamp & direct view button if approved
    const footer = document.createElement("div");
    footer.className = "flex justify-between items-center gap-4 text-sm";

    const formattedDate = req.requested_at ? new Date(req.requested_at).toLocaleDateString("en-IN", {
        year: "numeric", month: "short", day: "numeric"
    }) : "-";
    const dateSpan = document.createElement("span");
    dateSpan.className = "text-slate-400";
    dateSpan.textContent = `Submitted: ${formattedDate}`;

    footer.appendChild(dateSpan);

    if (req.status === "approved") {
        const viewLink = document.createElement("a");
        viewLink.href = `/static/pages/document_details.html?id=${encodeURIComponent(req.document_id)}`;
        viewLink.className = "bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg text-sm transition inline-flex items-center gap-1.5";
        viewLink.innerHTML = `<span>📄</span> View Document`;
        footer.appendChild(viewLink);
    }

    card.appendChild(header);
    card.appendChild(reasonDiv);
    card.appendChild(footer);

    return card;
}


// STATUS BADGE STYLING
function getStatusBadgeClass(status) {
    switch (status) {
        case "approved":
            return "text-xs font-bold bg-green-100 text-green-800 px-3 py-1.5 rounded-full border border-green-300";
        case "rejected":
            return "text-xs font-bold bg-red-100 text-red-800 px-3 py-1.5 rounded-full border border-red-300";
        case "pending":
        default:
            return "text-xs font-bold bg-amber-100 text-amber-800 px-3 py-1.5 rounded-full border border-amber-300";
    }
}

function getStatusBadgeLabel(status) {
    switch (status) {
        case "approved":
            return "✓ Access Approved";
        case "rejected":
            return "✕ Access Rejected";
        case "pending":
        default:
            return "⏳ Pending Review";
    }
}


// REVIEW REQUEST (APPROVE / REJECT)
async function reviewRequest(requestId, decision) {
    if (!confirm(`Are you sure you want to mark this request as ${decision}?`)) {
        return;
    }

    const card = document.getElementById(`req_card_${requestId}`);
    if (card) {
        card.style.opacity = "0.5";
    }

    try {
        const response = await fetch(`${API_BASE_URL}/access/approve`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                request_id: requestId,
                decision: decision
            })
        });

        if (response.status === 401) {
            sessionStorage.clear();
            window.location.href = "/";
            return;
        }

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || `Failed to ${decision} request.`);
        }

        // Reload incoming requests
        await loadIncomingRequests();

    } catch (err) {
        console.error("Review error:", err);
        alert(err.message || "Failed to update request status.");
        if (card) {
            card.style.opacity = "1";
        }
    }
}


// MODAL CONTROLS
function openNewRequestModal() {
    document.getElementById("modalMessage").classList.add("hidden");
    document.getElementById("modalDocId").value = "";
    document.getElementById("modalReason").value = "";
    document.getElementById("newRequestModal").classList.remove("hidden");
}

function closeNewRequestModal() {
    document.getElementById("newRequestModal").classList.add("hidden");
}

async function submitNewAccessRequest(event) {
    event.preventDefault();

    const docIdInput = document.getElementById("modalDocId");
    const reasonInput = document.getElementById("modalReason");
    const messageEl = document.getElementById("modalMessage");
    const submitBtn = document.getElementById("modalSubmitBtn");

    const docId = docIdInput.value.trim();
    const reason = reasonInput.value.trim();

    if (!docId || !reason) {
        messageEl.className = "text-sm p-3 rounded-lg bg-red-100 text-red-700";
        messageEl.textContent = "Please fill in all required fields.";
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
                document_id: docId,
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
            throw new Error(data.error || "Failed to submit request.");
        }

        messageEl.className = "text-sm p-3 rounded-lg bg-green-100 text-green-800 font-medium";
        messageEl.textContent = "Access request submitted successfully!";
        messageEl.classList.remove("hidden");

        setTimeout(() => {
            closeNewRequestModal();
            submitBtn.disabled = false;
            submitBtn.textContent = "Submit Request";
            switchTab("outgoing");
        }, 1200);

    } catch (err) {
        console.error("Submission error:", err);
        messageEl.className = "text-sm p-3 rounded-lg bg-red-100 text-red-700";
        messageEl.textContent = err.message || "Failed to submit request.";
        messageEl.classList.remove("hidden");
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit Request";
    }
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
