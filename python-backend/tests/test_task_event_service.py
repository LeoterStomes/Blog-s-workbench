from types import SimpleNamespace

from services.task_event_service import serialize_task_event


def test_serialize_task_event_preserves_payload_and_metadata():
    event = SimpleNamespace(
        id=42,
        event_type="tool_result",
        status="done",
        call_id="call-1",
        payload='{"tool":"search_articles","summary":"找到 2 篇文章"}',
        created_at=None,
    )

    assert serialize_task_event(event) == {
        "id": "42",
        "type": "tool_result",
        "status": "done",
        "callId": "call-1",
        "payload": {
            "tool": "search_articles",
            "summary": "找到 2 篇文章",
        },
        "createdAt": "",
    }


def test_serialize_task_event_falls_back_for_invalid_json():
    event = SimpleNamespace(
        id=7,
        event_type="thinking",
        status=None,
        call_id=None,
        payload="plain plan text",
        created_at=None,
    )

    serialized = serialize_task_event(event)
    assert serialized["payload"] == {"text": "plain plan text"}
    assert serialized["status"] == ""
    assert serialized["callId"] == ""
