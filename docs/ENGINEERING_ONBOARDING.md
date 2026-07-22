NairaLens AI – Engineering Onboarding Guide (v1.0)
1. Project Overview
NairaLens AI is an AI-powered financial intelligence platform that helps users understand, organize, and improve their financial lives.
Unlike traditional budgeting apps, NairaLens is an intelligent financial companion. It combines transaction analysis, conversational AI, memory, and personalized recommendations to provide meaningful financial insights rather than just charts and reports.

2. Mission
Empower individuals and small businesses to make better financial decisions through AI-driven insights.

3. Vision
Build Africa's most intelligent personal financial assistant, capable of understanding a user's financial behavior and providing contextual, personalized financial guidance.

4. MVP Scope
The first version focuses on:
User authentication
Uploading bank statements
Extracting transactions
Categorizing transactions
AI-powered financial insights
Conversational financial assistant
Persistent financial memory
Everything else is out of scope until MVP completion.

5. Technology Stack
Backend:
FastAPI
PostgreSQL
SQLAlchemy
Alembic
Pydantic
Docker
Future:
Redis
Celery
Object Storage
LLM APIs
Background workers

6. Architecture
The application follows a Modular Monolith architecture.
Each domain owns its:
models
schemas
repositories
services
routes
Domains communicate only through services.
No direct cross-domain database access.

7. Current Domains
Identity
Financial Data
Financial Intelligence
Conversation
Platform
New domains require architectural approval.

8. Engineering Principles
Keep business logic inside services.
Repositories only access the database.
Routes remain thin.
Validate all input with Pydantic.
Never expose database models directly.
Keep modules loosely coupled.
Prefer readability over clever code.
Follow SOLID principles where practical.

9. Coding Standards
Use type hints throughout.
Write descriptive function names.
Keep functions focused on a single responsibility.
Return consistent API responses.
Raise meaningful exceptions.
Avoid duplicated logic.

10. Security Principles
Hash passwords securely.
Never store plain-text passwords.
Use JWT authentication.
Keep secrets in environment variables.
Validate every request.
Never trust client input.

11. Database Principles
Every schema change requires an Alembic migration.
UUIDs are the preferred primary keys.
Include created_at and updated_at where appropriate.
Design relationships carefully to avoid unnecessary coupling.

12. API Design
RESTful endpoints.
Versioned APIs (/api/v1).
Consistent response formats.
Proper HTTP status codes.
Swagger documentation for every endpoint.

13. Sprint Workflow
For each sprint:
Review requirements.
Implement only the sprint scope.
Write/update tests.
Verify locally with Docker.
Submit implementation for review.
Do not implement future sprint features unless requested.

14. Definition of Done
A sprint is complete only when:
Code builds successfully.
Docker containers run correctly.
Database migrations succeed.
API endpoints work.
Tests pass.
Documentation is updated.
No architectural rules are violated.

15. Non-Negotiable Rules
Do not redesign the architecture.
Do not rename domains without approval.
Do not introduce new frameworks without approval.
Do not implement features outside the current sprint.
If requirements are ambiguous, ask questions instead of making assumptions.

Source of Truth
This guide summarizes the project. The following documents remain authoritative:
Project Charter – Vision and guiding principles.
Product Requirements Document (PRD) – Product requirements and MVP scope.
Software Design Document (SDD) – Technical architecture and implementation details.
If there is any conflict, seek clarification before proceeding.

