---
issue: 3
title: MedCAT Core Consolidation
analyzed: 2025-11-25T09:00:00Z
estimated_hours: 3
parallelization_factor: 3.0
---

# Parallel Work Analysis: Issue #3

## Overview
Consolidate MedCAT core implementations from myfork/development (Phase 1A), claude/sprints-6-8-* (Phase 3 CDS), and fix/medcat-demo-model-config (Phase 5 config fix).

## Parallel Streams

### Stream A: MedCAT Service Layer
**Scope**: Core MedCAT service and client implementations
**Files**:
- `app/services/medcat_service.py`
- `app/clients/medcat/client.py`
- `app/clients/medcat/__init__.py`
**Agent Type**: backend-specialist
**Can Start**: immediately
**Estimated Hours**: 1
**Dependencies**: none
**Source Branch**: myfork/development

### Stream B: Meta-Annotations & NLP
**Scope**: Meta-annotation processing and NLP integration
**Files**:
- `app/clients/medcat/meta_annotations.py`
- `app/services/nlp_processor.py`
- `app/schemas/medcat_schemas.py`
**Agent Type**: backend-specialist
**Can Start**: immediately
**Estimated Hours**: 1
**Dependencies**: none
**Source Branch**: myfork/development

### Stream C: CDS Integration
**Scope**: Clinical Decision Support features from Sprint 6-8
**Files**:
- `app/services/cds/`
- `app/api/v1/cds.py`
- `app/schemas/cds_schemas.py`
**Agent Type**: backend-specialist
**Can Start**: after Stream A completes
**Estimated Hours**: 1
**Dependencies**: Stream A
**Source Branch**: myfork/claude/sprints-6-8-implementation-011M46D5vbdi9FbGxSzThebK

## Coordination Points

### Shared Files
- `app/__init__.py` - Import registrations
- `app/services/__init__.py` - Service exports
- `requirements.txt` - MedCAT dependencies

### Sequential Requirements
1. Stream A (core services) before Stream C (CDS)
2. Stream B can run parallel to A
3. Config fix (Phase 5) after all streams

## Conflict Risk Assessment
- **Low Risk**: Streams work on different service files
- **Medium Risk**: Schema files may have overlapping types

## Parallelization Strategy
**Recommended Approach**: hybrid

Launch Streams A & B simultaneously. Start C when A completes.
Apply Phase 5 config fix last.

## Expected Timeline
With parallel execution:
- Wall time: 1.5 hours
- Total work: 3 hours
- Efficiency gain: 50%

## Cherry-Pick Commands
```bash
cd .worktrees/issue-3-medcat

# Stream A: MedCAT Services
git checkout myfork/development -- app/services/medcat_service.py app/clients/medcat/

# Stream B: Meta-Annotations
git checkout myfork/development -- app/clients/medcat/meta_annotations.py

# Stream C: CDS (after A)
git checkout myfork/claude/sprints-6-8-implementation-011M46D5vbdi9FbGxSzThebK -- app/services/cds/ app/api/v1/cds.py 2>/dev/null || echo "CDS files may not exist yet"

# Phase 5: Config Fix
git cherry-pick myfork/fix/medcat-demo-model-config --no-commit 2>/dev/null || echo "Fix branch may need manual merge"

git add -A && git commit -m "Issue #3: MedCAT core consolidation - Phases 1A, 3, 5"
```
