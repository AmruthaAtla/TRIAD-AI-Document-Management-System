const API_BASE_URL = "/api";

const token = sessionStorage.getItem("access_token");
const storedUser = sessionStorage.getItem("user");

let currentUser = {};


// CHECK ADMIN AUTHORIZATION
if (!token || !storedUser) {
    window.location.href = "/";
} else {
    try {
        currentUser = JSON.parse(storedUser);

        if (currentUser.role !== "admin") {
            alert("Access denied. Administrator privileges required.");
            window.location.href = "/static/pages/dashboard.html";
        }

    } catch (error) {
        sessionStorage.clear();
        window.location.href = "/";
    }
}


// INITIALIZE PAGE
document.addEventListener("DOMContentLoaded", () => {
    loadMetadataFields();
    toggleDropdownOptions();
});


// SHOW DROPDOWN OPTIONS
function toggleDropdownOptions() {
    const fieldType = document.getElementById("fieldType").value;

    const optionsContainer =
        document.getElementById("dropdownOptionsContainer");

    const optionsInput =
        document.getElementById("dropdownOptions");

    if (fieldType === "dropdown") {
        optionsContainer.classList.remove("hidden");
        optionsInput.required = true;
    } else {
        optionsContainer.classList.add("hidden");
        optionsInput.required = false;
        optionsInput.value = "";
    }
}


// DISPLAY ADMIN MESSAGE
function showAdminMessage(message, type) {
    const element = document.getElementById("adminMessage");

    element.textContent = message;

    element.className =
        type === "success"
            ? "message success mt-5"
            : "message error mt-5";
}


// CREATE METADATA FIELD
async function createMetadataField(event) {
    event.preventDefault();

    const fieldName =
        document.getElementById("fieldName").value.trim();

    const fieldType =
        document.getElementById("fieldType").value;

    const required =
        document.getElementById("isRequired").checked;

    const optionsText =
        document.getElementById("dropdownOptions").value.trim();

    let options = [];

    if (fieldType === "dropdown") {
        options = optionsText
            .split(",")
            .map(option => option.trim())
            .filter(option => option.length > 0);

        if (options.length === 0) {
            showAdminMessage(
                "Please enter at least one dropdown option.",
                "error"
            );
            return;
        }
    }

    if (!fieldName || !fieldType) {
        showAdminMessage(
            "Please complete all required fields.",
            "error"
        );
        return;
    }

    const button = document.getElementById("createFieldButton");

    button.disabled = true;
    button.textContent = "Creating...";

    try {
        const response = await fetch(
            `${API_BASE_URL}/admin/metadata`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },

                body: JSON.stringify({
                    field_name: fieldName,
                    field_type: fieldType,
                    required: required,
                    options: options
                })
            }
        );

        const result = await response.json();

        if (response.status === 401) {
            sessionStorage.clear();
            window.location.href = "/";
            return;
        }

        if (response.status === 403) {
            showAdminMessage(
                "You do not have administrator permission.",
                "error"
            );
            return;
        }

        if (!response.ok) {
            throw new Error(
                result.error || "Unable to create metadata field."
            );
        }

        showAdminMessage(
            result.message || "Metadata field created successfully!",
            "success"
        );

        document.getElementById("metadataForm").reset();

        toggleDropdownOptions();

        await loadMetadataFields();

    } catch (error) {
        console.error("Metadata creation error:", error);

        showAdminMessage(error.message, "error");

    } finally {
        button.disabled = false;
        button.textContent = "Create Metadata Field";
    }
}


// LOAD EXISTING METADATA FIELDS
async function loadMetadataFields() {
    const loading =
        document.getElementById("metadataLoading");

    const list =
        document.getElementById("metadataList");

    const empty =
        document.getElementById("metadataEmpty");

    loading.style.display = "block";
    list.innerHTML = "";
    empty.classList.add("hidden");

    try {
        const response = await fetch(
            `${API_BASE_URL}/admin/metadata`,
            {
                method: "GET",

                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        const result = await response.json();

        if (response.status === 401) {
            sessionStorage.clear();
            window.location.href = "/";
            return;
        }

        if (response.status === 403) {
            alert("Administrator access required.");

            window.location.href =
                "/static/pages/dashboard.html";

            return;
        }

        if (!response.ok) {
            throw new Error(
                result.error || "Unable to retrieve metadata fields."
            );
        }

        const fields = result.metadata_fields || [];

        loading.style.display = "none";

        if (fields.length === 0) {
            empty.classList.remove("hidden");
            return;
        }

        fields.forEach(field => {

            const card = document.createElement("div");

            card.className =
                "border border-slate-200 rounded-xl p-5 flex flex-col sm:flex-row justify-between gap-4";

            const details = document.createElement("div");

            const name = document.createElement("h4");

            name.className =
                "font-semibold text-slate-800 text-lg";

            name.textContent = field.field_name;

            const type = document.createElement("p");

            type.className =
                "text-sm text-slate-500 mt-1";

            type.textContent =
                `Type: ${field.field_type}`;

            const requirement = document.createElement("p");

            requirement.className =
                "text-sm text-slate-500 mt-1";

            requirement.textContent =
                field.required ? "Required field" : "Optional field";

            details.appendChild(name);
            details.appendChild(type);
            details.appendChild(requirement);

            if (
                field.field_type === "dropdown" &&
                Array.isArray(field.options)
            ) {
                const optionText = document.createElement("p");

                optionText.className =
                    "text-sm text-blue-600 mt-2";

                optionText.textContent =
                    "Options: " + field.options.join(", ");

                details.appendChild(optionText);
            }

            const badge = document.createElement("span");

            badge.className =
                "text-xs bg-blue-100 text-blue-700 px-3 py-2 rounded-full h-fit";

            badge.textContent =
                field.required ? "Mandatory" : "Optional";

            card.appendChild(details);
            card.appendChild(badge);

            list.appendChild(card);
        });

    } catch (error) {
        console.error("Metadata loading error:", error);

        loading.style.display = "none";

        empty.textContent = error.message;
        empty.classList.remove("hidden");
    }
}


// LOGOUT
function logoutUser() {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");

    window.location.href = "/";
}