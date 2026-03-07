"""
Base Agent — Abstract contract for all agents in the system.

Every agent must implement:
  - initialize(): set up resources (DB connections, API clients, etc.)
  - run(): execute the agent's primary task
  - health_check(): confirm the agent is operational
  - shutdown(): release resources gracefully
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Lifecycle status of an agent."""

    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class AgentResult:
    """Structured result returned by every agent run."""

    agent_name: str
    status: AgentStatus
    data: Any = None
    error: str | None = None
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float | None:
        """Wall-clock time for the run, or None if not yet complete."""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    def mark_complete(self, status: AgentStatus, data: Any = None, error: str | None = None) -> None:
        """Finalise the result after the agent task completes."""
        self.status = status
        self.data = data
        self.error = error
        self.completed_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary for logging / storage."""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }


class BaseAgent(ABC):
    """
    Abstract base class that every agent in the system must subclass.

    Lifecycle::

        agent = MyAgent(config)
        agent.initialize()
        result = agent.run(task_input)
        healthy = agent.health_check()
        agent.shutdown()

    Subclasses *must* implement :meth:`_execute`.  Override
    :meth:`initialize` and :meth:`shutdown` for resource management as
    needed.
    """

    def __init__(self, name: str, config: dict[str, Any] | None = None) -> None:
        self.name = name
        self.config: dict[str, Any] = config or {}
        self.status = AgentStatus.IDLE
        self._initialized = False
        self.logger = logging.getLogger(f"agent.{name}")

    # ------------------------------------------------------------------
    # Public lifecycle interface
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Set up agent resources (connections, caches, API clients).

        Subclasses should call ``super().initialize()`` first, then perform
        their own setup.
        """
        self.logger.info("Initializing agent: %s", self.name)
        self._initialized = True

    def run(self, task_input: Any = None) -> AgentResult:
        """Execute the agent task and return a structured result.

        This method handles timing, status transitions, and error capture so
        subclasses only need to implement :meth:`_execute`.
        """
        if not self._initialized:
            self.initialize()

        result = AgentResult(agent_name=self.name, status=AgentStatus.RUNNING)
        self.status = AgentStatus.RUNNING
        self.logger.info("Agent %s starting run", self.name)

        try:
            output = self._execute(task_input)
            result.mark_complete(AgentStatus.SUCCESS, data=output)
            self.status = AgentStatus.SUCCESS
            self.logger.info(
                "Agent %s completed successfully in %.2fs",
                self.name,
                result.duration_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            error_msg = str(exc)
            result.mark_complete(AgentStatus.ERROR, error=error_msg)
            self.status = AgentStatus.ERROR
            self.logger.error("Agent %s failed: %s", self.name, error_msg, exc_info=True)

        return result

    def health_check(self) -> bool:
        """Return True if the agent is healthy and ready to run."""
        return self._initialized and self.status not in (AgentStatus.ERROR, AgentStatus.SHUTDOWN)

    def shutdown(self) -> None:
        """Release all resources held by this agent."""
        self.logger.info("Shutting down agent: %s", self.name)
        self.status = AgentStatus.SHUTDOWN
        self._initialized = False

    # ------------------------------------------------------------------
    # Abstract implementation hook
    # ------------------------------------------------------------------

    @abstractmethod
    def _execute(self, task_input: Any = None) -> Any:
        """Implement the agent's core logic here.

        Args:
            task_input: Arbitrary task payload; type depends on the agent.

        Returns:
            Arbitrary output; type depends on the agent.

        Raises:
            Any exception signals failure and is captured by :meth:`run`.
        """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sleep_with_jitter(self, base_seconds: float, jitter_factor: float = 0.2) -> None:
        """Sleep for ``base_seconds`` ± random jitter to avoid thundering herd."""
        import random  # noqa: PLC0415

        jitter = random.uniform(-jitter_factor, jitter_factor) * base_seconds
        time.sleep(max(0.0, base_seconds + jitter))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, status={self.status.value!r})"
