"""Marketplace sections and categories (single source of truth for UI, search and AI)."""

SECTIONS = {
    "physical": {
        "label": "Physical Things",
        "categories": {
            "electronics": "Electronics",
            "furniture": "Furniture",
            "household": "Household Items",
            "cars": "Cars",
            "bikes": "Bikes",
            "clothing": "Clothing",
            "books": "Books",
            "sports-hobby": "Sports & Hobby",
        },
    },
    "services": {
        "label": "Skills & Services",
        "categories": {
            "tutoring": "Tutoring",
            "handyman": "Handyman Help",
            "furniture-assembly": "Furniture Assembly",
            "vehicle-repair": "Car & Bike Repair",
            "photography": "Photography",
            "design": "Design",
            "resume-interview": "Résumé & Interview Help",
            "excel-coding": "Excel & Coding Help",
            "music-lessons": "Music Lessons",
            "language-tutoring": "Language Tutoring",
        },
    },
}

CONDITIONS = ["new", "like new", "good", "fair"]
PRICE_UNITS = {"physical": ["item"], "services": ["hour", "session", "project"]}


def category_section(category: str) -> str | None:
    for section, info in SECTIONS.items():
        if category in info["categories"]:
            return section
    return None


def all_categories() -> list[str]:
    return [c for info in SECTIONS.values() for c in info["categories"]]
