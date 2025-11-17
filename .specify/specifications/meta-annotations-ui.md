# Specification: Meta-Annotations UI Integration

**Version**: 1.0.0
**Date**: 2025-01-07
**Status**: Draft
**Owner**: Product Team
**Stakeholders**: Clinicians, Researchers, Tech Lead

---

## Context

MedCAT provides meta-annotation capabilities (Negation, Temporality, Experiencer, Certainty) that add critical context to extracted medical concepts. Currently, these meta-annotations are available through the MedCAT API but not exposed in the Full Potential UI.

**Problem**: Users cannot filter search results by meta-annotations, leading to:
- False positives in patient cohorts (e.g., including family history mentions)
- Inability to distinguish current vs. historical conditions
- Manual post-processing of NLP results to apply context filters

**Business Impact**:
- Cohort identification precision: 60% → 95% (with meta-annotations)
- Time savings: 70% reduction in manual chart review
- Improved quality metrics by identifying active conditions only

---

## Goals

### Primary Goals

1. **Expose meta-annotations in search results**
   - Display Negation, Temporality, Experiencer for each concept
   - Visual indicators (icons, colors) for quick recognition

2. **Enable filtering by meta-annotations**
   - "Current conditions only" filter
   - "Exclude family history" filter
   - "Exclude negated mentions" filter

3. **Provide meta-annotation insights**
   - Show distribution of meta-annotations in search results
   - Analytics dashboard showing trends (e.g., % of conditions that are historical)

### Secondary Goals

- Educate users about meta-annotations (tooltips, help text)
- Export results with meta-annotation columns
- API endpoint for programmatic access to meta-annotations

---

## Non-Goals

**Explicitly out of scope for v1**:
- Training custom meta-annotation models (use existing models)
- Editing/correcting meta-annotations in UI
- Real-time meta-annotation model switching
- Custom meta-annotation types beyond the built-in 4 types

---

## User Stories

### Story 1: Filter for Active Conditions

**As a** clinician
**I want to** search for patients with **current** diabetes (not historical)
**So that** I enroll the right patients in the diabetes management pathway

**Acceptance Criteria**:
- Given search query "diabetes"
- When I check "Current conditions only" filter
- Then results show only patients with Temporality=Current/Recent
- And historical mentions are excluded
- And results update within 500ms of toggling filter

---

### Story 2: Exclude Family History

**As a** researcher
**I want to** exclude family history mentions from my cohort
**So that** I identify patients with actual diagnoses, not genetic risk only

**Acceptance Criteria**:
- Given search query "breast cancer"
- When I check "Exclude family history" filter
- Then results exclude concepts with Experiencer=Family
- And only Experiencer=Patient concepts shown
- And filter persists across page navigation

---

### Story 3: Visualize Meta-Annotations

**As a** quality improvement officer
**I want to** see the distribution of negation statuses for a concept
**So that** I understand how often conditions are affirmed vs. negated

**Acceptance Criteria**:
- Given search results for "pneumonia"
- Then I see a summary: "68% Affirmed, 32% Negated"
- And can click to drill down into each category
- And chart updates when filters applied

---

### Story 4: Understand Meta-Annotation Meaning

**As a** new user (non-technical)
**I want to** understand what "Experiencer: Family" means
**So that** I correctly interpret search results

**Acceptance Criteria**:
- When I hover over "Experiencer: Family" badge
- Then I see tooltip: "This condition refers to a family member, not the patient"
- And examples are provided
- And link to full documentation available

---

## Requirements

### Functional Requirements

#### FR1: Display Meta-Annotations in Search Results

- [x] Each search result row shows meta-annotations for identified concepts
- [x] Visual indicators:
  - Negation: ✓ Affirmed (green), ✗ Negated (red)
  - Temporality: 🕐 Current, 📅 Historical, ⏭ Future
  - Experiencer: 👤 Patient, 👨‍👩‍👧‍👦 Family, 👨‍⚕️ Other
  - Certainty: ✅ Confirmed, ❓ Suspected, 💭 Hypothetical
- [x] Icons are colorblind-friendly
- [x] Tooltips explain each meta-annotation value

#### FR2: Filter by Meta-Annotations

- [x] Filters available:
  - "Current conditions only" (Temporality=Current/Recent)
  - "Exclude family history" (Experiencer≠Family)
  - "Exclude negated mentions" (Negation=Affirmed)
  - "Confirmed only" (Certainty=Confirmed)
- [x] Filters can be combined (AND logic)
- [x] Active filters shown as chips/tags
- [x] Filter state persists in URL (shareable links)

#### FR3: Meta-Annotation Analytics

- [x] Summary statistics panel:
  - Distribution by Negation (% Affirmed vs. Negated)
  - Distribution by Temporality (% Current vs. Historical vs. Future)
  - Distribution by Experiencer (% Patient vs. Family vs. Other)
- [x] Visualizations (pie charts or bar charts)
- [x] Click chart segment to apply filter

#### FR4: Export with Meta-Annotations

- [x] CSV export includes columns:
  - `concept`, `cui`, `negation`, `temporality`, `experiencer`, `certainty`, `confidence`
- [x] Excel export with formatting (color-coded cells)
- [x] JSON export for programmatic use

---

### Non-Functional Requirements

#### NFR1: Performance

- [x] Filtering by meta-annotations adds <100ms latency
- [x] Page load with 100 results <2 seconds
- [x] Analytics calculations <500ms

#### NFR2: Usability

- [x] Filters understandable without training (tested with 5+ non-technical users)
- [x] Icons intuitive (>80% correct interpretation in user testing)
- [x] Help text available for all meta-annotation types

#### NFR3: Accessibility

- [x] WCAG 2.1 Level AA compliant
- [x] Keyboard navigation for all filters
- [x] Screen reader support (ARIA labels)
- [x] Colorblind-friendly palette

#### NFR4: Compatibility

- [x] Works with MedCAT models that have MetaCAT enabled
- [x] Graceful degradation if MetaCAT not available (hide filters, show warning)
- [x] Backward compatible with existing search API

---

### Constraints

#### Technical Constraints

- Must use existing MedCAT API (no changes to MedCAT service)
- Meta-annotations come from MetaCAT models (cannot be edited in UI)
- Elasticsearch query complexity limited (avoid performance degradation)

#### Regulatory Constraints

- HIPAA: Audit log all filter usage (track who filtered for what)
- GDPR: Meta-annotation filters do not bypass access controls

#### Organizational Constraints

- Timeline: Must be ready for Sprint 2 (weeks 3-4)
- Budget: No additional infrastructure costs
- Team: 2 developers, 1 UX designer

---

## Acceptance Criteria

### Definition of Done

- [ ] **Feature Complete**: All 4 user stories implemented
- [ ] **Tested**: 90% code coverage, usability tested with 5+ users
- [ ] **Documented**: User guide updated, API docs updated
- [ ] **Performance**: Meets NFR1 targets (verified via load testing)
- [ ] **Accessible**: WCAG 2.1 AA compliant (verified via Axe/Lighthouse)
- [ ] **Deployed**: Available in staging, smoke tested by Product Owner

### Validation Plan

**Unit Tests**:
- Filter logic (meta-annotation combinations)
- Analytics calculations (distribution percentages)
- Export formatting (CSV/Excel/JSON)

**Integration Tests**:
- Full search flow with filters applied
- API contract tests (meta-annotations in response)

**E2E Tests**:
- User can search, filter, and export results
- Charts update when filters applied

**User Acceptance Testing**:
- 5 clinicians test with real data
- Scenarios: cohort identification, quality audits
- Success: >4/5 complete tasks without assistance

---

## Open Questions

### Q1: Should we show confidence scores for meta-annotations?

**Options**:
- A: Yes, show confidence for each meta-annotation (e.g., "Negation: Affirmed (98%)")
- B: No, only show confidence for concept extraction
- C: Show confidence only on hover (advanced users)

**Recommendation**: Option C (show on hover)

**Rationale**: Avoids clutter, still provides transparency for power users

**Decision**: Pending Product Owner approval

---

### Q2: How to handle missing meta-annotations?

**Scenario**: Model lacks meta-annotation capability (older MedCAT version)

**Options**:
- A: Hide filters entirely, show warning banner
- B: Show filters but display "N/A" for missing meta-annotations
- C: Require MedCAT upgrade before enabling feature

**Recommendation**: Option A

**Rationale**: Avoids confusing users with incomplete data

**Decision**: Pending Tech Lead approval

---

### Q3: Should filters be applied client-side or server-side?

**Options**:
- A: Client-side (filter already-fetched results)
- B: Server-side (new Elasticsearch query)
- C: Hybrid (client-side for <100 results, server-side otherwise)

**Recommendation**: Option B (server-side)

**Rationale**:
- Correct result counts
- Better performance for large datasets
- Consistent with existing search architecture

**Decision**: Approved by Tech Lead

---

## Dependencies

### Upstream Dependencies

- [x] MedCAT Service with MetaCAT enabled
- [x] Meta-annotation models loaded (Negation, Temporality, Experiencer, Certainty)
- [x] Elasticsearch schema supports meta-annotation fields

### Downstream Dependencies

None (feature is self-contained)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MetaCAT accuracy <85% | Medium | High | Validate models before launch, provide manual override |
| Performance degradation with filters | Low | Medium | Optimize Elasticsearch queries, add caching |
| Users don't understand meta-annotations | Medium | Medium | Comprehensive tooltips, user training, help videos |
| Accessibility compliance issues | Low | High | Early accessibility audit, use established UI component library |

---

## Success Metrics

### Adoption Metrics

- **Target**: 70% of users use at least one meta-annotation filter within first month
- **Measurement**: Analytics tracking filter usage

### Accuracy Metrics

- **Target**: 95% precision for cohort identification (vs. 60% without filters)
- **Measurement**: Manual validation of 100-patient sample

### Satisfaction Metrics

- **Target**: NPS >60 for this feature
- **Measurement**: In-app survey after 2 weeks of use

### Performance Metrics

- **Target**: P95 latency <500ms for filtered searches
- **Measurement**: Application Performance Monitoring (APM)

---

## Alignment with Constitution

**Principles Addressed**:
- [x] **Evidence-Based Development**: Feature based on clinician feedback (cohort precision issues)
- [x] **Transparency**: Meta-annotations make NLP reasoning visible to users
- [x] **Privacy by Design**: Audit logging for filter usage
- [x] **Usability**: Filters designed with clinician input, tested before launch

**Non-Negotiable Requirements Met**:
- [x] Audit logging enabled (FR2)
- [x] Accessibility compliance (NFR3)
- [x] Performance targets defined (NFR1)

---

## Next Steps

1. **Review & Approval** (Week 1)
   - Product Owner review
   - Tech Lead review
   - Clinical SME feedback

2. **Technical Planning** (Week 1)
   - Create detailed technical plan
   - API design
   - Database schema updates

3. **Implementation** (Weeks 2-4)
   - Sprint 2 development
   - Testing
   - Documentation

4. **Validation** (Week 4)
   - UAT with 5+ clinicians
   - Performance testing
   - Accessibility audit

5. **Launch** (Week 5)
   - Deploy to production
   - User training
   - Monitor metrics

---

## References

- [Meta-Annotations Guide](../../docs/advanced/meta-annotations-guide.md)
- [MedCAT Documentation](https://github.com/CogStack/MedCAT)
- [Sprint 2 PRD](../../docs/prd/sprint-2/patient-timeline-view.md)

---

**Status**: Draft - Awaiting Approval

**Approvals**:
- [ ] Product Owner: _______________
- [ ] Tech Lead: _______________
- [ ] Clinical SME: _______________
- [ ] UX Lead: _______________
