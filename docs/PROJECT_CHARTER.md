NairaLens AI – Project Charter (v1.0)
Project Overview
NairaLens AI is an AI-powered Financial Intelligence Platform that transforms bank statements and financial records into personalized financial intelligence.
The platform does more than analyze transactions. It learns about users over time, builds contextual financial memory, explains spending patterns, and provides intelligent recommendations through a conversational AI experience.
The goal is to help users understand their finances better, not simply display financial data.

Product Vision
To become Africa's leading AI-powered Financial Intelligence Platform by helping individuals gain a deeper understanding of their financial lives through artificial intelligence.

Core Mission
Transform financial data into personalized financial intelligence.

Product Philosophy
Every feature must satisfy at least one of these principles:
Help the AI understand the user better.
Help the user understand their finances better.
If a feature does neither, it does not belong in the product.

Architecture
The backend must use a Modular Monolith Architecture following Domain-Driven Design (DDD) principles.
Core domains:
Identity
Financial Data
Financial Intelligence
Conversation
Platform
The architecture is considered frozen.
Do not redesign or replace it unless explicitly instructed.

Technology Stack
Backend
Python 3.13+
FastAPI
SQLAlchemy 2.0
Alembic
PostgreSQL
Pydantic v2
JWT Authentication
AI
LLM Provider (pluggable)
AI Orchestrator
Financial Intelligence Graph (FIG)
Infrastructure
Docker
Redis
Celery
S3-compatible Object Storage
Render (Backend)
Railway (Frontend)

Core Engineering Principles
API-First
Every feature must be exposed through well-defined REST APIs before frontend integration.

Thin Controllers
FastAPI routes should only:
Validate requests
Authenticate users
Call services
Return responses
Business logic belongs in the service layer.

Domain Ownership
Each domain owns its own business logic.
Domains communicate through services, not by directly manipulating each other's data.

AI is a Consumer
The AI consumes business data through services.
It must never write directly to the database.

Background Processing
Long-running tasks (such as statement parsing and AI analysis) must execute asynchronously using background workers.

Explainability
Every AI-generated insight should be traceable to supporting financial evidence.

Privacy by Design
Financial information is highly sensitive.
Security, encryption, and user control are mandatory.

Core Business Entities
The platform is centered around the following entities:
User
Account
Statement
Transaction
Merchant
Financial Memory
Evidence
Conversation
Message
Insight
Recommendation
Avoid introducing unnecessary entities unless required by future features.

AI Principles
The AI should:
Understand before advising.
Ask clarifying questions when confidence is low.
Remember confirmed information.
Explain every recommendation.
Learn continuously from interactions.
The AI should never fabricate facts.

Development Approach
Development will be completed incrementally using sprint-based implementation.
Each sprint must:
Compile successfully.
Pass tests.
Be production-ready.
Be committed before moving to the next sprint.
Do not implement future sprint features unless instructed.

Coding Standards
Follow PEP 8.
Use type hints throughout.
Use dependency injection where appropriate.
Keep functions focused and small.
Write reusable services.
Prefer composition over duplication.
Include docstrings for public classes and methods.
Generate clean, maintainable, production-quality code.

Non-Negotiable Rules
Do not:
Change the architecture.
Switch frameworks.
Replace PostgreSQL.
Convert the project to microservices.
Introduce unnecessary abstractions.
Implement features outside the current sprint.
Break backward compatibility without explicit approval.

Current Development Phase
The current phase will always be specified in each implementation prompt.
Example:
Current Sprint: Sprint 1 – Identity Domain
Antigravity should implement only the requested sprint while preserving the overall architecture defined in this charter.

Definition of Done
A sprint is considered complete only if:
The application runs successfully.
Code is production-ready.
Database migrations work.
APIs are functional.
Errors are handled gracefully.
Code follows the established architecture.
The implementation does not introduce regressions.

Final Instruction to Antigravity
Treat this Project Charter as the authoritative engineering guide for the NairaLens AI backend.
Maintain architectural consistency across all implementation phases.
When requirements are ambiguous, prefer clean, maintainable, and scalable solutions that align with the architecture and engineering principles defined above.
Do not redesign the product or architecture. Focus on implementing each sprint accurately and incrementally.

