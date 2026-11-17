# TRIAD AI — Document Management System (DMS)

An enterprise-grade, secure Document Management System (DMS) featuring dynamic custom metadata, role-based access control (RBAC) with division isolation, automated OCR content extraction, and an auditable cross-division access-request workflow.

---

## Key Features

1. Dynamic Custom Metadata
   - Administrators can configure custom document metadata attributes (`text`, `number`, `date`, `dropdown` with configurable options).
   - Fields can be marked as mandatory or optional.
   - Uploaded documents are validated against the dynamic schema in real time.
   - Regular authenticated users can read and supply configured metadata fields during upload.

2. Role-Based Access Control (RBAC) and Division Isolation
   - Users are registered into distinct Divisions (such as Engineering, Finance, Operations).
   - By default, documents are strictly isolated within their division: users can only view, search, and download documents uploaded to their own division.
   - The public signup portal registers users with the standard user role under their designated division. Admin accounts are provisioned through a controlled administrative process or database seeding, preventing unauthorized privilege escalation.
   - Administrative configuration endpoints are strictly restricted to accounts with the admin role.

3. Secure Cross-Division Access Workflow
   - When a user requires a document from another division, they can discover its header via search and submit an Access Request stating a business justification.
   - Users or admins in the document's owning division review incoming access requests on their Access Requests Portal and can approve or reject them.
   - Upon approval, the document immediately becomes accessible in the requester's document hub for details viewing and downloading.
   - Unauthorized access, unapproved downloads, and cross-division deletion attempts are strictly blocked with HTTP 403 Forbidden.

4. OCR and Intelligent Full-Text Search Engine
   - File Storage and Validation: Supports secure upload and storage of PDF, PNG, JPG/JPEG, TXT, and DOCX files in MongoDB GridFS.
   - Text Extraction and OCR: Standalone images (PNG, JPG, JPEG) and scanned PDF pages are processed through Tesseract OCR (`pytesseract`). Selectable text from standard PDFs is extracted directly using PyMuPDF (`fitz`), and plain text files (`txt`) are decoded directly. All extracted text is indexed for search.
   - Search Engine: Dedicated Advanced Search page searches across document titles, filenames, dynamic metadata attributes, and OCR-extracted text.
   - Search results display contextual match badges (`matched_in`: Title, Filename, Custom Metadata, OCR Content).

5. Document Hub and Dashboard
   - Clean, modern Tailwind CSS responsive interface.
   - Live metrics: Total Accessible Documents, User Division, Account Role.
   - Real-time client-side table filtering (title, division, metadata).
   - Pagination controls and a "View All" toggle.
   - Document Details page (`document_details.html?id=<id>`) with complete metadata, OCR text viewer, one-click text copying, and download triggers.
   - Document deletion with confirmation dialog for document owners and administrators.

---

## Technology Stack

- Backend: Python 3.10+ (tested on Python 3.13.17), Flask, Flask-CORS, Flask-JWT-Extended, Werkzeug
- Database and Storage: MongoDB Atlas, MongoDB GridFS (large binary chunks storage via `GridFSBucket`)
- OCR and Document Processing: PyMuPDF (`fitz`), Tesseract OCR (`pytesseract`), Pillow (`PIL`)
- Frontend: HTML5, Vanilla JavaScript (ES6+), Tailwind CSS (CDN), Custom CSS
- Testing: pytest, requests, unittest mock

---

## Project Structure

```text
TRIAD_AI_DMS/
├── run.py                          # Flask application launcher (host: 127.0.0.1, port: 5000)
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template with placeholder values
├── .gitignore                      # Git exclusion rules (ignores .env, .venv, logs, uploads)
├── test_api.py                     # Official TRIAD AI automated test script
├── test_sample.pdf                 # Sample PDF used for automated testing
├── app/
│   ├── __init__.py                 # Application factory (registers blueprints, CORS, static folder)
│   ├── config.py                   # Configuration validation and environment constants
│   ├── extensions.py               # MongoClient, GridFSBucket, and JWTManager initializers
│   ├── middleware/
│   │   └── auth_middleware.py      # @token_required and @admin_required decorators
│   ├── models/
│   │   ├── user_model.py           # User schema, password hashing, and queries
│   │   ├── document_model.py       # Document schema, metadata serialization, OCR storage
│   │   ├── access_model.py         # Access request schema helpers
│   │   └── metadata_model.py       # Metadata field configuration helpers
│   ├── routes/
│   │   ├── auth_routes.py          # /api/auth (register, login, me)
│   │   ├── document_routes.py      # /api/documents (upload, list, details, download, delete)
│   │   ├── access_routes.py        # /api/access (request, requests, approve)
│   │   ├── admin_routes.py         # /api/admin (metadata config creation and listing)
│   │   └── search_routes.py        # /api/search (full-text OCR and metadata search)
│   ├── services/
│   │   ├── storage_service.py      # GridFS stream upload, download, and delete
│   │   ├── ocr_service.py          # PyMuPDF selectable text + Tesseract OCR fallback
│   │   ├── access_service.py       # Cross-division access verification
│   │   └── metadata_service.py     # Metadata configuration service
│   └── utils/
│       ├── file_validation.py      # Extension and magic byte checks (PDF, PNG, JPG, TXT, DOCX)
│       └── validators.py           # Field validation helpers
├── frontend/
│   ├── index.html                  # Root Login page
│   ├── css/
│   │   └── style.css               # Focus states and message styling
│   ├── js/
│   │   ├── auth.js                 # Authentication logic (register, login, JWT storage)
│   │   ├── dashboard.js            # Dashboard stats, table filtering, pagination, delete
│   │   ├── upload.js               # Dynamic metadata form generation, XHR progress upload
│   │   ├── search.js               # Full-text search, matched_in badges, discovery actions
│   │   ├── documents.js            # Document details view, OCR viewer, delete, download
│   │   ├── access.js               # Incoming/outgoing access requests, approval controls
│   │   └── admin.js                # Custom metadata field builder and management
│   └── pages/
│       ├── login.html              # Standalone login view
│       ├── signup.html             # User registration (name, email, password, division)
│       ├── dashboard.html          # Document hub, summary cards, document table
│       ├── upload.html             # File upload dropzone, dynamic metadata inputs
│       ├── search.html             # Advanced OCR and metadata search page
│       ├── document_details.html   # Detailed document inspector with OCR text preview
│       ├── access_requests.html    # Cross-division access request inbox and outgoing status
│       └── admin.html              # Admin metadata configuration interface
└── tests/
    ├── test_full_system.py         # 31-point comprehensive end-to-end regression test suite
    ├── run_live_test_api.py        # Live server runner for test_api.py
    ├── test_normal_user_approval.py# Division peer approval verification test
    ├── test_image_ocr.py           # Standalone image OCR verification (PNG/JPG)
    └── test_metadata_access.py     # Metadata RBAC verification script
```

---

## Setup and Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- MongoDB Atlas cluster or local MongoDB instance (version 6.0+)
- Tesseract OCR installed (default path: C:\Program Files\Tesseract-OCR\tesseract.exe)

### 1. Clone and Set Up Virtual Environment

```bash
cd TRIAD_AI_DMS
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables (.env)

Create your local .env file by copying the provided .env.example template. Note that .env contains sensitive credentials, is excluded by .gitignore, and must never be committed to source control:

```bash
# On Linux/macOS:
cp .env.example .env

# On Windows (PowerShell):
Copy-Item .env.example .env
```

Populate .env with your MongoDB connection string and secret keys:

```env
SECRET_KEY=your_flask_secret_key
JWT_SECRET_KEY=your_jwt_secret_key
MONGO_URI=mongodb+srv://<username>:<password>@yourcluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=triad_dms
```

---

## Running the Application

Start the Flask server:

```bash
python run.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000/
```

- Login / Signup: Create a standard user account with your designated Division (such as Engineering, Finance, or Operations).
- Dashboard: View documents belonging to your division and approved cross-division documents.
- Upload Document: Select a file, enter title and description, and fill in dynamically configured metadata fields.
- Advanced Search: Search for keywords across titles, metadata attributes, or OCR-extracted contents.
- Access Requests: Review and approve/reject requests from other divisions, or request access to external documents.
- Admin Settings: (Admin accounts only) Configure custom metadata fields and validation rules.

---

## REST API Reference

### Authentication (/api/auth)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| POST | /api/auth/register | Public | Register new user (name, email, password, division). Creates standard user account. |
| POST | /api/auth/login | Public | Authenticate user; returns JWT access_token and user profile. |
| GET | /api/auth/me | User | Get profile of currently authenticated user. |

### Documents (/api/documents)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| POST | /api/documents/upload | User | Upload file with multipart file, title, description, metadata JSON. |
| GET | /api/documents | User | List documents in user's division and approved cross-division documents. Supports metadata query filters (e.g. ?Report Type=Financial). |
| GET | /api/documents/<id> | User | Get document details, custom metadata, and extracted OCR text (Division/Approved access required). |
| GET | /api/documents/<id>/download | User | Stream binary file from GridFS (Division/Approved access required). |
| DELETE | /api/documents/<id> | Owner/Admin | Permanently delete document record and GridFS binary file. |

### Access Control (/api/access)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| POST | /api/access/request | User | Request access to another division's document (document_id, reason). |
| GET | /api/access/requests | User | List incoming pending requests for user's division (?type=incoming) or outgoing requests (?type=outgoing). |
| POST | /api/access/approve | User | Approve or reject request (request_id, decision: "approved" \| "rejected"). |

### Full-Text Search (/api/search)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| GET | /api/search?q=<query> | User | Full-text search across titles, filenames, metadata, and OCR text with match badges. |

### Admin Settings (/api/admin)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| POST | /api/admin/metadata | Admin | Create custom metadata field (field_name, field_type, required, options). |
| GET | /api/admin/metadata | User | List all configured metadata field definitions. |

---

## Testing and Validation

The test suites verify end-to-end functionality, division isolation, role separation, OCR search, and access workflows.

Note: The terminal snippets below represent sample outputs from the latest local test runs executed on Python 3.13 against an active Flask server connected to MongoDB Atlas.

### 1. Official Starter Test Script (test_api.py)
Run the official test script against the active server:

```bash
python tests/run_live_test_api.py
```

Sample local output:
```text
=== TRIAD AI DMS API TEST REPORT ===

Total Tests: 3
Passed: 3
Failed: 0
```

### 2. Comprehensive 31-Point End-to-End Regression Suite
Execute the full integration test suite covering RBAC, division isolation, OCR search, cross-division approvals, and deletions:

```bash
python tests/test_full_system.py
```

Sample local output:
```text
=======================================================
   TRIAD AI DMS - FULL END-TO-END REGRESSION SUITE   
=======================================================

[PASS] 1.1 Normal User Registration (Division A)
[PASS] 1.2 Normal User Registration (Division B)
[PASS] 1.3 Admin User Registration (Controlled Setup)
[PASS] 2.1 User A Login
[PASS] 2.2 User B Login
[PASS] 2.3 Admin Login
[PASS] 3.1 Normal user blocked from POST /api/admin/metadata
[PASS] 3.2 Normal user can READ metadata configs
[PASS] 4.1 Document Upload with Metadata & Description
[PASS] 5.1 Owner can view Document Details
[PASS] 5.2 Description properly persisted and serialized
[PASS] 5.3 OCR text field returned in Document Details
[PASS] 6.1 Cross-Division User B blocked from viewing Doc A Details (403)
[PASS] 6.2 Cross-Division User B blocked from downloading Doc A (403)
[PASS] 7.1 User A can list Division A documents
[PASS] 7.2 User B does NOT see Doc A in their document listing
[PASS] 8.1 User A finds Doc A in search
[PASS] 8.2 Search result has_access is True for division member
[PASS] 8.3 User B discovers Doc A header in cross-division search
[PASS] 8.4 Discovered Doc A has has_access=False for User B
[PASS] 8.5 OCR content is NOT exposed to User B
[PASS] 9.1 User B submits cross-division access request
[PASS] 10.1 User A sees pending incoming request
[PASS] 10.2 User B sees their outgoing request with status pending
[PASS] 11.1 User A approves access request
[PASS] 12.1 User B can view details of Doc A after approval
[PASS] 12.2 User B can download Doc A after approval
[PASS] 12.3 Approved cross-division document appears in User B's documents list
[PASS] 13.1 User B (non-owner, non-admin) blocked from deleting Doc A (403)
[PASS] 13.2 Owner User A successfully deleted Doc A
[PASS] 13.3 Document correctly removed (404)

=======================================================
   ALL 31 REGRESSION TESTS PASSED! (Failed: 0)
=======================================================
```

### 3. Cross-Division Peer Approval Test
Verify that normal division members (non-admins) belonging to the document owner's division can approve access requests as required by the assignment specification:

```bash
python tests/test_normal_user_approval.py
```

Sample local output:
```text
[PASS] Normal Division A user successfully approved access request
[PASS] Requester in Division B successfully downloaded the document
[PASS] Division C user prevented from approving request (403)
[PASS] Requester prevented from approving own request (403)
```

### 4. Standalone Image OCR Test (PNG and JPG)
Verify that standalone image uploads (PNG and JPG) undergo OCR text extraction and indexing for full-text search:

```bash
python tests/run_live_image_ocr.py
```

Sample local output:
```text
[PASS] PNG Image uploaded successfully with document_id: 6afc4c52a69306ec22c2b0cb
Extracted Image OCR Text: 'SSECRET_QUARTERLY EARNINGS'
[PASS] Standalone Image OCR text extraction verified in Document Details!
[PASS] Standalone Image OCR full-text search verified!
[PASS] JPG Image uploaded successfully with document_id: 6afc4c53a69306ec22c2b0ce
Extracted JPG OCR Text: 'SPECIAL AUDIT.REPORT.2028'
[PASS] Standalone JPG Image OCR text extraction verified!

ALL STANDALONE IMAGE OCR TESTS PASSED!
```

---

## Security and Best Practices

- Division Isolation: Strict division boundaries prevent unauthorized access to document binary streams and OCR contents.
- Role Privilege Separation: Public user registration provisions standard division member accounts (`role: "user"`). Administrative privileges (`role: "admin"`) are provisioned exclusively through controlled setup and cannot be self-assigned.
- Environment and Secret Protection: Sensitive credentials, API keys, and database connection strings are stored exclusively in local .env files and excluded from version control via .gitignore. A clean .env.example template is provided for configuration.
- Dynamic Schema Validation: Uploads are strictly validated against administrator-defined metadata types (numbers, dates, dropdown options).
- Graceful Rollback: If OCR extraction or MongoDB document creation fails during upload, the orphaned GridFS binary chunk is automatically cleaned up.
- Auditable Access Log: All cross-division requests record requester identity, document ID, justification reason, reviewer ID, and timestamps.
