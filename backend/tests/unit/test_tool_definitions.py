"""Tests for NEXUS agent tool definitions.

Validates that all 12 tool definitions have correct JSON schema structure,
no duplicates, and valid enum values.
"""

from __future__ import annotations

from app.agents.orchestrator import TOOL_NAMES, TOOLS


EXPECTED_TOOL_NAMES = {
    "tavily_search",
    "yutori_browse",
    "yutori_scout",
    "reka_vision",
    "neo4j_query",
    "neo4j_write",
    "google_calendar",
    "resolve_social_accounts",
    "draft_message",
    "get_user_feedback",
    "notify_user",
    "wait",
}


class TestToolCount:
    def test_exactly_12_tools(self) -> None:
        assert len(TOOLS) == 12

    def test_tool_names_set_matches(self) -> None:
        assert TOOL_NAMES == EXPECTED_TOOL_NAMES


class TestNoDuplicates:
    def test_no_duplicate_tool_names(self) -> None:
        names = [t["name"] for t in TOOLS]
        assert len(names) == len(set(names))


class TestToolStructure:
    """Every tool must have name, description, and a valid input_schema."""

    def test_every_tool_has_name(self) -> None:
        for tool in TOOLS:
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert isinstance(tool["name"], str)
            assert len(tool["name"]) > 0

    def test_every_tool_has_description(self) -> None:
        for tool in TOOLS:
            assert "description" in tool, f"{tool['name']} missing 'description'"
            assert isinstance(tool["description"], str)
            assert len(tool["description"]) > 0

    def test_every_tool_has_input_schema(self) -> None:
        for tool in TOOLS:
            assert "input_schema" in tool, f"{tool['name']} missing 'input_schema'"

    def test_input_schema_is_object_type(self) -> None:
        for tool in TOOLS:
            schema = tool["input_schema"]
            assert schema["type"] == "object", (
                f"{tool['name']} input_schema type is '{schema.get('type')}', expected 'object'"
            )

    def test_input_schema_has_properties(self) -> None:
        for tool in TOOLS:
            schema = tool["input_schema"]
            assert "properties" in schema, (
                f"{tool['name']} input_schema missing 'properties'"
            )
            assert isinstance(schema["properties"], dict)

    def test_required_field_is_list_of_strings(self) -> None:
        for tool in TOOLS:
            schema = tool["input_schema"]
            if "required" in schema:
                assert isinstance(schema["required"], list), (
                    f"{tool['name']} 'required' should be a list"
                )
                for field_name in schema["required"]:
                    assert isinstance(field_name, str)
                    assert field_name in schema["properties"], (
                        f"{tool['name']} required field '{field_name}' not in properties"
                    )


class TestEnumValues:
    """All enum values in input schemas must be valid strings."""

    def _collect_enums(self, schema: dict, path: str = "") -> list[tuple[str, list]]:
        """Recursively collect all enum definitions from a schema."""
        enums: list[tuple[str, list]] = []
        if "enum" in schema:
            enums.append((path, schema["enum"]))
        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                if isinstance(prop_schema, dict):
                    enums.extend(
                        self._collect_enums(prop_schema, f"{path}.{prop_name}")
                    )
        if "items" in schema and isinstance(schema["items"], dict):
            enums.extend(self._collect_enums(schema["items"], f"{path}[]"))
        return enums

    def test_all_enum_values_are_strings(self) -> None:
        for tool in TOOLS:
            schema = tool["input_schema"]
            enums = self._collect_enums(schema, tool["name"])
            for path, values in enums:
                for val in values:
                    assert isinstance(val, str), (
                        f"Non-string enum value {val!r} at {path}"
                    )

    def test_enum_values_are_non_empty(self) -> None:
        for tool in TOOLS:
            schema = tool["input_schema"]
            enums = self._collect_enums(schema, tool["name"])
            for path, values in enums:
                assert len(values) > 0, f"Empty enum at {path}"


class TestSpecificTools:
    """Spot-check specific tool definitions for expected fields."""

    def _get_tool(self, name: str) -> dict:
        for t in TOOLS:
            if t["name"] == name:
                return t
        raise AssertionError(f"Tool '{name}' not found")

    def test_tavily_search_required_fields(self) -> None:
        tool = self._get_tool("tavily_search")
        assert tool["input_schema"]["required"] == ["query"]

    def test_yutori_browse_required_fields(self) -> None:
        tool = self._get_tool("yutori_browse")
        assert set(tool["input_schema"]["required"]) == {"task", "start_url"}

    def test_google_calendar_action_enum(self) -> None:
        tool = self._get_tool("google_calendar")
        action_prop = tool["input_schema"]["properties"]["action"]
        assert set(action_prop["enum"]) == {"check_busy", "create_event", "list_upcoming"}

    def test_draft_message_channel_enum(self) -> None:
        tool = self._get_tool("draft_message")
        channel_prop = tool["input_schema"]["properties"]["channel"]
        assert set(channel_prop["enum"]) == {
            "twitter_dm", "linkedin", "email", "instagram_dm"
        }

    def test_notify_user_type_enum(self) -> None:
        tool = self._get_tool("notify_user")
        type_prop = tool["input_schema"]["properties"]["type"]
        assert set(type_prop["enum"]) == {
            "event_suggested",
            "event_applied",
            "message_drafted",
            "person_found",
            "status_update",
        }

    def test_wait_requires_hours(self) -> None:
        tool = self._get_tool("wait")
        assert tool["input_schema"]["required"] == ["hours"]

    def test_get_user_feedback_no_required_fields(self) -> None:
        tool = self._get_tool("get_user_feedback")
        assert "required" not in tool["input_schema"] or tool["input_schema"].get("required") == []
