import pytest
from google.genai import types

from app.core.errors import NotFoundError
from app.modules.chat import service as chat_service_module
from app.modules.chat.service import MAX_TOOL_ROUNDS, ChatService


def _text_response(text: str) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[types.Part(text=text)]))]
    )


def _function_call_response(*calls: tuple[str, dict]) -> types.GenerateContentResponse:
    parts = [
        types.Part(function_call=types.FunctionCall(name=name, args=args)) for name, args in calls
    ]
    return types.GenerateContentResponse(candidates=[types.Candidate(content=types.Content(role="model", parts=parts))])


async def test_immediate_text_reply_makes_no_tool_call(monkeypatch):
    calls = []

    async def fake_generate(*, contents, config):
        calls.append(contents)
        return _text_response("Hello! How can I help?")

    monkeypatch.setattr(chat_service_module, "generate_with_tools", fake_generate)

    reply = await ChatService().send_message(message="hi", history=[])

    assert reply == "Hello! How can I help?"
    assert len(calls) == 1


async def test_single_tool_call_then_final_text(monkeypatch):
    responses = [
        _function_call_response(("get_labourer", {"labourer_id": "abc123"})),
        _text_response("That labourer is active."),
    ]
    dispatched = []

    async def fake_get_labourer(labourer_id: str) -> dict:
        dispatched.append(labourer_id)
        return {"id": labourer_id, "name": "Test", "status": "active"}

    async def fake_generate(*, contents, config):
        return responses.pop(0)

    monkeypatch.setattr(chat_service_module, "generate_with_tools", fake_generate)
    monkeypatch.setitem(chat_service_module.TOOL_DISPATCH, "get_labourer", fake_get_labourer)

    reply = await ChatService().send_message(message="Is Test active?", history=[])

    assert reply == "That labourer is active."
    assert dispatched == ["abc123"]


async def test_parallel_tool_calls_produce_one_combined_response_turn(monkeypatch):
    responses = [
        _function_call_response(
            ("get_labourer", {"labourer_id": "a"}), ("get_labourer", {"labourer_id": "b"})
        ),
        _text_response("Both found."),
    ]
    seen_contents_at_second_call = []

    async def fake_get_labourer(labourer_id: str) -> dict:
        return {"id": labourer_id}

    async def fake_generate(*, contents, config):
        if len(responses) == 1:
            seen_contents_at_second_call.append(list(contents))
        return responses.pop(0)

    monkeypatch.setattr(chat_service_module, "generate_with_tools", fake_generate)
    monkeypatch.setitem(chat_service_module.TOOL_DISPATCH, "get_labourer", fake_get_labourer)

    reply = await ChatService().send_message(message="Compare a and b", history=[])

    assert reply == "Both found."
    # user message + model function_call turn + one combined function_response turn
    last_contents = seen_contents_at_second_call[0]
    function_response_turns = [c for c in last_contents if c.role == "user" and c.parts and c.parts[0].function_response]
    assert len(function_response_turns) == 1
    assert len(function_response_turns[0].parts) == 2


async def test_not_found_error_from_tool_is_fed_back_gracefully(monkeypatch):
    responses = [
        _function_call_response(("get_labourer", {"labourer_id": "missing"})),
        _text_response("I couldn't find that labourer."),
    ]
    captured_results = []

    async def fake_get_labourer(labourer_id: str) -> dict:
        raise NotFoundError("Labourer not found")

    async def fake_generate(*, contents, config):
        if len(responses) == 1:
            last = contents[-1]
            captured_results.append(last.parts[0].function_response.response)
        return responses.pop(0)

    monkeypatch.setattr(chat_service_module, "generate_with_tools", fake_generate)
    monkeypatch.setitem(chat_service_module.TOOL_DISPATCH, "get_labourer", fake_get_labourer)

    reply = await ChatService().send_message(message="Find missing labourer", history=[])

    assert reply == "I couldn't find that labourer."
    assert captured_results[0] == {"error": "Labourer not found"}


async def test_unexpected_exception_from_tool_returns_generic_error(monkeypatch):
    responses = [
        _function_call_response(("get_labourer", {"labourer_id": "x"})),
        _text_response("Something went wrong."),
    ]
    captured_results = []

    async def fake_get_labourer(labourer_id: str) -> dict:
        raise ValueError("boom")

    async def fake_generate(*, contents, config):
        if len(responses) == 1:
            last = contents[-1]
            captured_results.append(last.parts[0].function_response.response)
        return responses.pop(0)

    monkeypatch.setattr(chat_service_module, "generate_with_tools", fake_generate)
    monkeypatch.setitem(chat_service_module.TOOL_DISPATCH, "get_labourer", fake_get_labourer)

    await ChatService().send_message(message="trigger a bug", history=[])

    assert captured_results[0] == {"error": chat_service_module.GENERIC_TOOL_ERROR}
    assert "boom" not in str(captured_results[0])


async def test_unknown_tool_name_is_handled_without_crashing(monkeypatch):
    responses = [
        _function_call_response(("not_a_real_tool", {})),
        _text_response("I can't do that."),
    ]

    async def fake_generate(*, contents, config):
        return responses.pop(0)

    monkeypatch.setattr(chat_service_module, "generate_with_tools", fake_generate)

    reply = await ChatService().send_message(message="do something unsupported", history=[])

    assert reply == "I can't do that."


async def test_max_tool_rounds_exhausted_returns_fallback(monkeypatch):
    async def fake_generate(*, contents, config):
        return _function_call_response(("get_labourer", {"labourer_id": "x"}))

    async def fake_get_labourer(labourer_id: str) -> dict:
        return {"id": labourer_id}

    monkeypatch.setattr(chat_service_module, "generate_with_tools", fake_generate)
    monkeypatch.setitem(chat_service_module.TOOL_DISPATCH, "get_labourer", fake_get_labourer)

    reply = await ChatService().send_message(message="loop forever", history=[])

    assert reply == chat_service_module.FALLBACK_REPLY


async def test_history_turns_are_included_in_contents(monkeypatch):
    from app.modules.chat.schemas import ChatTurn

    captured = []

    async def fake_generate(*, contents, config):
        captured.append(list(contents))
        return _text_response("ok")

    monkeypatch.setattr(chat_service_module, "generate_with_tools", fake_generate)

    history = [ChatTurn(role="user", content="earlier question"), ChatTurn(role="model", content="earlier answer")]
    await ChatService().send_message(message="follow up", history=history)

    sent = captured[0]
    assert len(sent) == 3
    assert sent[0].role == "user" and sent[0].parts[0].text == "earlier question"
    assert sent[1].role == "model" and sent[1].parts[0].text == "earlier answer"
    assert sent[2].role == "user" and sent[2].parts[0].text == "follow up"


def test_max_tool_rounds_is_bounded():
    assert 1 < MAX_TOOL_ROUNDS <= 10
