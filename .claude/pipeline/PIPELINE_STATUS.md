# Pipeline Status

## Ready Queue (Start These Next)

1. Phase 0: Environment Setup (Web-Adapted) ✅
   - Location: .specify/tasks/clinical-care-tools-base-tasks.md
   - Tasks: 7 (adapted for web environment - no Docker)
   - Priority: CRITICAL
   - Status: Ready to start
   - Environment: Claude Code on Web (PostgreSQL + Redis available, Docker unavailable)

2. Sprint 1: Patient Search & Discovery 🔜
   - Location: .specify/specifications/clinical-care-tools-base-app.md
   - Status: Specification complete, awaiting Phase 0 completion
   - Priority: HIGH

3. Sprint 2: Timeline View 🔜
   - Location: .specify/specifications/sprint-2-timeline-view.md
   - Status: Specification complete
   - Priority: MEDIUM

## In Progress

None - Starting Phase 0 now

## Blocked

None

## Completed

- ✅ Planning Phase (Constitution, Specifications, Technical Plans, Task Breakdown)
- ✅ 8 Implementation Skills created
- ✅ Git hooks configured
- ✅ Documentation framework established

## Next Action

**START Phase 0 Task 0.1 (adapted): Create project structure**

**Environment Adaptations**:
- Task 0.1: Skip Docker installation → Document for production
- Task 0.2: Skip model download → Mock MedCAT for testing
- Task 0.3: Skip docker-compose → Use native PostgreSQL/Redis
- Task 0.4: Use native PostgreSQL ✅
- Task 0.5: Use native Redis ✅
- Task 0.6: Create lightweight MedCAT mock → Full deployment documented for production
- Task 0.7: Create environment verification script (adapted for web)

**DO NOT stop to ask "What's next?" - Check this file and continue!**
