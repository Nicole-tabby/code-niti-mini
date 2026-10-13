"""Download a bounded set of supported text files from a public GitHub repo."""

import io
import re
import zipfile

import requests

SUPPORTED = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".c", ".h",
    ".cpp", ".cs", ".php", ".rb", ".swift", ".kt", ".html", ".css", ".sql",
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".xml", ".sh", ".bat",
    ".ps1", ".dockerfile", ".env.example",
}
MAX_FILES = 500
MAX_FILE_BYTES = 200_000
MAX_ARCHIVE_BYTES = 30_000_000
SKIP_PARTS = {".git", "node_modules", "vendor", "dist", "build", ".venv", "venv"}


def parse_repo_url(url: str) -> tuple[str, str]:
    match = re.fullmatch(r"https?://(?:www\.)?github\.com/([\w.-]+)/([\w.-]+)/?", url.strip())
    if not match:
        raise ValueError("Enter a repository URL like https://github.com/owner/repo.")
    return match.group(1), match.group(2).removesuffix(".git")


def load_repository(url: str) -> tuple[list[dict], str]:
    owner, repo = parse_repo_url(url)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Code-Niti-Mini"}
    response = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers, timeout=20)
    if response.status_code == 404:
        raise ValueError("Repository not found or it is private. Code-Niti Mini supports public repositories only.")
    response.raise_for_status()
    info = response.json()
    branch = info["default_branch"]
    archive = requests.get(info["archive_url"].replace("{archive_format}", "zipball").replace("{/ref}", f"/{branch}"), headers=headers, timeout=60)
    archive.raise_for_status()
    if len(archive.content) > MAX_ARCHIVE_BYTES:
        raise ValueError("Repository archive is larger than the 30 MB demo limit.")

    documents = []
    with zipfile.ZipFile(io.BytesIO(archive.content)) as bundle:
        for item in bundle.infolist():
            parts = item.filename.split("/")
            if len(parts) < 2 or any(part in SKIP_PARTS for part in parts):
                continue
            name = parts[-1]
            suffix = ".env.example" if name == ".env.example" else (".dockerfile" if name.lower() == "dockerfile" else "." + name.rsplit(".", 1)[-1].lower() if "." in name else "")
            if suffix not in SUPPORTED or item.file_size > MAX_FILE_BYTES or item.is_dir():
                continue
            try:
                text = bundle.read(item).decode("utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            path = "/".join(parts[1:])
            if text.strip():
                documents.append({"path": path, "text": text})
            if len(documents) >= MAX_FILES:
                break
    return documents, info.get("pushed_at", "unknown")
