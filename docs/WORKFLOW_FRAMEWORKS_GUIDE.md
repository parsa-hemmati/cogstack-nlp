# Workflow Frameworks: Spec-Kit vs CCPM vs Hybrid

**Last Updated**: 2025-01-07
**Purpose**: Help teams choose the right development workflow framework

---

## Executive Summary

This document compares three approaches for specification-driven development with AI agents:

1. **Spec-Kit** (currently implemented): Specification-first with local filesystem storage
2. **CCPM** (alternative): GitHub Issues-native with parallel agent orchestration
3. **Hybrid** (recommended for teams): Combine both for maximum benefit

---

## Framework Comparison

### Spec-Kit

**Repository**: [github.com/github/spec-kit](https://github.com/github/spec-kit)

**Philosophy**: Specifications are executable artifacts, stored in `.specify/` directory

**Workflow**:
```
Constitution → Specification → Technical Plan → Tasks → Implementation
```

**Storage**: Local filesystem (`.specify/` directory)

**Strengths**:
- ✅ Deep specifications with full context preservation
- ✅ Constitution establishes project governance and principles
- ✅ Version-controlled alongside code
- ✅ Works offline
- ✅ Clear separation: WHAT/WHY (spec) vs. HOW (plan) vs. DO (tasks)
- ✅ Ideal for complex features requiring detailed documentation

**Weaknesses**:
- ❌ No built-in parallel agent support
- ❌ Requires manual synchronization with issue trackers
- ❌ Less visibility for non-technical stakeholders
- ❌ Single-agent focused (sequential execution)

**Best For**:
- Solo developers or small teams (2-3 people)
- Projects requiring deep specifications and governance
- Regulated industries (healthcare, finance) with compliance needs
- Features with complex requirements and acceptance criteria

---

### CCPM (Claude Code Project Manager)

**Repository**: [github.com/automazeio/ccpm](https://github.com/automazeio/ccpm)

**Philosophy**: GitHub Issues as single source of truth, enabling parallel agent execution

**Workflow**:
```
PRD → Epic (GitHub Issue) → Tasks (sub-issues) → Worktrees → Parallel Implementation
```

**Storage**: GitHub Issues + Git worktrees

**Strengths**:
- ✅ Multiple agents work in parallel on independent tasks
- ✅ GitHub-native (issues, projects, labels)
- ✅ Excellent team visibility
- ✅ Built-in progress tracking
- ✅ Agent specialization (UI agent, API agent, DB agent)
- ✅ Traceability from idea to production code

**Weaknesses**:
- ❌ Requires GitHub (not suitable for air-gapped environments)
- ❌ Less detailed specifications (optimized for GitHub Issues format)
- ❌ Context split across multiple issues (can lose big picture)
- ❌ Steeper learning curve for CCPM commands
- ❌ No built-in governance/constitution layer

**Best For**:
- Teams (4+ people)
- Projects with independent feature streams
- Organizations already using GitHub Projects
- When parallel development is critical (time-sensitive projects)

---

## Detailed Comparison Matrix

| Dimension | Spec-Kit | CCPM | Hybrid |
|-----------|----------|------|--------|
| **Specification Depth** | Very deep (10+ page specs) | Moderate (GitHub Issue format) | Deep specs → Task decomposition |
| **Governance** | Constitution enforces principles | Manual policy enforcement | Constitution + Issue templates |
| **Parallel Execution** | Sequential (one agent) | Parallel (multiple agents) | Parallel with spec guardrails |
| **Visibility** | Code reviewers only | Entire team + stakeholders | Both spec artifacts and GitHub |
| **Traceability** | Spec → Code (via commit refs) | Issue → Branch → PR → Code | Spec → Epic → Issues → Code |
| **Context Preservation** | Excellent (full specs in repo) | Good (issues link context) | Excellent (specs + issues) |
| **Offline Support** | Full | None (requires GitHub API) | Partial (specs offline, sync later) |
| **Learning Curve** | Low (just files + structure) | Medium (CCPM commands) | Medium-high (both systems) |
| **Setup Time** | 30 minutes | 1-2 hours | 2-3 hours |
| **Compliance Ready** | Yes (audit trails, documentation) | Partial (requires export for audits) | Yes (specs cover compliance) |
| **Cost** | Free | Free (GitHub Issues free tier) | Free |

---

## Use Case Decision Tree

### Start Here: What's Your Team Size?

#### Solo Developer or Pair
**Recommendation**: **Spec-Kit**

**Rationale**:
- Parallel execution not needed
- Simpler workflow
- Full control over specifications
- No GitHub dependency

**Setup**:
```bash
# Already implemented in this repo!
cat .specify/README.md
```

---

#### Small Team (3-5 people)
**Recommendation**: **Hybrid** (Spec-Kit + Manual GitHub Issues)

**Rationale**:
- Benefit from detailed specs
- Manual issue creation manageable at small scale
- Avoid complexity of CCPM automation

**Setup**:
1. Write Spec-Kit specifications
2. Manually create GitHub Issues referencing specs
3. Link issues back to spec files

**Example**:
```markdown
# GitHub Issue #42: Implement FHIR Integration

**Specification**: See [.specify/specifications/fhir-integration.md]

**Tasks**:
- [ ] Task 1: Set up FHIR server
- [ ] Task 2: Create FHIR client wrapper
- [ ] Task 3: Map MedCAT → FHIR Observations
```

---

#### Medium Team (6-15 people)
**Recommendation**: **Hybrid** (Spec-Kit + CCPM)

**Rationale**:
- Multiple agents can work in parallel
- Detailed specs prevent misalignment
- CCPM orchestration reduces coordination overhead

**Setup**:
1. Write Spec-Kit specifications (constitution, detailed requirements)
2. Use CCPM to convert specs to epics and tasks
3. Launch parallel agents with CCPM

**Workflow**:
```bash
# 1. Write detailed spec (Spec-Kit)
.specify/specifications/patient-timeline-view.md

# 2. Convert to GitHub epic (CCPM)
/pm:prd-parse .specify/specifications/patient-timeline-view.md

# 3. Break into parallel tasks (CCPM)
/pm:epic-oneshot

# 4. Specialized agents work in parallel
/pm:issue-start #50  # Agent 1: Backend API
/pm:issue-start #51  # Agent 2: Frontend UI
/pm:issue-start #52  # Agent 3: Integration tests
```

---

#### Large Team (16+ people) or Enterprise
**Recommendation**: **Hybrid** (Spec-Kit + CCPM + Project Management Tools)

**Rationale**:
- Governance critical (constitution)
- Compliance documentation required
- Many parallel work streams
- Stakeholder visibility essential

**Additional Tools**:
- GitHub Projects for roadmap visualization
- Confluence/SharePoint for stakeholder-facing docs
- Automated spec → issue sync pipelines

---

## Hybrid Approach: Best of Both Worlds

### Architecture

```
┌─────────────────────────────────────────────────┐
│  .specify/constitution/                         │
│  Project Constitution (governance)              │
│  - Core principles                              │
│  - Non-negotiables                              │
│  - Quality standards                            │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  .specify/specifications/                       │
│  Detailed Feature Specifications                │
│  - Context and goals                            │
│  - User stories                                 │
│  - Requirements                                 │
│  - Acceptance criteria                          │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  CCPM: GitHub Epic                              │
│  - Links back to spec file                     │
│  - High-level milestone                         │
│  - Tracks overall progress                      │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  CCPM: GitHub Issues (Tasks)                    │
│  - Decomposed from spec                         │
│  - Independent work units                       │
│  - Agent assignments                            │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  Git Worktrees + Parallel Agents                │
│  - Agent 1: API (worktree-1)                    │
│  - Agent 2: UI (worktree-2)                     │
│  - Agent 3: Tests (worktree-3)                  │
└─────────────────────────────────────────────────┘
```

---

### Implementation Guide

#### Phase 1: Establish Governance (Spec-Kit)

**Duration**: 1-2 days

**Actions**:
1. Review and customize [.specify/constitution/project-constitution.md](.specify/constitution/project-constitution.md)
2. Get stakeholder buy-in (Product Owner, Tech Lead, Clinical SME)
3. Establish approval process for spec changes

**Deliverable**: Approved constitution

---

#### Phase 2: Write First Specification (Spec-Kit)

**Duration**: 2-3 days per major feature

**Template**: [.specify/specifications/meta-annotations-ui.md](.specify/specifications/meta-annotations-ui.md)

**Contents**:
- Context (WHAT and WHY)
- Goals and non-goals
- User stories with acceptance criteria
- Functional and non-functional requirements
- Risks and mitigation
- Alignment with constitution

**Review Process**:
1. Draft specification
2. Technical review (Tech Lead)
3. Product review (Product Owner)
4. Clinical review (if applicable)
5. Approval and commit

---

#### Phase 3: Set Up CCPM (If Using Hybrid)

**Duration**: 1-2 hours

**Prerequisites**:
- GitHub repository
- Claude Code access
- CCPM installed

**Setup**:
```bash
# 1. Install CCPM (if not already available)
# Follow: https://github.com/automazeio/ccpm

# 2. Initialize CCPM in your repo
/pm:init

# 3. Configure agent roles
# Edit .ccpm/config.yml to define agent specializations
```

---

#### Phase 4: Convert Spec to Epic (CCPM)

**Duration**: 30 minutes

**Process**:
```bash
# Parse specification into GitHub epic
/pm:prd-parse .specify/specifications/fhir-integration.md

# Review generated epic (will be created as GitHub Issue)
# Edit if needed to add labels, milestones, assignees

# Link epic back to spec file in issue description
```

**Epic Template**:
```markdown
# [EPIC] FHIR Integration

**Specification**: [.specify/specifications/fhir-integration.md]

## Goals
- Expose NLP results as FHIR Observations
- Support FHIR R4 DocumentReference input
- Enable CDS Hooks integration

## Tasks
Will be decomposed into sub-issues via `/pm:epic-oneshot`

## Acceptance Criteria
See specification file for detailed criteria.
```

---

#### Phase 5: Decompose and Execute (CCPM)

**Duration**: Ongoing

**Process**:
```bash
# 1. Break epic into independent tasks
/pm:epic-oneshot

# This creates GitHub sub-issues:
# - Issue #42: Set up FHIR server
# - Issue #43: Create FHIR client wrapper
# - Issue #44: Map MedCAT → FHIR Observations
# - Issue #45: Integration tests
# - Issue #46: Documentation

# 2. Launch agents on tasks
/pm:issue-start #42  # Agent 1: Infrastructure
/pm:issue-start #43  # Agent 2: API Development
/pm:issue-start #45  # Agent 3: Testing

# 3. Monitor progress
/pm:status

# 4. Review and merge
# Each agent creates PR, standard code review applies
```

---

## Workflow Recipes

### Recipe 1: Simple Feature (Spec-Kit Only)

**When**: Small feature, solo developer, no parallel work needed

**Steps**:
1. Write specification in `.specify/specifications/`
2. Create technical plan in `.specify/plans/`
3. Break into tasks in `.specify/tasks/`
4. Implement task-by-task
5. Test against acceptance criteria
6. Create PR with reference to spec

**Time**: 1-2 days (depending on complexity)

---

### Recipe 2: Complex Feature (Hybrid)

**When**: Large feature, team of 3-5, parallel work possible

**Steps**:
1. Write specification (Spec-Kit) - 1 day
2. Review and approve spec - 1 day
3. Convert to CCPM epic - 30 minutes
4. Decompose into tasks (CCPM) - 1 hour
5. Launch 3-5 agents in parallel (CCPM) - 1-2 days
6. Review and integrate PRs - 1 day
7. Final acceptance testing - 1 day

**Time**: 3-5 days (vs. 7-10 days sequential)

---

### Recipe 3: Emergency Hotfix (Skip Both)

**When**: Critical production bug, needs immediate fix

**Steps**:
1. Create hotfix branch
2. Fix bug
3. Write tests
4. Create PR
5. Deploy ASAP
6. **Retrospectively**: Create spec if bug reveals gap in requirements

**Time**: Hours (don't let process block critical fixes!)

---

## Migration Path

### Current State: No Framework

**Weeks 1-2**: Implement Spec-Kit
- Create constitution
- Write first 2-3 specifications for existing features (documentation)
- Establish review process

**Weeks 3-4**: Practice Spec-Kit
- Use for next 2-3 new features
- Refine templates based on feedback

**Weeks 5-6**: Evaluate Need for CCPM
- Are you frequently blocked waiting for sequential work?
- Do you have 3+ developers who could work in parallel?
- Is coordination overhead becoming painful?

**If yes → Weeks 7-8**: Add CCPM
- Set up CCPM
- Convert 1 existing spec to CCPM epic (pilot)
- Launch parallel agents on pilot feature

**If no → Continue with Spec-Kit**
- It's working! Don't add complexity unnecessarily

---

### Current State: Spec-Kit Implemented (This Repo)

**You are here!**

**Next Steps**:

**Option A: Stay with Spec-Kit** (Recommended if team < 3)
- Continue building specs
- Use existing workflow
- Re-evaluate quarterly

**Option B: Add CCPM** (If team growing)
- Install CCPM
- Convert one existing spec to pilot
- Run A/B comparison (one feature Spec-Kit only, one hybrid)
- Decide based on results

---

## Metrics to Track

### Spec-Kit Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Specification completion rate | 100% for features >4 hours | Count specs vs. features |
| Spec-to-code alignment | >90% | Code review checklist |
| Rework due to unclear requirements | <10% of dev time | Retrospective tracking |
| Time to create spec | <20% of total feature time | Time tracking |

---

### CCPM Metrics (If Using)

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Parallel efficiency | >2x speedup for 3 agents | Feature completion time comparison |
| Issue accuracy | <5% need re-decomposition | GitHub issue tracking |
| Agent idle time | <10% | CCPM logs |
| Integration conflicts | <1 per feature | PR merge conflicts |

---

### Hybrid Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Spec → Epic accuracy | >95% | Manual review |
| Epic → Issues coverage | 100% (all spec criteria covered) | Coverage checklist |
| Cross-agent consistency | Zero conflicting implementations | Integration testing |

---

## Recommendations by Project Type

### Healthcare SaaS Platform (This Project)

**Recommended**: **Hybrid** (Spec-Kit + CCPM when team grows)

**Rationale**:
- Compliance requires detailed specifications (Spec-Kit)
- Clinical workflows need governance (Constitution)
- Multiple independent features can be parallelized (CCPM)
- Team visibility important for clinical stakeholders (GitHub Issues)

**Current Status**: Spec-Kit implemented ✅

**Next Milestone**: Add CCPM when team reaches 4+ developers

---

### Internal Hospital IT Project

**Recommended**: **Spec-Kit Only**

**Rationale**:
- Smaller teams (1-3 people)
- Air-gapped environments common (no GitHub access)
- Compliance documentation critical
- Sequential development acceptable

---

### Open Source NLP Library

**Recommended**: **CCPM** (or Hybrid if complex)

**Rationale**:
- Community contributions (GitHub-native workflow)
- Many parallel feature streams
- Contributor visibility essential
- Less governance needed than SaaS

---

## Decision Matrix

Use this to decide:

| Question | Spec-Kit | CCPM | Hybrid |
|----------|----------|------|--------|
| Team size > 5? | ❌ | ✅ | ✅ |
| Need detailed compliance docs? | ✅ | ❌ | ✅ |
| Parallel work critical? | ❌ | ✅ | ✅ |
| GitHub required? | ❌ | ✅ | ✅ |
| Complex governance needs? | ✅ | ❌ | ✅ |
| Budget for learning curve? | ✅ | ⚠️ | ⚠️ |
| Air-gapped environment? | ✅ | ❌ | ❌ |

**Legend**: ✅ Good fit | ❌ Poor fit | ⚠️ Manageable but consider

---

## Conclusion

### For This Project (CogStack NLP)

**Current Setup**: Spec-Kit ✅ (Implemented)

**Recommendation**:
- **Now** (Team < 3): Continue with Spec-Kit
- **When team grows** (4+ devs): Evaluate CCPM addition
- **Always**: Maintain constitution and detailed specifications (compliance requirement)

---

### General Guidance

**Choose Spec-Kit if**:
- Solo developer or small team
- Need governance and compliance documentation
- Sequential development acceptable
- Want simplicity

**Choose CCPM if**:
- Team of 5+ developers
- Parallel execution critical
- GitHub-native workflow preferred
- Less governance needs

**Choose Hybrid if**:
- Team of 4-15 developers
- Need both governance and parallel execution
- Healthcare/regulated industry
- Can invest in setup and learning

---

## Resources

### Spec-Kit
- **Guide**: [.specify/README.md](.specify/README.md)
- **Constitution**: [.specify/constitution/project-constitution.md](.specify/constitution/project-constitution.md)
- **Example Spec**: [.specify/specifications/meta-annotations-ui.md](.specify/specifications/meta-annotations-ui.md)
- **Official**: [github.com/github/spec-kit](https://github.com/github/spec-kit)

### CCPM
- **Official**: [github.com/automazeio/ccpm](https://github.com/automazeio/ccpm)
- **Documentation**: See CCPM repo README

### Hybrid
- Use both of the above
- This guide (you're reading it!)

---

**Questions?** Open a discussion issue or contact the Tech Lead.

**Last Review**: 2025-01-07
**Next Review**: 2025-04-07 (Quarterly)
