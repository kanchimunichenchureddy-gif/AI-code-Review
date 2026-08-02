# Phase 0 Architecture Document: Requirements & System Specifications

> **Project Name:** AI-Powered Automated Code Reviewer & Feedback System for Students  
> **Document Version:** 1.0.0  
> **Status:** Approved / Specification Phase  
> **Date:** August 2026  

---

## Executive Summary

The **AI-Powered Automated Code Reviewer & Feedback System for Students** is an enterprise-grade, academic software engineering platform designed to automate code analysis, security scanning, complexity evaluation, rubric-based grading, and feedback generation for university programming assignments.

Unlike commercial code analysis tools or raw LLM wrappers, this system operates on a **strict deterministic-first architecture**:
1. All static analysis, security vulnerabilities, code smells, and complexity metrics are produced by **deterministic AST parsers** (Tree-sitter) and verified static analysis tools (Bandit, Semgrep, ESLint, Pylint, Flake8, Cppcheck, Clang-Tidy, PMD, SpotBugs).
2. Large Language Models (LLMs) are restricted **exclusively** to an **Explanation & Pedagogical Synthesis Layer**. The LLM receives structured, evidence-backed findings and translates them into beginner-friendly, educational feedback with "What, Why, How to Fix, and Code Examples".
3. The LLM is **never** permitted to declare bugs, invent line numbers, execute code, assign grades autonomously, or bypass evidence validation.

---

## 1. Problem Statement & Real-World Analysis

### Problem 1: Manual Review Scalability Bottlenecks
* **Context:** University courses with 300+ students generate thousands of code submissions per semester. Manual line-by-line review by TAs and professors leads to delayed grading (weeks) and inconsistent feedback quality.
* **Solution:** Automated deterministic line-by-line static review, complexity analysis, security scanning, and initial rubric scoring within seconds of submission.

### Problem 2: Superficial Feedback for Students
* **Context:** Students often receive only a single numerical score or pass/fail test output without understanding structural flaws or style deficiencies.
* **Solution:** Comprehensive feedback breakdown detailing strengths, weaknesses, maintainability metrics, code readability recommendations, and curated learning references.

### Problem 3: Cryptic Static Analysis Reports
* **Context:** Industrial static analyzers produce dense, noisy logs designed for senior engineers, overwhelming computer science novices.
* **Solution:** An AI explanation layer that translates rule IDs and compiler trace outputs into pedagogical explanations tailored to student skill levels.

### Problem 4: LLM Hallucinations in Automated Grading
* **Context:** Using raw LLM prompts to grade code results in fabricated compilation errors, missing line references, and unpredictable scoring.
* **Solution:** Strict evidence-bound validation (`EvidenceValidator`). Every AI-generated comment must link directly to a deterministic `ASTNode`, `StaticFinding`, or `SecurityFinding` record verified by source span ranges.

### Problem 5: Rigid vs. Course-Specific Rubrics
* **Context:** Introductory programming demands strict style and variable naming checks; advanced algorithms courses prioritize asymptotic time/space complexity; cybersecurity courses focus on secure input handling.
* **Solution:** A declarative JSON/YAML rubric engine supporting weighted rules, mandatory constraints, bonus points, and custom penalties configurable per assignment.

### Problem 6: Multi-Language Fragmentation
* **Context:** Computer Science curricula span Python, Java, JavaScript, C, C++, and C#.
* **Solution:** Unified AST parser abstraction layer powered by **Tree-sitter**, standardizing abstract syntax tree nodes into a common intermediate schema across all 6 supported languages.

### Problem 7: Subjective & Manual Plagiarism Detection
* **Context:** Traditional text-diff tools fail when students rename variables or reorder functions. Manual code comparison is impractically slow.
* **Solution:** Multi-layered similarity engine incorporating AST structure hashing, token stream normalization (Winnowing fingerprinting), and control flow graph comparison. Results output similarity tiers (`LOW`, `MEDIUM`, `HIGH`, `Requires Human Review`) and require instructor review before any academic integrity decision.

### Problem 8: Untrusted Code Execution Security Risks
* **Context:** Running student code on server infrastructure exposes systems to malicious shell commands, infinite loops, resource exhaustion, and remote code execution (RCE).
* **Solution:** Strict sandboxing using ephemeral Docker containers with cgroup resource constraints (CPU, RAM limits), dropped Linux capabilities, disabled networking, read-only root filesystems, and strict timeouts.

### Problem 9: Lack of Educational "Why" Context
* **Context:** Telling a student "Cyclomatic complexity is 14" does not teach them how to refactor nested loops into helper functions.
* **Solution:** Every issue output follows a structured 4-part pedagogical schema: (1) **What** is wrong, (2) **Why** it matters, (3) **How** to refactor, and (4) **Example** refactored code.

### Problem 10: Instructor Review Fatigue
* **Context:** Instructors spend significant time writing repetitive feedback for common mistakes across many students.
* **Solution:** Auto-generated draft feedback summaries that instructors can inspect, edit, override, and approve with a single click.

---

## 2. Stakeholders & User Personas

| Role | User Persona | Key Needs / Goals | Primary Touchpoints |
|---|---|---|---|
| **Student** | Alex (CS Undergrad) | Rapid feedback on submissions, actionable hints, clear rubric breakdown, progress tracking | Student Dashboard, Monaco Editor preview, Submission History, Feedback Timeline |
| **Teaching Assistant** | Priya (Graduate TA) | Fast batch reviewing, quick override of AI scores, highlighting common plagiarism flags | Submission Review Queue, Rubric Override Modal, Plagiarism Comparison Viewer |
| **Course Instructor / Professor** | Dr. Miller (CS Professor) | Assignment creation, custom rubric definition, class analytics, exportable gradebooks | Course & Assignment Builder, Rubric Designer, Class Performance Analytics |
| **Department Supervisor** | Prof. Chen (Supervising Chair) | Course quality auditing, cross-section rubric standardization, system usage reports | Audit Logs, Department Analytics Dashboard |
| **System Administrator** | DevOps Admin | System health monitoring, sandbox resource allocation, worker queue management | Grafana/Prometheus Dashboard, Health Check APIs, Docker Container Pool |

---

## 3. System Architecture & Component Design

```
+-----------------------------------------------------------------------------------+
|                                  REACT FRONTEND                                   |
|   (TypeScript + Vite + Tailwind CSS + Monaco Editor + Recharts + TanStack Query)   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v  (REST API / HTTP JSON)
+-----------------------------------------------------------------------------------+
|                                FASTAPI API GATEWAY                                |
|          (Authentication / JWT + RBAC, Rate Limiting, OpenAPI Docs)               |
+-----------------------------------------------------------------------------------+
      |                      |                           |                     |
      v                      v                           v                     v
+------------+     +--------------------+     +---------------------+    +--------------+
| Assignment |     | Submission Manager |     | Instructor Review   |    | Student      |
| Manager    |     | (Storage & Queue)  |     | & Grade Override    |    | Dashboard    |
+------------+     +--------------------+     +---------------------+    +--------------+
                             |
                             v  (Async Task Queue via Redis)
+-----------------------------------------------------------------------------------+
|                              CELERY WORKER PIPELINE                               |
|                                                                                   |
|  1. Language Detection & Tree-sitter AST Generator                                 |
|  2. Deterministic Static Analysis Engine (Bandit/Semgrep/ESLint/Pylint/Clang)      |
|  3. Complexity Engine (Cyclomatic, Cognitive, Halstead, MI, LOC)                  |
|  4. Security Engine (SAST rules + Ephemeral Docker Container Execution)          |
|  5. Similarity Engine (Winnowing Fingerprints + AST Hashing)                      |
|  6. Rubric Engine (Weighted Rule Evaluation + Score Calculation)                  |
|  7. Evidence Validator (Cross-checks findings against AST line spans)              |
|  8. AI Feedback Engine (Pedagogical explanation generation via strict prompt)      |
+-----------------------------------------------------------------------------------+
      |                                    |                                  |
      v                                    v                                  v
+------------------+             +--------------------+            +------------------+
|   MySQL 8.0 DB   |             | Redis Cache & Queue|            | Docker Engine    |
| (Relational Data)|             | (Celery / PubSub)  |            | (Isolated Box)   |
+------------------+             +--------------------+            +------------------+
```

---

## 4. Multi-Language AST Architecture

The system uses **Tree-sitter** for unified, incremental parsing of 6 programming languages:

```
Source Code (Py, Java, JS, C, C++, C#) 
  --> Tree-sitter Parser 
  --> Unified Concrete Syntax Tree (CST) 
  --> AST Normalizer 
  --> Unified AST Model (Nodes: Class, Function, Loop, Condition, Variable, Expression)
```

### Standardized AST Node Representation
```json
{
  "id": "ast_node_9842",
  "file_path": "src/binary_tree.py",
  "node_type": "FunctionDeclaration",
  "identifier": "insert_node",
  "start_point": {"line": 14, "column": 4},
  "end_point": {"line": 28, "column": 19},
  "parent_id": "ast_node_9800",
  "children_ids": ["ast_node_9843", "ast_node_9844"],
  "metrics": {
    "cyclomatic_complexity": 5,
    "nesting_depth": 3
  }
}
```

---

## 5. Deterministic Static & Security Analysis Architecture

Static analysis strictly executes deterministic tools in isolated environments:

| Language | Static Analyzers | Security Scanners | Key Metrics Evaluated |
|---|---|---|---|
| **Python** | Pylint, Flake8 | Bandit, Semgrep | Unused vars, PEP8, SQLi, Command Injection |
| **Java** | PMD, Checkstyle | SpotBugs + FindSecBugs | Type safety, dead code, null deref, deserialization |
| **JavaScript** | ESLint | Semgrep (JS) | Prototype pollution, XSS, loose equality, DOM security |
| **C / C++** | Cppcheck, Clang-Tidy | Flawfinder, Semgrep | Memory leaks, buffer overflow, dangling pointers, UB |
| **C#** | Roslyn Analyzers | Security Code Scan | Nullable contexts, SQL parameterization, async leaks |

---

## 6. Docker Sandbox Isolation Specification

To satisfy **Problem 8 (Unsafe Code Execution)**, dynamic checks or linter tools run inside ephemeral containers:

```dockerfile
# Isolation Properties:
# 1. User: non-root (uid=10001, gid=10001)
# 2. Network: --net=none
# 3. Memory Limit: --memory=256m --memory-swap=256m
# 4. CPU Limit: --cpus=0.5
# 5. Read-only filesystem: --read-only with tmpfs at /tmp (max 32MB)
# 6. Process limit: --pids-limit=32
# 7. Execution Timeout: 5.0 seconds hard limit via SIGKILL
# 8. Capabilities: --cap-drop=ALL
```

---

## 7. Rubric Engine Specification

Rubrics are defined in declarative JSON format and versioned per assignment:

```json
{
  "rubric_id": "rubric_alg_01",
  "title": "Binary Search Tree Implementation Rubric",
  "max_score": 100.0,
  "rules": [
    {
      "rule_id": "R_FUNC_NAMES",
      "category": "Style",
      "weight": 10.0,
      "mandatory": false,
      "condition": "naming_convention == 'snake_case'",
      "penalty_per_violation": 2.0,
      "max_deduction": 10.0
    },
    {
      "rule_id": "R_COMPLEXITY_INSERT",
      "category": "Performance",
      "weight": 25.0,
      "mandatory": true,
      "condition": "function['insert'].cyclomatic_complexity <= 5",
      "penalty_per_violation": 15.0,
      "max_deduction": 25.0
    },
    {
      "rule_id": "R_SEC_NO_UNSAFE",
      "category": "Security",
      "weight": 35.0,
      "mandatory": true,
      "condition": "security_findings.count(severity='HIGH') == 0",
      "penalty_per_violation": 35.0,
      "max_deduction": 35.0
    }
  ]
}
```

---

## 8. Plagiarism & Similarity Detection Engine

Plagiarism analysis utilizes a **three-tier similarity algorithm**:
1. **Identifier Normalization:** Replaces all user-defined variable/function names with canonical tokens (`VAR_1`, `FUNC_1`).
2. **Winnowing AST Fingerprinting:** Computes k-gram hashes over AST structure to detect reordered or refactored code.
3. **Control Flow Graph (CFG) Hashing:** Generates hashes of control flow graphs to detect algorithm structure copying.

### Risk Classification
- `LOW` (0% - 25% structural match): Normal submission variance.
- `MEDIUM` (26% - 50% structural match): Minor structural alignment; flagged for TA info.
- `HIGH` (51% - 75% structural match): Significant matching regions; flagged for instructor review.
- `Requires Human Review` (> 75% match): High probability of source sharing. **System never auto-penalizes; instructor must manually review.**

---

## 9. AI Feedback Engine & Guardrails Architecture

### Evidence Validation Contract
Before sending findings to the LLM explanation generator, the `EvidenceValidator` guarantees:
$$\forall f \in \text{Findings}, \quad \text{file}(f) \in \text{Files} \land \text{line\_start}(f) \ge 1 \land \text{line\_end}(f) \le \text{TotalLines}(\text{file}(f))$$

If an LLM response references a line or code snippet that does not match a deterministic finding from the AST or SAST pipeline, the `EvidenceValidator` **rejects the response** and triggers a fallback prompt using the exact rule template.

---

## 10. Relational Database Schema (MySQL 8.0)

```
[Users] 1---* [Courses] 1---* [Assignments] 1---* [Submissions] 1---* [SubmissionFiles]
  |                                 |                   |
  +-- (Roles)                       +-- [Rubrics]       +---* [ASTNodes]
                                           |            +---* [StaticFindings]
                                           +--* [Rules] +---* [SecurityFindings]
                                                        +---* [ComplexityMetrics]
                                                        +---* [Feedback]
                                                        +---* [Grades]
```

---

## 11. High-Level Repository Layout

```
code-review-system/
├── docs/                      # Architectural specs, API docs, ER diagrams
│   └── architecture/
├── frontend/                  # React + TypeScript + Vite UI
│   ├── src/
│   │   ├── components/       # Monaco Editor, Charts, Rubric tables
│   │   ├── pages/            # Student & Instructor dashboards
│   │   └── services/         # API hooks (TanStack Query)
├── backend/                   # FastAPI REST API & Gateway
│   ├── app/
│   │   ├── api/              # Routers (Auth, Assignments, Submissions)
│   │   ├── core/             # Auth, DB session, Config
│   │   ├── models/           # SQLAlchemy ORM models
│   │   └── schemas/          # Pydantic schemas
├── analysis/                  # Analysis Engines
│   ├── parsers/              # Tree-sitter parsers & AST normalizer
│   ├── static/               # Linter & SAST tool wrappers
│   ├── complexity/           # Cyclomatic & Cognitive complexity logic
│   ├── security/             # Vulnerability scanners & rule engines
│   ├── similarity/           # AST & Token Winnowing plagiarism engines
│   └── rubrics/              # Rubric score computation engine
├── ai/                        # AI Explanation Layer
│   ├── prompt_templates/     # Strict pedagogical prompt templates
│   ├── validator/            # EvidenceValidator logic
│   └── service.py            # LLM interface (Gemini API)
├── workers/                   # Celery worker task definitions
├── docker/                    # Dockerfiles & Sandbox security profiles
└── tests/                     # Unit, Integration, SAST, & E2E tests
```

---

## 12. Implementation Roadmap (Phases 0 - 10)

- **Phase 0:** Requirements, Risk Analysis, System Design (Current Step)
- **Phase 1:** Core Authentication, User Roles, Course & Assignment Management
- **Phase 2:** Submission Pipeline, File Storage, & Versioning System
- **Phase 3:** Multi-Language Tree-sitter AST Parser Engine
- **Phase 4:** Static Analysis & Complexity Engine Integration
- **Phase 5:** Security SAST Analysis Engine & Isolated Docker Sandbox
- **Phase 6:** Declarative Rubric Engine & Automatic Score Computation
- **Phase 7:** Plagiarism & Structural Similarity Detection Engine
- **Phase 8:** Evidence Validator & Pedagogical AI Feedback Generator
- **Phase 9:** Student & Instructor React Dashboards & Report Exporter
- **Phase 10:** End-to-End Verification, Performance Optimization & Test Suite Coverage
