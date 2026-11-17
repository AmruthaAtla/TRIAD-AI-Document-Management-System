const API_BASE_URL = "/api";

const token = sessionStorage.getItem("access_token");
const storedUser = sessionStorage.getItem("user");

let currentUser = {};

if (!token || !storedUser) {
    window.location.href = "/";
} else {
    try {
        currentUser = JSON.parse(storedUser);
    } catch (error) {
        sessionStorage.clear();
        window.location.href = "/";
    }
}


// INITIALIZE PAGE
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("division").value =
        currentUser.division || "";

    const adminLink = document.getElementById("adminLink");

    if (currentUser.role !== "admin" && adminLink) {
        adminLink.style.display = "none";
    }

    loadMetadataFields();
});


// LOAD DYNAMIC METADATA
async function loadMetadataFields() {
    const container = document.getElementById("metadataFields");

    try {
        const response = await fetch(`${API_BASE_URL}/admin/metadata`, {
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

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Unable to load metadata.");
        }

        const fields = Array.isArray(result)
            ? result
            : (result.metadata_fields || result.fields || result.metadata || []);

        container.innerHTML = "";

        if (!Array.isArray(fields) || fields.length === 0) {
            container.innerHTML = `
                <p class="text-sm text-slate-400">
                    No additional metadata fields configured.
                </p>
            `;
            return;
        }

        fields.forEach((field, index) => {
            const fieldName =
                field.name || field.field_name || field.key || `field_${index}`;

            const fieldType =
                (field.type || field.data_type || "text").toLowerCase();

            const required = field.required === true;

            const wrapper = document.createElement("div");

            const label = document.createElement("label");
            label.className =
                "block text-sm font-semibold text-slate-700 mb-2";

            label.textContent =
                fieldName + (required ? " *" : "");

            const input = document.createElement(
                fieldType === "dropdown" || fieldType === "select"
                    ? "select"
                    : "input"
            );

            input.id = `metadata_${index}`;
            input.dataset.fieldName = fieldName;
            input.dataset.fieldType = fieldType;
            input.className = "form-input";

            if (required) {
                input.required = true;
            }

            if (fieldType === "number") {
                input.type = "number";
            } else if (fieldType === "date") {
                input.type = "date";
            } else if (fieldType === "dropdown" || fieldType === "select") {

                const placeholder = document.createElement("option");
                placeholder.value = "";
                placeholder.textContent = "Select " + fieldName;
                input.appendChild(placeholder);

                const options = field.options || [];

                options.forEach(option => {
                    const optionElement =
                        document.createElement("option");

                    optionElement.value =
                        typeof option === "object"
                            ? option.value
                            : option;

                    optionElement.textContent =
                        typeof option === "object"
                            ? option.label || option.value
                            : option;

                    input.appendChild(optionElement);
                });

            } else {
                input.type = "text";
                input.placeholder = `Enter ${fieldName}`;
            }

            wrapper.appendChild(label);
            wrapper.appendChild(input);

            container.appendChild(wrapper);
        });

    } catch (error) {
        console.error("Metadata loading error:", error);

        container.innerHTML = `
            <p class="text-red-600 text-sm">
                Unable to load metadata fields: ${error.message}
            </p>
        `;
    }
}


// DISPLAY SELECTED FILE
function displaySelectedFile() {
    const fileInput = document.getElementById("file");
    const selectedFile = document.getElementById("selectedFile");

    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];

        selectedFile.textContent =
            `${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
    } else {
        selectedFile.textContent = "";
    }
}


// COLLECT METADATA
function collectMetadata() {
    const metadata = {};

    document.querySelectorAll("[data-field-name]").forEach(input => {
        const value = input.value.trim();

        if (value !== "") {
            if (input.type === "number" || input.dataset.fieldType === "number") {
                const num = Number(value);
                metadata[input.dataset.fieldName] = isNaN(num) ? value : num;
            } else {
                metadata[input.dataset.fieldName] = value;
            }
        }
    });

    return metadata;
}


// DISPLAY MESSAGE
function showUploadMessage(message, type) {
    const messageElement = document.getElementById("uploadMessage");

    messageElement.textContent = message;
    messageElement.className =
        type === "success"
            ? "message success mt-5"
            : "message error mt-5";
}


// UPLOAD DOCUMENT
function uploadDocument(event) {
    event.preventDefault();

    const form = document.getElementById("uploadForm");
    const fileInput = document.getElementById("file");
    const file = fileInput.files[0];

    const uploadButton = document.getElementById("uploadButton");
    const progressContainer =
        document.getElementById("uploadProgressContainer");

    const progressBar = document.getElementById("progressBar");
    const progressText = document.getElementById("progressText");

    if (!file) {
        showUploadMessage("Please select a document.", "error");
        return;
    }

    const allowedExtensions = [
        "pdf", "png", "jpg", "jpeg", "txt", "docx"
    ];

    const extension = file.name.split(".").pop().toLowerCase();

    if (!allowedExtensions.includes(extension)) {
        showUploadMessage("Unsupported file format.", "error");
        return;
    }

    if (file.size === 0) {
        showUploadMessage("The selected file is empty.", "error");
        return;
    }

    const metadata = collectMetadata();

    const formData = new FormData();

    formData.append("title", document.getElementById("title").value.trim());

    formData.append(
        "description",
        document.getElementById("description").value.trim()
    );

    formData.append("division", currentUser.division);

    formData.append("file", file);

    formData.append("metadata", JSON.stringify(metadata));

    uploadButton.disabled = true;
    uploadButton.textContent = "Uploading...";

    progressContainer.classList.remove("hidden");
    progressBar.style.width = "0%";
    progressText.textContent = "0%";

    showUploadMessage("Uploading your document...", "success");

    const xhr = new XMLHttpRequest();

    xhr.open("POST", `${API_BASE_URL}/documents/upload`);

    xhr.setRequestHeader(
        "Authorization",
        `Bearer ${token}`
    );

    // Upload progress
    xhr.upload.addEventListener("progress", event => {
        if (event.lengthComputable) {
            const percentage = Math.round(
                (event.loaded / event.total) * 100
            );

            progressBar.style.width = `${percentage}%`;
            progressText.textContent = `${percentage}%`;
        }
    });

    xhr.onload = function () {
        uploadButton.disabled = false;
        uploadButton.textContent = "Upload Document";

        let result = {};

        try {
            result = JSON.parse(xhr.responseText);
        } catch (error) {
            result = {};
        }

        if (xhr.status === 401) {
            sessionStorage.clear();
            window.location.href = "/";
            return;
        }

        if (xhr.status >= 200 && xhr.status < 300) {
            progressBar.style.width = "100%";
            progressText.textContent = "100%";

            showUploadMessage(
                result.message || "Document uploaded successfully!",
                "success"
            );

            form.reset();

            document.getElementById("division").value =
                currentUser.division || "";

            document.getElementById("selectedFile").textContent = "";

            loadMetadataFields();

        } else {
            progressContainer.classList.add("hidden");

            showUploadMessage(
                result.error || result.message || "Document upload failed.",
                "error"
            );
        }
    };

    xhr.onerror = function () {
        uploadButton.disabled = false;
        uploadButton.textContent = "Upload Document";

        progressContainer.classList.add("hidden");

        showUploadMessage(
            "Unable to connect to the server.",
            "error"
        );
    };

    xhr.send(formData);
}


// RESET FORM
function resetUploadForm() {
    setTimeout(() => {
        document.getElementById("division").value =
            currentUser.division || "";

        document.getElementById("selectedFile").textContent = "";

        document.getElementById("uploadMessage").textContent = "";

        document.getElementById("uploadProgressContainer")
            .classList.add("hidden");
    }, 0);
}


// LOGOUT
function logoutUser() {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("user");

    window.location.href = "/";
}