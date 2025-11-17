# Project Skills for CogStack NLP

Custom Claude Code skills for healthcare NLP development with MedCAT.

## Available Skills

### 🔴 Priority 1 (Critical for Safety & Accuracy)

#### 1. `healthcare-compliance-checker`
**When**: Working with patient data (PHI), authentication, API endpoints, database schemas, logging

**What it does**:
- Reviews code for HIPAA, GDPR, 21 CFR Part 11 compliance
- Catches PHI exposure in logs
- Ensures audit logging for patient data access
- Verifies encryption requirements (TLS 1.3, AES-256)
- Validates RBAC implementation

**Why critical**: Prevents regulatory violations, fines, and patient privacy breaches

---

#### 2. `medcat-meta-annotations`
**When**: Processing NLP results, building queries, displaying medical concepts, filtering entities

**What it does**:
- Explains MedCAT's 4 meta-annotations (Negation, Experiencer, Temporality, Certainty)
- Provides filtering patterns to avoid false positives
- Shows how to improve precision from 60% to 95%
- Demonstrates Elasticsearch integration patterns

**Why critical**: Core to NLP accuracy—without meta-annotation filtering, results include family history, negated conditions, and hypothetical scenarios

---

### 🟡 Priority 2 (Highly Recommended)

#### 3. `vue3-component-reuse`
**When**: Building UI features, implementing forms/tables/modals/charts

**What it does**:
- Discovers existing Vue 3 components from MedCAT Trainer (65 components)
- Provides Composition API + TypeScript patterns
- Shows how to search and adapt existing components
- Prevents rebuilding components that already exist

**Why useful**: Saves hours of development by reusing proven patterns from 34K+ line components

---

#### 4. `fhir-r4-mapper`
**When**: Implementing FHIR integration, clinical decision support, EHR interoperability

**What it does**:
- Maps MedCAT output to FHIR R4 resources (Observations, Conditions)
- Converts meta-annotations to FHIR qualifiers
- Provides CDS Hooks integration patterns
- Shows SNOMED-CT/LOINC code usage

**Why useful**: Required for EHR integration (Epic, Cerner) and clinical decision support (Sprint 3+)

---

### 🟢 Priority 3 (Quality Assurance)

#### 5. `spec-kit-enforcer`
**When**: Starting new features, before writing code

**What it does**:
- Enforces Spec-Kit workflow (Constitution → Spec → Plan → Tasks → Code)
- Checks for missing specifications, plans, or tasks
- Prevents "code first, document later" anti-pattern
- Verifies constitution alignment

**Why useful**: Ensures quality, prevents rework, maintains compliance documentation

---

### 🔵 Implementation Workflow Skills

#### 6. `spec-to-tech-plan`
**When**: Converting approved specifications to technical plans

**What it does**:
- Guides creation of detailed technical plans from specifications
- Provides OpenAPI API design templates
- Shows database schema design patterns (PostgreSQL, UUID, JSONB)
- Documents authentication/authorization architecture
- Defines testing strategy (unit, integration, E2E)
- Creates deployment architecture (Docker Compose)
- Identifies risks and mitigations

**Why useful**: Ensures complete technical planning before implementation, prevents architectural mistakes

---

#### 7. `tech-plan-to-tasks`
**When**: Breaking down technical plans into implementable tasks

**What it does**:
- Converts technical plans into 1-2 hour tasks
- Enforces Test-Driven Development (TDD) approach
- Defines clear acceptance criteria for each task
- Creates dependency graphs for parallel execution
- Provides task templates for common patterns (models, APIs, components)

**Why useful**: Enables granular tracking, facilitates parallel development, ensures testability

---

#### 8. `infrastructure-expert`
**When**: Implementing Docker, PostgreSQL, authentication, audit logging

**What it does**:
- Provides production-ready Docker Compose configurations
- Shows PostgreSQL security hardening patterns
- Implements JWT authentication with session management
- Creates immutable audit logging systems
- Includes HIPAA/GDPR compliance checklists
- Demonstrates backup/restore procedures

**Why useful**: Battle-tested patterns for healthcare infrastructure, ensures security from day one

---

## How Skills Work

Skills are **model-invoked**—Claude automatically uses them based on your request and the skill's description. You don't need to explicitly call them.

### Example Usage

```
You: "Implement patient search API endpoint"

Claude activates:
✓ spec-kit-enforcer (checks for specification)
✓ healthcare-compliance-checker (reviews PHI handling)
✓ medcat-meta-annotations (ensures proper filtering)

Claude: "I notice we don't have a specification for patient search.
Following Spec-Kit framework, should I help create:
1. Specification (.specify/specifications/patient-search.md)
2. Technical Plan
3. Task Breakdown

Also, this endpoint will access patient data, so I'll ensure:
- Audit logging for PHI access
- Proper meta-annotation filtering (Negation=Affirmed, Experiencer=Patient)
- Authentication requirements"
```

---

## Skill Structure

Each skill contains:
- `SKILL.md` - Main instructions (loaded when skill is triggered)
- Optional: Reference files (loaded as needed)

Skills use **progressive disclosure**:
1. Metadata (name + description) - Always loaded
2. SKILL.md body - Loaded when triggered
3. Additional files - Loaded only if referenced

---

## Testing Skills

### Test healthcare-compliance-checker
```
You: "Add logging to patient data endpoint"

Expected: Skill warns about PHI in logs, suggests audit logging pattern
```

### Test medcat-meta-annotations
```
You: "Build patient search for diabetes"

Expected: Skill suggests filtering by Negation=Affirmed, Experiencer=Patient
```

### Test vue3-component-reuse
```
You: "Create a data table component"

Expected: Skill searches medcat-trainer components, suggests existing patterns
```

### Test fhir-r4-mapper
```
You: "Export NLP results to FHIR format"

Expected: Skill provides Observation/Condition mapping examples
```

### Test spec-kit-enforcer
```
You: "Let's build timeline view"

Expected: Skill checks for specification, plan, tasks before allowing code
```

---

## Skill Activation Triggers

| Skill | Activated When |
|-------|----------------|
| healthcare-compliance-checker | Code involves: `Patient`, `auth`, `API`, `logs`, `/patients/` |
| medcat-meta-annotations | Working with: NLP results, medical concepts, queries, filtering |
| vue3-component-reuse | Building: UI components, forms, tables, frontend |
| fhir-r4-mapper | Mentions: FHIR, EHR integration, clinical decision support |
| spec-kit-enforcer | Requests: new feature, implementation, "build X" |
| spec-to-tech-plan | After specification approval, creating technical plan, architecture design |
| tech-plan-to-tasks | Breaking down plan, creating task list, estimating work |
| infrastructure-expert | Setting up Docker, PostgreSQL, authentication, audit logging, deployment |

---

## Modifying Skills

To update a skill:
1. Edit the `SKILL.md` file
2. Keep changes concise (under 500 lines)
3. Test with realistic requests
4. Commit changes to git

Team members automatically get updated skills after `git pull`.

---

## Adding New Skills

To create a new skill:

```bash
# Create skill directory
mkdir -p .claude/skills/your-skill-name

# Create SKILL.md with frontmatter
cat > .claude/skills/your-skill-name/SKILL.md << 'EOF'
---
name: your-skill-name
description: What it does and when to use it (max 1024 chars). Be specific with triggers.
---

# Your Skill Name

Content here...
EOF
```

**Best practices**:
- Be concise (assume Claude is smart)
- Specific descriptions with triggers
- Use third person in description
- Under 500 lines in SKILL.md
- Reference external files for details
- Test with real scenarios

See [Claude Code Skills documentation](https://code.claude.com/docs/skills) for details.

---

## Integration Points

Skills work together across the full development lifecycle:

```
Complete Feature Implementation Flow:
│
├── 1. Planning Phase
│   ├── spec-kit-enforcer (ensures spec exists)
│   ├── spec-to-tech-plan (creates technical plan)
│   └── tech-plan-to-tasks (breaks into tasks)
│
├── 2. Infrastructure Phase
│   ├── infrastructure-expert (Docker, PostgreSQL, auth)
│   └── healthcare-compliance-checker (security review)
│
├── 3. Implementation Phase
│   ├── medcat-meta-annotations (NLP filtering logic)
│   ├── vue3-component-reuse (frontend patterns)
│   ├── healthcare-compliance-checker (PHI handling review)
│   └── infrastructure-expert (audit logging patterns)
│
└── 4. Integration Phase
    ├── fhir-r4-mapper (export functionality)
    └── healthcare-compliance-checker (final compliance check)
```

**Example: Patient Search Feature**
1. `spec-kit-enforcer` - Checks specification exists
2. `spec-to-tech-plan` - Creates API design, database schema, testing strategy
3. `tech-plan-to-tasks` - Breaks into 8-12 implementable tasks
4. `infrastructure-expert` - Guides auth implementation, audit logging
5. `medcat-meta-annotations` - Ensures proper filtering (95% precision)
6. `vue3-component-reuse` - Finds existing search UI patterns
7. `healthcare-compliance-checker` - Validates PHI handling
8. `fhir-r4-mapper` - Adds FHIR export capability

---

## Troubleshooting

**Skill not activating?**
- Check description is specific enough
- Include use case triggers in description
- Verify YAML frontmatter is valid

**Skill providing wrong guidance?**
- Update SKILL.md with corrections
- Add examples showing correct patterns
- Test with edge cases

**Need more details?**
- Add reference files (e.g., `REFERENCE.md`)
- Link from SKILL.md: `See [REFERENCE.md](REFERENCE.md)`
- Keep references one level deep (no nested files)

---

## Metrics

**Total Skills**: 8
**Lines of Guidance**: ~6,500+ (compressed via progressive loading)
**Coverage**:
- ✅ Compliance & Safety (healthcare-compliance-checker)
- ✅ NLP Accuracy (medcat-meta-annotations)
- ✅ Frontend Development (vue3-component-reuse)
- ✅ Healthcare Standards (fhir-r4-mapper)
- ✅ Workflow Enforcement (spec-kit-enforcer)
- ✅ Technical Planning (spec-to-tech-plan)
- ✅ Task Breakdown (tech-plan-to-tasks)
- ✅ Infrastructure Implementation (infrastructure-expert)

---

## Maintenance

Skills are **project-specific** (stored in `.claude/skills/` and shared via git).

**When to update**:
- New compliance requirements discovered
- Meta-annotation patterns change
- New Vue components added
- FHIR mapping patterns evolve
- Spec-Kit workflow adjustments

**How to update**:
```bash
# Edit skill
vim .claude/skills/healthcare-compliance-checker/SKILL.md

# Test changes
# (trigger the skill with realistic request)

# Commit
git add .claude/skills/
git commit -m "docs(skills): update compliance patterns"
git push
```

Team gets updates automatically on next `git pull`.

---

## Resources

- **Claude Code Skills**: https://code.claude.com/docs/skills
- **Best Practices**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/authoring-best-practices
- **Project Guide**: [CLAUDE.md](../CLAUDE.md)
- **Constitution**: [.specify/constitution/project-constitution.md](../.specify/constitution/project-constitution.md)

---

**Questions?** Review individual SKILL.md files or refer to project documentation.
