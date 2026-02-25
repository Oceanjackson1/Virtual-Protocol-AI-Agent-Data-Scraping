"""
Main entry point for the Virtuals ACP Agent scraper.
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import ACPScraper, load_config
from src.excel_exporter import export_to_excel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("acp-scraper")


async def run_once(config: dict) -> str:
    """Execute a single scrape run and return the output file path."""
    scraper = ACPScraper(config)
    agents, global_metrics = await scraper.scrape_all()

    out_cfg = config.get("output", {})
    output_dir = out_cfg.get("directory", "./output")
    prefix = out_cfg.get("filename_prefix", "acp_agents")

    filepath = export_to_excel(agents, global_metrics, output_dir, prefix)
    logger.info("Excel exported: %s", filepath)
    logger.info("Total agents: %d | Platform AGDP: $%.2f", len(agents), global_metrics.total_agdp_latest)
    return filepath


def main():
    config = load_config()
    filepath = asyncio.run(run_once(config))
    print(f"\n完成！文件已保存至: {filepath}")


if __name__ == "__main__":
    main()
