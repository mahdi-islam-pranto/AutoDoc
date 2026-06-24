
from langchain_core.messages import ToolMessage
import json


def _extract_confirmed_doctor_from_messages(messages: list) -> dict | None:
    """
    Walk through agent messages in reverse and find the last
    ToolMessage that came from doctor_confirmation_tool.
    Returns the parsed doctor dict or None if not found.
    """
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name == "doctor_confirmation_tool":
            try:
                # ToolMessage content is a string — parse it back to dict
                content = msg.content
                if isinstance(content, str):
                    doctor_info = json.loads(content.replace("'", '"'))
                elif isinstance(content, dict):
                    doctor_info = content
                else:
                    continue

                # Only return if we actually got meaningful data
                if doctor_info.get("doctor_id") and doctor_info.get("doctor_name"):
                    return doctor_info

            except (json.JSONDecodeError, ValueError):
                continue
    return None
