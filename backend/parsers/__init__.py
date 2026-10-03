from typing import Type
from backend.parsers.base import BaseParser
from backend.parsers.nessus_parser import NessusParser
from backend.parsers.qualys_parser import QualysParser
from backend.parsers.burp_parser import BurpParser
from backend.parsers.generic_parser import GenericParser

PARSER_MAP: dict[str, Type[BaseParser]] = {
    "nessus": NessusParser,
    "qualys": QualysParser,
    "burp": BurpParser,
    "generic": GenericParser,
}

def detect_and_get_parser(filename: str, sample_content: str) -> BaseParser:
    """Auto-detect scanner type from filename and content snippet"""
    filename_lower = filename.lower()
    content_lower = sample_content[:2000].lower()

    if "nessus" in filename_lower or "<nessusclientdata_v2" in content_lower or "pluginid" in content_lower:
        return NessusParser()
    elif "qualys" in filename_lower or "<qid>" in content_lower or "<glossary" in content_lower:
        return QualysParser()
    elif "burp" in filename_lower or "<issues burpversion" in content_lower or '"issues"' in content_lower:
        return BurpParser()
    elif filename_lower.endswith(".json") or content_lower.strip().startswith("{") or content_lower.strip().startswith("["):
        # Could be Burp JSON or Generic JSON
        if '"issues"' in content_lower:
            return BurpParser()
        return GenericParser()
    else:
        return GenericParser()

__all__ = ["PARSER_MAP", "BaseParser", "NessusParser", "QualysParser", "BurpParser", "GenericParser", "detect_and_get_parser"]
