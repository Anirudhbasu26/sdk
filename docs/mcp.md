# MCP Server

The MCP (Model Context Protocol) server exposes all SDK methods as tools for LLM agents. It lives in the `mcp/` folder — separate from the published SDK package.

## Setup

```bash
cd mcp
pip install -r requirements.txt
```

## Run

```bash
SYNUP_API_KEY=your_api_key python server.py
```

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "synup": {
      "command": "python",
      "args": ["/full/path/to/mcp/server.py"],
      "env": {
        "SYNUP_API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

## How It Works

The MCP server wraps every `SynupClient` method as an LLM-callable tool:

```
LLM Agent → MCP Server → SynupClient → Synup REST API
```

- **97 tools** covering all SDK endpoints
- Uses `asyncio.to_thread()` to bridge the sync SDK with the async MCP server
- Authentication via `SYNUP_API_KEY` environment variable
