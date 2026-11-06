# SpendSmart

Expense tracker with AI categorization, budgets and analytics. Type `Uber 12.40`, get a category, a budget warning and a dashboard.

Built for UE606 Software Engineering (UFAZ). Stack: **Python 3.12, FastAPI, uv, pytest, Docker, GitHub Actions, GHCR, Render**.

## Run

```bash
uv sync                              # install deps
uv run uvicorn app.main:app --reload # http://localhost:8000/docs
uv run pytest                        # tests
uv run ruff check .                  # lint
```

## Team

| Member | Area |
|---|---|
| Farhad | Skeleton, DB/Repository layer, Render deploy, monitoring, rollback |
| Hakim | CI, Dockerfile, CD to GHCR, docker-compose |
| Huseyn | Auth, expenses, budgets, budget alerts |
| Maryam | AI categorizer, analytics, seed data |
| Sabuhi | Dashboard UI, tests, docs |

## Where each PW appears

| PW | Technology | In this repo |
|---|---|---|
| 1 | Git, branches, GitHub | Feature branches, PRs with review, no direct push to `main` |
| 2 | Web app | FastAPI app in `app/` (Swagger at `/docs`) |
| 3 | pytest | `tests/` |
| 4 | CI | `.github/workflows/ci.yml` |
| 5 | Docker | `Dockerfile` |
| 6 | CD, GHCR | `.github/workflows/cd.yml` |
| 7 | Render auto-deploy | Render service tracks `main` |
| 8 | Monitoring, rollback | `/health`, Render logs, UptimeRobot, rollback demo |

## Where each lecture appears

| Lecture | Concept | In this project |
|---|---|---|
| LC01–02 | SDLC, Agile, Scrum | Sprints and a board on GitHub Projects |
| LC03 | Planning, risks, collaboration | Task split per member, risk list in `docs/` |
| LC04 | Requirements | User stories in `docs/requirements.md` |
| LC05 | Architecture, cohesion/coupling | Layered: router, service, repository. One module per owner |
| LC06 | UML | Class and component diagrams in `docs/` |
| LC07 | OOP, design patterns | Strategy, Factory, Adapter, Observer, Singleton (below) |
| LC08 | Monads | `Maybe` in the categorizer pipeline, `Writer` for the audit log |
| LC09 | Testing/QA | Unit, integration and regression tests in CI; rollback test |
| LC10 | SCM, workflows, CI | Branch per feature, code review, automated build |
| LC11 | Refactoring, maintenance | `ruff` in CI, refactor commits kept separate |
| LC12 | Deployment, DevOps | CI/CD, deploy from `main`, continuous monitoring, rollback |

## Design patterns (LC07/LC08)

| Pattern | Used for |
|---|---|
| Strategy | Swappable categorizers: rules, ML, LLM |
| Factory | Builds the configured categorizer |
| Adapter | Wraps the external LLM provider |
| Observer | Budget exceeded notifies alert handlers |
| Singleton | App settings |
| Maybe monad | Categorizer returns a category or nothing, with no crashes |
| Writer monad | Collects an audit log while processing an expense |

## Branching rules

- `main` is protected. Work on `feat/*`, `fix/*`, `ci/*`, `docs/*`, `test/*`.
- Open a PR, have another member review it, then merge.
- Small commits with clear messages.
