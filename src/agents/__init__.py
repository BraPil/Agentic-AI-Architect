"""Agents package for the Agentic AI Architect system."""
from .base_agent import BaseAgent, AgentStatus, AgentResult
from .crawler_agent import CrawlerAgent
from .research_agent import ResearchAgent
from .trend_tracker_agent import TrendTrackerAgent
from .tool_discovery_agent import ToolDiscoveryAgent
from .documentation_agent import DocumentationAgent
from .orchestrator import Orchestrator

__all__ = [
    "BaseAgent",
    "AgentStatus",
    "AgentResult",
    "CrawlerAgent",
    "ResearchAgent",
    "TrendTrackerAgent",
    "ToolDiscoveryAgent",
    "DocumentationAgent",
    "Orchestrator",
]
