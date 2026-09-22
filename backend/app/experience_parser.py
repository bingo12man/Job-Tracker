import html
import re
from typing import Optional, Tuple

def clean_job_text(
    text: str,
) -> str:

    if not text:
        return ""

    # Convert things like:
    # &lt;li&gt;
    # &amp;
    # &#39;
    text = html.unescape(
        text
    )

    # Remove HTML tags
    text = re.sub(
        r"<[^>]+>",
        "\n",
        text,
    )

    # Normalize non-breaking spaces
    text = text.replace(
        "\xa0",
        " "
    )

    # Reduce repeated whitespace
    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    # Reduce excessive blank lines
    text = re.sub(
        r"\n+",
        "\n",
        text,
    )

    return text.strip()

def _to_float(value: str) -> float:
    return float(value.strip())


def _find_range(text: str):
    """
    Examples:

    0-1 years
    1 to 3 years
    7-10 plus years
    10–15 years
    """

    match = re.search(
        r"(\d+(?:\.\d+)?)"
        r"\s*(?:-|–|—|to)\s*"
        r"(\d+(?:\.\d+)?)"
        r"\s*(?:\+|plus)?\s*"
        r"(?:years?|yrs?)",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    return (
        _to_float(
            match.group(1)
        ),
        _to_float(
            match.group(2)
        ),
    )


def _find_plus(text: str):
    """
    Examples:
    1+ years
    2+ yrs
    """
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    return (
        _to_float(match.group(1)),
        None,
    )


def _find_minimum(text: str):
    """
    Examples:
    minimum 2 years
    minimum of 2 years
    at least 3 years
    """
    match = re.search(
        r"(?:minimum|min\.?|at least)\s*(?:of\s*)?"
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    return (
        _to_float(match.group(1)),
        None,
    )


def _find_maximum(text: str):
    """
    Examples:
    up to 2 years
    maximum 3 years
    max 1 year
    """
    match = re.search(
        r"(?:up to|maximum|max\.?)\s*(?:of\s*)?"
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    return (
        None,
        _to_float(match.group(1)),
    )


def _find_single(text: str):
    """
    Examples:
    1 year of experience
    2 years experience
    3 years relevant experience
    """
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)"
        r"(?:\s+of)?\s+(?:relevant\s+)?experience",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    value = _to_float(
        match.group(1)
    )

    return (
        value,
        value,
    )


def _find_fresher(text: str):
    fresher_patterns = [
        r"\bfresher\b",
        r"\bfreshers\b",
        r"\bentry[\s-]?level\b",
        r"\bnew college grad\b",
        r"\bnew grad\b",
        r"\bgraduate role\b",
        r"\bgraduate engineer\b",
        r"\bapprentice\b",
        r"\bno experience required\b",
        r"\bno prior experience required\b",
        r"\bzero years? experience\b",
        r"\b0 years? experience\b",
    ]

    for pattern in fresher_patterns:
        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):
            return (
                0.0,
                1.0,
            )

    return None


def _parse_block(text: str):
    """
    Parse one text block in priority order.
    """

    if not text:
        return None

    # Fresher/new-grad first
    result = _find_fresher(text)

    if result:
        return result

    # Exact ranges are strongest
    result = _find_range(text)

    if result:
        return result

    # Then explicit minimums
    result = _find_plus(text)

    if result:
        return result

    result = _find_minimum(text)

    if result:
        return result

    result = _find_maximum(text)

    if result:
        return result

    result = _find_single(text)

    if result:
        return result

    return None


def parse_experience(
    text: str,
    title: str = "",
) -> Tuple[
    Optional[float],
    Optional[float],
    bool,
]:
    """
    Returns:
        min_experience
        max_experience
        experience_not_specified

    Priority:
    1. title
    2. requirement/qualification lines
    3. full description
    """

    title = clean_job_text(
        title or ""
    )

    text = clean_job_text(
        text or ""
    )

    # ----------------------------
    # 1. TITLE FIRST
    # ----------------------------
    title_result = _parse_block(
        title
    )

    if title_result:
        return (
            title_result[0],
            title_result[1],
            False,
        )

    # ----------------------------
    # 2. IMPORTANT LINES
    # ----------------------------
    important_lines = []

    for line in text.splitlines():
        normalized = line.lower()

        keywords = [
            "experience",
            "required",
            "requirement",
            "minimum",
            "qualification",
            "qualifications",
            "years",
            "yrs",
            "fresher",
            "entry level",
            "new grad",
            "graduate",
            "apprentice",
        ]

        if any(
            keyword in normalized
            for keyword in keywords
        ):
            important_lines.append(
                line
            )

    important_text = "\n".join(
        important_lines
    )

    important_result = _parse_block(
        important_text
    )

    if important_result:
        return (
            important_result[0],
            important_result[1],
            False,
        )

    # ----------------------------
    # 3. FULL DESCRIPTION
    # ----------------------------
    full_result = _parse_block(
        text
    )

    if full_result:
        return (
            full_result[0],
            full_result[1],
            False,
        )

    return None, None, True