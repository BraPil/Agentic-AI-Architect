"""
Documentation Agent — Generates and updates structured markdown documents
from the knowledge base and agent outputs.

Responsibilities:
  - Daily digest of new findings
  - Phase document updates (phase-1 through phase-5)
  - Tool comparison tables
  - "What's new this week" reports
  - Knowledge base summary statistics
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .base_agent import BaseAgent


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class GeneratedDocument:
    """A documentation artifact produced by the DocumentationAgent."""

    doc_type: str  # daily_digest | weekly_report | tool_comparison | phase_update | summary
    title: str
    content: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_type": self.doc_type,
            "title": self.title,
            "content": self.content,
            "generated_at": self.generated_at.isoformat(),
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# DocumentationAgent
# ---------------------------------------------------------------------------

class DocumentationAgent(BaseAgent):
    """
    Generates structured documentation from agent outputs.

    Configuration keys:
        output_dir (str): Directory to write generated documents (default None = in-memory only).
        include_raw_data (bool): Include data tables in documents (default True).
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="DocumentationAgent", config=config)
        self._output_dir: str | None = self.config.get("output_dir")
        self._include_raw_data: bool = self.config.get("include_raw_data", True)

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    def _execute(self, task_input: Any = None) -> list[dict[str, Any]]:
        """
        Generate documentation from orchestrator cycle data.

        Args:
            task_input: dict with keys: findings, trend_data, tool_data, cycle_number

        Returns:
            List of GeneratedDocument dicts.
        """
        if not isinstance(task_input, dict):
            task_input = {}

        findings: list[dict[str, Any]] = task_input.get("findings", [])
        trend_data: dict[str, Any] = task_input.get("trend_data", {})
        tool_data: dict[str, Any] = task_input.get("tool_data", {})
        cycle_number: int = task_input.get("cycle_number", 1)

        documents: list[dict[str, Any]] = []

        # Daily digest
        digest = self._generate_daily_digest(findings, trend_data, tool_data, cycle_number)
        documents.append(digest.to_dict())

        # Tool comparison table (if tools are present)
        if tool_data.get("registry"):
            tool_doc = self._generate_tool_comparison(tool_data)
            documents.append(tool_doc.to_dict())

        # Trend report
        if trend_data.get("scores"):
            trend_doc = self._generate_trend_report(trend_data)
            documents.append(trend_doc.to_dict())

        # Write to disk if output_dir configured
        if self._output_dir:
            self._write_documents(documents)

        self.logger.info("DocumentationAgent generated %d documents", len(documents))
        return documents

    # ------------------------------------------------------------------
    # Document generators
    # ------------------------------------------------------------------

    def _generate_daily_digest(
        self,
        findings: list[dict[str, Any]],
        trend_data: dict[str, Any],
        tool_data: dict[str, Any],
        cycle_number: int,
    ) -> GeneratedDocument:
        """Generate a daily digest markdown document."""
        now = datetime.now(timezone.utc)
        lines = [
            f"# AI Architect Intelligence Digest — Cycle #{cycle_number}",
            f"> Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Summary",
            f"- **New findings**: {len(findings)}",
            f"- **Trends tracked**: {trend_data.get('total_trends', 0)}",
            f"- **Tools in registry**: {tool_data.get('total_tools', 0)}",
            f"- **New tools discovered**: {len(tool_data.get('newly_discovered', []))}",
            f"- **Trend alerts**: {len(trend_data.get('alerts', []))}",
            "",
        ]

        # Top trends
        top_trends = trend_data.get("scores", [])[:5]
        if top_trends:
            lines.append("## Top 5 Trends This Cycle")
            lines.append("")
            lines.append("| Rank | Trend | Score |")
            lines.append("|------|-------|-------|")
            for i, t in enumerate(top_trends, 1):
                lines.append(f"| {i} | {t['trend_name']} | {t['composite']:.1f} |")
            lines.append("")

        # Alerts
        all_alerts = trend_data.get("alerts", []) + tool_data.get("alerts", [])
        if all_alerts:
            lines.append("## Alerts")
            lines.append("")
            for alert in all_alerts:
                lines.append(f"- **[{alert.get('alert_type', 'ALERT')}]** {alert.get('message', '')}")
            lines.append("")

        # New tools
        new_tools = tool_data.get("newly_discovered", [])
        if new_tools:
            lines.append("## Newly Discovered Tools")
            lines.append("")
            for tool in new_tools:
                lines.append(f"- {tool}")
            lines.append("")

        # Key findings
        if findings and self._include_raw_data:
            lines.append("## Key Findings")
            lines.append("")
            for finding in findings[:10]:
                lines.append(f"### {finding.get('title', 'Untitled')}")
                lines.append(f"**Type**: {finding.get('content_type', 'unknown')} | "
                              f"**Namespace**: {finding.get('namespace', 'general')} | "
                              f"**Confidence**: {finding.get('confidence', 0):.1%}")
                lines.append("")
                lines.append(finding.get("summary", "")[:300])
                if finding.get("tools_mentioned"):
                    lines.append(f"\n**Tools**: {', '.join(finding['tools_mentioned'][:5])}")
                lines.append("")
                lines.append(f"*Source: [{finding.get('source_name', finding.get('source_url', 'unknown'))}]({finding.get('source_url', '#')})*")
                lines.append("")

        return GeneratedDocument(
            doc_type="daily_digest",
            title=f"AI Architect Intelligence Digest — Cycle #{cycle_number}",
            content="\n".join(lines),
            metadata={"cycle_number": cycle_number, "findings_count": len(findings)},
        )

    def _generate_tool_comparison(self, tool_data: dict[str, Any]) -> GeneratedDocument:
        """Generate a tool comparison matrix document."""
        registry = tool_data.get("registry", [])
        categories: dict[str, list[dict[str, Any]]] = {}
        for tool in registry:
            cat = tool.get("category", "other")
            categories.setdefault(cat, []).append(tool)

        lines = [
            "# AI Tools Registry",
            f"> Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            f"**Total tools tracked**: {len(registry)}",
            "",
        ]

        for category, tools in sorted(categories.items()):
            lines.append(f"## {category.replace('_', ' ').title()}")
            lines.append("")
            lines.append("| Tool | Status | Score | Description |")
            lines.append("|------|--------|-------|-------------|")
            for tool in sorted(tools, key=lambda t: t.get("evaluation_score", 0), reverse=True):
                status_emoji = {"active": "🟢", "deprecated": "🔴", "archived": "🔴", "experimental": "🟡"}.get(
                    tool.get("status", "active"), "⚪"
                )
                lines.append(
                    f"| [{tool['name']}]({tool.get('url', '#')}) "
                    f"| {status_emoji} {tool.get('status', 'active')} "
                    f"| {tool.get('evaluation_score', 0):.1f} "
                    f"| {tool.get('description', '')[:80]} |"
                )
            lines.append("")

        return GeneratedDocument(
            doc_type="tool_comparison",
            title="AI Tools Registry",
            content="\n".join(lines),
            metadata={"tool_count": len(registry)},
        )

    def _generate_trend_report(self, trend_data: dict[str, Any]) -> GeneratedDocument:
        """Generate a trend scoring report."""
        scores = trend_data.get("scores", [])
        alerts = trend_data.get("alerts", [])
        lines = [
            "# AI Architecture Trend Report",
            f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            trend_data.get("summary", ""),
            "",
            "## Full Trend Ranking",
            "",
            "| Rank | Trend | Composite | Recency | Velocity | Credibility | Evidence |",
            "|------|-------|-----------|---------|----------|-------------|----------|",
        ]
        for i, s in enumerate(scores, 1):
            lines.append(
                f"| {i} | {s['trend_name']} | **{s['composite']:.1f}** "
                f"| {s.get('recency', 0):.1f} | {s.get('adoption_velocity', 0):.1f} "
                f"| {s.get('credibility', 0):.1f} | {s.get('evidence_count', 0)} |"
            )

        if alerts:
            lines.append("")
            lines.append("## Alerts")
            lines.append("")
            for alert in alerts:
                emoji = {"NEW_TREND": "🆕", "BREAKTHROUGH": "🚀", "DECLINE": "📉"}.get(
                    alert.get("alert_type", ""), "🔔"
                )
                lines.append(f"{emoji} {alert.get('message', '')}")

        return GeneratedDocument(
            doc_type="trend_report",
            title="AI Architecture Trend Report",
            content="\n".join(lines),
            metadata={"trend_count": len(scores), "alert_count": len(alerts)},
        )

    # ------------------------------------------------------------------
    # File output
    # ------------------------------------------------------------------

    def _write_documents(self, documents: list[dict[str, Any]]) -> None:
        """Write generated documents to the output directory."""
        import os  # noqa: PLC0415
        import pathlib  # noqa: PLC0415

        output_path = pathlib.Path(self._output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for doc in documents:
            filename = (
                f"{doc['doc_type']}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.md"
            )
            filepath = output_path / filename
            filepath.write_text(doc["content"], encoding="utf-8")
            self.logger.info("Written: %s", filepath)
