import requests

def fetch_species_info(species_name):
    """Queries Wikipedia/eBird for structured species data."""
    try:
        # Mock response for hackathon stability
        return {
            "Scientific Name": f"Example {species_name.lower()}",
            "Conservation Status": "Least Concern",
            "Habitat": "Temperate forests & wetlands",
            "Diet": "Seeds, insects, berries",
            "Fun Fact": "Migrates up to 3000km annually."
        }
    except Exception as e:
        return {"Error": str(e)}