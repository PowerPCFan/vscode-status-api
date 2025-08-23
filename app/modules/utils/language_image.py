import re as regexp
import json
from pathlib import Path
from typing import Any


map_file: Path = Path(__file__).parent.parent.parent.parent / "assets" / "icons" / ".map.json"


with open(file=map_file, mode="r", encoding='utf-8') as file:
    imgmap: dict[str, Any] = json.load(file)


known_languages: list[dict[str, str]] = imgmap["KNOWN_LANGUAGES"]
known_extensions: dict[str, dict[str, str]] = imgmap["KNOWN_EXTENSIONS"]


def _get_imgurl(image_name: str) -> str:
    return f"https://raw.githubusercontent.com/PowerPCFan/vscode-status-api/refs/heads/master/assets/icons/{image_name}.png"


def get(language: str, filename: str) -> str:
    #* preferred method: known languages
    for lang_obj in known_languages:
        if lang_obj["language"] == language:
            image_name: str = lang_obj["image"]
            return _get_imgurl(image_name)

    #* alternative method: file extension
    extension: str = Path(filename).suffix
    filename_lower: str = filename.lower()

    for pattern, ext_info in known_extensions.items():
        if pattern.startswith('/') and pattern.endswith('/i'):
            #? regex
            regex_pattern: str = pattern[1:-2]
            try:
                if regexp.search(regex_pattern, filename, regexp.IGNORECASE):
                    image_name: str = ext_info["image"]
                    return _get_imgurl(image_name)
            except regexp.error:
                continue
        else:
            #? exact match
            if pattern == filename_lower or pattern == extension:
                image_name: str = ext_info["image"]
                return _get_imgurl(image_name)

    #* fallback: return vscode logo
    return _get_imgurl("vscode")
