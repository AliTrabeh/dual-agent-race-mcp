"""Constructs agents, MCP servers, and MCP clients for a local match (Chunk 6).

The default LLM backend is a deterministic, no-network stub — this project
never makes a real API call unless the caller explicitly supplies a real
LLMClient (HW-F19). Swapping in a real provider requires no change here beyond
the constructor argument, proving the architecture's pluggability.
"""

from hw6_race.constants import AgentRole
from hw6_race.services.agents.cop_agent import CopAgent
from hw6_race.services.agents.llm_client import GatekeptLLMClient, LLMClient
from hw6_race.services.agents.strategies.heuristic_strategy import HeuristicStrategy
from hw6_race.services.agents.thief_agent import ThiefAgent
from hw6_race.services.mcp.auth import TokenAuthManager
from hw6_race.services.mcp.client import AgentMCPClient
from hw6_race.services.mcp.server_a import create_cop_server
from hw6_race.services.mcp.server_b import create_thief_server
from hw6_race.shared.gatekeeper import ApiGatekeeper

LOCAL_COP_TOKEN = "local-cop-token"
LOCAL_THIEF_TOKEN = "local-thief-token"


def _stub_complete(prompt: str) -> str:
    """No-network default LLM backend: never crashes, never leaks true state."""
    if "ROW,COL" in prompt:
        return "UNKNOWN"
    return "no comment"


def build_default_llm_client(gatekeeper: ApiGatekeeper) -> LLMClient:
    """Build the safe, no-network default LLM client, routed through `gatekeeper`."""
    return GatekeptLLMClient(gatekeeper, _stub_complete)


def build_auth_manager() -> TokenAuthManager:
    """Build a TokenAuthManager with both local agent tokens pre-registered."""
    manager = TokenAuthManager()
    manager.register(LOCAL_COP_TOKEN, AgentRole.COP.value)
    manager.register(LOCAL_THIEF_TOKEN, AgentRole.THIEF.value)
    return manager


def build_agents(llm_client: LLMClient) -> tuple[CopAgent, ThiefAgent]:
    """Build a Cop/Thief agent pair sharing one LLMClient and a heuristic strategy each."""
    return CopAgent(llm_client, HeuristicStrategy()), ThiefAgent(llm_client, HeuristicStrategy())


def build_clients(auth_manager: TokenAuthManager) -> tuple[AgentMCPClient, AgentMCPClient]:
    """Build the Cop/Thief MCP servers (in-process) and their bound clients."""
    cop_server = create_cop_server(auth_manager)
    thief_server = create_thief_server(auth_manager)
    cop_client = AgentMCPClient(cop_server, LOCAL_COP_TOKEN)
    thief_client = AgentMCPClient(thief_server, LOCAL_THIEF_TOKEN)
    return cop_client, thief_client
