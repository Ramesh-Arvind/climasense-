"""Crop disease diagnosis and treatment tools.

Combines a curated knowledge base (FAO/CABI-derived) with real-time
Wikipedia API lookups for broader disease coverage.
"""

import logging
import requests

from climasense.cache.cached_tool import cached_tool

logger = logging.getLogger(__name__)

# Core knowledge base of common crop diseases affecting smallholder farmers
DISEASE_DB = {
    "early_blight": {
        "name": "Early Blight",
        "crops": ["tomato", "potato", "eggplant"],
        "pathogen": "Alternaria solani",
        "symptoms": "Dark brown concentric rings on older leaves, starting from bottom. Leaves yellow and drop.",
        "conditions": "Warm (24-29C), humid, poor air circulation",
        "treatment": [
            "Remove and destroy infected leaves immediately",
            "Apply copper-based fungicide (Bordeaux mixture)",
            "Improve plant spacing for air circulation",
            "Mulch to prevent soil splash onto leaves",
            "Rotate crops - avoid planting Solanaceae in same spot for 2-3 years",
        ],
        "prevention": "Use resistant varieties, ensure proper spacing, avoid overhead irrigation",
        "severity": "moderate",
    },
    "late_blight": {
        "name": "Late Blight",
        "crops": ["tomato", "potato"],
        "pathogen": "Phytophthora infestans",
        "symptoms": "Water-soaked dark lesions on leaves, white fuzzy mold underneath. Rapid plant death.",
        "conditions": "Cool (10-20C), wet, spreads rapidly in rain",
        "treatment": [
            "URGENT: Remove and burn all infected plants immediately",
            "Apply metalaxyl-based fungicide if available",
            "Do NOT compost infected material",
            "Alert neighboring farmers - spreads by wind",
            "Harvest any unaffected tubers/fruit immediately",
        ],
        "prevention": "Use certified disease-free seed, resistant varieties, avoid planting near previous infection sites",
        "severity": "critical",
    },
    "maize_streak": {
        "name": "Maize Streak Virus",
        "crops": ["maize", "corn"],
        "pathogen": "Maize streak virus (MSV), transmitted by leafhoppers",
        "symptoms": "Yellow streaks along leaf veins, stunted growth, reduced ear size",
        "conditions": "Warm dry seasons when leafhopper populations peak",
        "treatment": [
            "No cure once infected - remove severely affected plants",
            "Control leafhopper vectors with neem-based sprays",
            "Plant resistant varieties (e.g., CIMMYT MSV-resistant lines)",
            "Early planting to avoid peak leafhopper season",
            "Intercrop with non-host plants to reduce vector landing",
        ],
        "prevention": "Use MSV-resistant cultivars, control volunteer maize, synchronize planting dates regionally",
        "severity": "high",
    },
    "cassava_mosaic": {
        "name": "Cassava Mosaic Disease",
        "crops": ["cassava"],
        "pathogen": "Cassava mosaic geminiviruses (CMGs), transmitted by whiteflies",
        "symptoms": "Yellow/green mosaic pattern on leaves, leaf curling, stunted growth, reduced tuber yield",
        "conditions": "Tropical, spread by whitefly Bemisia tabaci and infected cuttings",
        "treatment": [
            "Remove and burn severely infected plants",
            "Use only disease-free planting material from certified sources",
            "Control whiteflies with yellow sticky traps",
            "Apply neem oil spray for whitefly control",
            "Plant CMD-tolerant varieties (e.g., IITA improved varieties)",
        ],
        "prevention": "Source certified clean cuttings, rogue infected plants early, plant tolerant varieties",
        "severity": "high",
    },
    "rice_blast": {
        "name": "Rice Blast",
        "crops": ["rice"],
        "pathogen": "Magnaporthe oryzae",
        "symptoms": "Diamond-shaped lesions on leaves with gray centers. Neck rot causes panicle to break.",
        "conditions": "High humidity, moderate temperatures (25-28C), excess nitrogen fertilization",
        "treatment": [
            "Apply tricyclazole or isoprothiolane fungicide",
            "Reduce nitrogen fertilization",
            "Drain fields periodically to reduce humidity",
            "Use silicon-based fertilizers to strengthen cell walls",
            "Remove crop residues after harvest",
        ],
        "prevention": "Plant resistant varieties, balanced fertilization, avoid dense planting",
        "severity": "high",
    },
    "fall_armyworm": {
        "name": "Fall Armyworm",
        "crops": ["maize", "corn", "sorghum", "rice", "wheat"],
        "pathogen": "Spodoptera frugiperda (insect pest)",
        "symptoms": "Ragged holes in leaves, sawdust-like frass in whorl, larvae inside ear",
        "conditions": "Warm, can migrate long distances, multiple generations per year",
        "treatment": [
            "Hand-pick larvae from whorl (effective for small plots)",
            "Apply Bt (Bacillus thuringiensis) spray - safe biological control",
            "Use neem seed extract as natural pesticide",
            "Apply sand + ash mixture into whorl to suffocate larvae",
            "Release Trichogramma parasitoid wasps if available",
        ],
        "prevention": "Early planting, intercrop with repellent plants (desmodium), push-pull technology",
        "severity": "high",
    },
    "bacterial_wilt": {
        "name": "Bacterial Wilt",
        "crops": ["tomato", "potato", "eggplant", "pepper"],
        "pathogen": "Ralstonia solanacearum",
        "symptoms": "Sudden wilting of entire plant despite moist soil, brown discoloration of stem vascular tissue",
        "conditions": "Warm (25-35C), moist soils, spread through contaminated tools and water",
        "treatment": [
            "No chemical cure - remove and destroy infected plants immediately",
            "Do NOT compost infected material",
            "Solarize soil before replanting",
            "Disinfect all tools with bleach solution",
            "Rotate with non-host crops (cereals, grasses) for 3+ years",
        ],
        "prevention": "Use resistant rootstocks, improve drainage, avoid injuring roots during cultivation",
        "severity": "critical",
    },
    "rust": {
        "name": "Wheat Rust",
        "crops": ["wheat", "barley"],
        "pathogen": "Puccinia spp. (P. striiformis, P. triticina, P. graminis)",
        "symptoms": "Orange-brown pustules on leaves and stems, powdery spores released when touched",
        "conditions": "Cool-warm depending on species, high humidity, wind-dispersed spores",
        "treatment": [
            "Apply propiconazole or tebuconazole fungicide at first signs",
            "Remove volunteer wheat and alternative hosts",
            "Plant resistant varieties from your agricultural extension office",
            "Monitor fields regularly during susceptible growth stages",
        ],
        "prevention": "Use resistant cultivars, diversify varieties, early planting to avoid peak infection period",
        "severity": "high",
    },
}


def _search_wikipedia(query: str) -> str | None:
    """Search Wikipedia for disease information."""
    try:
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": query.replace(" ", "_"),
                "format": "json",
            },
            timeout=10,
            headers={"User-Agent": "ClimaSense/1.0 (Agricultural Advisory)"},
        )
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        for pid, page in pages.items():
            if pid != "-1":
                return page.get("extract", "")
    except requests.RequestException:
        pass
    return None


def _search_disease_articles(crop: str, symptoms: str) -> list[dict]:
    """Search Wikipedia for disease articles matching crop and symptoms."""
    results = []
    try:
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "format": "json",
                "srsearch": f"{crop} disease {symptoms}",
                "srlimit": 5,
            },
            timeout=10,
            headers={"User-Agent": "ClimaSense/1.0 (Agricultural Advisory)"},
        )
        resp.raise_for_status()
        for item in resp.json().get("query", {}).get("search", []):
            results.append({
                "title": item["title"],
                "snippet": item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
            })
    except requests.RequestException:
        pass
    return results


@cached_tool("disease")
def diagnose_crop_disease(
    crop: str,
    symptoms: str,
) -> dict:
    """Diagnose potential crop diseases based on symptoms.

    Uses curated knowledge base + Wikipedia API for comprehensive coverage.

    Args:
        crop: The crop type (e.g., 'tomato', 'maize', 'rice', 'cassava').
        symptoms: Description of observed symptoms.

    Returns:
        Dictionary with potential diagnoses ranked by likelihood.
    """
    crop_lower = crop.lower().strip()
    symptoms_lower = symptoms.lower()

    # Step 1: Check curated database
    matches = []
    for disease_id, info in DISEASE_DB.items():
        crop_match = any(c in crop_lower for c in info["crops"])
        if not crop_match:
            continue

        symptom_keywords = info["symptoms"].lower().split()
        overlap = sum(1 for w in symptom_keywords if w in symptoms_lower)
        relevance = overlap / max(len(symptom_keywords), 1)

        matches.append({
            "disease": info["name"],
            "pathogen": info["pathogen"],
            "expected_symptoms": info["symptoms"],
            "favorable_conditions": info["conditions"],
            "severity": info["severity"],
            "relevance_score": round(relevance, 2),
            "source": "curated_database",
        })

    matches.sort(key=lambda x: x["relevance_score"], reverse=True)

    # Step 2: Supplement with Wikipedia search for broader coverage
    wiki_results = _search_disease_articles(crop, symptoms)
    wiki_suggestions = []
    for wr in wiki_results:
        title = wr["title"]
        # Skip if already in our matches
        if any(title.lower() in m["disease"].lower() or m["disease"].lower() in title.lower() for m in matches):
            continue
        wiki_suggestions.append({
            "disease": title,
            "snippet": wr["snippet"],
            "source": "wikipedia",
        })

    return {
        "crop": crop,
        "reported_symptoms": symptoms,
        "potential_diagnoses": matches[:3],
        "additional_possibilities": wiki_suggestions[:3],
        "note": "For definitive diagnosis, submit a clear photo of affected plant parts for visual analysis.",
    }


@cached_tool("disease")
def get_treatment_recommendation(
    disease_name: str,
) -> dict:
    """Get treatment recommendations for a diagnosed crop disease.

    Checks curated database first, then falls back to Wikipedia for info.

    Args:
        disease_name: Name of the disease (e.g., 'Early Blight', 'Fall Armyworm').

    Returns:
        Dictionary with treatment steps, prevention tips, and urgency level.
    """
    name_lower = disease_name.lower().replace(" ", "_")

    # Check curated DB first
    best_match = None
    for disease_id, info in DISEASE_DB.items():
        if name_lower in disease_id or disease_id in name_lower:
            best_match = info
            break
        if name_lower in info["name"].lower().replace(" ", "_"):
            best_match = info
            break

    if best_match:
        return {
            "disease": best_match["name"],
            "severity": best_match["severity"],
            "affected_crops": best_match["crops"],
            "treatment_steps": best_match["treatment"],
            "prevention": best_match["prevention"],
            "urgency": "IMMEDIATE ACTION REQUIRED" if best_match["severity"] == "critical" else "Act within 1-2 days",
            "source": "curated_database",
        }

    # Fallback: search Wikipedia for the disease
    wiki_text = _search_wikipedia(disease_name)
    if wiki_text:
        return {
            "disease": disease_name,
            "description": wiki_text[:500],
            "source": "wikipedia",
            "note": "This information is from Wikipedia. Consult your local agricultural extension officer for specific treatment advice.",
        }

    return {
        "disease": disease_name,
        "error": "Disease not found. Please check spelling or use diagnose_crop_disease first.",
    }
