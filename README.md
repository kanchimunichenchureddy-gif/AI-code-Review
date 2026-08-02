# AI-Powered Automated Code Reviewer & Feedback System for Students

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.112.0-emerald.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-cyan.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4-purple.svg)](https://vitejs.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade educational code review and feedback platform designed for software engineering courses. The platform combines multi-language AST parsing, static analysis, SAST security vulnerability scanning, isolated Docker sandbox execution, weighted rubric scoring, Winnowing plagiarism detection, and evidence-bound pedagogical AI feedback.

---

## Key Features & Architecture

### 1. Multi-Language Concrete Syntax Tree (AST) Parser
- Built on **Tree-sitter** for accurate, concrete syntax tree parsing across **Python, JavaScript, Java, C, C++, and C#**.
- Persists AST spans with line and column byte coordinates (`ASTNodeModel`).

### 2. Static Code Smell & Complexity Engine
- **Deterministic Complexity Engine:** Computes Cyclomatic Complexity ($V(G)$), Cognitive Complexity, Halstead Volume/Difficulty/Effort ($V, D, E$), Maintainability Index (MI), Lines of Code (LOC), and Max Nesting Depth.
- **Static Analysis Rules Engine:** Detects structural code smells including `DEAD_CODE`, `DEEP_NESTING`, `LONG_METHOD`, `MAGIC_NUMBER`, `POOR_NAMING`, and `GOD_OBJECT`.

### 3. Security SAST & Isolated Docker Sandbox
- **Security SAST Engine:** Scans 13 vulnerability categories (`SQL_INJECTION`, `COMMAND_INJECTION`, `PATH_TRAVERSAL`, `HARDCODED_SECRET`, `XSS`, `CSRF`, etc.).
- **Containerized Execution Sandbox:** Runs untrusted student code inside isolated Docker containers enforcing cgroup limits (`--memory=256m`, `--cpus=0.5`, `--net=none`, `--read-only`, `--tmpfs=/tmp`, `--cap-drop=ALL`, user `10001:10001`, and 5.0s timeout limit).

### 4. Configurable Rubric Engine & Scoring
- Evaluates category-weighted rubrics (`Style`, `Complexity`, `Security`, `Performance`, `Correctness`, `Maintainability`).
- Enforces **Mandatory Constraints**: Failure of mandatory rules (e.g. critical security vulnerabilities) triggers maximum category penalty caps.

### 5. Winnowing AST Plagiarism & Similarity Engine
- **Positional Identifier Normalization:** Replaces user-defined variables and functions with canonical tokens (`VAR_0`, `VAR_1`) based on order of appearance, defeating variable renaming evasions.
- **Winnowing $k$-Gram Fingerprinting:** Computes rolling hash fingerprints ($k=5, w=4$).
- **Tiered Risk Classification:** Categorizes similarity into `LOW` ($\le 25\%$), `MEDIUM` ($25-50\%$), `HIGH` ($50-75\%$), and `Requires Human Review` ($> 75\%$).
- **Strict Human-in-the-Loop:** Flags submissions for instructor review without automatically failing students.

### 6. Evidence-Bound Pedagogical AI Feedback
- **EvidenceValidator Guardrail:** Rejects AI responses that invent non-existent line numbers or unverified compilation bugs.
- **4-Part Educational Cards:** Every feedback item includes (1) **What** is wrong, (2) **Why** it matters, (3) **How to Fix**, and (4) **Example** refactored code.

### 7. Dashboards, Reports & Gradebook Export
- **Student Dashboard:** View submission history, scores, complexity metrics, rubric breakdown, and AI feedback cards.
- **Instructor Dashboard:** Manage courses, view class analytics, execute pairwise plagiarism scans, override grades with audit logging, and export CSV gradebooks.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | Python 3.14+, FastAPI, Pydantic v2 |
| **Database & ORM** | SQLAlchemy 2.0, SQLite / PostgreSQL |
| **AST Parsers** | Tree-sitter (Python, JS, Java, C, C++, C#) |
| **Security Sandbox** | Docker Engine (cgroups, `--net=none`, `--read-only`) |
| **Frontend UI** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons |
| **Test Suite** | Pytest, HTTPX TestClient |

---

## Project Directory Structure

```text
AI_Code_Reviewer/
├── backend/
│   └── app/
│       ├── api/               # REST API Endpoints (Auth, Submissions, Courses, Rubrics, Instructor, Reports, Health)
│       ├── core/              # Config, Security (native bcrypt), Storage Manager, Database
│       ├── models/            # SQLAlchemy ORM Models (User, Course, Assignment, Rubric, Submission, Finding, AST, Similarity)
│       ├── schemas/           # Pydantic v2 Validation Schemas
│       └── main.py            # FastAPI Application Entrypoint
├── analysis/
│   ├── parsers/               # Tree-sitter AST Parsers & Detector
│   ├── complexity/            # Cyclomatic & Cognitive Complexity Engine
│   ├── static/                # Static Code Smell Scanner
│   ├── security/              # SAST Engine & Docker Sandbox Interface
│   ├── rubrics/               # Configurable Rubric Score Evaluator
│   └── similarity/            # Winnowing AST Plagiarism & Similarity Engine
├── ai/
│   ├── validator/             # EvidenceValidator Anti-Hallucination Guardrail
│   └── service.py             # 4-Part Pedagogical Feedback Generator
├── reports/
│   └── export_service.py      # CSV Gradebook Exporter & JSON Audit Exporter
├── frontend/                  # React 18 + TypeScript + Vite Dashboard Application
│   ├── src/
│   │   ├── pages/             # StudentDashboard.tsx, InstructorDashboard.tsx
│   │   └── services/          # REST API Client (axios)
│   ├── package.json
│   └── vite.config.ts
├── tests/                     # Comprehensive Pytest Test Suite (30 Integration & Unit Tests)
├── scripts/
│   └── run_tests.sh           # Test Runner Script
└── README.md                  # Project Documentation
```

---

## Local Setup & Installation Guide

Follow these step-by-step instructions to set up and run the application locally.

### Prerequisites

Ensure you have the following installed on your machine:
- **Python 3.10+** (Python 3.14 recommended)
- **Node.js 18+** and `npm`
- **Docker Engine** (Required for isolated code execution sandbox)
- **Git**

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/AI_Code_Reviewer.git
cd AI_Code_Reviewer
```

---

### Step 2: Set Up Python Virtual Environment

Create and activate a Python virtual environment:

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Upgrade `pip` and install backend dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

The default local database is MySQL:

```env
SECRET_KEY=supersecretjwtkey_replace_in_production_123456789
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=mysql+pymysql://code_reviewer:code_reviewer_password@127.0.0.1:3306/code_reviewer?charset=utf8mb4
```

Start the local MySQL container:

```bash
docker compose up -d mysql
```

If you already have MySQL installed locally, create a database/user matching the `DATABASE_URL`, or update `.env` with your own MySQL credentials.

For an existing local MySQL installation, sign in with your MySQL admin user and run:

```bash
mysql -uroot -p < scripts/setup_mysql.sql
```

Or run the SQL manually:

```sql
CREATE DATABASE IF NOT EXISTS code_reviewer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'code_reviewer'@'localhost' IDENTIFIED BY 'code_reviewer_password';
CREATE USER IF NOT EXISTS 'code_reviewer'@'127.0.0.1' IDENTIFIED BY 'code_reviewer_password';
GRANT ALL PRIVILEGES ON code_reviewer.* TO 'code_reviewer'@'localhost';
GRANT ALL PRIVILEGES ON code_reviewer.* TO 'code_reviewer'@'127.0.0.1';
FLUSH PRIVILEGES;
```

Example command when your MySQL root user has a password:

```bash
mysql -uroot -p
```

Then verify the app credentials:

```bash
mysql -h 127.0.0.1 -P 3306 -ucode_reviewer -pcode_reviewer_password code_reviewer
```

---

### Step 4: Run Backend Server

Start the FastAPI backend server:

```bash
# Set PYTHONPATH to project root
export PYTHONPATH=.

# Start Uvicorn development server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running:
- **Interactive OpenAPI Specs:** Visit [http://localhost:8000/docs](http://localhost:8000/docs)
- **System Health Check:** Visit [http://localhost:8000/api/v1/health/](http://localhost:8000/api/v1/health/)

---

### Step 5: Set Up & Run Frontend Dashboard

Navigate to the `frontend/` directory, install Node dependencies, and launch Vite dev server:

```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server
npm run dev
```

Open your browser at [http://localhost:5173](http://localhost:5173).

---

### Step 5.1: Review Code Through the UI

1. Keep the backend running on [http://127.0.0.1:8000](http://127.0.0.1:8000).
2. Open the Vite frontend URL shown by `npm run dev` (usually `http://localhost:5173`, or another free Vite port such as `5174`).
3. Click **Login as Demo Student**.
4. In **Student View**, use the **Student Code Review Workspace**:
   - Set `Assignment ID` to `1` for the seeded demo assignment.
   - Choose the language.
   - Paste code into the editor, drag files/folders/ZIPs onto the upload bar, or use the compact **Files or ZIP** / **Folder** buttons.
   - Use the file list on the left to inspect selected project files before review.
   - Click **Submit & Run Review**.
   - For archives, choose a `.zip` and click **Upload ZIP & Review**.
5. The results page shows:
   - draft rubric score,
   - complexity metrics,
   - static findings with evidence snippets,
   - security findings,
   - beginner-friendly feedback generated only from deterministic findings.

The frontend sends submissions to `/api/v1/submissions/assignment/{assignment_id}`, triggers `/api/v1/submissions/{id}/analyze`, then generates feedback through `/api/v1/submissions/{id}/generate-feedback`.

---

### Step 6: Run Automated Tests

Execute the complete test suite (30/30 unit and integration tests across all 10 project phases):

```bash
# From project root directory
bash scripts/run_tests.sh
```

Or run pytest directly:

```bash
PYTHONPATH=. ./.venv/bin/pytest -v
```

---

## API Summary & Key Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health/` | System Health Audit | No |
| `POST` | `/api/v1/auth/register` | Register New User | No |
| `POST` | `/api/v1/auth/login` | OAuth2 Password Login | No |
| `POST` | `/api/v1/submissions/assignment/{id}` | Submit Code Assignment | Yes (Student) |
| `POST` | `/api/v1/submissions/assignment/{id}/upload` | Upload `.zip` Code Submission | Yes (Student) |
| `POST` | `/api/v1/submissions/{id}/analyze` | Trigger Static, Security & Rubric Analysis | Yes |
| `GET` | `/api/v1/submissions/{id}/rubric-evaluation` | Get Itemized Rubric Score Breakdown | Yes |
| `POST` | `/api/v1/submissions/assignment/{id}/check-plagiarism` | Run Assignment Pairwise Plagiarism Check | Yes (Instructor) |
| `POST` | `/api/v1/submissions/{id}/generate-feedback` | Generate Evidence-Bound AI Feedback Cards | Yes |
| `POST` | `/api/v1/instructor/submissions/{id}/override-score` | Instructor Score Override with Audit Log | Yes (Instructor) |
| `GET` | `/api/v1/instructor/courses/{id}/analytics` | Course Analytics & Violation Aggregations | Yes (Instructor) |
| `GET` | `/api/v1/reports/course/{id}/gradebook` | Download CSV Course Gradebook | Yes (Instructor) |
| `GET` | `/api/v1/reports/submission/{id}/export` | Export JSON Submission Audit Report | Yes |

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
