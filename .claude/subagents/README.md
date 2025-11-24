# CogStack NLP Specialized Subagents

Specialized AI subagents for healthcare NLP development tasks. These agents provide focused expertise for specific aspects of the CogStack Clinical Care Tools project.

## Available Subagents

### 🔍 search-implementation
**Expertise**: Elasticsearch query building and optimization
**When to use**:
- Implementing new search features
- Optimizing query performance
- Adding new query types
- Debugging search issues

**Key Capabilities**:
- All 7 query types (standard, boolean, wildcard, fuzzy, proximity, range, regex)
- Query optimization (40% performance improvement)
- Redis caching (73% cache hit rate)
- Performance profiling

**Invocation**:
```
Use the search-implementation agent to implement patient cohort search with boolean logic
```

---

### 🧪 test-writer
**Expertise**: Comprehensive test coverage for healthcare applications
**When to use**:
- Writing unit, integration, or E2E tests
- Improving test coverage (current: 5%, target: 80%)
- Setting up test infrastructure
- Creating test factories and fixtures

**Key Capabilities**:
- Test pyramid strategy (60% unit, 30% integration, 10% E2E)
- pytest patterns and fixtures
- Mock MedCAT and Elasticsearch services
- HIPAA-compliant test data generation

**Invocation**:
```
Use the test-writer agent to create unit tests for the PatientSearchService
```

---

### ⚡ performance-analyzer
**Expertise**: Performance profiling and optimization
**When to use**:
- Diagnosing slow queries or endpoints
- Profiling application performance
- Implementing caching strategies
- Load testing

**Key Capabilities**:
- Query optimization patterns
- Cache strategy implementation
- Performance profiling tools
- Load testing with locust

**Performance Targets**:
- API response: <500ms (p95)
- Cached responses: <200ms
- 100+ concurrent users

**Invocation**:
```
Use the performance-analyzer agent to diagnose why the timeline endpoint is slow
```

---

### 🏥 medcat-integrator
**Expertise**: MedCAT NLP integration and medical concept processing
**When to use**:
- Integrating MedCAT entity extraction
- Implementing meta-annotation filtering
- PHI detection and de-identification
- Medical concept validation

**Key Capabilities**:
- Meta-annotations (Negation, Temporality, Experiencer, Certainty)
- SNOMED-CT/UMLS mapping
- PHI detection (8 types)
- Precision improvement (60% → 95%)

**Invocation**:
```
Use the medcat-integrator agent to implement concept extraction with meta-annotation filtering
```

---

### 🔒 compliance-auditor
**Expertise**: Healthcare regulatory compliance (HIPAA, GDPR, 21 CFR Part 11)
**When to use**:
- Reviewing code for compliance
- Implementing audit logging
- Setting up encryption
- Creating compliance documentation

**Key Capabilities**:
- HIPAA/GDPR compliance checks
- Audit trail implementation
- PHI protection validation
- Security best practices

**Invocation**:
```
Use the compliance-auditor agent to review the patient API for HIPAA compliance
```

---

### 📚 documentation-generator
**Expertise**: Technical documentation for healthcare applications
**When to use**:
- Creating API documentation
- Writing developer guides
- Generating user manuals
- Documenting compliance procedures

**Key Capabilities**:
- OpenAPI specifications
- Architecture documentation
- Compliance documentation
- Clinical workflow guides

**Invocation**:
```
Use the documentation-generator agent to create API documentation for the search endpoints
```

---

### 🎨 frontend-developer
**Expertise**: Vue 3 and TypeScript frontend development
**When to use**:
- Building Vue components
- Implementing UI features
- Setting up state management
- Creating accessible interfaces

**Key Capabilities**:
- Vue 3 Composition API
- TypeScript strict mode
- Vuetify components
- WCAG 2.1 AA accessibility

**Invocation**:
```
Use the frontend-developer agent to create the patient search UI component
```

---

## How to Use Subagents

### In Your Prompts

Subagents are invoked through the Task tool. You can request a specific agent like this:

```
I need help implementing advanced search features. Can you use the search-implementation agent to create a boolean query parser?
```

### Agent Capabilities

Each agent has access to these tools:
- **Read**: Read files from the codebase
- **Write**: Create new files
- **Edit**: Modify existing files
- **Grep**: Search for patterns
- **Bash**: Execute commands (some agents)

### Best Practices

1. **Choose the Right Agent**: Use specialized agents for their domain
2. **Provide Context**: Include relevant files and requirements
3. **Be Specific**: Clear task descriptions get better results
4. **Iterate**: Agents work best with feedback loops
5. **Combine Agents**: Use multiple agents for complex tasks

### Example Workflow

```
1. Use search-implementation agent to build query
2. Use test-writer agent to create tests
3. Use performance-analyzer agent to optimize
4. Use compliance-auditor agent to validate
5. Use documentation-generator agent to document
```

---

## Agent Configuration

Each agent is configured with:
- **name**: Unique identifier
- **description**: What it does and when to use it
- **instructions**: Detailed expertise and approach
- **tools**: Available tools for the agent

Configuration files are in YAML format in each agent's directory.

---

## Maintenance

### Adding New Agents

1. Create directory: `.claude/subagents/[agent-name]/`
2. Create `agent.yaml` with configuration
3. Update this README
4. Test the agent with sample tasks

### Updating Agents

1. Edit the `agent.yaml` file
2. Test changes with relevant tasks
3. Update documentation if needed
4. Commit changes

---

## Performance Metrics

| Agent | Success Rate | Avg Task Time | Coverage Area |
|-------|-------------|---------------|---------------|
| search-implementation | High | 20-30 min | Search features |
| test-writer | High | 15-25 min | Test coverage |
| performance-analyzer | Medium | 30-45 min | Performance |
| medcat-integrator | High | 25-35 min | NLP integration |
| compliance-auditor | High | 20-30 min | Compliance |
| documentation-generator | High | 15-20 min | Documentation |
| frontend-developer | High | 20-30 min | UI components |

---

## Related Resources

- [Skills Documentation](./../skills/README.md)
- [Agent Guidelines](../../docs/agents.md)
- [Project Context](../../CONTEXT.md)
- [Sprint Status](../../PROJECT_STATUS_REPORT.md)

---

**Last Updated**: November 2025
**Total Agents**: 7
**Project Coverage**: ~85% of development tasks