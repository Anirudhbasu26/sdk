# Synup MCP Server

MCP server that exposes all synup-sdk methods as tools for LLM agents (97 tools).

## Setup

```bash
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
