import re

TARGET_EXPERIENCE = 1.5


ROLE_KEYWORDS = {
    "software_engineer": [
        "software engineer",
        "software developer",
        "software development engineer",
        "sde",
        "sde i",
        "sde 1",
        "associate software engineer",
        "junior software engineer",
        "graduate software engineer",
        "software engineer i",
        "software engineer 1",
        "application developer",
        "application engineer",
        "product engineer",
        "systems software engineer",
"system software engineer",
"applications software engineer",
"application software engineer",
"software engineer intern",
"software engineering intern",
    ],

    "backend_engineer": [
        "backend engineer",
        "back end engineer",
        "backend developer",
        "back end developer",
        "backend software engineer",
        "api developer",
        "api engineer",
        "platform engineer",
    ],

    "python_developer": [
        "python developer",
        "python engineer",
        "python software engineer",
        "python backend developer",
        "python backend engineer",
    ],

    "data_scientist": [
        "data scientist",
        "junior data scientist",
        "associate data scientist",
        "data scientist i",
        "data scientist 1",
        "applied data scientist",
        "decision scientist",
        "analytics scientist",
        "data science engineer",
        "data science analyst",
    ],

    "ml_engineer": [
        "machine learning engineer",
        "ml engineer",
        "machine learning developer",
        "machine learning software engineer",
        "ml developer",
        "ml software engineer",
        "associate machine learning engineer",
        "junior machine learning engineer",
        "applied machine learning engineer",
        "applied ml engineer",
        "ai infrastructure engineer",
"ai systems engineer",
"ai automation engineer",
    ],

    "ai_engineer": [
        "ai engineer",
        "artificial intelligence engineer",
        "ai developer",
        "ai software engineer",
        "applied ai engineer",
        "associate ai engineer",
        "junior ai engineer",
    ],

    "genai_engineer": [
        "genai engineer",
        "gen ai engineer",
        "generative ai engineer",
        "generative ai developer",
        "genai developer",
        "gen ai developer",
        "generative ai software engineer",
        "applied genai engineer",
    ],

    "llm_engineer": [
        "llm engineer",
        "large language model engineer",
        "llm developer",
        "large language model developer",
        "llm application engineer",
        "llm software engineer",
        "language model engineer",
    ],

    "rag_engineer": [
        "rag engineer",
        "rag developer",
        "retrieval augmented generation engineer",
        "retrieval-augmented generation engineer",
        "retrieval engineer",
    ],

    "nlp_engineer": [
        "nlp engineer",
        "natural language processing engineer",
        "nlp developer",
        "nlp scientist",
        "language ai engineer",
        "text analytics engineer",
    ],

    "computer_vision_engineer": [
        "computer vision engineer",
        "computer vision developer",
        "computer vision scientist",
        "cv engineer",
        "vision engineer",
        "vision ai engineer",
        "image processing engineer",
    ],

    "deep_learning_engineer": [
        "deep learning engineer",
        "deep learning developer",
        "deep learning scientist",
    ],

    "mlops_engineer": [
        "mlops engineer",
        "ml ops engineer",
        "machine learning operations engineer",
        "ml platform engineer",
        "machine learning platform engineer",
        "ai platform engineer",
        "model deployment engineer",
    ],

    "frontend_engineer": [
    "frontend engineer",
    "front end engineer",
    "frontend developer",
    "front end developer",
    "frontend software engineer",
    "ui engineer",
    "web engineer",
    "frontend apprentice",
],

"site_reliability_engineer": [
    "site reliability engineer",
    "sre",
    "reliability engineer",
    "production engineer",
],

"forward_deployed_engineer": [
    "forward deployed engineer",
    "forward deployment engineer",
    "fde",
],

"compiler_engineer": [
    "compiler engineer",
    "compiler developer",
    "compiler software engineer",
],

"ai_infrastructure_engineer": [
    "ai infrastructure engineer",
    "ml infrastructure engineer",
    "machine learning infrastructure engineer",
    "ai systems engineer",
    "ml systems engineer",
    "machine learning systems engineer",
],

"data_platform_engineer": [
    "data platform engineer",
    "data infrastructure engineer",
    "data application engineer",
    "data and platform engineer",
],

"graduate_engineer": [
    "graduate engineer",
    "new college grad",
    "new grad",
    "college graduate",
    "graduate software engineer",
    "graduate developer",
],

"apprentice_engineer": [
    "apprentice",
    "software apprentice",
    "engineering apprentice",
    "developer apprentice",
],

"associate_engineer": [
    "associate engineer",
    "associate software engineer",
    "associate developer",
    "associate ai engineer",
    "associate ml engineer",
],

"solutions_engineer": [
    "solutions engineer",
    "solution engineer",
    "ai solutions engineer",
    "ml solutions engineer",
    "technical solutions engineer",
],

    "research_engineer": [
        "research engineer",
        "machine learning research engineer",
        "ai research engineer",
        "applied research engineer",
        "research software engineer",
    ],

    "research_scientist": [
        "research scientist",
        "machine learning research scientist",
        "ai research scientist",
        "applied scientist",
        "applied research scientist",
    ],

    "data_engineer": [
        "data engineer",
        "junior data engineer",
        "associate data engineer",
        "data engineer i",
        "data engineer 1",
        "data pipeline engineer",
        "analytics engineer",
        "data platform engineer",
    ],

    "ai_product_engineer": [
        "ai product engineer",
        "ml product engineer",
        "generative ai product engineer",
        "ai solutions engineer",
        "ml solutions engineer",
    ],

    "full_stack_engineer": [
        "full stack engineer",
        "full-stack engineer",
        "full stack developer",
        "full-stack developer",
    ],

    "cloud_engineer": [
        "cloud engineer",
        "cloud software engineer",
        "cloud application engineer",
        "cloud developer",
    ],
}


LOCATION_KEYWORDS = [
    "bangalore",
    "bengaluru",
    "chennai",
]


REMOTE_KEYWORDS = [
    "remote india",
    "india remote",
    "remote - india",
    "remote, india",
    "india - remote",
    "remote within india",
    "wfh india",
]


def normalize_text(text: str):
    return (
        text.lower()
        .strip()
        .replace("_", " ")
        .replace("/", " ")
    )


def keyword_matches_title(
    title: str,
    keyword: str,
):
    """
    Match complete role phrases instead of
    accidental substrings.

    Example:
    SDE should match:
        "SDE I"

    But should NOT match:
        "SDET"
    """

    title = normalize_text(title)
    keyword = normalize_text(keyword)

    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(keyword)
        + r"(?![a-z0-9])"
    )

    return bool(
        re.search(
            pattern,
            title,
            re.IGNORECASE,
        )
    )


def detect_role(title: str):
    if not title:
        return None

    normalized_title = normalize_text(
        title
    )

    for (
        role_category,
        keywords,
    ) in ROLE_KEYWORDS.items():

        for keyword in keywords:

            if keyword_matches_title(
                normalized_title,
                keyword,
            ):
                return role_category

    return None


def location_matches(location: str | None):
    if not location:
        return False

    location = normalize_text(location)

    for keyword in LOCATION_KEYWORDS:
        if keyword in location:
            return True

    for keyword in REMOTE_KEYWORDS:
        if keyword in location:
            return True

    return False


def experience_matches(
    min_experience: float | None,
    max_experience: float | None,
):
    # No experience mentioned
    if min_experience is None and max_experience is None:
        return True

    # Example: up to 1 year / up to 2 years
    if min_experience is None and max_experience is not None:
        return max_experience >= 1

    # Example: 0+ / 1+ / 2+
    if min_experience is not None and max_experience is None:
        return min_experience <= TARGET_EXPERIENCE

    if min_experience is not None and max_experience is not None:

        # Special rule: include 0-1
        if min_experience == 0 and max_experience >= 1:
            return True

        # Include if 1.5 falls inside the range
        if min_experience <= TARGET_EXPERIENCE <= max_experience:
            return True

    return False


def job_matches(
    title: str,
    location: str | None,
    min_experience: float | None,
    max_experience: float | None,
):
    role = detect_role(title)

    if role is None:
        return False

    if not location_matches(location):
        return False

    if not experience_matches(
        min_experience,
        max_experience,
    ):
        return False

    return True


def evaluate_job(
    title: str,
    location: str | None,
    min_experience: float | None,
    max_experience: float | None,
):
    role = detect_role(title)

    role_match = role is not None
    location_match = location_matches(location)
    experience_match = experience_matches(
        min_experience,
        max_experience,
    )

    reasons = []

    if not role_match:
        reasons.append("ROLE_NOT_MATCHED")

    if not location_match:
        reasons.append("LOCATION_NOT_MATCHED")

    if not experience_match:
        reasons.append("EXPERIENCE_NOT_MATCHED")

    return {
        "role_category": role,
        "role_match": role_match,
        "location_match": location_match,
        "experience_match": experience_match,
        "is_match": (
            role_match
            and location_match
            and experience_match
        ),
        "reasons": reasons,
    }

def evaluate_job(
    title: str,
    location: str | None,
    min_experience: float | None,
    max_experience: float | None,
):
    role = detect_role(title)

    role_match = role is not None
    location_match = location_matches(location)
    experience_match = experience_matches(
        min_experience,
        max_experience,
    )

    reasons = []

    if not role_match:
        reasons.append("ROLE_NOT_MATCHED")

    if not location_match:
        reasons.append("LOCATION_NOT_MATCHED")

    if not experience_match:
        reasons.append("EXPERIENCE_NOT_MATCHED")

    return {
        "role_category": role,
        "role_match": role_match,
        "location_match": location_match,
        "experience_match": experience_match,
        "is_match": (
            role_match
            and location_match
            and experience_match
        ),
        "reasons": reasons,
    }