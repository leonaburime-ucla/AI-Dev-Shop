# System Blueprint — AI/RAG Platform

- Status: APPROVED
- Scope: New internal platform

## Macro Components

- source ingestion and document normalization
- chunking, indexing, and retrieval layer
- answer orchestration and model routing
- policy and redaction boundary
- evaluation, feedback, and replay tooling

## Runtime Topology

- synchronous analyst question and answer path
- async ingestion, chunking, and index refresh path
- async evaluation and replay path for prompt/model changes

## Dominant Quality Attributes

- security
- performance
- compliance_auditability

## Risks

- the fastest managed AI path may violate restricted-data handling or residency
  expectations if raw ticket content crosses an unapproved external boundary
- citation quality depends on retrieval freshness, corpus versioning, and
  prompt/model traceability remaining explicit
- vector store, embedding model, and base model choices remain open enough that
  vendor certainty would be unjustified without further research
- internal role-scoped workspaces are not customer tenancy and should not be
  treated as a multi-tenant SaaS boundary by default
- two macro directions remain plausible after first pass: a more managed AI
  suite with tighter vendor coupling, or an application-owned RAG core with
  swappable policy, retrieval, and model-routing boundaries

## Spec Decomposition

- `ingestion-domain`
- `retrieval-domain`
- `answer-orchestration-domain`
- `policy-domain`
- `evaluation-ops-domain`
