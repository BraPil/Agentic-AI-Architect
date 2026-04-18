"""
Orchestrator — Master agent that coordinates all specialist agents.

Manages:
  - Agent lifecycle (initialize, run, shutdown)
  - Intelligence cycle scheduling
  - Inter-agent data flow
  - Error recovery and retries
  - CLI and programmatic entry points

Usage (CLI):
    python -m src.agents.orchestrator --mode full
    python -m src.agents.orchestrator --mode trends
    python -m src.agents.orchestrator --mode tools
    python -m src.agents.orchestrator --mode server --port 8080

Usage (Python):
    from src.agents.orchestrator import Orchestrator
    orch = Orchestrator()
    orch.initialize()
    result = orch.run_cycle()
"""

import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .base_agent import AgentResult, AgentStatus, BaseAgent
from .crawler_agent import CrawlerAgent
from .documentation_agent import DocumentationAgent
from .research_agent import ResearchAgent
from .tool_discovery_agent import ToolDiscoveryAgent
from .trend_tracker_agent import TrendTrackerAgent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cycle result
# ---------------------------------------------------------------------------

@dataclass
class CycleResult:
    """Result of a complete intelligence cycle."""

    cycle_number: int
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    crawled_count: int = 0
    findings_count: int = 0
    trend_alerts: int = 0
    tool_alerts: int = 0
    documents_generated: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_number": self.cycle_number,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "crawled_count": self.crawled_count,
            "findings_count": self.findings_count,
            "trend_alerts": self.trend_alerts,
            "tool_alerts": self.tool_alerts,
            "documents_generated": self.documents_generated,
            "success": self.success,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    """
    Coordinates all specialist agents through a complete intelligence cycle.

    A cycle follows this data flow::

        CrawlerAgent
            → raw documents
        ResearchAgent
            → research findings
        TrendTrackerAgent (receives findings)
            → trend scores + alerts
        ToolDiscoveryAgent (receives findings)
            → tool registry + alerts
        DocumentationAgent (receives all outputs)
            → generated documents

    Configuration keys (``config`` dict):
        crawler_config (dict): Config passed to CrawlerAgent.
        research_config (dict): Config passed to ResearchAgent.
        trend_config (dict): Config passed to TrendTrackerAgent.
        tool_config (dict): Config passed to ToolDiscoveryAgent.
        doc_config (dict): Config passed to DocumentationAgent.
        max_cycle_errors (int): Abort cycle if this many agent errors occur (default 3).
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: dict[str, Any] = config or {}
        self._cycle_count: int = 0
        self._cycle_history: list[CycleResult] = []
        self._agents_initialized: bool = False

        # Instantiate agents with their configs
        self.crawler = CrawlerAgent(config=self.config.get("crawler_config"))
        self.researcher = ResearchAgent(config=self.config.get("research_config"))
        self.trend_tracker = TrendTrackerAgent(config=self.config.get("trend_config"))
        self.tool_discovery = ToolDiscoveryAgent(config=self.config.get("tool_config"))
        self.documentation = DocumentationAgent(config=self.config.get("doc_config"))

        self._all_agents = [
            self.crawler,
            self.researcher,
            self.trend_tracker,
            self.tool_discovery,
            self.documentation,
        ]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize all agents."""
        logger.info("Orchestrator initializing %d agents", len(self._all_agents))
        for agent in self._all_agents:
            try:
                agent.initialize()
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to initialize %s: %s", agent.name, exc)
        self._agents_initialized = True
        logger.info("Orchestrator ready")

    def shutdown(self) -> None:
        """Gracefully shut down all agents."""
        logger.info("Orchestrator shutting down agents")
        for agent in self._all_agents:
            try:
                agent.shutdown()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Error shutting down %s: %s", agent.name, exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_agent_step(
        self,
        agent: BaseAgent,
        task_input: Any = None,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ) -> AgentResult:
        """Run an agent step with exponential-backoff retry on ERROR status."""
        result = agent.run(task_input)
        attempts = 1
        while result.status == AgentStatus.ERROR and attempts < max_retries:
            delay = retry_delay * (2 ** (attempts - 1))
            logger.warning(
                "%s failed (attempt %d/%d), retrying in %.1fs: %s",
                agent.name, attempts, max_retries, delay, result.error,
            )
            time.sleep(delay)
            result = agent.run(task_input)
            attempts += 1
        return result

    def _run_parallel_analysis(
        self, findings: list[dict[str, Any]]
    ) -> tuple[AgentResult, AgentResult]:
        """Run TrendTracker and ToolDiscovery concurrently; return (trend_result, tool_result)."""
        with ThreadPoolExecutor(max_workers=2) as pool:
            trend_future = pool.submit(self._run_agent_step, self.trend_tracker, findings)
            tool_future = pool.submit(self._run_agent_step, self.tool_discovery, findings)
            trend_result = trend_future.result()
            tool_result = tool_future.result()
        return trend_result, tool_result

    # ------------------------------------------------------------------
    # Intelligence cycle
    # ------------------------------------------------------------------

    def run_cycle(self, mode: str = "full") -> CycleResult:
        """
        Execute one complete intelligence cycle.

        Args:
            mode: 'full' | 'trends' | 'tools' | 'crawl_only'

        Returns:
            CycleResult with metrics and error summary.
        """
        if not self._agents_initialized:
            self.initialize()

        self._cycle_count += 1
        cycle = CycleResult(cycle_number=self._cycle_count)
        logger.info("Starting intelligence cycle #%d (mode=%s)", self._cycle_count, mode)

        max_errors: int = self.config.get("max_cycle_errors", 3)
        error_count = 0

        # Step 1: Crawl
        raw_documents: list[dict[str, Any]] = []
        if mode in ("full", "crawl_only"):
            crawl_result = self.crawler.run()
            if crawl_result.status == AgentStatus.SUCCESS:
                raw_documents = crawl_result.data or []
                cycle.crawled_count = len(raw_documents)
                logger.info("Crawled %d documents", cycle.crawled_count)
            else:
                cycle.errors.append(f"CrawlerAgent: {crawl_result.error}")
                error_count += 1

        if error_count >= max_errors:
            cycle.completed_at = datetime.now(timezone.utc)
            self._cycle_history.append(cycle)
            return cycle

        # Step 2: Research
        findings: list[dict[str, Any]] = []
        if mode in ("full", "trends", "tools") and raw_documents:
            research_result = self.researcher.run(raw_documents)
            if research_result.status == AgentStatus.SUCCESS:
                findings = research_result.data or []
                cycle.findings_count = len(findings)
                logger.info("Research produced %d findings", cycle.findings_count)
            else:
                cycle.errors.append(f"ResearchAgent: {research_result.error}")
                error_count += 1

        if error_count >= max_errors:
            cycle.completed_at = datetime.now(timezone.utc)
            self._cycle_history.append(cycle)
            return cycle

        # Steps 3 + 4: Trend tracking and tool discovery — run in parallel (independent)
        trend_data: dict[str, Any] = {}
        tool_data: dict[str, Any] = {}
        run_trends = mode in ("full", "trends")
        run_tools = mode in ("full", "tools")

        if run_trends and run_tools:
            trend_result, tool_result = self._run_parallel_analysis(findings)
        elif run_trends:
            trend_result = self._run_agent_step(self.trend_tracker, findings)
            tool_result = None
        elif run_tools:
            tool_result = self._run_agent_step(self.tool_discovery, findings)
            trend_result = None
        else:
            trend_result = tool_result = None

        if trend_result is not None:
            if trend_result.status == AgentStatus.SUCCESS:
                trend_data = trend_result.data or {}
                cycle.trend_alerts = len(trend_data.get("alerts", []))
                logger.info(
                    "Trend tracker: %d trends, %d alerts",
                    trend_data.get("total_trends", 0),
                    cycle.trend_alerts,
                )
            else:
                cycle.errors.append(f"TrendTrackerAgent: {trend_result.error}")
                error_count += 1

        if tool_result is not None:
            if tool_result.status == AgentStatus.SUCCESS:
                tool_data = tool_result.data or {}
                cycle.tool_alerts = len(tool_data.get("alerts", []))
                logger.info(
                    "Tool discovery: %d tools, %d alerts, %d new",
                    tool_data.get("total_tools", 0),
                    cycle.tool_alerts,
                    len(tool_data.get("newly_discovered", [])),
                )
            else:
                cycle.errors.append(f"ToolDiscoveryAgent: {tool_result.error}")
                error_count += 1

        # Step 5: Documentation
        if mode in ("full", "trends", "tools") and (trend_data or tool_data or findings):
            doc_input = {
                "findings": findings,
                "trend_data": trend_data,
                "tool_data": tool_data,
                "cycle_number": self._cycle_count,
            }
            doc_result = self.documentation.run(doc_input)
            if doc_result.status == AgentStatus.SUCCESS:
                docs = doc_result.data or []
                cycle.documents_generated = len(docs)
                logger.info("Documentation: %d documents generated", cycle.documents_generated)
            else:
                cycle.errors.append(f"DocumentationAgent: {doc_result.error}")

        cycle.completed_at = datetime.now(timezone.utc)
        self._cycle_history.append(cycle)

        duration = (cycle.completed_at - cycle.started_at).total_seconds()
        logger.info(
            "Cycle #%d complete in %.1fs — %s (errors: %d)",
            self._cycle_count,
            duration,
            "SUCCESS" if cycle.success else "PARTIAL",
            len(cycle.errors),
        )

        return cycle

    # ------------------------------------------------------------------
    # Query interface
    # ------------------------------------------------------------------

    def query_trends(self, top_n: int = 10) -> list[dict[str, Any]]:
        """Return top trends from the trend tracker."""
        return self.trend_tracker.get_top_trends(n=top_n)

    def query_tools(self, category: str | None = None, top_n: int = 10) -> list[dict[str, Any]]:
        """Return tools from the tool discovery registry."""
        if category:
            return self.tool_discovery.get_tools_by_category(category)
        return self.tool_discovery.get_top_tools(n=top_n)

    def get_cycle_history(self) -> list[dict[str, Any]]:
        """Return summary of all completed cycles."""
        return [c.to_dict() for c in self._cycle_history]

    def health_check(self) -> dict[str, bool]:
        """Return health status of all agents."""
        return {agent.name: agent.health_check() for agent in self._all_agents}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agentic AI Architect — Intelligence Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  full        Run a complete intelligence cycle (crawl → research → trends → tools → docs)
  trends      Run trend analysis only (skips crawl if no new data)
  tools       Run tool discovery only
  crawl_only  Crawl sources and print raw document count
  query       Query the knowledge base interactively

Examples:
  python -m src.agents.orchestrator --mode full
  python -m src.agents.orchestrator --mode trends --verbose
  python -m src.agents.orchestrator --mode query --query "best vector databases 2025"
        """,
    )
    parser.add_argument("--mode", choices=["full", "trends", "tools", "crawl_only", "query"],
                        default="full", help="Operating mode (default: full)")
    parser.add_argument("--query", type=str, default=None, help="Query string for query mode")
    parser.add_argument("--top-n", type=int, default=10, help="Number of results to return (default: 10)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    parser.add_argument("--no-crawl", action="store_true",
                        help="Skip crawling (use existing knowledge base)")

    args = parser.parse_args()
    _setup_logging(verbose=args.verbose)

    orchestrator = Orchestrator()

    try:
        orchestrator.initialize()

        if args.mode == "query":
            if not args.query:
                print("Error: --query is required in query mode", file=sys.stderr)
                sys.exit(1)
            trends = orchestrator.query_trends(top_n=args.top_n)
            print(f"\nTop {args.top_n} trends related to '{args.query}':")
            for i, t in enumerate(trends, 1):
                print(f"  {i}. {t['trend_name']} — score {t.get('composite', t.get('recency', 0)):.1f}")
        else:
            effective_mode = args.mode
            if args.no_crawl and effective_mode == "full":
                effective_mode = "trends"

            cycle_result = orchestrator.run_cycle(mode=effective_mode)
            print("\n" + "=" * 60)
            print(f"Cycle #{cycle_result.cycle_number} Complete")
            print("=" * 60)
            print(f"  Documents crawled  : {cycle_result.crawled_count}")
            print(f"  Findings produced  : {cycle_result.findings_count}")
            print(f"  Trend alerts       : {cycle_result.trend_alerts}")
            print(f"  Tool alerts        : {cycle_result.tool_alerts}")
            print(f"  Docs generated     : {cycle_result.documents_generated}")
            if cycle_result.errors:
                print(f"\n  Errors ({len(cycle_result.errors)}):")
                for err in cycle_result.errors:
                    print(f"    - {err}")
            print("=" * 60)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        orchestrator.shutdown()


if __name__ == "__main__":
    main()
