#!/usr/bin/env python3
"""
Orchestrator Agent - Meta-agent for coordinating autonomous development loops

This agent:
1. Reads task queues from all modules
2. Identifies ready tasks (no blocking dependencies)
3. Spawns multiple agents in parallel (up to max_parallel_agents)
4. Implements wave-based execution strategy
5. Continues loop until all tasks complete or termination condition met
"""

import os
import sys
import yaml
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class Task:
    """Represents a task from a module's task queue"""
    module: str
    task_num: str
    name: str
    status: str
    agent_type: str
    depends_on: List[str] = field(default_factory=list)
    parallel: bool = False
    priority: str = "P1"
    estimated_hours: int = 0

    @property
    def task_id(self) -> str:
        return f"{self.module}:{self.task_num}"

    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Check if task is ready to start (all dependencies completed)"""
        if self.status != "open":
            return False

        for dep in self.depends_on:
            dep_id = f"{self.module}:{dep}"
            if dep_id not in completed_tasks:
                return False

        return True


@dataclass
class Module:
    """Represents a module with its task queue"""
    name: str
    priority: str
    task_count: int
    completed: int
    worktree: str
    tasks: List[Task] = field(default_factory=list)

    @property
    def progress(self) -> float:
        return (self.completed / self.task_count * 100) if self.task_count > 0 else 0


class OrchestratorAgent:
    """Orchestrator agent for coordinating autonomous development loops"""

    def __init__(self, config_path: str = ".claude/agent-coordination.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.modules: Dict[str, Module] = {}
        self.completed_tasks: Set[str] = set()
        self.running_agents: Dict[str, subprocess.Popen] = {}
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = Path(".claude/logs/orchestrator")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.iteration_count = 0
        self.consecutive_failures = 0

    def _load_config(self) -> dict:
        """Load agent coordination configuration"""
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def _load_modules(self) -> None:
        """Load all modules and their task queues"""
        module_config = self.config.get("modules", {})

        for module_name, module_info in module_config.items():
            module = Module(
                name=module_name,
                priority=module_info["priority"],
                task_count=module_info["task_count"],
                completed=module_info["completed"],
                worktree=module_info["worktree"]
            )

            # Load task queue
            queue_file = Path(f".claude/autonomous-worktrees/{module_name}/TASK_QUEUE.md")
            if queue_file.exists():
                module.tasks = self._parse_task_queue(module_name, queue_file)

            self.modules[module_name] = module

    def _parse_task_queue(self, module_name: str, queue_file: Path) -> List[Task]:
        """Parse task queue markdown file"""
        tasks = []

        # Read all task files in the epic directory
        epic_dir = Path(f".claude/ccpm/epics/{module_name}")
        if not epic_dir.exists():
            return tasks

        for task_file in sorted(epic_dir.glob("[0-9][0-9][0-9].md")):
            task_num = task_file.stem

            # Parse frontmatter
            with open(task_file) as f:
                content = f.read()

            if not content.startswith("---"):
                continue

            # Extract frontmatter
            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            frontmatter = yaml.safe_load(parts[1])

            task = Task(
                module=module_name,
                task_num=task_num,
                name=frontmatter.get("name", ""),
                status=frontmatter.get("status", "open"),
                agent_type=frontmatter.get("agent_type", "developer"),
                depends_on=frontmatter.get("depends_on", []),
                parallel=frontmatter.get("parallel", False),
                priority=frontmatter.get("priority", "P1"),
                estimated_hours=frontmatter.get("estimated_hours", 0)
            )

            tasks.append(task)

            # Track completed tasks
            if task.status == "completed":
                self.completed_tasks.add(task.task_id)

        return tasks

    def _get_ready_tasks(self) -> List[Task]:
        """Get all tasks ready to start (no blocking dependencies)"""
        ready_tasks = []

        for module in self.modules.values():
            for task in module.tasks:
                if task.is_ready(self.completed_tasks):
                    ready_tasks.append(task)

        # Sort by priority (P0 > P1 > P2)
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        ready_tasks.sort(key=lambda t: priority_order.get(t.priority, 99))

        return ready_tasks

    def _spawn_agent(self, task: Task) -> Optional[subprocess.Popen]:
        """Spawn an agent to work on a task"""
        log_file = self.log_dir / f"{task.module}-{task.task_num}-{self.session_id}.log"

        # Create agent prompt
        prompt = f"""You are a specialized {task.agent_type} agent working on an autonomous development loop.

**Task**: {task.name}
**Module**: {task.module}
**Task File**: .claude/ccpm/epics/{task.module}/{task.task_num}.md
**Priority**: {task.priority}
**Estimated Time**: {task.estimated_hours} hours

**Your responsibilities**:
1. Read the task file completely
2. Implement the requirements following TDD approach
3. Write tests first, then implementation
4. Update CONTEXT.md and AUDIT.md with your changes
5. Commit with proper message format
6. Mark task as completed in the task file

**Important**:
- Follow the Spec-Kit workflow
- Ensure HIPAA/GDPR compliance
- Update documentation
- Run validation checks before committing

**When complete**:
- Update task status to "completed"
- Commit and push changes
- The orchestrator will spawn the next wave of agents

Begin implementation now.
"""

        # In real implementation, this would use Claude Agent SDK
        # For now, we'll create a placeholder that simulates agent work

        try:
            with open(log_file, "w") as f:
                f.write(f"Agent: {task.agent_type}\n")
                f.write(f"Task: {task.task_id}\n")
                f.write(f"Status: Starting...\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"\nPrompt:\n{prompt}\n")

            print(f"  → Spawned {task.agent_type} agent for {task.task_id}")
            print(f"    Log: {log_file}")

            # Simulate agent process (in real implementation, spawn actual agent)
            return None

        except Exception as e:
            print(f"  ✗ Failed to spawn agent for {task.task_id}: {e}")
            self.consecutive_failures += 1
            return None

    def _execute_wave(self, phase: dict) -> None:
        """Execute a wave of agents according to phase strategy"""
        phase_name = phase["phase"]
        agent_types = phase["agents"]
        wait_for_completion = phase.get("wait_for_completion", True)
        condition = phase.get("condition")

        print(f"\n📋 Phase: {phase_name}")
        print(f"   Agents: {', '.join(agent_types)}")

        # Check condition if specified
        if condition:
            print(f"   Condition: {condition}")
            # Simplified condition check - real implementation would evaluate properly
            if "Issues detected" in condition and self.consecutive_failures == 0:
                print(f"   ⊘ Condition not met, skipping phase")
                return

        # Get ready tasks
        ready_tasks = self._get_ready_tasks()

        if not ready_tasks:
            print(f"   ⊘ No ready tasks")
            return

        # Spawn agents up to max_parallel_agents
        max_parallel = self.config.get("max_parallel_agents", 6)
        spawned = 0

        for task in ready_tasks[:max_parallel]:
            if task.agent_type in agent_types or "developer" in agent_types:
                self._spawn_agent(task)
                spawned += 1

        print(f"   ✓ Spawned {spawned} agents")

        if wait_for_completion:
            print(f"   ⏳ Waiting for agents to complete...")
            # In real implementation, wait for agent processes
            time.sleep(2)

    def _update_context_md(self, ready_tasks: List[Task]) -> None:
        """Update CONTEXT.md with orchestrator status"""
        context_file = Path("CONTEXT.md")

        timestamp = datetime.now().isoformat()

        update = f"""

### Orchestrator Agent [{timestamp}]
**Session**: {self.session_id}
**Iteration**: {self.iteration_count}
**Ready Tasks**: {len(ready_tasks)}
**Completed Tasks**: {len(self.completed_tasks)}
**Running Agents**: {len(self.running_agents)}
**Status**: {"Active" if ready_tasks else "Complete"}

**Module Progress**:
"""

        for module in self.modules.values():
            update += f"- {module.name}: {module.completed}/{module.task_count} ({module.progress:.1f}%)\n"

        if ready_tasks:
            update += f"\n**Next Wave** ({len(ready_tasks)} tasks):\n"
            for task in ready_tasks[:6]:  # Show first 6
                update += f"- {task.task_id}: {task.name} ({task.agent_type}, {task.priority})\n"

        update += "\n"

        # Append to CONTEXT.md
        with open(context_file, "a") as f:
            f.write(update)

    def _check_termination_conditions(self) -> Tuple[bool, str]:
        """Check if any termination condition is met"""
        conditions = self.config["continuous_loop"]["termination_conditions"]

        # Check all tasks complete
        total_tasks = sum(m.task_count for m in self.modules.values())
        if len(self.completed_tasks) >= total_tasks:
            return True, "All tasks in all modules complete"

        # Check no pending tasks
        ready_tasks = self._get_ready_tasks()
        if not ready_tasks and len(self.running_agents) == 0:
            return True, "No pending tasks in any queue"

        # Check loop timeout
        safety = self.config.get("safety", {})
        max_iterations = safety.get("max_loop_iterations", 100)
        if self.iteration_count >= max_iterations:
            return True, f"Loop timeout exceeded ({max_iterations} iterations)"

        # Check consecutive failures
        max_failures = safety.get("max_consecutive_failures", 5)
        if self.consecutive_failures >= max_failures:
            return True, f"Max consecutive failures ({max_failures})"

        return False, ""

    def run_continuous_loop(self) -> None:
        """Run the continuous autonomous development loop"""
        print(f"🚀 Orchestrator Agent Starting")
        print(f"Session ID: {self.session_id}")
        print(f"Configuration: {self.config_path}")
        print("")

        # Load modules and tasks
        print("📋 Loading modules and task queues...")
        self._load_modules()

        print(f"   Modules: {len(self.modules)}")
        print(f"   Total tasks: {sum(m.task_count for m in self.modules.values())}")
        print(f"   Completed: {len(self.completed_tasks)}")
        print("")

        # Continuous loop
        wave_strategy = self.config["continuous_loop"]["wave_strategy"]

        while True:
            self.iteration_count += 1

            print(f"\n{'='*60}")
            print(f"🔄 Iteration {self.iteration_count}")
            print(f"{'='*60}")

            # Check termination conditions
            should_terminate, reason = self._check_termination_conditions()
            if should_terminate:
                print(f"\n✓ Termination condition met: {reason}")
                break

            # Get ready tasks
            ready_tasks = self._get_ready_tasks()

            if not ready_tasks:
                print("\n⊘ No ready tasks, waiting for agents to complete...")
                time.sleep(5)
                continue

            print(f"\n📊 Status:")
            print(f"   Ready tasks: {len(ready_tasks)}")
            print(f"   Running agents: {len(self.running_agents)}")
            print(f"   Completed: {len(self.completed_tasks)}")

            # Update CONTEXT.md
            self._update_context_md(ready_tasks)

            # Execute wave strategy
            for phase in wave_strategy:
                self._execute_wave(phase)

            # Wait before next iteration
            time.sleep(10)

        # Final summary
        print(f"\n{'='*60}")
        print(f"✅ Orchestrator Agent Complete")
        print(f"{'='*60}")
        print(f"Total iterations: {self.iteration_count}")
        print(f"Total tasks completed: {len(self.completed_tasks)}")
        print(f"Session ID: {self.session_id}")
        print("")

        # Save session summary
        summary_file = self.log_dir / f"session-{self.session_id}-summary.json"
        summary = {
            "session_id": self.session_id,
            "iterations": self.iteration_count,
            "completed_tasks": len(self.completed_tasks),
            "modules": {
                name: {
                    "completed": module.completed,
                    "total": module.task_count,
                    "progress": module.progress
                }
                for name, module in self.modules.items()
            },
            "timestamp": datetime.now().isoformat()
        }

        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"Summary saved: {summary_file}")


def main():
    """Main entry point"""
    orchestrator = OrchestratorAgent()

    try:
        orchestrator.run_continuous_loop()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("Saving state and exiting...")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
