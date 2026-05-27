import re

class ContentModerationService:
    """Egyszerű prompt moderációs szolgáltatás.

    Ez egy helyettesítő megoldás, amely alapvető tiltó listát használ
    az ismert kockázatos tartalmak kiszűréséhez.
    """

    BANNED_PATTERNS = [
        r"\bkill\b",
        r"\bbomb\b",
        r"\bhate\b",
        r"\battack\b",
        r"<script>",
        r"rm\s+-rf",
        r"sudo",
    ]

    async def is_prompt_safe(self, prompt: str) -> bool:
        if not prompt or not prompt.strip():
            return False

        normalized = prompt.lower()
        for pattern in self.BANNED_PATTERNS:
            if re.search(pattern, normalized):
                return False
        return True
