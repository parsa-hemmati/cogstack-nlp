# Project Context - Living Architecture & Decisions

**Status**: Living Document - Updated with EVERY commit
**Last Updated**: 2025-01-07
**Version**: 1.0.0

> ⚠️ **CRITICAL**: This document MUST be updated before any code commit. No PR can be merged without context updates.

---

## 📌 Purpose

**This document serves as the project's memory and context for:**
- AI assistants starting new sessions (avoid context loss)
- New developers onboarding
- Architectural decision tracking
- Current system state documentation
- Technical debt and future plans

**Update Frequency**: With EVERY code change (no exceptions)

---

## 🎯 Project Overview

### Mission Statement
Build a comprehensive, modular platform that leverages MedCAT's full NLP capabilities to transform healthcare research, delivery, and governance.

### Current Phase
**Phase**: Planning & Foundation (Spec-Kit framework implementation complete)
**Sprint**: Pre-Sprint 1 (specifications and documentation complete)
**Next Milestone**: Implement first feature using Spec-Kit workflow

### Team
- **Size**: 1-3 developers (small team, sequential development acceptable)
- **Roles**: Full-stack developers + clinical SME input
- **AI Assistance**: Claude Code (primary), GitHub Copilot (optional)

---

## 🏗️ System Architecture

### High-Level Architecture (Current State)

```
┌─────────────────────────────────────────────────────┐
│  NOT YET IMPLEMENTED - PLANNED ARCHITECTURE         │
│                                                      │
│  Frontend (Vue 3 + TypeScript)                      │
│  ├── Clinical Dashboard                             │
│  ├── Research Workbench                             │
│  └── Governance Portal                              │
│                                                      │
│  Backend (FastAPI + Python)                         │
│  ├── Patient Search API                             │
│  ├── Timeline View API                              │
│  ├── FHIR Integration                               │
│  └── Authentication/Authorization                   │
│                                                      │
│  Data Layer                                         │
│  ├── PostgreSQL (relational data)                   │
│  ├── Elasticsearch (search + analytics)             │
│  └── Redis (caching)                                │
│                                                      │
│  External Services                                  │
│  ├── MedCAT Service (NLP processing)                │
│  ├── AnonCAT Service (de-identification)            │
│  └── FHIR Server (optional integration)             │
└─────────────────────────────────────────────────────┘
```

**Status**:
- ✅ Documentation complete
- ✅ Specifications written
- ⏳ Implementation NOT started
- 📋 Following Spec-Kit workflow for all features

---

## 🗂️ Current System State

### Implemented Features
**As of 2025-01-07: NONE (Documentation Phase)**

No code has been implemented yet. Current state:
- ✅ Project structure defined
- ✅ Spec-Kit framework implemented
- ✅ Constitution established
- ✅ Documentation written (guides, specs, plans)
- ⏳ Awaiting first feature implementation

### In Progress
1. **Documentation & Planning** (100% complete)
   - Spec-Kit framework
   - Project constitution
   - Technical documentation
   - Compliance framework

### Planned (Not Started)
1. **Sprint 1**: Patient Search & Discovery
2. **Sprint 2**: Patient Timeline View
3. **Sprint 3**: Real-Time Clinical Decision Support
4. **Sprint 4**: Authentication & Authorization

---

## 🧠 Architecture Decision Records (ADRs)

### ADR-001: Specification-Driven Development (Spec-Kit)

**Date**: 2025-01-07
**Status**: ✅ Accepted
**Context**: Need systematic approach for AI-assisted development

**Decision**: Adopt Spec-Kit framework
- Constitution → Specifications → Technical Plans → Tasks → Implementation

**Rationale**:
- Healthcare compliance requires detailed documentation
- Reduces rework through clear specifications
- Enables effective AI-assisted development
- Maintains governance through constitutional principles

**Consequences**:
- ✅ Better alignment with stakeholders
- ✅ Clear audit trail for compliance
- ✅ Reduced context loss between AI sessions
- ⚠️ Additional upfront effort for specifications
- ⚠️ Must maintain discipline (no shortcuts)

**Alternatives Considered**:
- CCPM (Claude Code Project Manager): Too complex for small team
- No framework: Risk of chaos and context loss
- Traditional waterfall: Too rigid for iterative development

**Review Date**: 2025-04-07 (quarterly review)

---

### ADR-002: Technology Stack Selection

**Date**: 2025-01-07
**Status**: ✅ Accepted
**Context**: Need modern, maintainable tech stack for healthcare application

**Decisions**:

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Frontend** | Vue 3 + TypeScript | Composition API, strong typing, excellent DX |
| **Backend** | FastAPI (Python) | Async support, automatic OpenAPI docs, MedCAT integration |
| **Database** | PostgreSQL | ACID compliance, JSON support, proven reliability |
| **Search** | Elasticsearch | Full-text search, analytics, MedCAT results storage |
| **Caching** | Redis | Fast, simple, widely supported |
| **Container** | Docker + Compose | Portability, reproducibility, easy deployment |

**Alternatives Considered**:
- React: More complex, larger bundle size
- Django: More heavyweight, slower than FastAPI
- MongoDB: Less suitable for relational healthcare data
- Solr: More complex than Elasticsearch for our use case

**Consequences**:
- ✅ Modern stack with strong typing
- ✅ Excellent developer experience
- ✅ Well-documented technologies
- ⚠️ Team needs Vue 3 experience (training may be needed)
- ⚠️ Elasticsearch operational complexity

**Review Date**: 2025-07-07 (when tech debt review scheduled)

---

### ADR-003: Healthcare Standards Adoption (FHIR R4)

**Date**: 2025-01-07
**Status**: ✅ Accepted
**Context**: Need interoperability with EHR systems

**Decision**: Adopt FHIR R4 as primary integration standard
- SNOMED-CT for concept coding
- LOINC for lab/observation codes
- CDS Hooks for clinical decision support

**Rationale**:
- FHIR R4 is industry standard (Epic, Cerner, AllScripts support)
- Vendor-neutral interoperability
- ONC interoperability rules compliance
- Future-proof architecture

**Consequences**:
- ✅ Wide ecosystem compatibility
- ✅ Regulatory alignment
- ✅ No vendor lock-in
- ⚠️ Complex specification (learning curve)
- ⚠️ FHIR R5 migration eventually needed

**Alternatives Considered**:
- HL7 v2: Legacy, limited structure
- Proprietary APIs: Vendor lock-in
- FHIR R5: Too new, limited adoption

**Implementation Status**: Documented, not yet implemented

---

### ADR-004: Compliance Framework (HIPAA + GDPR)

**Date**: 2025-01-07
**Status**: ✅ Accepted
**Context**: Healthcare application must comply with regulations

**Decisions**:
- HIPAA Security Rule compliance mandatory
- GDPR/UK GDPR compliance for EU/UK deployments
- 21 CFR Part 11 if used for clinical trials
- Audit logging for ALL PHI access
- Encryption: TLS 1.3 (transit), AES-256 (rest)
- Access Control: RBAC with MFA

**Rationale**:
- Legal requirement (not optional)
- Patient privacy and safety
- Avoid regulatory fines
- Build trust with healthcare organizations

**Consequences**:
- ✅ Regulatory compliance
- ✅ Competitive advantage (certified system)
- ⚠️ Increased development complexity
- ⚠️ Ongoing compliance maintenance required
- ⚠️ Cannot take shortcuts with security

**Documentation**: [docs/compliance/healthcare-compliance-framework.md]

---

## 💾 Data Architecture

### Database Schema (Planned, Not Implemented)

```sql
-- NOT YET CREATED - PLANNED SCHEMA

-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'clinician', 'researcher', 'admin'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Patients (minimal demographics, PHI)
CREATE TABLE patients (
    id UUID PRIMARY KEY,
    mrn VARCHAR(100) UNIQUE NOT NULL,
    -- Additional fields TBD based on requirements
    created_at TIMESTAMP DEFAULT NOW()
);

-- Clinical Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients(id),
    document_type VARCHAR(100), -- 'progress_note', 'discharge_summary', etc.
    content TEXT, -- Encrypted at rest
    created_at TIMESTAMP DEFAULT NOW()
);

-- NLP Annotations (from MedCAT)
-- Stored in Elasticsearch, not PostgreSQL
```

**Status**: Schema design phase, no tables created yet

**Encryption**:
- `documents.content`: Encrypted at rest using database-level encryption
- `patients.*`: All fields encrypted, access logged

---

### Elasticsearch Indices (Planned, Not Implemented)

```json
// NOT YET CREATED - PLANNED INDEX

{
  "patients": {
    "mappings": {
      "properties": {
        "patient_id": { "type": "keyword" },
        "document_id": { "type": "keyword" },
        "concepts": {
          "type": "nested",
          "properties": {
            "cui": { "type": "keyword" },
            "pretty_name": { "type": "text" },
            "source_value": { "type": "text" },
            "confidence": { "type": "float" },
            "negation": { "type": "keyword" },
            "temporality": { "type": "keyword" },
            "experiencer": { "type": "keyword" },
            "certainty": { "type": "keyword" }
          }
        },
        "indexed_at": { "type": "date" }
      }
    }
  }
}
```

**Status**: Index design phase, not created yet

---

## 🔐 Security Architecture

### Authentication & Authorization (Planned)

**Not Yet Implemented**

**Planned Approach**:
- JWT tokens (1 hour expiry, refresh tokens 7 days)
- Role-Based Access Control (RBAC): Clinician, Researcher, Admin, Auditor
- Multi-Factor Authentication (MFA) for production
- OAuth 2.0 / SMART-on-FHIR for EHR integration

**Security Principles** (from Constitution):
1. Privacy by Design (not bolted on)
2. Minimum necessary access
3. Audit logging for all PHI access
4. Encryption everywhere (TLS 1.3, AES-256)

**Reference**: [docs/compliance/healthcare-compliance-framework.md]

---

### API Security (Planned)

**Not Yet Implemented**

**Planned Controls**:
- Rate limiting: 100 req/min per user
- Input validation: Pydantic schemas on all endpoints
- Output sanitization: Prevent XSS
- CORS: Whitelist allowed origins
- CSRF protection: SameSite cookies

---

## 🧪 Testing Strategy

### Test Pyramid (Target Coverage)

```
      /\
     /  \    E2E (10%)      - Critical user workflows
    /----\
   /      \  Integration (30%) - API contracts, service interactions
  /--------\
 /          \ Unit (60%)      - Business logic, pure functions
```

**Minimum Coverage**: 80% overall, 100% for critical paths

**Critical Paths** (require 100% coverage):
- Authentication/authorization
- PHI access and audit logging
- Meta-annotation filtering (clinical decision support)
- De-identification (AnonCAT)
- FHIR resource mapping

**Status**: No tests written yet (no code implemented)

---

## 📊 Performance Requirements

### Response Time Targets

| Operation | Target (P95) | Rationale |
|-----------|--------------|-----------|
| Patient Search | <500ms | User expectation for interactive search |
| API Endpoints | <200ms | Keep UI responsive |
| Document Processing (MedCAT) | <2s | Acceptable for batch processing |
| Dashboard Load | <2s | Initial page load |
| FHIR Resource Creation | <500ms | Real-time integration |

**Status**: Targets defined, no benchmarking done yet

**Validation**: Load testing required before production (500 concurrent users)

---

## 🔌 Integration Points

### MedCAT Service

**Status**: External dependency, assumed available

**Integration**:
- REST API: `http://medcat-service:5000`
- Input: Raw clinical text
- Output: JSON with entities + meta-annotations
- Expected Response Time: <2 seconds per document

**Configuration**:
```python
# Planned configuration (not implemented)
MEDCAT_SERVICE_URL = os.getenv("MEDCAT_SERVICE_URL", "http://localhost:5000")
MEDCAT_API_KEY = os.getenv("MEDCAT_API_KEY")
MEDCAT_TIMEOUT = 5  # seconds
```

**Meta-Annotations Required**:
- Negation (Affirmed/Negated)
- Temporality (Current/Historical/Future)
- Experiencer (Patient/Family/Other)
- Certainty (Confirmed/Suspected/Hypothetical)

**Reference**: [docs/advanced/meta-annotations-guide.md]

---

### FHIR Server (Optional)

**Status**: Planned, not implemented

**Integration Options**:
1. HAPI FHIR (Java, open source)
2. Firely Server (.NET, open source)
3. Epic FHIR API (if integrating with Epic)

**Planned Usage**:
- Read: DocumentReference (clinical notes)
- Write: Observation (NLP-extracted concepts)
- Hooks: CDS Hooks for real-time alerts

**Reference**: [docs/integration/fhir-integration-guide.md]

---

## 🐛 Known Issues & Technical Debt

### Current Issues
**None** (no code implemented yet)

### Technical Debt Register

| ID | Issue | Impact | Priority | Plan |
|----|-------|--------|----------|------|
| DEBT-001 | No implementation yet | N/A | - | Start with Sprint 1 |

**Future Debt Tracking**: Update this section when code is implemented

---

## 🚧 Work In Progress

### Active Development

**As of 2025-01-07**: No active development

**Next Steps**:
1. Review and approve all specifications
2. Begin Sprint 1 implementation (Patient Search)
3. Set up development environment (Docker, databases)
4. Initialize frontend and backend projects

---

## 🗺️ Roadmap & Future Plans

### Phase 1: Foundation (Weeks 1-8) - NOT STARTED
- [ ] Sprint 1: Patient Search & Discovery
- [ ] Sprint 2: Patient Timeline View
- [ ] Sprint 3: Real-Time Clinical Decision Support
- [ ] Sprint 4: Authentication & Authorization

### Phase 2: Research & Analytics (Weeks 9-16) - PLANNED
- [ ] Sprint 5: Cohort Builder
- [ ] Sprint 6: Concept Analytics Dashboard
- [ ] Sprint 7: Clinical Trial Recruitment
- [ ] Sprint 8: Export & Integration Tools

### Phase 3: Governance & Quality (Weeks 17-22) - PLANNED
- [ ] Sprint 9: Quality Dashboard
- [ ] Sprint 10: Clinical Coding Assistant
- [ ] Sprint 11: Privacy & Compliance Monitor
- [ ] Sprint 12: Adverse Event Surveillance

### Phase 4: Polish & Launch (Weeks 23-24) - PLANNED
- [ ] Sprint 13: Performance Optimization
- [ ] Sprint 14: Documentation & Training

**Reference**: [docs/PROJECT_PLAN.md]

---

## 🔄 Recent Changes

### Change Log Format

```markdown
## [Date] - [Commit SHA] - [Author]
### Added
- What was added

### Changed
- What was changed

### Removed
- What was removed

### Why
- Rationale for changes

### Impact
- How this affects the system

### Migration Notes
- What users/developers need to do
```

---

### 2025-01-07 - Living Context Document + Git Hooks

**Commits**:
- [Current] - CONTEXT.md + enforcement hooks

**Added**:
- **CONTEXT.md** - Living architecture and decisions document
  - System architecture (current and planned)
  - Architecture Decision Records (ADR framework)
  - Current system state (features implemented/planned)
  - Integration points and dependencies
  - Technical debt register
  - Recent changes log
  - Design patterns and conventions
  - Context for AI assistants (prevents context loss!)

- **Git Hooks** - Enforce CONTEXT.md updates
  - Pre-commit hook requires CONTEXT.md update with code changes
  - Warns about console.log/debugger statements
  - Warns about TODOs without tasks
  - Installation script: `scripts/install-git-hooks.sh`
  - Documentation: `.git-hooks/README.md`

**Changed**:
- **CLAUDE.md** - Added mandatory CONTEXT.md section
  - Prominent warning at top to read CONTEXT.md first
  - Added to code review checklist (mandatory)
  - "NO COMMIT WITHOUT CONTEXT.MD UPDATE" rule

**Why**:
- **Solve context loss problem** between AI-assisted coding sessions
- **Create institutional memory** that persists across team changes
- **Enable better AI assistance** by providing complete system context
- **Document architectural decisions** with rationale (ADRs)
- **Track system evolution** through living documentation

**Impact**:
- ✅ AI assistants have complete context at start of each session
- ✅ New developers can onboard by reading CONTEXT.md
- ✅ Architectural decisions documented with rationale
- ✅ Technical debt tracked systematically
- ✅ System state always up-to-date
- ⚠️ Requires discipline to update CONTEXT.md (enforced by git hook)

**Migration Notes**:
- Install git hooks: `./scripts/install-git-hooks.sh`
- Read CONTEXT.md before making any changes
- Update CONTEXT.md with EVERY code commit

---

### 2025-01-07 - Initial Setup

**Commits**:
- `da363edf` - Documentation merge
- `84ba0193` - Enhanced documentation + Spec-Kit
- `840084bf` - Quick start guide + workflow comparison
- `0952bd4a` - CLAUDE.md AI assistant guide

**Added**:
- Spec-Kit framework (`.specify/`)
- Project constitution with 10 core principles
- Comprehensive documentation (Meta-annotations, FHIR, Compliance)
- Enhancement analysis (40+ identified gaps)
- Workflow frameworks comparison guide
- AI assistant guide (CLAUDE.md)

**Changed**:
- README.md with quick start guides
- Documentation structure (added advanced/, integration/, compliance/)

**Why**:
- Establish systematic development workflow
- Leverage MedCAT's full potential
- Ensure compliance with healthcare regulations
- Enable effective AI-assisted development

**Impact**:
- Foundation laid for systematic feature development
- Clear governance through constitution
- Reduced context loss for AI assistants
- Improved onboarding for developers

**Migration Notes**: None (initial setup)

---

## 📝 Key Design Patterns

### Not Yet Established (No Code Implemented)

**Planned Patterns**:

#### Backend
- Repository Pattern (data access abstraction)
- Service Layer Pattern (business logic separation)
- Dependency Injection (FastAPI dependencies)
- Async/Await (non-blocking I/O)

#### Frontend
- Composition API (Vue 3)
- Composables (reusable stateful logic)
- Pinia Stores (state management)
- Component-based architecture

**Update when implemented**: Add examples and rationale

---

## 🧩 Module Dependencies

### Not Yet Established (No Code Implemented)

**Planned Structure**:

```
frontend/
├── src/
│   ├── components/ (UI components)
│   ├── composables/ (reusable logic)
│   ├── services/ (API clients)
│   ├── stores/ (state management)
│   └── views/ (page components)

backend/
├── app/
│   ├── api/ (endpoints)
│   ├── services/ (business logic)
│   ├── models/ (database models)
│   ├── schemas/ (Pydantic schemas)
│   └── clients/ (external service clients)
```

**Update when implemented**: Document actual dependencies

---

## 🔍 Debugging & Troubleshooting

### Common Issues (To Be Populated)

**This section will be updated as issues are discovered during development**

Format:
```markdown
### Issue: [Description]
**Symptoms**: What you see
**Cause**: Root cause
**Solution**: How to fix
**Prevention**: How to avoid
```

---

## 📚 Important Resources

### Internal Documentation
- [Constitution](.specify/constitution/project-constitution.md) - Core principles
- [Spec-Kit Guide](.specify/README.md) - Development workflow
- [CLAUDE.md](CLAUDE.md) - AI assistant guide
- [Project Plan](docs/PROJECT_PLAN.md) - Sprint breakdown
- [Workflow Frameworks](docs/WORKFLOW_FRAMEWORKS_GUIDE.md) - Spec-Kit vs CCPM

### Domain Knowledge
- [Meta-Annotations Guide](docs/advanced/meta-annotations-guide.md)
- [FHIR Integration Guide](docs/integration/fhir-integration-guide.md)
- [Compliance Framework](docs/compliance/healthcare-compliance-framework.md)

### External Resources
- [MedCAT GitHub](https://github.com/CogStack/MedCAT)
- [FHIR R4 Spec](https://hl7.org/fhir/R4/)
- [Vue 3 Docs](https://vuejs.org/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

---

## 🤝 Contributing to This Document

### Update Guidelines

**MANDATORY**: Update CONTEXT.md with EVERY code commit

**What to Update**:

1. **Architecture changes**: Update "System Architecture" section
2. **New features**: Update "Implemented Features" and add ADR if needed
3. **Tech stack changes**: Update "Technology Stack" and create ADR
4. **Dependencies**: Update "Module Dependencies" and "Integration Points"
5. **Issues found**: Add to "Known Issues & Technical Debt"
6. **Performance data**: Update "Performance Requirements" with actuals
7. **Security changes**: Update "Security Architecture"
8. **Recent changes**: Add entry to "Change Log" with every commit

**Format for ADRs**:
```markdown
### ADR-XXX: [Title]

**Date**: YYYY-MM-DD
**Status**: ✅ Accepted / ⏳ Proposed / ❌ Rejected / 🔄 Superseded by ADR-YYY
**Context**: Why this decision is needed

**Decision**: What we decided

**Rationale**:
- Why this decision was made
- What problem it solves

**Consequences**:
- ✅ Positive impacts
- ⚠️ Negative impacts / trade-offs

**Alternatives Considered**:
- Option A: Why rejected
- Option B: Why rejected

**Review Date**: When to re-evaluate
```

---

## ✅ Pre-Commit Checklist

**Before committing code, verify:**

- [ ] CONTEXT.md updated with relevant changes
- [ ] New ADR added if architecture decision made
- [ ] "Recent Changes" section updated
- [ ] "Implemented Features" or "In Progress" updated
- [ ] Technical debt noted if shortcuts taken
- [ ] Integration points documented if new service added
- [ ] Performance data added if benchmarking done
- [ ] Security implications documented
- [ ] Module dependencies updated if new modules added

**Enforce with pre-commit hook** (see [.git/hooks/pre-commit.sample])

---

## 🎯 Context for AI Assistants

### Quick Onboarding (Read This First!)

**Project State**: Documentation complete, no code implemented yet

**What Exists**:
- ✅ Spec-Kit framework and constitution
- ✅ Detailed specifications for 14 sprints
- ✅ Comprehensive documentation (compliance, FHIR, meta-annotations)
- ✅ CLAUDE.md guide for AI assistants

**What Doesn't Exist**:
- ❌ No frontend code
- ❌ No backend code
- ❌ No database
- ❌ No tests

**Your First Task Should Be**:
1. Read CLAUDE.md (AI assistant guide)
2. Read constitution (.specify/constitution/project-constitution.md)
3. Read this CONTEXT.md file completely
4. Check for specification of feature you're implementing
5. Follow Spec-Kit workflow (spec → plan → tasks → implement)

**Critical Requirements**:
- Patient safety first (validate accuracy >90% for safety-critical)
- Privacy by design (audit log ALL PHI access)
- Use meta-annotations (Negation, Temporality, Experiencer) - required!
- Write tests first (TDD approach, 80% coverage minimum)
- Update CONTEXT.md with EVERY commit

**Healthcare-Specific Context**:
- Meta-annotations prevent false positives (60% → 95% precision)
- Always filter: Negation=Affirmed, Experiencer=Patient, Temporality=Current
- FHIR R4 is the integration standard (not R5, not HL7 v2)
- HIPAA compliance is non-negotiable (audit everything)
- Confidence scores must be displayed to users (transparency principle)

---

## 🔗 Cross-References

**This document is part of the project knowledge base:**

- **CLAUDE.md**: How AI assistants should work (references this doc for context)
- **Spec-Kit**: Workflow framework (this doc tracks implementation state)
- **Constitution**: Principles (this doc ensures compliance via ADRs)
- **Documentation**: Domain guides (this doc links to them for context)

**Update Cascade**: Changes here may require updates to other documents

---

## 📊 Metrics & KPIs

### Development Metrics (To Be Tracked)

**Code Quality**:
- Test Coverage: Target >80% (Not yet measurable - no code)
- Code Review: 100% of PRs reviewed before merge
- Security Vulnerabilities: Target 0 critical (Will track via Snyk)

**Performance** (Once Implemented):
- API Response Time (P95): Target <500ms
- Search Latency (P95): Target <500ms
- Page Load Time (P95): Target <2s
- Uptime: Target >99.5%

**Adoption** (Post-Launch):
- Active Users: Target 50+ within 6 months
- Daily Searches: Target 1000+
- NPS Score: Target >50

**Status**: Baselines will be established during Sprint 1

---

## 🚨 Breaking Changes & Migrations

### Migration History

**This section will track breaking changes that require migration steps**

Format:
```markdown
### [Date] - [Version] - [Description]

**Breaking Change**: What broke
**Migration Steps**: How to migrate
**Timeline**: Deadline for migration
**Support**: Who to contact for help
```

**Current Status**: No migrations needed (no code implemented)

---

## 🎓 Lessons Learned

### Development Lessons (To Be Populated)

**This section will capture lessons learned during development**

Format:
```markdown
### Lesson: [Title]
**Context**: What happened
**What Went Wrong**: The mistake
**What We Learned**: The lesson
**Action**: How we'll prevent this
```

**Example (Placeholder)**:
```markdown
### Lesson: Importance of Meta-Annotations

**Context**: Initial cohort query without meta-annotation filtering
**What Went Wrong**: 60% precision, many false positives (family history included)
**What We Learned**: Meta-annotations are CRITICAL for healthcare NLP
**Action**: Always filter by Negation, Experiencer, Temporality (now in CLAUDE.md)
```

---

## 📞 Support & Escalation

### When You Need Help

**Stuck on implementation?**
1. Check this CONTEXT.md (system state, ADRs, design patterns)
2. Check CLAUDE.md (code standards, common pitfalls)
3. Check specifications (.specify/specifications/)
4. Check domain guides (docs/advanced/, docs/integration/)
5. Ask user with specific context

**Found a gap in documentation?**
- Update the relevant document
- Add clarification
- Commit with descriptive message

**Major architecture decision needed?**
- Create ADR in this file
- Discuss with user/team
- Get approval before implementing
- Reference ADR in code comments

---

## 📅 Review Schedule

### Regular Reviews

**Weekly** (During Active Development):
- Update "Work In Progress" section
- Update "Recent Changes" log
- Review technical debt register

**Monthly**:
- Review ADRs (still valid?)
- Update roadmap status
- Assess performance metrics

**Quarterly**:
- Full architecture review
- Constitution review (any principles need updating?)
- Technology stack review (any major changes needed?)

**Next Scheduled Review**: TBD (when development starts)

---

**END OF CONTEXT DOCUMENT**

---

## 📝 Meta Information

**Document Owner**: Tech Lead / Development Team
**Maintained By**: All developers + AI assistants
**Update Frequency**: With EVERY code commit
**Version Control**: Git (committed with code)
**Enforcement**: Pre-commit hook (recommended)

**Questions about this document?**
- Check CLAUDE.md for AI assistant guidance
- Ask the team lead
- Open a discussion issue

**Remember**: This document is only valuable if it's kept up-to-date. Update it religiously! 🙏
