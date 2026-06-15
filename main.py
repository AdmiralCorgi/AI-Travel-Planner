from collections import Counter
from functools import lru_cache
from html import unescape
import os
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


MODEL_NAME = os.getenv("TRAVEL_MODEL", "google/flan-t5-small")
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_HEADERS = {
    "User-Agent": "AI Travel Planner student project (local development)"
}

INTEREST_IDEAS = {
    "Food": [
        "try a popular local cafe, market, food hall, or street-food area",
        "book one memorable local meal and compare it with a casual neighborhood eatery",
        "join a food walk or build your own tasting route around snacks, dessert, and drinks",
    ],
    "Culture": [
        "visit a major temple, heritage district, or old town area",
        "add a museum, cultural performance, or guided historical walk",
        "walk through a historic neighborhood and learn local etiquette as you go",
    ],
    "Nature": [
        "start early at a park, garden, riverside path, viewpoint, or nearby nature escape",
        "choose one outdoor activity with shade and rest breaks during the hottest hours",
        "take a slower scenic route so the day is not only city stops and transport",
    ],
    "Shopping": [
        "compare a modern mall, local market, and small independent shops",
        "save souvenir shopping for the late afternoon when indoor areas feel useful",
        "set a shopping budget before visiting markets so bargaining stays fun",
    ],
    "Adventure": [
        "add one active experience such as cycling, kayaking, hiking, or a day tour",
        "book the adventure activity ahead and keep the evening flexible for recovery",
        "check safety rules, weather, and pickup times before committing to the activity",
    ],
    "Relaxation": [
        "leave a slower morning for a spa, cafe, pool, scenic walk, or quiet neighborhood",
        "avoid stacking too many attractions and keep one unplanned hour after lunch",
        "choose a sunset spot or calm dinner instead of rushing to another landmark",
    ],
    "Museums": [
        "visit one major museum and pair it with a smaller gallery or specialty collection",
        "check opening hours first because museums often close one day each week",
        "use the museum visit as a midday indoor break from heat or rain",
    ],
    "Nightlife": [
        "plan dinner near an evening district so the night does not require extra travel",
        "pick one night market, rooftop, live music venue, or late cafe as the main stop",
        "keep transport home simple by checking last train times or ride-hailing options",
    ],
    "Family-friendly": [
        "choose attractions with short travel times, restrooms, and easy food nearby",
        "keep the afternoon flexible for breaks, snacks, and weather changes",
        "mix one educational stop with one playful activity so the day stays balanced",
    ],
}

DAY_THEMES = [
    "Arrival, orientation, and easy highlights",
    "Landmarks and local culture",
    "Markets, food, and neighborhoods",
    "Nature, views, and slower exploration",
    "Shopping, cafes, and hidden corners",
    "Day trip or deeper local experience",
    "Favorites, souvenirs, and relaxed finish",
]

INTEREST_PLACE_HINTS = {
    "Food": "markets food streets restaurants",
    "Culture": "temples historic districts cultural landmarks",
    "Nature": "parks gardens viewpoints nature",
    "Shopping": "markets shopping streets malls",
    "Adventure": "tours hikes outdoor activities",
    "Relaxation": "parks spas waterfront scenic walks",
    "Museums": "museums galleries",
    "Nightlife": "nightlife districts night markets bars",
    "Family-friendly": "family attractions parks museums",
}

PLACE_KEYWORDS = {
    "aquarium",
    "archaeological",
    "avenue",
    "bazaar",
    "beach",
    "bridge",
    "castle",
    "cathedral",
    "church",
    "citadel",
    "crossing",
    "district",
    "fort",
    "fortress",
    "gallery",
    "garden",
    "heritage",
    "historic",
    "island",
    "lake",
    "landmark",
    "market",
    "monument",
    "mosque",
    "mountain",
    "museum",
    "national park",
    "neighborhood",
    "palace",
    "park",
    "plaza",
    "river",
    "road",
    "shrine",
    "square",
    "street",
    "temple",
    "theater",
    "theatre",
    "tower",
    "tourist attraction",
    "waterfall",
    "wat",
    "zoo",
}

NON_PLACE_KEYWORDS = {
    "championship",
    "crime",
    "demographics",
    "election",
    "festival",
    "football",
    "marathon",
    "politics",
    "population",
    "prostitution",
    "sport",
}

app = FastAPI(title="AI Travel Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TravelRequest(BaseModel):
    destination: str = Field(..., min_length=2, max_length=80)
    days: int = Field(..., ge=1, le=21)
    budget: str = Field(..., min_length=3, max_length=20)
    interests: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=400)


class RecommendedPlace(BaseModel):
    name: str
    description: str = ""
    maps_url: str


class DayPlan(BaseModel):
    day: int
    theme: str
    morning: str
    afternoon: str
    evening: str
    food: str
    transport: str


class TravelResponse(BaseModel):
    itinerary: str
    model: str
    recommended_places: list[RecommendedPlace] = Field(default_factory=list)
    day_plans: list[DayPlan] = Field(default_factory=list)


@lru_cache(maxsize=1)
def get_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return tokenizer, model


def clean_place_title(title: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", title).strip()


def destination_parts(destination: str) -> list[str]:
    return [part.strip().lower() for part in destination.split(",") if part.strip()]


def destination_aliases(destination: str) -> set[str]:
    aliases = {destination.lower().strip()}
    aliases.update(destination_parts(destination))
    return aliases


def looks_like_place_title(title: str, destination: str) -> bool:
    lowered = title.lower()
    parts = destination_parts(destination)
    blocked = [
        "list of",
        "lists of",
        "category:",
        "template:",
        "portal:",
        "tourism in",
        "outline of",
        "index of",
        "history of",
        "geography of",
        "transport in",
        "demographics of",
        "economy of",
        "politics of",
    ]
    generic_titles = {
        "tourist attraction",
        "tourism",
        "travel",
        "landmark",
        "museum",
        "park",
        "market",
        "temple",
    }
    if any(lowered.startswith(item) for item in blocked):
        return False
    if lowered in generic_titles or lowered in destination_aliases(destination):
        return False
    if "," in lowered and len(parts) > 1:
        before_comma, after_comma = [part.strip() for part in lowered.split(",", 1)]
        if before_comma == parts[0] and not any(part in after_comma for part in parts[1:]):
            return False
    if len(title) < 3 or len(title) > 60:
        return False
    return True


def clean_wikipedia_snippet(snippet: str) -> str:
    text = re.sub(r"<[^>]+>", "", snippet)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_wikipedia_description(
    text: str, place_name: str = "", destination: str = ""
) -> str:
    text = clean_wikipedia_snippet(text)
    text = re.sub(
        r"\([^)]*(arabic|thai|rtgs|romanized|pronounced|tamil|lit\.|literally)[^)]*\)",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\([^)]{0,140}\)", "", text)
    text = re.sub(r"\s*\[[^\]]+\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return summarize_description(text)


def summarize_description(text: str, max_chars: int = 260) -> str:
    if not text:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary = ""
    for sentence in sentences:
        sentence = sentence.strip(" ,;:-")
        if not sentence:
            continue

        candidate = f"{summary} {sentence}".strip() if summary else sentence
        if len(candidate) <= max_chars:
            summary = candidate
            if len(summary) >= 85:
                break
        elif not summary:
            shortened = re.sub(
                r"\s+(from|until|since|before|after|during)\s+.+$",
                "",
                sentence,
                flags=re.IGNORECASE,
            ).strip(" ,;:-")
            if 45 <= len(shortened) <= max_chars:
                summary = shortened
            else:
                clause = re.split(r",\s+|;\s+|:\s+", sentence)[0].strip(" ,;:-")
                if len(clause) >= 45:
                    summary = clause
                else:
                    words = sentence.split()
                    short_words = []
                    for word in words:
                        if len(" ".join(short_words + [word])) > max_chars:
                            break
                        short_words.append(word)
                    summary = " ".join(short_words).strip(" ,;:-")
            break

    if not summary:
        return ""

    summary = re.sub(
        r"\s+(a|an|and|as|for|from|in|is|of|or|the|to|until|with)$",
        "",
        summary,
        flags=re.IGNORECASE,
    ).strip(" ,;:-")

    if summary[-1] not in ".!?":
        summary += "."
    return summary


def make_place(
    name: str,
    description: str = "",
    description_is_clean: bool = False,
    destination: str = "",
) -> dict[str, str]:
    cleaned_name = clean_place_title(name)
    return {
        "name": cleaned_name,
        "description": (
            description
            if description_is_clean
            else clean_wikipedia_description(description, cleaned_name, destination)
        ),
    }


def looks_like_visitable_place(place: dict[str, str]) -> bool:
    title = place["name"].lower()
    title_blocked = [
        "art and architecture",
        "architecture of",
        "culture of",
        "history of",
    ]
    if any(term in title for term in title_blocked):
        return False

    searchable = f"{place['name']} {place.get('description', '')}".lower()
    if any(term in title for term in NON_PLACE_KEYWORDS):
        return False
    return any(term in searchable for term in PLACE_KEYWORDS)


def matches_destination(place: dict[str, str], destination: str) -> bool:
    parts = destination_parts(destination)
    if len(parts) < 2:
        return True

    title = place["name"].lower()
    description = place.get("description", "").lower()
    searchable = f"{title} {description}"
    city = parts[0]
    country_terms = parts[1:]

    if "," in title:
        before_comma, after_comma = [part.strip() for part in title.split(",", 1)]
        if before_comma == city and not any(term in after_comma for term in country_terms):
            return False

    return city in searchable


def place_name(place: dict[str, str] | str) -> str:
    if isinstance(place, dict):
        return place.get("name", "")
    return place


def unique_places(places: list[dict[str, str] | str], limit: int = 10) -> list[dict[str, str]]:
    seen = set()
    cleaned_places = []
    for place in places:
        cleaned = clean_place_title(place_name(place))
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            description = ""
            if isinstance(place, dict):
                description = place.get("description", "")
            cleaned_places.append(
                make_place(cleaned, description, description_is_clean=True)
            )
        if len(cleaned_places) >= limit:
            break
    return cleaned_places


def wikipedia_search_queries(data: TravelRequest) -> list[str]:
    destination = data.destination.strip()
    interest_terms = [
        INTEREST_PLACE_HINTS.get(interest, interest) for interest in data.interests
    ]
    base_queries = [
        f"palaces in {destination}",
        f"famous places in {destination}",
        f"landmarks in {destination}",
        f"temples in {destination}",
        f"shrines in {destination}",
        f"museums in {destination}",
        f"markets in {destination}",
        f"parks in {destination}",
        f"towers in {destination}",
        f"squares in {destination}",
        f"historic sites in {destination}",
        f"neighborhoods in {destination}",
        f"tourist attractions in {destination}",
    ]
    interest_queries = [
        f"{term} in {destination}" for term in interest_terms if term.strip()
    ]
    return base_queries + interest_queries


def fetch_wikipedia_extracts(page_ids: list[int]) -> dict[int, str]:
    if not page_ids:
        return {}

    params = {
        "action": "query",
        "format": "json",
        "pageids": "|".join(str(page_id) for page_id in page_ids),
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "exsentences": 2,
        "utf8": 1,
    }

    response = requests.get(
        WIKIPEDIA_API_URL,
        params=params,
        headers=WIKIPEDIA_HEADERS,
        timeout=8,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    return {
        int(page_id): page.get("extract", "")
        for page_id, page in pages.items()
        if page.get("extract")
    }


def fetch_wikipedia_search(query: str, destination: str, limit: int = 8) -> list[dict[str, str]]:
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "utf8": 1,
    }

    response = requests.get(
        WIKIPEDIA_API_URL,
        params=params,
        headers=WIKIPEDIA_HEADERS,
        timeout=8,
    )
    response.raise_for_status()
    results = response.json().get("query", {}).get("search", [])
    page_ids = [item["pageid"] for item in results if "pageid" in item]
    extracts = fetch_wikipedia_extracts(page_ids)

    places = []
    for item in results:
        if not looks_like_place_title(item.get("title", ""), destination):
            continue

        title = item.get("title", "")
        clean_title = clean_place_title(title)
        extract = clean_wikipedia_description(
            extracts.get(item.get("pageid"), ""), clean_title, destination
        )
        snippet = clean_wikipedia_description(
            item.get("snippet", ""), clean_title, destination
        )
        description = extract or snippet
        places.append(make_place(title, description, description_is_clean=True))

    return [
        place
        for place in places
        if looks_like_visitable_place(place) and matches_destination(place, destination)
    ]


def fetch_wikipedia_places(data: TravelRequest) -> list[dict[str, str]]:
    places = []
    for query in wikipedia_search_queries(data):
        try:
            places.extend(fetch_wikipedia_search(query, data.destination, limit=5))
        except requests.RequestException:
            continue
    return unique_places(places, limit=8)


def recommend_places(data: TravelRequest) -> list[dict[str, str]]:
    try:
        return fetch_wikipedia_places(data)
    except requests.RequestException:
        return []


def build_prompt(data: TravelRequest, places: list[dict[str, str]]) -> str:
    interests = ", ".join(data.interests) if data.interests else "general sightseeing"
    notes = f" Additional traveler notes: {data.notes}" if data.notes.strip() else ""
    place_context = (
        "Recommended named places to include when they fit: \n"
        + "\n".join(
            f"- {place['name']}: {place['description']}" if place["description"] else f"- {place['name']}"
            for place in places
        )
        + "\n"
        if places
        else (
            "Recommend real, specific named landmarks, neighborhoods, markets, "
            "museums, parks, viewpoints, or local districts for this destination.\n"
        )
    )

    return (
        "Create a detailed, non-repetitive travel itinerary.\n"
        f"Destination: {data.destination}\n"
        f"Trip length: {data.days} days\n"
        f"Budget: {data.budget}\n"
        f"Traveler interests: {interests}\n"
        f"{notes}\n"
        f"{place_context}"
        "Mention specific local attractions by name, not only generic activity types. "
        "Include a short 'Recommended places' section before the day-by-day plan. "
        "For each day include morning, afternoon, evening, food, and transport notes. "
        "Avoid repeating the same sentence. Use practical bullet points."
    )


def is_useful_model_output(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    repeated_lines = Counter(lines).most_common(1)
    has_repetition = bool(repeated_lines and repeated_lines[0][1] > 1)
    has_day_plan = "Day 1" in text and ("Morning" in text or "Afternoon" in text)
    has_support_sections = "Food" in text and ("Budget" in text or "Transport" in text)
    looks_like_prompt = "Include a day-by-day plan" in text or "Traveler notes:" in text

    return (
        len(text) > 350
        and has_day_plan
        and has_support_sections
        and not has_repetition
        and not looks_like_prompt
    )


def rotate(items: list[str], index: int) -> str:
    return items[index % len(items)]


def day_theme(day: int) -> str:
    if day <= len(DAY_THEMES):
        return DAY_THEMES[day - 1]
    return f"Custom interest day {day}"


def activity_for_interest(interest: str, day: int) -> str:
    ideas = INTEREST_IDEAS.get(
        interest,
        [
            "choose one well-reviewed local highlight",
            "explore a nearby neighborhood at a comfortable pace",
            "add one flexible stop based on weather and energy",
        ],
    )
    return rotate(ideas, day - 1)


def choose_interest(interests: list[str], day: int, slot: str) -> str:
    if slot == "evening" and "Nightlife" in interests:
        return "Nightlife"

    daytime = [interest for interest in interests if interest != "Nightlife"]
    usable = daytime or interests
    offset = 0 if slot == "morning" else 1
    return usable[(day - 1 + offset) % len(usable)]


def recommended_place(places: list[dict[str, str]], index: int, destination: str) -> str:
    if places:
        return places[index % len(places)]["name"]
    return f"a well-reviewed local highlight in {destination}"


def place_summary(place: dict[str, str], data: TravelRequest, index: int) -> str:
    name = place["name"]
    description = place.get("description") or (
        f"A worthwhile stop in {data.destination}; check its location, opening hours, "
        "and nearby food options before adding it to the route."
    )
    return f"- **{name}:** {description}"


def google_maps_url(query: str) -> str:
    return f"https://www.google.com/maps/search/{requests.utils.quote(query)}"


def structured_places(
    places: list[dict[str, str]], data: TravelRequest
) -> list[RecommendedPlace]:
    return [
        RecommendedPlace(
            name=place["name"],
            description=place.get("description", ""),
            maps_url=google_maps_url(f"{place['name']} {data.destination}"),
        )
        for place in places
    ]


def build_day_plans(data: TravelRequest, places: list[dict[str, str]]) -> list[DayPlan]:
    interests = data.interests or ["Culture", "Food", "Relaxation"]
    destination = data.destination
    budget = data.budget.lower()
    day_plans = []

    for day in range(1, data.days + 1):
        morning_interest = choose_interest(interests, day, "morning")
        afternoon_interest = choose_interest(interests, day, "afternoon")
        evening_interest = choose_interest(interests, day, "evening")
        morning_place = recommended_place(places, (day - 1) * 3, destination)
        afternoon_place = recommended_place(places, (day - 1) * 3 + 1, destination)
        evening_place = recommended_place(places, (day - 1) * 3 + 2, destination)

        day_plans.append(
            DayPlan(
                day=day,
                theme=day_theme(day),
                morning=(
                    f"Start at {morning_place}. For {morning_interest.lower()}, "
                    f"{activity_for_interest(morning_interest, day)}."
                ),
                afternoon=(
                    f"Continue around {afternoon_place}. For {afternoon_interest.lower()}, "
                    f"{activity_for_interest(afternoon_interest, day + 1)}. Include a rest "
                    "break or indoor stop if the weather is hot or rainy."
                ),
                evening=(
                    f"End near {evening_place}. For {evening_interest.lower()}, "
                    f"{activity_for_interest(evening_interest, day + 2)} in an area that is "
                    "convenient for dinner and the trip back."
                ),
                food=(
                    f"Try one local specialty near {morning_place} or {evening_place}, one "
                    f"casual snack, and one place that matches your {budget} budget."
                ),
                transport="Group nearby places together and check travel time before adding extra stops.",
            )
        )

    return day_plans


def build_rich_itinerary(data: TravelRequest, places: list[dict[str, str]]) -> str:
    interests = data.interests or ["Culture", "Food", "Relaxation"]
    destination = data.destination
    budget = data.budget.lower()
    day_plans = build_day_plans(data, places)
    lines = [
        f"## {data.days}-Day Travel Plan for {destination}",
        "",
        f"**Trip style:** {', '.join(interests)}",
        f"**Budget level:** {data.budget}",
    ]

    if data.notes.strip():
        lines.append(f"**Traveler notes:** {data.notes.strip()}")

    lines.extend(["", f"## Recommended Places in {destination}"])
    if places:
        lines.extend(place_summary(place, data, index) for index, place in enumerate(places))
    else:
        lines.extend(
            [
                "- Ask the AI to choose real named landmarks, neighborhoods, markets, museums, parks, and viewpoints for this destination.",
                "- Confirm current opening hours and booking rules before the trip.",
            ]
        )

    for plan in day_plans:
        lines.extend(
            [
                "",
                f"### Day {plan.day}: {plan.theme}",
                f"- **Morning:** {plan.morning}",
                f"- **Afternoon:** {plan.afternoon}",
                f"- **Evening:** {plan.evening}",
                f"- **Food idea:** {plan.food}",
                f"- **Transport note:** {plan.transport}",
            ]
        )

    lines.extend(
        [
            "",
            "## Food Ideas",
            f"- Look for busy local restaurants, markets, food courts, and cafes in {destination}.",
            "- Mix famous dishes with simple neighborhood meals so the plan feels local and affordable.",
            "- Keep one flexible meal each day for discoveries near your route.",
            "",
            "## Local Research Checklist",
            f"- Search for the top current attractions, neighborhoods, and day trips in {destination} before finalizing bookings.",
            "- Confirm whether major sights need reservations, timed entry, dress codes, or closed-day planning.",
            "- Check local transport apps, airport transfer options, common scams, and emergency numbers.",
            "",
            "## Budget Tips",
            f"- For a {budget} budget, plan paid attractions first, then fill gaps with free walks, markets, parks, and viewpoints.",
            "- Compare public transport passes, ride-hailing, and walking routes before each day starts.",
            "- Book high-demand activities early, but avoid pre-booking every meal so the trip stays flexible.",
            "",
            "## Travel Reminders",
            "- Check opening hours, local holidays, weather, and dress codes before leaving each morning.",
            "- Save hotel address, offline maps, and important booking screenshots.",
            "- Keep the final evening lighter so packing, souvenirs, and transport to the airport or station are easy.",
        ]
    )

    return "\n".join(lines)


def append_recommendations(text: str, data: TravelRequest, places: list[dict[str, str]]) -> str:
    if not places or "Recommended Places" in text or "Recommended places" in text:
        return text

    recommendations = [
        "",
        f"## Recommended Places in {data.destination}",
        *[place_summary(place, data, index) for index, place in enumerate(places)],
    ]
    return f"{text}\n{chr(10).join(recommendations)}"


def improve_format(raw_text: str, data: TravelRequest, places: list[dict[str, str]]) -> str:
    text = raw_text.strip()
    if is_useful_model_output(text):
        return append_recommendations(text, data, places)

    return build_rich_itinerary(data, places)


@app.get("/")
def read_root():
    return {"message": "AI Travel Planner API is running"}


@app.post("/plan", response_model=TravelResponse)
def create_plan(data: TravelRequest):
    try:
        places = recommend_places(data)
        prompt = build_prompt(data, places)
        tokenizer, model = get_model()
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
        outputs = model.generate(
            **inputs,
            max_new_tokens=500,
            do_sample=True,
            temperature=0.8,
            top_p=0.95,
        )
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return TravelResponse(
            itinerary=improve_format(generated_text, data, places),
            model=MODEL_NAME,
            recommended_places=structured_places(places, data),
            day_plans=build_day_plans(data, places),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not generate travel plan: {exc}",
        ) from exc
