"""
Data models for Virtuals ACP Agent scraper.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Offering:
    name: str = ""
    description: str = ""
    type: str = ""
    price: float = 0.0
    price_type: str = ""
    sla_minutes: int = 0
    requires_funds: bool = False
    requirement: str = ""
    deliverable: str = ""


@dataclass
class AgentData:
    # -- Core Info --
    rank: int = 0
    agent_id: int = 0
    agent_link: str = ""
    name: str = ""
    category: str = ""
    description: str = ""

    # -- Key Metrics --
    volume: float = 0.0
    gross_agdp: float = 0.0
    revenue: float = 0.0
    success_rate: float = 0.0
    rating: Optional[float] = None

    # -- Activity --
    total_jobs: int = 0
    successful_jobs: int = 0
    unique_active_wallets: int = 0
    unique_buyers: int = 0
    online_status: str = ""
    last_active_at: str = ""
    transaction_count: int = 0

    # -- What I Offer --
    offerings: List[Offering] = field(default_factory=list)

    # -- Identity & Links --
    wallet_address: str = ""
    contract_address: str = ""
    token_address: str = ""
    owner_address: str = ""
    twitter_handle: str = ""
    symbol: str = ""
    profile_pic_url: str = ""
    role: str = ""
    cluster: str = ""
    has_graduated: bool = False
    wallet_balance: str = ""
    enabled_chains: str = ""
    virtual_agent_id: str = ""
    is_virtual_agent: bool = False
    created_at: str = ""


@dataclass
class GlobalMetrics:
    scrape_time: str = ""
    total_agdp_latest: float = 0.0
    total_agents: int = 0
