from __future__ import annotations

from collections.abc import Callable

from tool.base import ToolMeta


class DuplicateToolName(Exception):
    """Raised when a tool with the same name is registered twice."""
    pass


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self, tools: list[Callable]) -> None:
        self._tools: dict[str, ToolMeta] = {}
        for tool_fn in tools:
            if not hasattr(tool_fn, "_tool_meta"):
                raise ValueError(f"Function {tool_fn.__name__} is not a @tool decorated function")
            meta = tool_fn._tool_meta
            if meta.name in self._tools:
                raise DuplicateToolName(f"Duplicate tool name: {meta.name}")
            self._tools[meta.name] = meta

    def get(self, name: str) -> ToolMeta | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def filter(self, names: list[str]) -> list[ToolMeta]:
        """Filter tools by a list of names."""
        result = []
        for name in names:
            meta = self._tools.get(name)
            if meta is None:
                raise ValueError(f"Tool not found: {name}")
            result.append(meta)
        return result

    def all(self) -> list[ToolMeta]:
        """Get all registered tools."""
        return list(self._tools.values())

    def to_json_schema(self, tools: list[ToolMeta] | None = None) -> list[dict]:
        """Convert tools to OpenAI-compatible JSON schema format."""
        if tools is None:
            tools = self.all()

        schemas = []
        for meta in tools:
            schema = {
                "type": "function",
                "function": {
                    "name": meta.name,
                    "description": meta.description,
                    "parameters": meta.args_model.model_json_schema(),
                },
            }
            schemas.append(schema)
        return schemas
