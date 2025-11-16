import asyncio
import os
import logging
from app.services.sports_api import TheSportsDBService
from app.data_store import match_store

INTERVAL_SECONDS = 60 * 30

# Configure logging
logger = logging.getLogger("data_updater")

# Load teams from environment variable or use default
DEFAULT_TEAMS = ["Arsenal", "Chelsea", "Liverpool", "Brighton and Hove Albion"]
TEAM_NAMES = os.getenv("TEAM_NAMES", ",".join(DEFAULT_TEAMS)).split(",")


async def fetch_and_store_matches():
    service = TheSportsDBService()
    while True:
        logger.info("[Updater] Fetching latest matches...")
        try:
            all_matches = []
            for team_name in TEAM_NAMES:
                team = await service.search_team(team_name)
                matches = await service.get_recent_matches(team.id, limit=10)
                all_matches.extend(matches)
                # Add delay to avoid rate limiting
                await asyncio.sleep(1)
            if all_matches:
                match_store.update_matches(all_matches)
                logger.info(f"[Updater] Stored {len(all_matches)} matches.")
        except Exception as e:
            logger.error(f"[Updater] Error: {e}")
        await asyncio.sleep(INTERVAL_SECONDS)


async def update_matches():
    service = TheSportsDBService()

    all_matches = []

    for team_name in TEAM_NAMES:
        try:
            team = await service.search_team(team_name)
            matches = await service.get_latest_events(team.id)
            logger.info(f"[Updater] {team.name}: {len(matches)} recent matches fetched")
            all_matches.extend(matches)
        except Exception as e:
            logger.error(f"[Updater] Error fetching matches for {team_name}: {e}")
        # Add delay to avoid rate limiting
        await asyncio.sleep(1)

    await service.close()
    logger.info(f"[Updater] Total fetched matches: {len(all_matches)}")
