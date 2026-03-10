import requests

EBIRD_API_URL = "https://api.ebird.org/v2/data/obs/IN/recent"  # "IN" = India
EBIRD_TOKEN = "3l4240bdqvt7"  # Replace with your actual API key from https://documenter.getpostman.com/view/664302/ebird-api-20/2HTbHW

def get_rarity(scientific_name: str, lat: float = None, lon: float = None):
    """
    Estimate bird rarity from eBird sightings.
    Uses optional lat/lon for regional data (if available).
    """
    try:
        headers = {"X-eBirdApiToken": EBIRD_TOKEN}

        # Location-based endpoint (if lat/lon provided)
        if lat and lon:
            url = f"https://api.ebird.org/v2/data/obs/geo/recent"
            params = {"lat": lat, "lng": lon, "maxResults": 100}
        else:
            url = EBIRD_API_URL
            params = {"maxResults": 100}

        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            return "unknown"

        data = response.json()
        sightings = [d for d in data if scientific_name.lower() in d.get("sciName", "").lower()]

        if not sightings:
            return "rare"

        freq = len(sightings)
        if freq > 50:
            return "common"
        elif freq > 10:
            return "uncommon"
        else:
            return "rare"

    except Exception as e:
        print(f"[eBird ERROR] {e}")
        return "unknown"
