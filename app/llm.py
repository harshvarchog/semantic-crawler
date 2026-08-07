import os
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "claude-3-5-haiku-20241022"
MAX_TOKENS = 150


def summarize_diff(zone_name: str, old_text: str, new_text: str) -> str:
    """
    Generate a 2-3 sentence human-readable summary of what changed
    between old_text and new_text for the given zone.
    """
    prompt = f"""You are a change detection analyst. Compare the OLD and NEW versions of a webpage section and write a concise 2-3 sentence summary of what substantively changed. Ignore formatting, whitespace, or trivial wording differences. Focus on meaningful content changes.

Section: {zone_name}

OLD:
{old_text[:3000]}

NEW:
{new_text[:3000]}

Summary (2-3 sentences):"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()