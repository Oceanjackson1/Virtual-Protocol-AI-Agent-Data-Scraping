"""
Core scraper: fetches all agent data via discovered API endpoints.
No browser needed — pure HTTP API calls.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import aiohttp
import yaml

from .models import AgentData, Offering, GlobalMetrics

logger = logging.getLogger(__name__)

BASE_URL = "https://acpx.virtuals.io/api"

ENDPOINTS = {
    "agents_list": "/agents",
    "metrics_agents": "/metrics/agents",
    "four_metrics": "/metrics/four-metrics",
    "agent_detail": "/agents/{agent_id}/details",
    "agent_metrics": "/metrics/agent/{agent_id}",
    "agent_ratings": "/job-ratings/agents/{agent_id}",
}


def load_config(path: str = "config.yaml") -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


class ACPScraper:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or load_config()
        scraper_cfg = self.config.get("scraper", {})
        self.concurrency = scraper_cfg.get("concurrency", 3)
        self.delay = scraper_cfg.get("request_delay_sec", 1.5)
        self.max_retries = scraper_cfg.get("max_retries", 3)
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        for attempt in range(self.max_retries):
            try:
                async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    logger.warning("HTTP %d for %s (attempt %d)", resp.status, url, attempt + 1)
            except Exception as e:
                logger.warning("Request error for %s: %s (attempt %d)", url, e, attempt + 1)
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        return None

    async def fetch_all_agents(self) -> List[dict]:
        """Fetch the full agent list from /agents endpoint."""
        url = BASE_URL + ENDPOINTS["agents_list"]
        params = {
            "filters[hasGraduated]": "all",
            "sort": "successfulJobCount",
            "search": "",
        }
        result = await self._get(url, params)
        if result and "data" in result:
            logger.info("Fetched %d agents from agent list", len(result["data"]))
            return result["data"]
        return []

    async def fetch_metrics_leaderboard(self, page: int = 1, page_size: int = 100) -> List[dict]:
        """Fetch agent leaderboard with volume/revenue metrics."""
        url = BASE_URL + ENDPOINTS["metrics_agents"]
        params = {
            "page": page,
            "pageSize": page_size,
            "sortBy": "volume",
            "sortOrder": "desc",
        }
        result = await self._get(url, params)
        if result and "data" in result:
            return result["data"]
        return []

    async def fetch_all_metrics_pages(self) -> List[dict]:
        """Paginate through the metrics leaderboard to get all agents."""
        all_agents = []
        page = 1
        page_size = 100
        while True:
            batch = await self.fetch_metrics_leaderboard(page, page_size)
            if not batch:
                break
            all_agents.extend(batch)
            logger.info("Metrics leaderboard page %d: got %d agents (total %d)", page, len(batch), len(all_agents))
            if len(batch) < page_size:
                break
            page += 1
            await asyncio.sleep(self.delay)
        return all_agents

    async def fetch_global_metrics(self) -> GlobalMetrics:
        """Fetch platform-level four-metrics."""
        url = BASE_URL + ENDPOINTS["four_metrics"]
        result = await self._get(url)
        gm = GlobalMetrics(scrape_time=datetime.now().isoformat())
        if result and "data" in result:
            data = result["data"].get("result", {})
            gav = data.get("GAV", {})
            seven_d = gav.get("7D", [])
            if seven_d:
                gm.total_agdp_latest = seven_d[-1].get("value", 0)
        return gm

    async def fetch_agent_detail(self, agent_id: int) -> Optional[dict]:
        """Fetch detailed info for a single agent."""
        url = BASE_URL + ENDPOINTS["agent_detail"].format(agent_id=agent_id)
        result = await self._get(url)
        if result and "data" in result:
            return result["data"]
        return None

    async def fetch_agent_metrics(self, agent_id: int) -> Optional[dict]:
        """Fetch metrics (volume, revenue, 7d data) for a single agent."""
        url = BASE_URL + ENDPOINTS["agent_metrics"].format(agent_id=agent_id)
        result = await self._get(url)
        if result and "data" in result:
            return result["data"]
        return None

    @staticmethod
    def _fix_capped_agdp(gross_agdp: float, volume: float) -> float:
        """API caps grossAgenticAmount at 99,999,999.99; fall back to volume when hit."""
        AGDP_CAP = 99_999_999.99
        if float(gross_agdp) >= AGDP_CAP and float(volume) > AGDP_CAP:
            return float(volume)
        return float(gross_agdp)

    def _parse_offerings(self, jobs_raw: list) -> List[Offering]:
        offerings = []
        for j in (jobs_raw or []):
            req = j.get("requirement", {})
            req_str = json.dumps(req, ensure_ascii=False) if isinstance(req, dict) else str(req)
            dlv = j.get("deliverable", {})
            dlv_str = json.dumps(dlv, ensure_ascii=False) if isinstance(dlv, dict) else str(dlv)
            price_v2 = j.get("priceV2", {}) or {}
            offerings.append(Offering(
                name=j.get("name", ""),
                description=j.get("description", ""),
                type=j.get("type", ""),
                price=price_v2.get("value", j.get("price", 0)) or 0,
                price_type=price_v2.get("type", ""),
                sla_minutes=j.get("slaMinutes", 0) or 0,
                requires_funds=j.get("requiredFunds", False),
                requirement=req_str if req_str != "{}" else "",
                deliverable=dlv_str if dlv_str != "{}" else "",
            ))
        return offerings

    def _merge_agent(
        self,
        rank: int,
        list_data: dict,
        metrics_data: Optional[dict],
        detail_data: Optional[dict],
    ) -> AgentData:
        """Merge data from multiple API sources into a single AgentData."""
        d = detail_data or {}
        m = metrics_data or {}
        l = list_data

        jobs_raw = d.get("jobs") or l.get("offerings") or []

        chains = l.get("enabledChains") or d.get("enabledChains") or []
        chains_str = ", ".join(c.get("name", "") for c in chains) if chains else ""

        last_active = m.get("lastActiveAt") or d.get("lastActiveAt") or l.get("lastActiveAt") or ""
        if last_active.startswith("2999"):
            online_status = "在线"
        else:
            online_status = "离线"

        agent_id = l.get("id") or d.get("id", 0)

        CATEGORY_CN = {
            "ON_CHAIN": "链上操作", "INFORMATION": "信息分析",
            "FUNCTIONAL": "功能型", "SOCIAL": "社交",
            "CREATIVE": "创意", "ENTERTAINMENT": "娱乐",
            "DEFI": "去中心化金融", "TRADING": "交易",
            "GAMING": "游戏", "DATA": "数据",
            "PRODUCTIVITY": "生产力", "UTILITY": "实用工具",
            "NONE": "未分类", "": "未分类",
        }
        ROLE_CN = {
            "PROVIDER": "服务提供者", "HYBRID": "混合型",
            "CONSUMER": "消费者", "EVALUATOR": "评估者",
            "PRODUCTIVITY": "生产力", "": "未指定",
        }
        CLUSTER_CN = {
            "hedgefund": "对冲基金", "trading": "交易",
            "defi": "去中心化金融", "social": "社交",
            "gaming": "游戏", "data": "数据分析",
            "mediahouse": "媒体", "infrastructure": "基础设施",
            "": "",
        }

        raw_category = str(l.get("category") or d.get("category") or "").strip()
        raw_role = str(d.get("role") or l.get("role") or "").strip()
        raw_cluster = str(d.get("cluster") or l.get("cluster") or "").strip()
        if raw_cluster == "None":
            raw_cluster = ""

        return AgentData(
            rank=rank,
            agent_id=agent_id,
            agent_link=f"https://app.virtuals.io/acp/agent-details/{agent_id}",
            name=l.get("name") or d.get("name", ""),
            category=CATEGORY_CN.get(raw_category, raw_category),
            description=d.get("description") or l.get("description") or "",
            volume=m.get("volume") or l.get("grossAgenticAmount", 0) or 0,
            gross_agdp=self._fix_capped_agdp(
                m.get("grossAgenticAmount") or l.get("grossAgenticAmount", 0) or 0,
                m.get("volume") or l.get("grossAgenticAmount", 0) or 0,
            ),
            revenue=m.get("revenue", 0) or 0,
            success_rate=min(max(float(m.get("successRate") or d.get("successRate") or l.get("successRate", 0) or 0), 0), 100),
            rating=l.get("rating") or d.get("rating"),
            total_jobs=m.get("successfulJobCount") or d.get("transactionCount") or l.get("transactionCount", 0) or 0,
            successful_jobs=m.get("successfulJobCount") or d.get("successfulJobCount") or l.get("successfulJobCount", 0) or 0,
            unique_active_wallets=m.get("uniqueBuyerCount") or d.get("uniqueBuyerCount") or l.get("uniqueBuyerCount", 0) or 0,
            unique_buyers=m.get("uniqueBuyerCount") or d.get("uniqueBuyerCount") or l.get("uniqueBuyerCount", 0) or 0,
            online_status=online_status,
            last_active_at=last_active if not last_active.startswith("2999") else "始终在线",
            transaction_count=d.get("transactionCount") or l.get("transactionCount", 0) or 0,
            offerings=self._parse_offerings(jobs_raw),
            wallet_address=d.get("walletAddress") or l.get("walletAddress", ""),
            contract_address=d.get("contractAddress") or l.get("contractAddress", ""),
            token_address=d.get("tokenAddress") or l.get("tokenAddress", ""),
            owner_address=d.get("ownerAddress") or l.get("ownerAddress", ""),
            twitter_handle=d.get("twitterHandle") or l.get("twitterHandle") or "",
            symbol=d.get("symbol") or l.get("symbol") or "",
            profile_pic_url=d.get("profilePic") or l.get("profilePic", ""),
            role=ROLE_CN.get(raw_role, raw_role),
            cluster=CLUSTER_CN.get(raw_cluster, raw_cluster),
            has_graduated=d.get("hasGraduated", False) or l.get("hasGraduated", False),
            wallet_balance=str(d.get("walletBalance") or l.get("walletBalance") or ""),
            enabled_chains=chains_str,
            virtual_agent_id=str(d.get("virtualAgentId") or l.get("virtualAgentId") or ""),
            is_virtual_agent=d.get("isVirtualAgent", False) or l.get("isVirtualAgent", False),
            created_at=d.get("createdAt") or l.get("createdAt") or "",
        )

    async def scrape_all(self) -> Tuple[List[AgentData], GlobalMetrics]:
        """Main entry: scrape everything and return merged data."""
        async with aiohttp.ClientSession() as session:
            self.session = session

            logger.info("Fetching global metrics...")
            global_metrics = await self.fetch_global_metrics()

            logger.info("Fetching agent list...")
            agents_list = await self.fetch_all_agents()

            logger.info("Fetching metrics leaderboard (all pages)...")
            metrics_list = await self.fetch_all_metrics_pages()

            metrics_map: Dict[int, dict] = {a["id"]: a for a in metrics_list}
            agents_map: Dict[int, dict] = {a["id"]: a for a in agents_list}

            all_ids = sorted(set(list(agents_map.keys()) + list(metrics_map.keys())))
            global_metrics.total_agents = len(all_ids)
            logger.info("Total unique agents: %d", len(all_ids))

            semaphore = asyncio.Semaphore(self.concurrency)

            async def fetch_detail_throttled(aid: int) -> Tuple[int, Optional[dict], Optional[dict]]:
                async with semaphore:
                    detail = await self.fetch_agent_detail(aid)
                    await asyncio.sleep(self.delay)
                    metrics = await self.fetch_agent_metrics(aid)
                    await asyncio.sleep(self.delay)
                    return aid, detail, metrics

            logger.info("Fetching details for %d agents (concurrency=%d)...", len(all_ids), self.concurrency)
            tasks = [fetch_detail_throttled(aid) for aid in all_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            detail_map: Dict[int, dict] = {}
            ind_metrics_map: Dict[int, dict] = {}
            for r in results:
                if isinstance(r, Exception):
                    logger.error("Detail fetch error: %s", r)
                    continue
                aid, detail, ind_metrics = r
                if detail:
                    detail_map[aid] = detail
                if ind_metrics:
                    ind_metrics_map[aid] = ind_metrics

            sorted_ids = sorted(
                all_ids,
                key=lambda x: (ind_metrics_map.get(x, {}).get("volume", 0) or metrics_map.get(x, {}).get("volume", 0) or 0),
                reverse=True,
            )

            agent_data_list: List[AgentData] = []
            for rank, aid in enumerate(sorted_ids, 1):
                list_entry = agents_map.get(aid, {"id": aid})
                merged_metrics = ind_metrics_map.get(aid) or metrics_map.get(aid)
                detail = detail_map.get(aid)
                agent = self._merge_agent(rank, list_entry, merged_metrics, detail)
                agent_data_list.append(agent)

            logger.info("Scraping complete. Total agents: %d", len(agent_data_list))
            return agent_data_list, global_metrics
