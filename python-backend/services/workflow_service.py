from __future__ import annotations

import json
import re
from typing import Any


def _parse_result(result: Any) -> Any:
    if not isinstance(result, str):
        return result
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return result


def tool_result_status(result: Any) -> str:
    parsed = _parse_result(result)
    if not isinstance(parsed, dict):
        return "done"
    status = str(parsed.get("status", "")).lower()
    if parsed.get("cancelled") or parsed.get("skipped") or status in {"cancelled", "canceled"}:
        return "cancelled"
    if (
        parsed.get("error")
        or parsed.get("success") is False
        or status in {"error", "failed", "timeout"}
    ):
        return "error"
    return "done"


def summarize_tool_result(result: Any, limit: int = 240) -> str:
    parsed = _parse_result(result)
    if isinstance(parsed, str):
        text = parsed
    elif isinstance(parsed, dict):
        text = (
            parsed.get("error")
            or parsed.get("reason")
            or parsed.get("summary")
            or parsed.get("message")
            or parsed.get("text")
            or parsed.get("content")
            or parsed.get("filename")
            or parsed.get("url")
            or ""
        )
        if not text and isinstance(parsed.get("results"), list):
            results = parsed["results"]
            titles = []
            for item in results[:2]:
                if isinstance(item, dict):
                    titles.append(str(item.get("title") or item.get("name") or item.get("url") or ""))
                elif item:
                    titles.append(str(item))
            detail = "；".join(title for title in titles if title)
            text = f"返回 {len(results)} 条结果" + (f"：{detail}" if detail else "")
        elif not text and "results" in parsed:
            text = str(parsed.get("results") or "")
    else:
        text = str(parsed or "")

    text = re.sub(r"\s+", " ", str(text)).strip()
    if not text:
        return "工具执行完成"
    return text if len(text) <= limit else f"{text[:limit].rstrip()}…"


def tool_result_workflow_meta(result: Any) -> dict[str, str]:
    return {
        "status": tool_result_status(result),
        "summary": summarize_tool_result(result),
    }
