"""Модуль генерации диаграмм Mermaid и отображения графа."""

import base64
import re
import urllib.request
import webbrowser

MERMAID_INK_BASE = "https://mermaid.ink/img/"
SAFE_ID_PATTERN = re.compile(r"[^0-9A-Za-z_]")
HTTP_TIMEOUT = 15


def sanitize_node_id(name: str) -> str:
    """Преобразует имя пакета в безопасный идентификатор Mermaid."""
    cleaned = SAFE_ID_PATTERN.sub("_", name)
    return f"node_{cleaned}"


def generate_mermaid(graph: dict[str, list[str]]) -> str:
    """Формирует текстовое представление графа на языке Mermaid."""
    lines = ["graph TD"]
    for src, targets in sorted(graph.items()):
        src_id = sanitize_node_id(src)
        lines.append(f'    {src_id}["{src}"]')
        for dst in targets:
            dst_id = sanitize_node_id(dst)
            lines.append(f'    {src_id} --> {dst_id}["{dst}"]')
    return "\n".join(lines)


def build_mermaid_image_url(mermaid_code: str) -> str:
    """Создает URL изображения графа через сервис mermaid.ink."""
    encoded_bytes = base64.urlsafe_b64encode(mermaid_code.encode("utf-8"))
    encoded_str = encoded_bytes.decode("ascii")
    return f"{MERMAID_INK_BASE}{encoded_str}"


def display_graph_image(
    mermaid_code: str, output_file: str = "graph.png"
) -> str:
    """Скачивает изображение графа и открывает его на экране."""
    url = build_mermaid_image_url(mermaid_code)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        img_data = resp.read()
    with open(output_file, "wb") as handle:
        handle.write(img_data)
    webbrowser.open(url)
    return url