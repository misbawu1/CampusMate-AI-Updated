"""Small reusable functions used by CampusMate."""

import json
import re
from pathlib import Path


def load_knowledge():
    """Read the campus information stored beside this file."""
    file_path = Path(__file__).with_name("knowledge.json")
    with file_path.open(encoding="utf-8") as file:
        return json.load(file)


def find_resource(resources, topic):
    """Return resources whose name, description, or keywords mention a topic."""
    search_term = topic.casefold()
    return [
        resource
        for resource in resources
        if search_term in resource["name"].casefold()
        or search_term in resource["description"].casefold()
        or any(search_term in word.casefold() for word in resource["keywords"])
    ]


def find_relevant_resources(resources, question, limit=3):
    """Find the best few resources for a natural-language question."""
    common_words = {
        "a", "an", "and", "are", "at", "can", "could", "do", "does", "for",
        "get", "help", "how", "i", "in", "is", "me", "my", "of", "on", "or",
        "please", "the", "there", "to", "we", "what", "where", "which", "who",
        "with", "would",
    }
    search_terms = {
        word for word in re.findall(r"[a-z0-9]+", question.casefold())
        if word not in common_words and len(word) > 1
    }
    if not search_terms:
        return []

    ranked_resources = []
    for index, resource in enumerate(resources):
        searchable_text = " ".join(
            [resource.get("name", ""), resource.get("description", "")]
            + resource.get("keywords", [])
        ).casefold()
        score = sum(term in searchable_text for term in search_terms)
        if score:
            ranked_resources.append((score, -index, resource))

    ranked_resources.sort(reverse=True, key=lambda item: (item[0], item[1]))
    return [resource for _, _, resource in ranked_resources[:limit]]
