import requests
from urllib.parse import quote

IMAGE_MAP = {
    "Eurasian Pygmy-Owl": "https://upload.wikimedia.org/wikipedia/commons/7/79/Eurasian_pygmy_owl_%28Glaucidium_passerinum%29_Bia%C5%82owieza.jpg",

    "House Crow": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Corvus_splendens.jpg/500px-Corvus_splendens.jpg",
    "Jungle Crow": "https://upload.wikimedia.org/wikipedia/commons/7/7e/Jungle_Crow_%28Corvus_macrorhynchos%29.jpg",
    "Carrion Crow": "https://upload.wikimedia.org/wikipedia/commons/8/8e/Carrion_Crow_%28Corvus_corone%29.jpg",

    "Alexandrine Parakeet": "https://upload.wikimedia.org/wikipedia/commons/7/7d/Alexandrine_Parakeet.jpg",
    "Rose-ringed Parakeet": "https://upload.wikimedia.org/wikipedia/commons/0/05/Ringnecked_Parakeet_-_Psittacula_krameri.jpg",
    "Blue-headed Parrot": "https://upload.wikimedia.org/wikipedia/commons/5/57/Blue-headed_Parrot.jpg",
    "Plum-headed Parakeet": "https://upload.wikimedia.org/wikipedia/commons/e/eb/Plum-headed_Parakeet.jpg",

    "Yellow-throated Sparrow": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Yellow-throated_sparrow_%28Petronia_xanthocollis%29_by_Shantanu_Kuveskar.jpg/500px-Yellow-throated_sparrow_%28Petronia_xanthocollis%29_by_Shantanu_Kuveskar.jpg",
    "Russet Sparrow": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Passer_rutilans.JPG/500px-Passer_rutilans.JPG",
    "House Sparrow": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/House_sparrow_male_in_Prospect_Park_%2853532%29.jpg/500px-House_sparrow_male_in_Prospect_Park_%2853532%29.jpg",

    "DEFAULT": "https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg",
}

PLACEHOLDER_IMAGE = IMAGE_MAP["DEFAULT"]

HEADERS = {
    "User-Agent": "BirdNova/1.0 (bird image lookup)"
}


def fetch_summary_image(title: str):
    try:
        safe_title = quote(title.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe_title}"
        res = requests.get(url, headers=HEADERS, timeout=5)

        if res.status_code == 200:
            data = res.json()

            if "originalimage" in data and "source" in data["originalimage"]:
                return data["originalimage"]["source"]

            if "thumbnail" in data and "source" in data["thumbnail"]:
                return data["thumbnail"]["source"]

    except Exception:
        pass

    return None


def search_wikipedia_title(query: str):
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
        }

        res = requests.get(url, params=params, headers=HEADERS, timeout=5)

        if res.status_code == 200:
            data = res.json()
            results = data.get("query", {}).get("search", [])

            if results:
                return results[0]["title"]

    except Exception:
        pass

    return None


def get_bird_image(common_name, scientific_name=None):
    # 1. Manual mapping first
    img = IMAGE_MAP.get(common_name)
    if img:
        return img

    # 2. Try scientific name directly
    if scientific_name:
        img = fetch_summary_image(scientific_name)
        if img:
            return img

    # 3. Try common name directly
    img = fetch_summary_image(common_name)
    if img:
        return img

    # 4. Search Wikipedia by scientific name, then fetch that page
    if scientific_name:
        found_title = search_wikipedia_title(scientific_name)
        if found_title:
            img = fetch_summary_image(found_title)
            if img:
                return img

    # 5. Search Wikipedia by common name, then fetch that page
    found_title = search_wikipedia_title(common_name)
    if found_title:
        img = fetch_summary_image(found_title)
        if img:
            return img

    # 6. Final fallback
    return PLACEHOLDER_IMAGE