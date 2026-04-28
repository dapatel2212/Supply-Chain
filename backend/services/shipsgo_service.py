"""
ShipsGo API v2 Integration
Docs: https://shipsgo.com/api/
The v1 endpoint (/api/v1/) returned 404 — this uses the correct v2 base URL.
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)

SHIPSGO_API_KEY = os.getenv('SHIPSGO_API_KEY')

# ShipsGo API v2 base URL (v1 is deprecated and returns 404)
BASE_URL = 'https://shipsgo.com/api/v2'

SHIPSGO_WORKING = None  # None = untested


def _test_shipsgo():
    """Test ShipsGo connectivity on first use."""
    global SHIPSGO_WORKING
    if SHIPSGO_WORKING is not None:
        return SHIPSGO_WORKING
    if not SHIPSGO_API_KEY:
        logger.warning("SHIPSGO_API_KEY not set. ShipsGo integration disabled.")
        SHIPSGO_WORKING = False
        return False
    try:
        # Lightweight auth check
        r = requests.get(
            f'{BASE_URL}/ContainerService/GetContainerInfo',
            params={'authCode': SHIPSGO_API_KEY, 'containerNumber': 'PING'},
            timeout=8
        )
        # A 400/422 (bad container) still means the auth worked
        if r.status_code in (200, 400, 422):
            SHIPSGO_WORKING = True
            logger.info("✓ ShipsGo API v2 connected successfully")
        else:
            logger.warning(f"⚠️ ShipsGo API returned {r.status_code}. Falling back to local data.")
            SHIPSGO_WORKING = False
    except Exception as e:
        logger.warning(f"⚠️ ShipsGo API unavailable: {e}. Falling back to local data.")
        SHIPSGO_WORKING = False
    return SHIPSGO_WORKING


class ShipsGoService:
    """
    Real vessel/container tracking via ShipsGo API v2.
    Falls back to None (caller uses local DB data) when unavailable.
    """

    def get_container_info(self, container_number: str) -> dict | None:
        """
        Fetch live container tracking info.
        Returns dict on success, None on failure.
        """
        if not _test_shipsgo():
            return None
        try:
            r = requests.get(
                f'{BASE_URL}/ContainerService/GetContainerInfo',
                params={'authCode': SHIPSGO_API_KEY, 'containerNumber': container_number},
                timeout=10
            )
            r.raise_for_status()
            data = r.json()
            logger.info(f"✓ ShipsGo container info fetched for {container_number}")
            return data
        except requests.HTTPError as e:
            logger.error(f"ShipsGo HTTP error for {container_number}: {e}")
            return None
        except Exception as e:
            logger.error(f"ShipsGo error for {container_number}: {e}")
            return None

    def get_vessel_position(self, imo_number: str) -> dict | None:
        """
        Fetch real-time vessel position by IMO number.
        Returns dict on success, None on failure.
        """
        if not _test_shipsgo():
            return None
        try:
            r = requests.get(
                f'{BASE_URL}/VesselService/GetVesselInfo',
                params={'authCode': SHIPSGO_API_KEY, 'imoNumber': imo_number},
                timeout=10
            )
            r.raise_for_status()
            data = r.json()
            # Normalise to lat/lng for the tracking service
            position = {
                'lat': data.get('lat') or data.get('Lat') or data.get('latitude'),
                'lng': data.get('lon') or data.get('Lon') or data.get('longitude'),
                'speed': data.get('speed') or data.get('Speed'),
                'vessel_name': data.get('vesselName') or data.get('VesselName'),
                'raw': data
            }
            logger.info(f"✓ ShipsGo vessel position fetched for IMO {imo_number}")
            return position
        except requests.HTTPError as e:
            logger.error(f"ShipsGo HTTP error for IMO {imo_number}: {e}")
            return None
        except Exception as e:
            logger.error(f"ShipsGo error for IMO {imo_number}: {e}")
            return None
