# utils/media_fetcher.py
# utils/media_fetcher.py
import requests

# Manual image mapping for common birds (Crow & Parrot included)
IMAGE_MAP = {
    # Crows
    "House Crow": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Corvus_splendens.jpg/500px-Corvus_splendens.jpg",
    "Jungle Crow": "https://upload.wikimedia.org/wikipedia/commons/7/7e/Jungle_Crow_%28Corvus_macrorhynchos%29.jpg",
    "Carrion Crow": "https://upload.wikimedia.org/wikipedia/commons/8/8e/Carrion_Crow_%28Corvus_corone%29.jpg",

    # Parrots / Parakeets
    "Alexandrine Parakeet": "https://upload.wikimedia.org/wikipedia/commons/7/7d/Alexandrine_Parakeet.jpg",
    "Rose-ringed Parakeet": "https://upload.wikimedia.org/wikipedia/commons/0/05/Ringnecked_Parakeet_-_Psittacula_krameri.jpg",
    "Blue-headed Parrot": "https://upload.wikimedia.org/wikipedia/commons/5/57/Blue-headed_Parrot.jpg",
    "Plum-headed Parakeet": "https://upload.wikimedia.org/wikipedia/commons/e/eb/Plum-headed_Parakeet.jpg",

    # Sparrows (just for reference)
    "Yellow-throated Sparrow": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Yellow-throated_sparrow_%28Petronia_xanthocollis%29_by_Shantanu_Kuveskar.jpg/500px-Yellow-throated_sparrow_%28Petronia_xanthocollis%29_by_Shantanu_Kuveskar.jpg",
    "Russet Sparrow": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Passer_rutilans.JPG/500px-Passer_rutilans.JPG",
    "House Sparrow": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/House_sparrow_male_in_Prospect_Park_%2853532%29.jpg/500px-House_sparrow_male_in_Prospect_Park_%2853532%29.jpg",

    # Placeholder for birds not in map
    "DEFAULT": "https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg",
}

PLACEHOLDER_IMAGE = IMAGE_MAP["DEFAULT"]

def get_bird_image(common_name, scientific_name=None):
    """
    Returns image URL for the bird.
    First checks manual IMAGE_MAP using common_name.
    If not found and scientific_name is provided, tries scientific_name.
    Else returns placeholder image.
    """
    # Try common name
    img_url = IMAGE_MAP.get(common_name)
    if img_url:
        return img_url

    # Try scientific name
    if scientific_name:
        img_url = IMAGE_MAP.get(scientific_name)
        if img_url:
            return img_url

    # Fallback
    return PLACEHOLDER_IMAGE
