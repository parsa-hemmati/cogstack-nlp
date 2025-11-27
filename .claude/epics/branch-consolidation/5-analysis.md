---
issue: 5
title: Search & NLP Features
analyzed: 2025-11-25T09:00:00Z
estimated_hours: 3
parallelization_factor: 3.0
---

# Parallel Work Analysis: Issue #5

## Overview
Consolidate search and NLP features from myfork/development (Phase 1C), claude/sprint3-integration-* (Phase 2 advanced search), and autonomous/mvp-execution (Phase 4 selective).

## Parallel Streams

### Stream A: Base Search Services
**Scope**: Core patient search implementation
**Files**:
- `app/services/patient_search_service.py`
- `app/services/elasticsearch_service.py`
- `app/schemas/patient_search.py`
**Agent Type**: backend-specialist
**Can Start**: immediately
**Estimated Hours**: 1
**Dependencies**: none
**Source Branch**: myfork/development

### Stream B: Advanced Query Parsing
**Scope**: Sprint 3 advanced query features
**Files**:
- `app/services/query_parser.py`
- `app/services/advanced_search.py`
- `app/services/semantic_search.py`
**Agent Type**: backend-specialist
**Can Start**: immediately
**Estimated Hours**: 1
**Dependencies**: none
**Source Branch**: myfork/claude/sprint3-integration-011M46D5vbdi9FbGxSzThebK

### Stream C: Search API Endpoints
**Scope**: FastAPI endpoints for search
**Files**:
- `app/api/v1/patients.py`
- `app/api/v1/search.py`
- `app/api/deps.py`
**Agent Type**: backend-specialist
**Can Start**: after Stream A
**Estimated Hours**: 1
**Dependencies**: Stream A
**Source Branch**: myfork/development + myfork/autonomous/mvp-execution (selective)

## Coordination Points

### Shared Files
- `app/api/v1/__init__.py` - Router registration
- `app/services/__init__.py` - Service exports
- `app/schemas/__init__.py` - Schema exports

### Sequential Requirements
1. Stream A (base services) before Stream C (API)
2. Stream B can run parallel to A
3. Phase 4 (autonomous) selective cherry-pick after review

## Conflict Risk Assessment
- **Medium Risk**: Search service may have different implementations across branches
- **Resolution**: Prefer sprint3-integration for advanced features

## Parallelization Strategy
**Recommended Approach**: hybrid

Launch Streams A & B simultaneously. Start C when A completes.
Phase 4 (autonomous) requires manual review for selective cherry-pick.

## Expected Timeline
With parallel execution:
- Wall time: 1.5 hours
- Total work: 3 hours
- Efficiency gain: 50%

## Cherry-Pick Commands
```bash
cd .worktrees/issue-5-search

# Stream A: Base Search (Phase 1C)
git checkout myfork/development -- \
  app/services/patient_search_service.py \
  app/services/elasticsearch_service.py \
  app/schemas/patient_search.py 2>/dev/null || echo "Creating base search files"

# Stream B: Advanced Query (Phase 2)
git checkout myfork/claude/sprint3-integration-011M46D5vbdi9FbGxSzThebK -- \
  app/services/query_parser.py \
  app/services/advanced_search.py 2>/dev/null || echo "Sprint 3 files may have different paths"

# Stream C: API Endpoints
git checkout myfork/development -- \
  app/api/v1/patients.py \
  app/api/v1/search.py 2>/dev/null || echo "Creating API endpoints"

# Phase 4: Selective from autonomous (review before applying)
# git log myfork/autonomous/mvp-execution --oneline | head -20
# git cherry-pick <specific-commit> --no-commit

git add -A && git commit -m "Issue #5: Search & NLP consolidation - Phases 1C, 2, 4"
```
