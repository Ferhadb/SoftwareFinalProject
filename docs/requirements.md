# SpendSmart — Requirements Specification (LC04)

> **Audience:** Evaluators, stakeholders, and the SpendSmart engineering team.  
> **Author:** Sabuhi Garibov (Frontend, Tests & Documentation)  
> **Reference Document:** [`docs/TECH_TASK.md`](./TECH_TASK.md)

---

## 1. Introduction & Product Vision

**SpendSmart** is an intelligent personal expense tracking and financial budgeting web application designed for students and professionals. Rather than forcing users through tedious multi-field form entry, SpendSmart empowers users to type natural expense descriptions (e.g., `Uber 12.40`, `Starbucks latte 6.50`), automatically categorizing transactions using rules, machine learning, and LLM strategies. 

The platform monitors spending against user-defined monthly budgets in real-time, fires threshold notifications, and presents visual breakdowns and 6-month trends on an interactive dashboard.

---

## 2. User Roles & Personas

- **Guest / Unregistered User:** A visitor who lands on the web service and can view registration/login forms.
- **Registered User:** An authenticated user who manages their personal expenses, configures monthly budgets, receives budget alerts, and tracks spending analytics.
- **System / Autonomous Observers:** Background processes that evaluate transactions against budget policies and dispatch event-driven alerts.

---

## 3. Functional Requirements & User Stories

As specified in LC04 and `TECH_TASK.md §7.5`, the functional requirements are broken down into **14 detailed user stories** across the application domains. Each story follows the standard format:
$$\text{As a } \langle \text{role} \rangle, \text{ I want } \langle \text{goal} \rangle \text{ so that } \langle \text{benefit} \rangle$$
along with formal **Acceptance Criteria (Gherkin format: Given / When / Then)**.

---

### Epic 1: Authentication & Access Control

#### US-01: User Account Registration (FR1)
- **Statement:** As a new user, I want to create an account using my email and a secure password so that I can store and access my private financial records.
- **Acceptance Criteria:**
  - **AC-01.1:** *Given* a unique email and a password of at least 8 characters, *when* submitted to `/auth/register`, *then* a new user is created with status code `201 Created` and password hashed with bcrypt.
  - **AC-01.2:** *Given* an email address that is already registered, *when* submission occurs, *then* the system returns `409 Conflict` with `{"detail": "Email already registered"}`.
  - **AC-01.3:** *Given* a password with fewer than 8 characters, *when* submission occurs, *then* the system rejects it with `422 Unprocessable Entity`.

#### US-02: User Login & JWT Session Management (FR1)
- **Statement:** As a registered user, I want to authenticate with my email and password so that I receive an access token to interact with secure endpoints.
- **Acceptance Criteria:**
  - **AC-02.1:** *Given* valid credentials, *when* `POST /auth/login` is called, *then* return `200 OK` with `{ "access_token": "<jwt>", "token_type": "bearer" }`.
  - **AC-02.2:** *Given* invalid credentials, *when* `POST /auth/login` is called, *then* return `401 Unauthorized`.
  - **AC-02.3:** *Given* a valid bearer token, *when* `GET /auth/me` is called, *then* return the authenticated user's ID and email.

#### US-03: Multi-tenant Data Isolation (NFR1, FR1)
- **Statement:** As an authenticated user, I want strict isolation for my data so that other registered users can never view, update, or delete my expenses and budgets.
- **Acceptance Criteria:**
  - **AC-03.1:** *Given* User A attempts to retrieve an expense belonging to User B via `GET /expenses/{id}`, *then* the system returns `404 Not Found` (preventing ID enumeration).
  - **AC-03.2:** *Given* any analytical query or list request, *then* database queries explicitly filter by `user_id == current_user.id`.

---

### Epic 2: Expense Ingestion & Categorization

#### US-04: Free-Text Expense Parsing (FR2)
- **Statement:** As a busy user, I want to type unstructured text like `"Uber 12.40"` so that the system automatically extracts the monetary amount and clean merchant description without manual form entry.
- **Acceptance Criteria:**
  - **AC-04.1:** *Given* inputs like `"Uber 12.40"`, `"Starbucks 6.50"`, or `"15 Netflix"`, *when* parsed via `ExpenseTextParser`, *then* the numeric token is captured as `Decimal(12.40)` and the remainder as description `"Uber"`.
  - **AC-04.2:** *Given* inputs with no numeric amount, negative numbers, or amount equal to 0, *when* parsed, *then* return `Maybe.nothing()` and reject the request with `422 Unprocessable Entity`.

#### US-05: Automated Categorization via Strategy Pattern (FR3, LC07)
- **Statement:** As a user adding an expense, I want the system to automatically assign an accurate category (Food, Transport, Subscriptions, Shopping, Bills, Health, Entertainment, Other) so that I don't have to select it manually.
- **Acceptance Criteria:**
  - **AC-05.1:** *Given* an expense without an explicit category, *when* processed by the active categorizer strategy (`rules`, `ml`, or `llm`), *then* the category is resolved and recorded with `category_source` matching the strategy name.
  - **AC-05.2:** *Given* unrecognized descriptions where the strategy yields `Nothing`, *then* default safely to `Category.Other` without throwing unhandled exceptions (utilizing the `Maybe` monad).

#### US-06: Manual Category Override (FR3)
- **Statement:** As a user reviewing my transaction list, I want to edit the category of any transaction if the automated categorizer misclassified it.
- **Acceptance Criteria:**
  - **AC-06.1:** *Given* an existing expense, *when* a `PATCH /expenses/{id}` request supplies `{ "category": "Food" }`, *then* update the category and set `category_source = "manual"`.
  - **AC-06.2:** *Given* an expense created with an explicit category field, *then* set `category_source = "manual"` upon creation.

#### US-07: Expense Filtering & History (FR2)
- **Statement:** As an active user, I want to browse my expense history filtered by month and category so that I can inspect specific past expenditures.
- **Acceptance Criteria:**
  - **AC-07.1:** *Given* `GET /expenses?month=2026-11`, *then* return only transactions where `occurred_on` matches November 2026, sorted in descending chronological order.
  - **AC-07.2:** *Given* `GET /expenses?category=Transport`, *then* return only transactions with category `Transport`.

---

### Epic 3: Budget Management & Event-Driven Alerts

#### US-08: Monthly Category Budget Configuration (FR4)
- **Statement:** As a financially conscious user, I want to set or adjust a monthly spending ceiling for each category so that I can manage my budget boundaries.
- **Acceptance Criteria:**
  - **AC-08.1:** *Given* `PUT /budgets/{category}` with `{ "monthly_limit": 200.00 }`, *then* create or update the budget constraint and return `200 OK`.
  - **AC-08.2:** *Given* a negative or zero budget limit, *then* the API rejects with `422 Unprocessable Entity`.
  - **AC-08.3:** *Given* duplicate attempts for the same category, *then* update the existing record (enforcing unique constraint `(user_id, category)`).

#### US-09: Real-time Budget Status Evaluation (FR4)
- **Statement:** As a user viewing my budgets, I want to see current spending amounts, percentages, and health statuses so that I know where I stand relative to my limits.
- **Acceptance Criteria:**
  - **AC-09.1:** *Given* `GET /budgets/status?month=YYYY-MM`, *then* return limit, spent, percent, and level for all configured budgets.
  - **AC-09.2:** Status levels must strictly follow boundary definitions:
    - `ok`: spent percentage $< 80\%$
    - `warning`: spent percentage $\ge 80\%$ and $< 100\%$
    - `exceeded`: spent percentage $\ge 100\%$

#### US-10: Automated Threshold Alert Notification (FR5, LC07 Observer)
- **Statement:** As a budget-constrained user, I want to be alerted when spending reaches 80% or 100% of my monthly limit so that I can immediately curb discretionary spending.
- **Acceptance Criteria:**
  - **AC-10.1:** *Given* an `ExpenseCreated` event published to the `EventBus`, *when* `BudgetAlertObserver` computes monthly spending $\ge 80\%$ (or $\ge 100\%$), *then* an `Alert` record is persisted.
  - **AC-10.2:** *Given* an alert has already fired for a specific `(user_id, category, level, month)`, *then* subsequent expenses in that month must **not** generate duplicate alerts for that level.
  - **AC-10.3:** *Given* an unexpected error occurs inside an observer handler, *then* the error is logged as an error/warning and must **not** abort or roll back the primary expense creation transaction.

---

### Epic 4: Financial Analytics & Aggregation

#### US-11: Monthly Spending Summary & Top Merchants (FR6)
- **Statement:** As an analytic user, I want high-level monthly summaries (total spent, average transaction amount, top category, and top 5 merchants) so that I can assess my consumption habits.
- **Acceptance Criteria:**
  - **AC-11.1:** *Given* `GET /analytics/summary?month=YYYY-MM`, *then* return `{ month, total, count, average, top_category }` computed via SQL aggregates (`SUM`, `COUNT`, `AVG`).
  - **AC-11.2:** *Given* `GET /analytics/top-merchants?month=YYYY-MM&limit=5`, *then* return top 5 merchant names sorted by total spending descending.
  - **AC-11.3:** *Given* a month with no recorded expenses, *then* return total 0, count 0, average 0, and null top category without crashing.

#### US-12: Multi-Month Spending Trend & Breakdown (FR6)
- **Statement:** As a user planning long-term finances, I want a 6-month historical trend line and category percentage breakdown so that I can identify seasonal spending surges.
- **Acceptance Criteria:**
  - **AC-12.1:** *Given* `GET /analytics/trend?months=6`, *then* return 6 chronological months; months with zero expenditure must be explicitly included with `total = 0.00`.
  - **AC-12.2:** *Given* `GET /analytics/by-category?month=YYYY-MM`, *then* return list of categories with totals and percentages that sum up to 100%.

---

### Epic 5: Dashboard & User Experience

#### US-13: Unified Interactive Dashboard (FR7)
- **Statement:** As an active user, I want an integrated single-page dashboard containing quick-add inputs, visual charts, budget progress gauges, and recent transactions.
- **Acceptance Criteria:**
  - **AC-13.1:** *Given* an authenticated user navigates to `/`, *then* render summary cards, Chart.js pie and trend charts, budget progress bars, and recent expense rows.
  - **AC-13.2:** *Given* an unauthenticated visitor navigates to `/`, *then* redirect immediately to `/login`.
  - **AC-13.3:** *Given* quick expense submission via the single text box, *then* refresh the table, charts, and budget progress bars without requiring a full browser page reload.

#### US-14: Responsive Mobile Layout (NFR4, FR7)
- **Statement:** As a mobile smartphone user, I want the dashboard to adapt cleanly to phone-width screens so that I can log expenses on the go.
- **Acceptance Criteria:**
  - **AC-14.1:** At viewport widths $\le 768\text{px}$, columns stack vertically with touch-friendly input sizes and horizontally scrollable tables.

---

## 4. Non-Functional Requirements (NFRs)

| ID | Category | Requirement Specification | Verification Metric |
|---|---|---|---|
| **NFR1** | **Security** | Passwords hashed using `bcrypt`. Authentication via signed JWT tokens (HS256). All queries explicitly scoped by `user_id`. No secret credentials committed to source control. | Automated ruff security linting, manual code review, and isolated user tests. |
| **NFR2** | **Reliability & Availability** | Health endpoint `GET /health` verifies live database connectivity (`SELECT 1`). Returns `200 OK` when healthy and `503 Service Unavailable` when degraded. Zero cold DB crash on initial startup. | UptimeRobot periodic health ping (every 5 minutes); automated tests. |
| **NFR3** | **Maintainability & Modularity** | Clean layered architecture (Router $\rightarrow$ Service $\rightarrow$ Repository). Monads (`Maybe`, `Writer`) and design patterns (Strategy, Factory, Adapter, Observer, Singleton) strictly implemented. Code passes `ruff` and formatting checks. | `ruff check app tests` passes with 0 warnings; CI pipeline enforcement. |
| **NFR4** | **Portability & Containerization** | App must execute with identical behavior across local virtual environments, Docker containers, and Cloud PaaS (Render). Pinned dependencies via `uv.lock`. | Docker multi-stage build under 250 MB; local and dockerized pytest suite passes. |
| **NFR5** | **Observability** | Structured HTTP request logging capturing method, path, HTTP status, and duration in milliseconds. Critical domain events (alerts triggered, categorizer decisions) logged at `INFO`/`WARNING`. | Render runtime application logs stream clean structured lines. |
| **NFR6** | **Performance** | Typical API request latency under 300 ms for CRUD and analytics queries under standard database loads on the free cloud tier. | Database indexing on `expenses.user_id`, `expenses.occurred_on`, `users.email`. |

---

## 5. System Constraints & Out-of-Scope Boundaries

### 5.1 Technology Constraints
- **Runtime:** Python 3.12 exclusively.
- **Database:** SQLite for local development and unit tests; PostgreSQL 16 for production on Render.
- **No Heavy External ORM Migrations:** In accordance with the course specification (`TECH_TASK.md §5.2`), schema tables are generated via `Base.metadata.create_all(engine)` without Alembic to maintain bounded complexity.

### 5.2 Out-of-Scope Features
To maintain focus on core software engineering principles and design patterns, the following are deliberately out of scope:
- Multi-currency conversions (all amounts treated in primary currency, e.g. USD / AZN).
- Direct bank integrations, Open Banking APIs, or live credit card feeds.
- Optical Character Recognition (OCR) / Receipt photo scanning.
- Native mobile applications (iOS/Android store builds).
- Automated email dispatch for password resets or budget notifications.
- Administrative superuser dashboard.
