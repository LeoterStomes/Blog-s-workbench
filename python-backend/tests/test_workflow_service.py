import json

from services.workflow_service import summarize_tool_result, tool_result_workflow_meta


def test_workflow_marks_tool_error():
    meta = tool_result_workflow_meta(json.dumps({"error": "读取失败"}))
    assert meta == {"status": "error", "summary": "读取失败"}


def test_workflow_marks_cancelled_tool():
    meta = tool_result_workflow_meta({"cancelled": True, "reason": "批次超时"})
    assert meta["status"] == "cancelled"
    assert meta["summary"] == "批次超时"


def test_workflow_summarizes_search_results():
    summary = summarize_tool_result({
        "results": [
            {"title": "第一篇文章"},
            {"title": "第二篇文章"},
            {"title": "第三篇文章"},
        ]
    })
    assert summary == "返回 3 条结果：第一篇文章；第二篇文章"


def test_workflow_caps_long_tool_summary():
    summary = summarize_tool_result({"content": "很长的结果" * 100}, limit=20)
    assert len(summary) == 21
    assert summary.endswith("…")


def test_workflow_handles_structured_error_value():
    meta = tool_result_workflow_meta({"error": {"message": "服务不可用"}})
    assert meta["status"] == "error"
    assert "服务不可用" in meta["summary"]
