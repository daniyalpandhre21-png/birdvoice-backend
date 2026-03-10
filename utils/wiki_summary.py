import wikipediaapi

# Add custom user agent (required by Wikipedia)
USER_AGENT = "BirdVoiceApp/1.0 (https://github.com/yourusername/birdvoice)"  # tum chahe to apna naam ya link daal sakte ho

# Initialize Wikipedia API with user agent
wiki = wikipediaapi.Wikipedia(
    user_agent=USER_AGENT,
    language="en"
)

def get_bird_summary(species_name: str) -> str:
    """Fetch a short summary for the bird from Wikipedia."""
    try:
        page = wiki.page(species_name)
        if page.exists():
            # Return first 500 characters of summary
            return page.summary
        return None
    except Exception as e:
        print(f"Error fetching summary for {species_name}: {e}")
        return None
