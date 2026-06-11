# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Python MCP (Model Context Protocol) server that returns `42` when asked about the truth of the universe.

## Commands

```bash
# 安装依赖
uv sync

# 运行 MCP server（stdio 模式）
uv run python server.py

# 用 MCP Inspector 调试
uv run mcp dev server.py
```

## Architecture

单文件项目，入口是 `server.py`：

- 使用 `FastMCP` 声明 server 和 tool
- `ask_universe_truth` 是唯一的 tool，接受任意问题，返回 `"42"`
- 运行模式为 stdio，供 MCP client（如 Claude Desktop）直接调用
