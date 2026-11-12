"""Модуль получения данных о прямых зависимостях пакетов."""

import json
import re
import urllib.error
import urllib.parse
import urllib.request

HTTP_TIMEOUT = 10
SEMVER_EXTRACT = re.compile(r"(\d+\.\d+\.\d+)")
TEST_NAME_REGEX = re.compile(r"^[A-Z]+$")


class CollectorError(RuntimeError):
    """Ошибка при получении или разборе данных о зависимостях."""


def clean_semver(raw_version: str) -> str:
    """Извлекает конкретную версию из semver-диапазона npm."""
    match = SEMVER_EXTRACT.search(raw_version)
    if match:
        return match.group(1)
    return "latest"


def fetch_json(url: str) -> dict:
    """Выполняет HTTP GET запрос и возвращает распарсенный JSON."""
    req = urllib.request.Request(
        url, headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            payload = resp.read().decode("utf-8")
            return json.loads(payload)
    except urllib.error.HTTPError as exc:
        raise CollectorError(f"HTTP ошибка {exc.code} для {url}") from exc
    except urllib.error.URLError as exc:
        raise CollectorError(f"Ошибка сети для {url}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise CollectorError(f"Ошибка чтения JSON от {url}") from exc


def fetch_npm_dependencies(
    repo_url: str, package: str, version: str
) -> dict[str, str]:
    """Получает прямые зависимости пакета из реестра npm."""
    base = repo_url.rstrip("/")
    encoded_pkg = urllib.parse.quote(package, safe="@/")
    norm_ver = clean_semver(version) if version != "latest" else "latest"
    target_url = f"{base}/{encoded_pkg}/{norm_ver}"
    try:
        data = fetch_json(target_url)
    except CollectorError:
        if norm_ver == "latest":
            raise
        fallback_url = f"{base}/{encoded_pkg}/latest"
        data = fetch_json(fallback_url)
    deps = data.get("dependencies", {})
    if not isinstance(deps, dict):
        return {}
    return {str(k): str(v) for k, v in deps.items()}


def load_test_repo(file_path: str) -> dict[str, list[str]]:
    """Загружает граф тестового репозитория из JSON-файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            raw_data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CollectorError(f"Ошибка чтения файла: {file_path}") from exc
    if not isinstance(raw_data, dict):
        raise CollectorError("Тестовый репозиторий должен быть объектом.")
    validated: dict[str, list[str]] = {}
    for pkg, deps in raw_data.items():
        if not TEST_NAME_REGEX.match(str(pkg)):
            raise CollectorError(f"Недопустимое имя пакета: {pkg}")
        if not isinstance(deps, list):
            raise CollectorError(f"Зависимости {pkg} должны быть списком.")
        validated[str(pkg)] = [str(d) for d in deps]
    return validated