import logging
import httpx
import asyncio
from typing import List, Dict, Any, Tuple, Optional
from backend.app.config import settings

logger = logging.getLogger(__name__)

class BrightDataClient:
    """
    HTTP client wrapper for the Bright Data Data Collector API (DCA).
    Integrates with the trigger and dataset polling endpoints using BRIGHT_DATA_API_TOKEN.
    """
    def __init__(self):
        self.api_token = settings.BRIGHT_DATA_API_TOKEN
        self.base_url = "https://api.brightdata.com/dca"
        
    @property
    def is_configured(self) -> bool:
        return bool(self.api_token and self.api_token.strip())

    async def trigger_run(self, collector_id: str, target_url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Triggers a new scraping run for a specific collector.
        Returns: (collection_id, error_message)
        """
        if not self.is_configured:
            return None, "Bright Data API Token is not configured."

        url = f"{self.base_url}/trigger"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        params = {
            "collector": collector_id,
            "queue_next": 1
        }
        # Payload specifies the target URL(s) to scrape
        payload = [{"url": target_url}]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                logger.info(f"Triggering Bright Data collector {collector_id} for URL {target_url}")
                response = await client.post(url, headers=headers, params=params, json=payload)
                
                if response.status_code == 401:
                    return None, "Unauthorized: Invalid Bright Data API Token."
                elif response.status_code != 200:
                    return None, f"Failed to trigger collector. HTTP {response.status_code}: {response.text}"
                
                res_data = response.json()
                collection_id = res_data.get("collection_id") or res_data.get("snapshot_id")
                if not collection_id:
                    return None, f"Trigger succeeded but no collection_id or snapshot_id was returned. Response: {res_data}"
                
                return collection_id, None

        except Exception as e:
            logger.error(f"Error triggering Bright Data collector: {e}")
            return None, str(e)

    async def get_dataset(self, collection_id: str) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Retrieves the scraped dataset for a completed run using the collection_id.
        Returns: (dataset_records, error_message)
        """
        if not self.is_configured:
            return None, "Bright Data API Token is not configured."

        url = f"{self.base_url}/dataset"
        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        params = {
            "id": collection_id
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                logger.info(f"Retrieving Bright Data dataset for collection {collection_id}")
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    # Dataset is ready and returned
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            return data, None
                        else:
                            return [data], None
                    except Exception as parse_err:
                        return None, f"Failed to parse dataset JSON: {parse_err}"
                elif response.status_code == 202:
                    # Job is still running/processing
                    return None, "RUNNING"
                elif response.status_code == 404:
                    return None, f"Collection ID {collection_id} not found."
                else:
                    return None, f"HTTP Error {response.status_code}: {response.text}"

        except Exception as e:
            logger.error(f"Error fetching Bright Data dataset: {e}")
            return None, str(e)

    async def poll_dataset(self, collection_id: str, max_attempts: int = 15, delay_seconds: int = 5) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Polls the dataset endpoint until the results are ready or a timeout/error occurs.
        """
        for attempt in range(max_attempts):
            records, status = await self.get_dataset(collection_id)
            if status == "RUNNING":
                logger.info(f"Dataset {collection_id} still processing. Retrying in {delay_seconds}s... (Attempt {attempt+1}/{max_attempts})")
                await asyncio.sleep(delay_seconds)
                continue
            
            # If records are found, or some other terminal error occurs, return it
            return records, status

        return None, f"Polling timed out after {max_attempts * delay_seconds} seconds."
