import re

class OutputSelfCorrectionService:
    @staticmethod
    async def sanitize_and_validate_output(text: str) -> str:
        """Egyszerű szövegfeldolgozás a generált kimenet tisztítására."""
        if text is None:
            return ""

        sanitized = text.strip()
        sanitized = re.sub(r"\s+", " ", sanitized)
        return sanitized
