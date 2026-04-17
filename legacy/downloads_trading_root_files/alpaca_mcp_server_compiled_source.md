# Alpaca MCP Server Compiled Source Bundle

Source repo: `https://github.com/alpacahq/alpaca-mcp-server`
Compilation date: 2026-04-10

This file concatenates the repository text files that are most useful for source ingestion, preserving relative paths.
Binary assets were omitted.

## File index

- `.dockerignore` (16 bytes)
- `.gitignore` (304 bytes)
- `AGENTS.md` (4,998 bytes)
- `Dockerfile` (672 bytes)
- `LICENSE` (1,068 bytes)
- `README.md` (28,919 bytes)
- `pyproject.toml` (2,077 bytes)
- `requirements.txt` (76 bytes)
- `server.json` (1,368 bytes)
- `server.yaml` (3,523 bytes)
- `uv.lock` (298,892 bytes)
- `.github/core/user_agent_mixin.py` (208 bytes)
- `.github/workflows/ci.yml` (1,940 bytes)
- `.github/workflows/stale.yaml` (913 bytes)
- `.well-known/mcp/manifest.json` (3,817 bytes)
- `scripts/sync-specs.sh` (329 bytes)
- `src/alpaca_mcp_server/__init__.py` (623 bytes)
- `src/alpaca_mcp_server/cli.py` (1,573 bytes)
- `src/alpaca_mcp_server/server.py` (5,279 bytes)
- `src/alpaca_mcp_server/names.py` (14,048 bytes)
- `src/alpaca_mcp_server/toolsets.py` (3,933 bytes)
- `src/alpaca_mcp_server/overrides.py` (12,130 bytes)
- `src/alpaca_mcp_server/market_data_overrides.py` (15,254 bytes)
- `src/alpaca_mcp_server/specs/trading-api.json` (158,995 bytes)
- `src/alpaca_mcp_server/specs/market-data-api.json` (127,480 bytes)
- `tests/conftest.py` (1,077 bytes)
- `tests/test_integrity.py` (3,916 bytes)
- `tests/test_server_construction.py` (4,507 bytes)
- `tests/test_paper_integration.py` (22,862 bytes)
- `charts/alpaca-mcp-server/.helmignore` (349 bytes)
- `charts/alpaca-mcp-server/Chart.yaml` (1,145 bytes)
- `charts/alpaca-mcp-server/values.yaml` (4,873 bytes)
- `charts/alpaca-mcp-server/templates/NOTES.txt` (1,756 bytes)
- `charts/alpaca-mcp-server/templates/_helpers.tpl` (1,812 bytes)
- `charts/alpaca-mcp-server/templates/deployment.yaml` (2,800 bytes)
- `charts/alpaca-mcp-server/templates/hpa.yaml` (1,000 bytes)
- `charts/alpaca-mcp-server/templates/ingress.yaml` (1,097 bytes)
- `charts/alpaca-mcp-server/templates/secrets.yaml` (320 bytes)
- `charts/alpaca-mcp-server/templates/service.yaml` (370 bytes)
- `charts/alpaca-mcp-server/templates/serviceaccount.yaml` (395 bytes)
- `charts/alpaca-mcp-server/templates/tests/test-connection.yaml` (388 bytes)

---

## File: `.dockerignore`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/.dockerignore`

```text
.env
.gitignore
```

---

## File: `.gitignore`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/.gitignore`

```text
# Environment and secrets
.env
.env.local
*.secret
secret.py

# Python
__pycache__/
*.py[cod]
*.so
.Python
env/
venv/
.venv/

# Build and distribution
dist/
build/
*.egg-info/
*.egg

# IDE
.vscode/
.idea/
.cursor/
.claude/
*.swp
*.swo

.scratch/

# OS
.DS_Store
Thumbs.db

# Project-specific
_collection/
```

---

## File: `AGENTS.md`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/AGENTS.md`

```markdown
# Agent Instructions

## Architecture Overview

This MCP server auto-generates tools from bundled OpenAPI specs (`src/alpaca_mcp_server/specs/`) using FastMCP's `from_openapi()`. Tool names and descriptions are customized in `names.py`. Complex endpoints (orders, historical data) use hand-written overrides in `overrides.py` and `market_data_overrides.py`. Toolset filtering is defined in `toolsets.py`.

The test suite has three layers:
- `tests/test_integrity.py` — Spec ↔ toolset ↔ names consistency (no network)
- `tests/test_server_construction.py` — Server builds correctly, exposes 61 tools (no network)
- `tests/test_paper_integration.py` — Real API calls against Alpaca paper (needs credentials)

CI is defined in `.github/workflows/ci.yml` with two jobs: `test-core` (runs on every PR) and `test-integration` (runs when `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` secrets are available).

---

# Syncing OpenAPI Specs

When asked to "sync the MCP server" or "update specs", follow this process:

## Step 1: Download latest specs

Run the sync script:

```bash
./scripts/sync-specs.sh
```

## Step 2: Diff the specs

Check what changed:

```bash
git diff src/alpaca_mcp_server/specs/
```

Classify every change into one of three categories:

### A. Modified existing endpoints

Parameter or schema changes to endpoints already in the allowlist (`toolsets.py`).
**Action:** No code changes needed — the spec update is sufficient.

### B. New endpoints

Endpoints with operationIds not present in any toolset.
**Action:** Evaluate each:

1. **Is this endpoint useful for LLM interactions?** (e.g., CRUD for a core trading resource = yes; internal/admin endpoints = no)
2. **If yes:** Add the operationId to the appropriate toolset in `toolsets.py`. Add a `ToolOverride` entry to the `TOOLS` dict in `names.py` with a `snake_case` name and a curated description (see existing entries for the pattern).
3. **If the endpoint is complex** (many conditional params, multiple use cases in one schema like `POST /v2/orders`): Write an override function in `overrides.py`, add the operationId to `OVERRIDE_OPERATION_IDS` in `toolsets.py`, and do NOT add it to any toolset's operations.
4. **If not useful:** Note in the commit message that the endpoint was evaluated and excluded.

### C. Removed or renamed endpoints

OperationIds in `toolsets.py` that no longer exist in the specs.
**Action:** Flag as a breaking change. Remove the stale operationId from `toolsets.py` and the corresponding `ToolOverride` entry from `TOOLS` in `names.py`.

## Step 3: Validate

Run the integrity test suite. It checks that every operationId in `toolsets.py` exists in the specs, has a `ToolOverride` in `names.py`, and that all tool names are unique:

```bash
python -m pytest tests/test_integrity.py -v
```

All 7 tests must pass before proceeding. The tests are self-updating — they read `toolsets.py`, `names.py`, and the spec JSONs at runtime, so they never need manual changes.

## Step 4: Update README.md

If tools were added, removed, or renamed, update the **Available Tools** section in `README.md` to match. The section uses `<details>` blocks grouped by category. Each tool is listed as:

```
* `tool_name` — Short description
```

Use the tool name and description from the `ToolOverride` entry you added in `names.py`. Place the tool in the correct category block (Account & Portfolio, Trading, Positions, etc.). If a new toolset was created, add a new `<details>` block for it.

## Step 5: Extend Tests

If new tools were added (either auto-generated or overrides), add integration test coverage in `tests/test_paper_integration.py`:

1. Follow the existing patterns in the file — each test is an `async def test_...` function marked with `@pytest.mark.integration`.
2. Tests call tools via `server.call_tool(tool_name, arguments)` and parse results with the `_to_dict` / `_parse` helpers at the top of the file.
3. Assert the response contains expected keys or structure. Keep assertions loose enough to tolerate live data variability (e.g., check a key exists rather than asserting an exact value).
4. If a test requires placing orders or creating resources, clean up after itself (cancel orders, delete watchlists, etc.).
5. Run the full suite locally to verify:

```bash
# Core tests (fast, no credentials)
pytest tests/test_integrity.py tests/test_server_construction.py -v

# Integration tests (requires paper API keys)
ALPACA_API_KEY=... ALPACA_SECRET_KEY=... pytest tests/ -m integration -v
```

All tests must pass before proceeding. The CI pipeline (`.github/workflows/ci.yml`) runs core tests on every PR and integration tests when secrets are available.

## Step 6: Commit

Write a descriptive commit message listing:
- What changed in the API specs
- Which new endpoints were added to toolsets (and which toolset)
- Which new endpoints were excluded (and why)
- Any breaking changes (removed/renamed endpoints)
- Whether README was updated
- Whether new tests were added
```

---

## File: `Dockerfile`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/Dockerfile`

```dockerfile
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
COPY .github/core/ ./.github/core/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

CMD ["alpaca-mcp-server", "serve"]

# For cloud deployment
# CMD ["alpaca-mcp-server", "serve", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
```

---

## File: `LICENSE`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/LICENSE`

```text
MIT License

Copyright (c) 2025-2026 Alpaca

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## File: `README.md`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/README.md`

```markdown
<p align="center">
  <img src="https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/main/assets/01-primary-alpaca-logo.png" alt="Alpaca logo" width="220">
</p>

<div align="center">

<a href="https://x.com/alpacahq?lang=en" target="_blank"><img src="https://img.shields.io/badge/X-DCDCDC?logo=x&logoColor=000" alt="X"></a>
<a href="https://www.reddit.com/r/alpacamarkets/" target="_blank"><img src="https://img.shields.io/badge/Reddit-DCDCDC?logo=reddit&logoColor=000" alt="Reddit"></a>
<a href="https://alpaca.markets/slack" target="_blank"><img src="https://img.shields.io/badge/Slack-DCDCDC?logo=slack&logoColor=000" alt="Slack"></a>
<a href="https://www.linkedin.com/company/alpacamarkets/" target="_blank"><img src="https://img.shields.io/badge/LinkedIn-DCDCDC" alt="LinkedIn"></a>
<a href="https://forum.alpaca.markets/" target="_blank"><img src="https://img.shields.io/badge/Forum-DCDCDC?logo=discourse&logoColor=000" alt="Forum"></a>
<a href="https://docs.alpaca.markets/docs/getting-started" target="_blank"><img src="https://img.shields.io/badge/Docs-DCDCDC" alt="Docs"></a>
<a href="https://alpaca.markets/sdks/python/" target="_blank"><img src="https://img.shields.io/badge/Python_SDK-DCDCDC?logo=python&logoColor=000" alt="Python SDK"></a>

</div>

<p align="center">
  A comprehensive Model Context Protocol (MCP) server for Alpaca's Trading API. Enable natural language trading operations through AI assistants like Claude, Cursor, and VS Code. Supports stocks, options, crypto, portfolio management, and real-time market data.
</p>

> **Alpaca MCP Server v2 is here.** This version is a complete rewrite built with FastMCP and OpenAPI. If you're upgrading from v1, please read the [Upgrade Guide](#upgrading-from-v1) — tool names, parameters, and configuration have changed.

## Table of Contents

- [Upgrading from V1](#upgrading-from-v1)
- [Prerequisites](#prerequisites)
- [Getting Your API Keys](#getting-your-api-keys)
- [Setup](#setup)
- [Configuration](#configuration)
- [Features](#features)
- [Example Prompts](#example-prompts)
- [Available Tools](#available-tools)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Disclosure](#disclosure)

---

## Upgrading from V1

V2 is a **complete rewrite** built with FastMCP and OpenAPI. **None of the V1 tools exist in V2** — tool names, parameters, and schemas have changed. You cannot use V2 as a drop-in replacement if your setup depends on specific V1 tool names or parameters.

### What changes


| Aspect             | V1                                     | V2                                                                                           |
| ------------------ | -------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Tool names**     | Hand-crafted (e.g. `get_account_info`) | Spec-derived with overrides (e.g. `get_account_info` — names may overlap but schemas differ) |
| **Parameters**     | Custom schemas                         | Aligned with Alpaca API specs                                                                |
| **Configuration**  | `.env` + `init` command                | Env vars in MCP client config only                                                           |
| **Tool filtering** | Not supported                          | `ALPACA_TOOLSETS` env var                                                                    |
| **Whitelisting**   | Not supported                          | Use `ALPACA_TOOLSETS` to restrict tools                                                      |


### How to avoid V1-style usage in V2

MCP clients discover tools dynamically from the server. There is no config file where you "whitelist" tool names — the client gets whatever tools the server exposes. To avoid your client or AI assistant using V2 incorrectly:

1. **Do not reuse V1 config** — Treat V2 as a new server. Update your MCP client config with the new command/args; remove any `.env` or `init`-based setup.
2. **Clear tool caches** — Restart your MCP client (Claude Desktop, Cursor, VS Code, etc.) after switching so it fetches the new tool list instead of using a stale one.
3. **Start a fresh chat/session** — Existing conversations may have cached references to old tool names. Start a new chat so the LLM sees the current V2 tools and their schemas.
4. **Update custom instructions and rules** — If you have Cursor rules, Claude instructions, or other prompts that mention specific V1 tool names (e.g. "use `get_account_info`"), update them to match V2 tool names or remove those references and let the LLM discover tools from context.
5. **Restrict tools with** `ALPACA_TOOLSETS` — If you previously limited which capabilities your assistant could use, V2 supports server-side filtering via the `ALPACA_TOOLSETS` env var. See [Configuration > Toolset Filtering](#toolset-filtering) for the list of toolsets.

### Summary

Assume **no backward compatibility** with V1. Reconfigure your MCP client for V2, restart it, and use a fresh session. Check the [Available Tools](#available-tools) section for the current tool list.

### If you had custom V1 workflows

If you documented allowed tools, wrote scripts that call tools by name, or built prompts around specific V1 tool/parameter shapes — treat them as obsolete. Recreate them using the [Available Tools](#available-tools) listed below and the current parameter schemas exposed by the server.

### Staying on V1

If you need to stay on V1, pin to the last V1 release (e.g. `uvx alpaca-mcp-server==1.x.x serve`) in your MCP client config. V1 remains available on PyPI for existing setups.

---

## Prerequisites

- **Python 3.10+** ([installation guide](https://www.python.org/downloads/))
- **uv** ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Alpaca Trading API keys** (free paper trading account)
- **MCP client** (Claude Desktop, Cursor, VS Code, etc.)

## Getting Your API Keys

1. Visit the [Alpaca Dashboard](https://app.alpaca.markets/paper/dashboard/overview)
2. Create a free paper trading account
3. Generate API keys from the dashboard

## Setup

Add the server to your MCP client config, then restart the client. No `init` command, no `.env` files — credentials are set in **one place only**.

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "alpaca": {
      "command": "uvx",
      "args": ["alpaca-mcp-server"],
      "env": {
        "ALPACA_API_KEY": "your_alpaca_api_key",
        "ALPACA_SECRET_KEY": "your_alpaca_secret_key"
      }
    }
  }
}
```

### Cursor

Install from the [Cursor Directory](https://cursor.directory/mcp/alpaca) in a few clicks, or add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "alpaca": {
      "command": "uvx",
      "args": ["alpaca-mcp-server"],
      "env": {
        "ALPACA_API_KEY": "your_alpaca_api_key",
        "ALPACA_SECRET_KEY": "your_alpaca_secret_key"
      }
    }
  }
}
```

### VS Code

Create `.vscode/mcp.json` in your project root. See the [official docs](https://code.visualstudio.com/docs/copilot/chat/mcp-servers).

```json
{
  "mcp": {
    "servers": {
      "alpaca": {
        "type": "stdio",
        "command": "uvx",
        "args": ["alpaca-mcp-server"],
        "env": {
          "ALPACA_API_KEY": "your_alpaca_api_key",
          "ALPACA_SECRET_KEY": "your_alpaca_secret_key"
        }
      }
    }
  }
}
```

**PyCharm**  

See the [official guide](https://www.jetbrains.com/help/ai-assistant/configure-an-mcp-server.html).

1. Go to File → Settings → Tools → Model Context Protocol (MCP)
2. Add a new server:
  - **Type**: stdio
  - **Command**: uvx
  - **Arguments**: alpaca-mcp-server
3. Set environment variables:
  ```
   ALPACA_API_KEY=your_alpaca_api_key
   ALPACA_SECRET_KEY=your_alpaca_secret_key
  ```

**Claude Code**  

```bash
claude mcp add alpaca --scope user --transport stdio uvx alpaca-mcp-server \
  --env ALPACA_API_KEY=your_alpaca_api_key \
  --env ALPACA_SECRET_KEY=your_alpaca_secret_key
```

Verify with `/mcp` in the Claude Code CLI.

**Gemini CLI**  

See the [Gemini CLI MCP docs](https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md).

Add to your `settings.json`:

```json
{
  "mcpServers": {
    "alpaca": {
      "type": "stdio",
      "command": "uvx",
      "args": ["alpaca-mcp-server"],
      "env": {
        "ALPACA_API_KEY": "your_alpaca_api_key",
        "ALPACA_SECRET_KEY": "your_alpaca_secret_key"
      }
    }
  }
}
```

**Docker**  

```bash
git clone https://github.com/alpacahq/alpaca-mcp-server.git
cd alpaca-mcp-server
docker build -t mcp/alpaca:latest .
```

Add to your MCP client config:

```json
{
  "mcpServers": {
    "alpaca": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ALPACA_API_KEY=your_key",
        "-e", "ALPACA_SECRET_KEY=your_secret",
        "-e", "ALPACA_PAPER_TRADE=true",
        "mcp/alpaca:latest"
      ]
    }
  }
}
```

## Configuration

All configuration is through environment variables set in your MCP client config. No files are written to disk.


| Variable             | Required | Default | Description                                |
| -------------------- | -------- | ------- | ------------------------------------------ |
| `ALPACA_API_KEY`     | Yes      | —       | Your Alpaca API key                        |
| `ALPACA_SECRET_KEY`  | Yes      | —       | Your Alpaca secret key                     |
| `ALPACA_PAPER_TRADE` | No       | `true`  | Set to `false` for live trading            |
| `ALPACA_TOOLSETS`    | No       | all     | Comma-separated list of toolsets to enable |


### Switching to Live Trading

Update the `env` block in your MCP client config and restart:

```json
{
  "env": {
    "ALPACA_API_KEY": "your_live_api_key",
    "ALPACA_SECRET_KEY": "your_live_secret_key",
    "ALPACA_PAPER_TRADE": "false"
  }
}
```

### Toolset Filtering

By default, all tools are enabled. To limit the server to specific toolsets, set `ALPACA_TOOLSETS`:

```json
{
  "env": {
    "ALPACA_API_KEY": "...",
    "ALPACA_SECRET_KEY": "...",
    "ALPACA_TOOLSETS": "stock-data,crypto-data"
  }
}
```

Available toolsets:


| Toolset             | Description                                                   |
| ------------------- | ------------------------------------------------------------- |
| `account`           | Account info, config, portfolio history, activities           |
| `trading`           | Orders, positions, exercise options                           |
| `watchlists`        | Watchlist CRUD operations                                     |
| `assets`            | Asset lookup, option contracts, calendar, clock               |
| `stock-data`        | Stock bars, quotes, trades, snapshots, screeners              |
| `crypto-data`       | Crypto bars, quotes, trades, snapshots, orderbooks            |
| `options-data`      | Option bars, quotes, trades, snapshots, chain, exchange codes |
| `corporate-actions` | Corporate action announcements                                |


## Features

- **Market Data** — Real-time quotes, trades, and price bars for stocks, crypto, and options. Historical data with flexible timeframes. Option Greeks and implied volatility.
- **Account Management** — View balances, buying power, account status, and portfolio history.
- **Order Management** — Place market, limit, stop, stop-limit, and trailing-stop orders for stocks, crypto, and options. Cancel orders individually or in bulk.
- **Options Trading** — Search contracts by expiration/strike/type. Place single-leg or multi-leg strategies. Get latest quotes, Greeks, and IV.
- **Crypto Trading** — Market, limit, and stop-limit orders with GTC/IOC. Quantity or notional-based.
- **Position Management** — View, close, or liquidate positions. Exercise option contracts.
- **Market Status** — Market open/close times, calendar, corporate actions.
- **Watchlists** — Create, update, and manage watchlists.
- **Asset Search** — Query details for stocks, ETFs, crypto, and options with filtering.

## Example Prompts

**Basic Trading**

1. What's my current account balance and buying power on Alpaca?
2. Show me my current positions in my Alpaca account.
3. Buy 5 shares of AAPL at market price.
4. Sell 5 shares of TSLA with a limit price of $300.
5. Cancel all open stock orders.
6. Cancel the order with ID abc123.
7. Liquidate my entire position in GOOGL.
8. Close 10% of my position in NVDA.
9. Place a limit order to buy 100 shares of MSFT at $450.
10. Place a market order to sell 25 shares of META.

**Crypto Trading**

1. Place a market order to buy 0.01 ETH/USD.
2. Place a limit order to sell 0.01 BTC/USD at $110,000.

**Option Trading**

1. Show me available option contracts for AAPL expiring next month.
2. Get the latest quote for the AAPL250613C00200000 option.
3. Retrieve the option snapshot for the SPY250627P00400000 option.
4. Liquidate my position in 2 contracts of QQQ calls expiring next week.
5. Place a market order to buy 1 call option on AAPL expiring next Friday.
6. What are the option Greeks for the TSLA250620P00500000 option?
7. Find TSLA option contracts with strike prices within 5% of the current market price.
8. Get SPY call options expiring the week of June 16th, 2025, within 10% of market price.
9. Place a bull call spread using AAPL June 6th options: one with a 190.00 strike and the other with a 200.00 strike.
10. Exercise my NVDA call option contract NVDA250919C001680.

**Market Information**

> To access the latest 15-minute data, you need to subscribe to the [Algo Trader Plus Plan](https://alpaca.markets/data).
>
> 1. What are the market open and close times today?
> 2. Show me the market calendar for next week.
> 3. Show me recent cash dividends and stock splits for AAPL, MSFT, and GOOGL in the last 3 months.
> 4. Get all corporate actions for SPY including dividends, splits, and any mergers in the past year.
> 5. What are the upcoming corporate actions scheduled for SPY in the next 6 months?

**Historical & Real-time Data**

1. Show me AAPL's daily price history for the last 5 trading days.
2. What was the closing price of TSLA yesterday?
3. Get the latest bar for GOOGL.
4. What was the latest trade price for NVDA?
5. Show me the most recent quote for MSFT.
6. Retrieve the last 100 trades for AMD.
7. Show me 1-minute bars for AMZN from the last 2 hours.
8. Get 5-minute intraday bars for TSLA from last Tuesday through last Friday.
9. Get a comprehensive stock snapshot for AAPL showing latest quote, trade, minute bar, daily bar, and previous daily bar all in one view.
10. Compare market snapshots for TSLA, NVDA, and MSFT to analyze their current bid/ask spreads, latest trade prices, and daily performance.

**Orders**

1. Show me all my open and filled orders from this week.
2. What orders do I have for AAPL?
3. List all limit orders I placed in the past 3 days.
4. Filter all orders by status: filled.
5. Get me the order history for yesterday.

**Watchlists**

> At this moment, you can only view and update trading watchlists created via Alpaca's Trading API through the API itself
>
> 1. Create a new watchlist called "Tech Stocks" with AAPL, MSFT, and NVDA.
> 2. Update my "Tech Stocks" watchlist to include TSLA and AMZN.
> 3. What stocks are in my "Dividend Picks" watchlist?
> 4. Remove META from my "Growth Portfolio" watchlist.
> 5. List all my existing watchlists.

**Asset Information**

1. Search for details about the asset 'AAPL'.
2. Show me the top 5 tradable crypto assets by trading volume.
3. Get all NASDAQ active US equity assets and filter the results to show only tradable securities

**Combined Scenarios**

1. Get today's market clock and show me my buying power before placing a limit buy order for TSLA at $340.
2. Place a bull call spread with SPY July 3rd options: sell one 5% above and buy one 3% below the current SPY price.

## Available Tools

**Account & Portfolio**

- `get_account_info` — Balance, margin, and account status
- `get_account_config` — Trading restrictions, margin settings, PDT checks
- `update_account_config` — Update account configuration settings
- `get_portfolio_history` — Equity and P/L over time
- `get_account_activities` — Fills, dividends, transfers
- `get_account_activities_by_type` — Activities filtered by type

**Trading (Orders)**

- `get_orders` — Retrieve orders with filters
- `get_order_by_id` — Single order by ID
- `get_order_by_client_id` — Single order by client order ID
- `replace_order_by_id` — Replace an existing open order
- `cancel_order_by_id` — Cancel a specific order
- `cancel_all_orders` — Cancel all open orders
- `place_stock_order` — Stocks/ETFs (market, limit, stop, stop-limit, trailing-stop, brackets)
- `place_crypto_order` — Crypto (market, limit, stop-limit)
- `place_option_order` — Options (single-leg or multi-leg)

**Positions**

- `get_all_positions` — All current positions
- `get_open_position` — Details for a specific position
- `close_position` — Close a specific position
- `close_all_positions` — Liquidate entire portfolio
- `exercise_options_position` — Exercise a held option contract
- `do_not_exercise_options_position` — Do-not-exercise instruction

**Watchlists**

- `create_watchlist` — Create a new watchlist
- `get_watchlists` — List all watchlists
- `get_watchlist_by_id` — Get a specific watchlist
- `update_watchlist_by_id` — Update a watchlist
- `delete_watchlist_by_id` — Delete a watchlist
- `add_asset_to_watchlist_by_id` — Add an asset to a watchlist
- `remove_asset_from_watchlist_by_id` — Remove an asset from a watchlist

**Assets & Market Info**

- `get_all_assets` — List assets with optional filtering
- `get_asset` — Detailed info for a specific asset
- `get_option_contracts` — Option contracts for underlying symbol(s)
- `get_option_contract` — Single option contract by symbol or ID
- `get_calendar` — Market calendar for a date range
- `get_clock` — Current market status and next open/close
- `get_corporate_action_announcements` — Corporate action announcements
- `get_corporate_action_announcement` — Single announcement by ID

**Stock Data**

- `get_stock_bars` — Historical OHLCV bars
- `get_stock_quotes` — Historical bid/ask quotes
- `get_stock_trades` — Historical trades
- `get_stock_latest_bar` — Latest minute bar
- `get_stock_latest_quote` — Latest quote
- `get_stock_latest_trade` — Latest trade
- `get_stock_snapshot` — Comprehensive snapshot
- `get_most_active_stocks` — Most active by volume/trade count
- `get_market_movers` — Top gainers and losers

**Crypto Data**

- `get_crypto_bars` — Historical OHLCV bars
- `get_crypto_quotes` — Historical quotes
- `get_crypto_trades` — Historical trades
- `get_crypto_latest_bar` — Latest minute bar
- `get_crypto_latest_quote` — Latest quote
- `get_crypto_latest_trade` — Latest trade
- `get_crypto_snapshot` — Comprehensive snapshot
- `get_crypto_latest_orderbook` — Latest orderbook

**Options Data**

- `get_option_bars` — Historical OHLCV bars
- `get_option_trades` — Historical trades
- `get_option_latest_trade` — Latest trade
- `get_option_latest_quote` — Latest quote with bid/ask and exchange info
- `get_option_snapshot` — Snapshot with Greeks and IV
- `get_option_chain` — Full option chain for an underlying
- `get_option_exchange_codes` — Exchange code to name mapping

**Corporate Actions**

- `get_corporate_actions` — Corporate action announcements from market data

## Testing

The project includes a multi-layered test suite that runs in CI on every pull request:

- **Integrity tests** — Validate consistency between OpenAPI specs, toolset definitions, and tool name/description overrides. No network or credentials required.
- **Server construction tests** — Build the server with mocked credentials and verify the correct number of tools are exposed. No network required.
- **Paper API integration tests** — Execute real calls against the Alpaca paper trading API, covering account info, market data, order lifecycle, watchlists, positions, and more. Requires `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`.

Run the full suite locally:

```bash
# Core tests (no credentials needed)
pytest tests/test_integrity.py tests/test_server_construction.py -v

# Integration tests (requires paper API keys)
ALPACA_API_KEY=... ALPACA_SECRET_KEY=... pytest tests/ -m integration -v
```

## Project Structure

```
alpaca-mcp-server/
├── src/
│   └── alpaca_mcp_server/
│       ├── __init__.py
│       ├── cli.py            ← CLI entry point
│       ├── server.py         ← FastMCP server built from OpenAPI specs
│       ├── names.py          ← Tool name and description overrides
│       ├── toolsets.py       ← Toolset → operationId allowlists
│       ├── overrides.py      ← Hand-crafted tools for complex trading endpoints
│       ├── market_data_overrides.py ← Hand-crafted tools for historical data
│       └── specs/
│           ├── trading-api.json
│           └── market-data-api.json
├── tests/
│   ├── conftest.py           ← Shared fixtures and paper-account cleanup
│   ├── test_integrity.py     ← Spec ↔ toolset ↔ names consistency checks
│   ├── test_server_construction.py ← Server build verification
│   └── test_paper_integration.py   ← Paper API integration tests
├── scripts/
│   └── sync-specs.sh        ← Download latest OpenAPI specs
├── .github/
│   └── workflows/
│       └── ci.yml            ← CI pipeline (core + integration)
├── AGENTS.md                 ← Instructions for coding agents
├── pyproject.toml
└── README.md
```

## Troubleshooting

- **uv/uvx not found**: Install uv from the official guide ([https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)) and then restart your terminal so `uv`/`uvx` are on PATH.
- **Credentials missing**: Set `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` in the client's `env` block. Paper mode default is `ALPACA_PAPER_TRADE = True`.
- **Client didn't pick up new config**: Restart the client (Cursor, Claude Desktop, VS Code) after changes.
- **HTTP port conflicts**: If using `--transport streamable-http`, change `--port` to a free port.

## Disclosure

Insights generated by our MCP server and connected AI agents are for educational and informational purposes only and should not be taken as investment advice. Alpaca does not recommend any specific securities or investment strategies.Please conduct your own due diligence before making any decisions. All firms mentioned operate independently and are not liable for one another.

Options trading is not suitable for all investors due to its inherent high risk, which can potentially result in significant losses. Please read Characteristics and Risks of Standardized Options ([Options Disclosure Document](https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document?ref=alpaca.markets)) before investing in options.

Alpaca does not prepare, edit, endorse, or approve Third Party Content. Alpaca does not guarantee the accuracy, timeliness, completeness or usefulness of Third Party Content, and is not responsible or liable for any content, advertising, products, or other materials on or available from third party sites.

All investments involve risk, and the past performance of a security, or financial product does not guarantee future results or returns. There is no guarantee that any investment strategy will achieve its objectives. Please note that diversification does not ensure a profit, or protect against loss. There is always the potential of losing money when you invest in securities, or other financial products. Investors should consider their investment objectives and risks carefully before investing.

The algorithm's calculations are based on historical and real-time market data but may not account for all market factors, including sudden price moves, liquidity constraints, or execution delays. Model assumptions, such as volatility estimates and dividend treatments, can impact performance and accuracy. Trades generated by the algorithm are subject to brokerage execution processes, market liquidity, order priority, and timing delays. These factors may cause deviations from expected trade execution prices or times. Users are responsible for monitoring algorithmic activity and understanding the risks involved. Alpaca is not liable for any losses incurred through the use of this system.

Past hypothetical backtest results do not guarantee future returns, and actual results may vary from the analysis.

The Paper Trading API is offered by AlpacaDB, Inc. and does not require real money or permit a user to transact in real securities in the market. Providing use of the Paper Trading API is not an offer or solicitation to buy or sell securities, securities derivative or futures products of any kind, or any type of trading or investment advice, recommendation or strategy, given or in any manner endorsed by AlpacaDB, Inc. or any AlpacaDB, Inc. affiliate and the information made available through the Paper Trading API is not an offer or solicitation of any kind in any jurisdiction where AlpacaDB, Inc. or any AlpacaDB, Inc. affiliate (collectively, "Alpaca") is not authorized to do business.

Securities brokerage services are provided by Alpaca Securities LLC ("Alpaca Securities"), member [FINRA](https://www.finra.org/)/[SIPC](https://www.sipc.org/), a wholly-owned subsidiary of AlpacaDB, Inc. Technology and services are offered by AlpacaDB, Inc.

Cryptocurrency services are provided by Alpaca Crypto LLC ("Alpaca Crypto"), a FinCEN registered money services business (NMLS # 2160858), and a wholly-owned subsidiary of AlpacaDB, Inc. Alpaca Crypto is not a member of SIPC or FINRA. Cryptocurrencies are not stocks and your cryptocurrency investments are not protected by either FDIC or SIPC.  Cryptocurrency assets are highly volatile and speculative, involving substantial risk of loss, and are not insured by the FDIC or any government agency. Customers should be aware of the various risks prior to engaging these services, including potential loss of principal, cybersecurity considerations, regulatory developments, and the evolving nature of digital asset technology. For additional information on the risks of cryptocurrency, please click [here](https://files.alpaca.markets/disclosures/library/CryptoRiskDisclosures.pdf).

This is not an offer, solicitation of an offer, or advice to buy or sell securities or cryptocurrencies or open a brokerage account or cryptocurrency account in any jurisdiction where Alpaca Securities or Alpaca Crypto, respectively, are not registered or licensed, as applicable.

## Privacy Policy

For information about how Alpaca handles your data, please review:

- [Privacy Policy](https://s3.amazonaws.com/files.alpaca.markets/disclosures/PrivacyPolicy.pdf)
- [Disclosure Library](https://alpaca.markets/disclosures)

### Data Collection

- **What is collected**: User agent string ('ALPACA-MCP-SERVER') for API calls
- **How it's used**: To identify MCP server usage and improve user experience
- **Third-party sharing**: Not shared with third parties
- **Retention**: Retained per Alpaca's standard data retention policy
- **Opt-out**: Modify the 'USER_AGENT' constant in '.github/core/user_agent_mixin.py' or remove 'UserAgentMixin' from client class definitions

## Security Notice

This server can place real trades and access your portfolio. Treat your API keys as sensitive credentials. Review all actions proposed by the LLM carefully, especially for complex options strategies or multi-leg trades.

**HTTP Transport Security**: When using HTTP transport, the server defaults to localhost (127.0.0.1:8000) for security. For remote access, you can bind to all interfaces with `--host 0.0.0.0`, use SSH tunneling (`ssh -L 8000:localhost:8000 user@server`), or set up a reverse proxy with authentication for secure access.

## Support

For issues or questions, please contact us at [support@alpaca.markets](mailto:support@alpaca.markets).

GitHub Issues: [https://github.com/alpacahq/alpaca-mcp-server/issues](https://github.com/alpacahq/alpaca-mcp-server/issues)
GitHub Pull requests: [https://github.com/alpacahq/alpaca-mcp-server/pulls](https://github.com/alpacahq/alpaca-mcp-server/pulls)

### MCP Registry Metadata

mcp-name: io.github.alpacahq/alpaca-mcp-server
```

---

## File: `pyproject.toml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "alpaca-mcp-server"
version = "2.0.0"
description = "Alpaca Trading API integration for Model Context Protocol (MCP)"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}

authors = [
    {name = "Alpaca", email = "info@alpaca.markets"}
]

keywords = ["mcp", "alpaca", "trading", "finance", "ai", "llm", "model-context-protocol"]

classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Office/Business :: Financial :: Investment",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Scientific/Engineering :: Artificial Intelligence"
]

dependencies = [
    "fastmcp>=2.0.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
    "click>=8.1.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pytest>=7.0.0",
    "pytest-asyncio>=0.23.0",
]

[project.urls]
Homepage = "https://alpaca.markets/"
Repository = "https://github.com/alpacahq/alpaca-mcp-server"
"Bug Tracker" = "https://github.com/alpacahq/alpaca-mcp-server/issues"
Documentation = "https://github.com/alpacahq/alpaca-mcp-server#readme"

[project.scripts]
alpaca-mcp-server = "alpaca_mcp_server.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/alpaca_mcp_server"]

[tool.hatch.build]
include = [
    "src/alpaca_mcp_server/**/*.py",
    "src/alpaca_mcp_server/specs/*.json",
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = ["-v", "--tb=short"]
asyncio_mode = "auto"
markers = [
    "integration: requires paper API credentials (ALPACA_API_KEY, ALPACA_SECRET_KEY)",
]
```

---

## File: `requirements.txt`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/requirements.txt`

```text
alpaca-py
mcp>=1.23.0
python-dotenv
urllib3>=2.6.3
python-multipart>=0.0.22
```

---

## File: `server.json`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/server.json`

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-10-17/server.schema.json",
  "name": "io.github.alpacahq/alpaca-mcp-server",
  "title": "Alpaca's MCP Server",
  "description": "Alpaca Trading API integration for Model Context Protocol (MCP). V2 generates 60+ tools directly from Alpaca's OpenAPI specs using FastMCP.",
  "repository": {
    "url": "https://github.com/alpacahq/alpaca-mcp-server",
    "source": "github"
  },
  "version": "2.0.0",
  "packages": [
    {
      "registryType": "pypi",
      "identifier": "alpaca-mcp-server",
      "version": "2.0.0",
      "transport": {
        "type": "stdio"
      },
      "environmentVariables": [
        {
          "name": "ALPACA_API_KEY",
          "description": "Alpaca Trading API key",
          "isRequired": true,
          "isSecret": true,
          "format": "string"
        },
        {
          "name": "ALPACA_SECRET_KEY",
          "description": "Alpaca Trading API secret key",
          "isRequired": true,
          "isSecret": true,
          "format": "string"
        },
        {
          "name": "ALPACA_TOOLSETS",
          "description": "Comma-separated list of toolsets to enable (e.g. account,trading,stock-data). All enabled by default.",
          "isRequired": false,
          "isSecret": false,
          "format": "string"
        }
      ]
    }
  ]
}
```

---

## File: `server.yaml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/server.yaml`

```yaml
# server.yaml
#
# Docker MCP Registry Configuration
# Location: /server.yaml
# Purpose: Metadata for Docker MCP Registry submission and container deployment

name: alpaca-mcp-server
image: alpaca/mcp-server
type: server

meta:
  category: finance
  tags:
    - trading
    - finance
    - alpaca
    - stocks
    - options
    - crypto
    - portfolio
    - market-data
    - ai
    - llm

about:
  title: Alpaca MCP Server
  description: |
    Alpaca Trading API integration for Model Context Protocol.

    V2 generates 60+ MCP tools directly from Alpaca's published OpenAPI specs
    using FastMCP's from_openapi(). Covers account management, order placement,
    position tracking, market data (stocks, options, crypto), watchlists,
    corporate actions, and more.

    Key capabilities:
    - Account & portfolio — balances, buying power, positions, portfolio history, activity log
    - Order management — place, replace, cancel orders for stocks, options, and crypto
    - Stock market data — historical bars, quotes, trades, snapshots, screener
    - Options data — contract search, quotes with Greeks, snapshots
    - Crypto data — bars, quotes, trades, orderbook, snapshots
    - Watchlists — create, update, delete, add/remove symbols
    - Corporate actions — dividends, splits, earnings
    - Market calendar & clock

    Toolset filtering lets you control exactly which capabilities the model can access
    via the ALPACA_TOOLSETS environment variable.

source:
  project: https://github.com/alpacahq/alpaca-mcp-server
  documentation: https://github.com/alpacahq/alpaca-mcp-server#readme
  issues: https://github.com/alpacahq/alpaca-mcp-server/issues

config:
  description: |
    Configure your Alpaca API credentials to connect to your trading account.

    Get free API keys for paper trading at:
    https://app.alpaca.markets/dashboard/overview

  secrets:
    - name: ALPACA_API_KEY
      description: Your Alpaca API key for account access
      required: true

    - name: ALPACA_SECRET_KEY
      description: Your Alpaca secret key for account access
      required: true

  env:
    - name: ALPACA_TOOLSETS
      description: Comma-separated list of toolsets to enable (e.g. account,trading,stock-data). All enabled by default.
      default: ""

    - name: DATA_API_URL
      description: Custom Alpaca data API URL (leave empty for default)
      default: ""

    - name: DEBUG
      description: Enable debug logging (true/false)
      default: "false"

metadata:
  license: MIT
  maintainer: Alpaca <https://alpaca.markets/contact>
  version: "2.0.0"

  docker:
    transport: stdio
    working_dir: /app
    user: alpaca

    healthcheck:
      test: ["CMD", "python", "-c", "import alpaca_mcp_server"]
      interval: 30s
      timeout: 10s
      retries: 3

  platforms:
    - linux/amd64
    - linux/arm64

  examples:
    basic_usage: |
      docker run -e ALPACA_API_KEY -e ALPACA_SECRET_KEY alpaca/mcp-server

    claude_desktop: |
      {
        "mcpServers": {
          "alpaca": {
            "command": "docker",
            "args": ["run", "-i", "--rm", "-e", "ALPACA_API_KEY", "-e", "ALPACA_SECRET_KEY", "alpaca/mcp-server"],
            "env": {
              "ALPACA_API_KEY": "your_api_key",
              "ALPACA_SECRET_KEY": "your_secret_key"
            }
          }
        }
      }

    filtered_toolsets: |
      docker run -e ALPACA_API_KEY -e ALPACA_SECRET_KEY \
        -e ALPACA_TOOLSETS=account,stock-data,crypto-data \
        alpaca/mcp-server
```

---

## File: `uv.lock`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/uv.lock`

```toml
version = 1
revision = 3
requires-python = ">=3.10"
resolution-markers = [
    "python_full_version >= '3.12'",
    "python_full_version == '3.11.*'",
    "python_full_version < '3.11'",
]

[[package]]
name = "aiofile"
version = "3.9.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "caio" },
]
sdist = { url = "https://files.pythonhosted.org/packages/67/e2/d7cb819de8df6b5c1968a2756c3cb4122d4fa2b8fc768b53b7c9e5edb646/aiofile-3.9.0.tar.gz", hash = "sha256:e5ad718bb148b265b6df1b3752c4d1d83024b93da9bd599df74b9d9ffcf7919b", size = 17943, upload-time = "2024-10-08T10:39:35.846Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/50/25/da1f0b4dd970e52bf5a36c204c107e11a0c6d3ed195eba0bfbc664c312b2/aiofile-3.9.0-py3-none-any.whl", hash = "sha256:ce2f6c1571538cbdfa0143b04e16b208ecb0e9cb4148e528af8a640ed51cc8aa", size = 19539, upload-time = "2024-10-08T10:39:32.955Z" },
]

[[package]]
name = "alpaca-mcp-server"
version = "2.0.0"
source = { editable = "." }
dependencies = [
    { name = "click" },
    { name = "fastmcp" },
    { name = "httpx" },
    { name = "python-dotenv" },
]

[package.optional-dependencies]
dev = [
    { name = "mypy" },
    { name = "pytest" },
    { name = "pytest-asyncio" },
    { name = "ruff" },
]

[package.metadata]
requires-dist = [
    { name = "click", specifier = ">=8.1.0" },
    { name = "fastmcp", specifier = ">=2.0.0" },
    { name = "httpx", specifier = ">=0.27.0" },
    { name = "mypy", marker = "extra == 'dev'", specifier = ">=1.0.0" },
    { name = "pytest", marker = "extra == 'dev'", specifier = ">=7.0.0" },
    { name = "pytest-asyncio", marker = "extra == 'dev'", specifier = ">=0.23.0" },
    { name = "python-dotenv", specifier = ">=1.0.0" },
    { name = "ruff", marker = "extra == 'dev'", specifier = ">=0.1.0" },
]
provides-extras = ["dev"]

[[package]]
name = "annotated-types"
version = "0.7.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/ee/67/531ea369ba64dcff5ec9c3402f9f51bf748cec26dde048a2f973a4eea7f5/annotated_types-0.7.0.tar.gz", hash = "sha256:aff07c09a53a08bc8cfccb9c85b05f1aa9a2a6f23728d790723543408344ce89", size = 16081, upload-time = "2024-05-20T21:33:25.928Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/78/b6/6307fbef88d9b5ee7421e68d78a9f162e0da4900bc5f5793f6d3d0e34fb8/annotated_types-0.7.0-py3-none-any.whl", hash = "sha256:1f02e8b43a8fbbc3f3e0d4f0f4bfc8131bcb4eebe8849b8e5c773f3a1c582a53", size = 13643, upload-time = "2024-05-20T21:33:24.1Z" },
]

[[package]]
name = "anyio"
version = "4.12.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "exceptiongroup", marker = "python_full_version < '3.11'" },
    { name = "idna" },
    { name = "typing-extensions", marker = "python_full_version < '3.13'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/16/ce/8a777047513153587e5434fd752e89334ac33e379aa3497db860eeb60377/anyio-4.12.0.tar.gz", hash = "sha256:73c693b567b0c55130c104d0b43a9baf3aa6a31fc6110116509f27bf75e21ec0", size = 228266, upload-time = "2025-11-28T23:37:38.911Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/7f/9c/36c5c37947ebfb8c7f22e0eb6e4d188ee2d53aa3880f3f2744fb894f0cb1/anyio-4.12.0-py3-none-any.whl", hash = "sha256:dad2376a628f98eeca4881fc56cd06affd18f659b17a747d3ff0307ced94b1bb", size = 113362, upload-time = "2025-11-28T23:36:57.897Z" },
]

[[package]]
name = "attrs"
version = "25.4.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/6b/5c/685e6633917e101e5dcb62b9dd76946cbb57c26e133bae9e0cd36033c0a9/attrs-25.4.0.tar.gz", hash = "sha256:16d5969b87f0859ef33a48b35d55ac1be6e42ae49d5e853b597db70c35c57e11", size = 934251, upload-time = "2025-10-06T13:54:44.725Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/3a/2a/7cc015f5b9f5db42b7d48157e23356022889fc354a2813c15934b7cb5c0e/attrs-25.4.0-py3-none-any.whl", hash = "sha256:adcf7e2a1fb3b36ac48d97835bb6d8ade15b8dcce26aba8bf1d14847b57a3373", size = 67615, upload-time = "2025-10-06T13:54:43.17Z" },
]

[[package]]
name = "authlib"
version = "1.6.9"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "cryptography" },
]
sdist = { url = "https://files.pythonhosted.org/packages/af/98/00d3dd826d46959ad8e32af2dbb2398868fd9fd0683c26e56d0789bd0e68/authlib-1.6.9.tar.gz", hash = "sha256:d8f2421e7e5980cc1ddb4e32d3f5fa659cfaf60d8eaf3281ebed192e4ab74f04", size = 165134, upload-time = "2026-03-02T07:44:01.998Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/53/23/b65f568ed0c22f1efacb744d2db1a33c8068f384b8c9b482b52ebdbc3ef6/authlib-1.6.9-py2.py3-none-any.whl", hash = "sha256:f08b4c14e08f0861dc18a32357b33fbcfd2ea86cfe3fe149484b4d764c4a0ac3", size = 244197, upload-time = "2026-03-02T07:44:00.307Z" },
]

[[package]]
name = "backports-asyncio-runner"
version = "1.2.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/8e/ff/70dca7d7cb1cbc0edb2c6cc0c38b65cba36cccc491eca64cabd5fe7f8670/backports_asyncio_runner-1.2.0.tar.gz", hash = "sha256:a5aa7b2b7d8f8bfcaa2b57313f70792df84e32a2a746f585213373f900b42162", size = 69893, upload-time = "2025-07-02T02:27:15.685Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/a0/59/76ab57e3fe74484f48a53f8e337171b4a2349e506eabe136d7e01d059086/backports_asyncio_runner-1.2.0-py3-none-any.whl", hash = "sha256:0da0a936a8aeb554eccb426dc55af3ba63bcdc69fa1a600b5bb305413a4477b5", size = 12313, upload-time = "2025-07-02T02:27:14.263Z" },
]

[[package]]
name = "backports-tarfile"
version = "1.2.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/86/72/cd9b395f25e290e633655a100af28cb253e4393396264a98bd5f5951d50f/backports_tarfile-1.2.0.tar.gz", hash = "sha256:d75e02c268746e1b8144c278978b6e98e85de6ad16f8e4b0844a154557eca991", size = 86406, upload-time = "2024-05-28T17:01:54.731Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b9/fa/123043af240e49752f1c4bd24da5053b6bd00cad78c2be53c0d1e8b975bc/backports.tarfile-1.2.0-py3-none-any.whl", hash = "sha256:77e284d754527b01fb1e6fa8a1afe577858ebe4e9dad8919e34c862cb399bc34", size = 30181, upload-time = "2024-05-28T17:01:53.112Z" },
]

[[package]]
name = "beartype"
version = "0.22.9"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/c7/94/1009e248bbfbab11397abca7193bea6626806be9a327d399810d523a07cb/beartype-0.22.9.tar.gz", hash = "sha256:8f82b54aa723a2848a56008d18875f91c1db02c32ef6a62319a002e3e25a975f", size = 1608866, upload-time = "2025-12-13T06:50:30.72Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/71/cc/18245721fa7747065ab478316c7fea7c74777d07f37ae60db2e84f8172e8/beartype-0.22.9-py3-none-any.whl", hash = "sha256:d16c9bbc61ea14637596c5f6fbff2ee99cbe3573e46a716401734ef50c3060c2", size = 1333658, upload-time = "2025-12-13T06:50:28.266Z" },
]

[[package]]
name = "cachetools"
version = "7.0.5"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/af/dd/57fe3fdb6e65b25a5987fd2cdc7e22db0aef508b91634d2e57d22928d41b/cachetools-7.0.5.tar.gz", hash = "sha256:0cd042c24377200c1dcd225f8b7b12b0ca53cc2c961b43757e774ebe190fd990", size = 37367, upload-time = "2026-03-09T20:51:29.451Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/06/f3/39cf3367b8107baa44f861dc802cbf16263c945b62d8265d36034fc07bea/cachetools-7.0.5-py3-none-any.whl", hash = "sha256:46bc8ebefbe485407621d0a4264b23c080cedd913921bad7ac3ed2f26c183114", size = 13918, upload-time = "2026-03-09T20:51:27.33Z" },
]

[[package]]
name = "caio"
version = "0.9.25"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/92/88/b8527e1b00c1811db339a1df8bd1ae49d146fcea9d6a5c40e3a80aaeb38d/caio-0.9.25.tar.gz", hash = "sha256:16498e7f81d1d0f5a4c0ad3f2540e65fe25691376e0a5bd367f558067113ed10", size = 26781, upload-time = "2025-12-26T15:21:36.501Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/6a/80/ea4ead0c5d52a9828692e7df20f0eafe8d26e671ce4883a0a146bb91049e/caio-0.9.25-cp310-cp310-macosx_10_9_universal2.whl", hash = "sha256:ca6c8ecda611478b6016cb94d23fd3eb7124852b985bdec7ecaad9f3116b9619", size = 36836, upload-time = "2025-12-26T15:22:04.662Z" },
    { url = "https://files.pythonhosted.org/packages/17/b9/36715c97c873649d1029001578f901b50250916295e3dddf20c865438865/caio-0.9.25-cp310-cp310-manylinux2010_x86_64.manylinux2014_x86_64.manylinux_2_12_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:db9b5681e4af8176159f0d6598e73b2279bb661e718c7ac23342c550bd78c241", size = 79695, upload-time = "2025-12-26T15:22:18.818Z" },
    { url = "https://files.pythonhosted.org/packages/0b/ab/07080ecb1adb55a02cbd8ec0126aa8e43af343ffabb6a71125b42670e9a1/caio-0.9.25-cp310-cp310-manylinux_2_34_aarch64.whl", hash = "sha256:bf61d7d0c4fd10ffdd98ca47f7e8db4d7408e74649ffaf4bef40b029ada3c21b", size = 79457, upload-time = "2026-03-04T22:08:16.024Z" },
    { url = "https://files.pythonhosted.org/packages/88/95/dd55757bb671eb4c376e006c04e83beb413486821f517792ea603ef216e9/caio-0.9.25-cp310-cp310-manylinux_2_34_x86_64.whl", hash = "sha256:ab52e5b643f8bbd64a0605d9412796cd3464cb8ca88593b13e95a0f0b10508ae", size = 77705, upload-time = "2026-03-04T22:08:17.202Z" },
    { url = "https://files.pythonhosted.org/packages/ec/90/543f556fcfcfa270713eef906b6352ab048e1e557afec12925c991dc93c2/caio-0.9.25-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:d6956d9e4a27021c8bd6c9677f3a59eb1d820cc32d0343cea7961a03b1371965", size = 36839, upload-time = "2025-12-26T15:21:40.267Z" },
    { url = "https://files.pythonhosted.org/packages/51/3b/36f3e8ec38dafe8de4831decd2e44c69303d2a3892d16ceda42afed44e1b/caio-0.9.25-cp311-cp311-manylinux2010_x86_64.manylinux2014_x86_64.manylinux_2_12_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:bf84bfa039f25ad91f4f52944452a5f6f405e8afab4d445450978cd6241d1478", size = 80255, upload-time = "2025-12-26T15:22:20.271Z" },
    { url = "https://files.pythonhosted.org/packages/df/ce/65e64867d928e6aff1b4f0e12dba0ef6d5bf412c240dc1df9d421ac10573/caio-0.9.25-cp311-cp311-manylinux_2_34_aarch64.whl", hash = "sha256:ae3d62587332bce600f861a8de6256b1014d6485cfd25d68c15caf1611dd1f7c", size = 80052, upload-time = "2026-03-04T22:08:20.402Z" },
    { url = "https://files.pythonhosted.org/packages/46/90/e278863c47e14ec58309aa2e38a45882fbe67b4cc29ec9bc8f65852d3e45/caio-0.9.25-cp311-cp311-manylinux_2_34_x86_64.whl", hash = "sha256:fc220b8533dcf0f238a6b1a4a937f92024c71e7b10b5a2dfc1c73604a25709bc", size = 78273, upload-time = "2026-03-04T22:08:21.368Z" },
    { url = "https://files.pythonhosted.org/packages/d3/25/79c98ebe12df31548ba4eaf44db11b7cad6b3e7b4203718335620939083c/caio-0.9.25-cp312-cp312-macosx_10_13_universal2.whl", hash = "sha256:fb7ff95af4c31ad3f03179149aab61097a71fd85e05f89b4786de0359dffd044", size = 36983, upload-time = "2025-12-26T15:21:36.075Z" },
    { url = "https://files.pythonhosted.org/packages/a3/2b/21288691f16d479945968a0a4f2856818c1c5be56881d51d4dac9b255d26/caio-0.9.25-cp312-cp312-manylinux2010_x86_64.manylinux2014_x86_64.manylinux_2_12_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:97084e4e30dfa598449d874c4d8e0c8d5ea17d2f752ef5e48e150ff9d240cd64", size = 82012, upload-time = "2025-12-26T15:22:20.983Z" },
    { url = "https://files.pythonhosted.org/packages/03/c4/8a1b580875303500a9c12b9e0af58cb82e47f5bcf888c2457742a138273c/caio-0.9.25-cp312-cp312-manylinux_2_34_aarch64.whl", hash = "sha256:4fa69eba47e0f041b9d4f336e2ad40740681c43e686b18b191b6c5f4c5544bfb", size = 81502, upload-time = "2026-03-04T22:08:22.381Z" },
    { url = "https://files.pythonhosted.org/packages/d1/1c/0fe770b8ffc8362c48134d1592d653a81a3d8748d764bec33864db36319d/caio-0.9.25-cp312-cp312-manylinux_2_34_x86_64.whl", hash = "sha256:6bebf6f079f1341d19f7386db9b8b1f07e8cc15ae13bfdaff573371ba0575d69", size = 80200, upload-time = "2026-03-04T22:08:23.382Z" },
    { url = "https://files.pythonhosted.org/packages/31/57/5e6ff127e6f62c9f15d989560435c642144aa4210882f9494204bc892305/caio-0.9.25-cp313-cp313-macosx_10_13_universal2.whl", hash = "sha256:d6c2a3411af97762a2b03840c3cec2f7f728921ff8adda53d7ea2315a8563451", size = 36979, upload-time = "2025-12-26T15:21:35.484Z" },
    { url = "https://files.pythonhosted.org/packages/a3/9f/f21af50e72117eb528c422d4276cbac11fb941b1b812b182e0a9c70d19c5/caio-0.9.25-cp313-cp313-manylinux2010_x86_64.manylinux2014_x86_64.manylinux_2_12_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:0998210a4d5cd5cb565b32ccfe4e53d67303f868a76f212e002a8554692870e6", size = 81900, upload-time = "2025-12-26T15:22:21.919Z" },
    { url = "https://files.pythonhosted.org/packages/9c/12/c39ae2a4037cb10ad5eb3578eb4d5f8c1a2575c62bba675f3406b7ef0824/caio-0.9.25-cp313-cp313-manylinux_2_34_aarch64.whl", hash = "sha256:1a177d4777141b96f175fe2c37a3d96dec7911ed9ad5f02bac38aaa1c936611f", size = 81523, upload-time = "2026-03-04T22:08:25.187Z" },
    { url = "https://files.pythonhosted.org/packages/22/59/f8f2e950eb4f1a5a3883e198dca514b9d475415cb6cd7b78b9213a0dd45a/caio-0.9.25-cp313-cp313-manylinux_2_34_x86_64.whl", hash = "sha256:9ed3cfb28c0e99fec5e208c934e5c157d0866aa9c32aa4dc5e9b6034af6286b7", size = 80243, upload-time = "2026-03-04T22:08:26.449Z" },
    { url = "https://files.pythonhosted.org/packages/69/ca/a08fdc7efdcc24e6a6131a93c85be1f204d41c58f474c42b0670af8c016b/caio-0.9.25-cp314-cp314-macosx_10_15_universal2.whl", hash = "sha256:fab6078b9348e883c80a5e14b382e6ad6aabbc4429ca034e76e730cf464269db", size = 36978, upload-time = "2025-12-26T15:21:41.055Z" },
    { url = "https://files.pythonhosted.org/packages/5e/6c/d4d24f65e690213c097174d26eda6831f45f4734d9d036d81790a27e7b78/caio-0.9.25-cp314-cp314-manylinux2010_x86_64.manylinux2014_x86_64.manylinux_2_12_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:44a6b58e52d488c75cfaa5ecaa404b2b41cc965e6c417e03251e868ecd5b6d77", size = 81832, upload-time = "2025-12-26T15:22:22.757Z" },
    { url = "https://files.pythonhosted.org/packages/87/a4/e534cf7d2d0e8d880e25dd61e8d921ffcfe15bd696734589826f5a2df727/caio-0.9.25-cp314-cp314-manylinux_2_34_aarch64.whl", hash = "sha256:628a630eb7fb22381dd8e3c8ab7f59e854b9c806639811fc3f4310c6bd711d79", size = 81565, upload-time = "2026-03-04T22:08:27.483Z" },
    { url = "https://files.pythonhosted.org/packages/3f/ed/bf81aeac1d290017e5e5ac3e880fd56ee15e50a6d0353986799d1bc5cfd5/caio-0.9.25-cp314-cp314-manylinux_2_34_x86_64.whl", hash = "sha256:0ba16aa605ccb174665357fc729cf500679c2d94d5f1458a6f0d5ca48f2060a7", size = 80071, upload-time = "2026-03-04T22:08:28.751Z" },
    { url = "https://files.pythonhosted.org/packages/86/93/1f76c8d1bafe3b0614e06b2195784a3765bbf7b0a067661af9e2dd47fc33/caio-0.9.25-py3-none-any.whl", hash = "sha256:06c0bb02d6b929119b1cfbe1ca403c768b2013a369e2db46bfa2a5761cf82e40", size = 19087, upload-time = "2025-12-26T15:22:00.221Z" },
]

[[package]]
name = "certifi"
version = "2025.11.12"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/a2/8c/58f469717fa48465e4a50c014a0400602d3c437d7c0c468e17ada824da3a/certifi-2025.11.12.tar.gz", hash = "sha256:d8ab5478f2ecd78af242878415affce761ca6bc54a22a27e026d7c25357c3316", size = 160538, upload-time = "2025-11-12T02:54:51.517Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/70/7d/9bc192684cea499815ff478dfcdc13835ddf401365057044fb721ec6bddb/certifi-2025.11.12-py3-none-any.whl", hash = "sha256:97de8790030bbd5c2d96b7ec782fc2f7820ef8dba6db909ccf95449f2d062d4b", size = 159438, upload-time = "2025-11-12T02:54:49.735Z" },
]

[[package]]
name = "cffi"
version = "2.0.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "pycparser", marker = "implementation_name != 'PyPy'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/eb/56/b1ba7935a17738ae8453301356628e8147c79dbb825bcbc73dc7401f9846/cffi-2.0.0.tar.gz", hash = "sha256:44d1b5909021139fe36001ae048dbdde8214afa20200eda0f64c068cac5d5529", size = 523588, upload-time = "2025-09-08T23:24:04.541Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/93/d7/516d984057745a6cd96575eea814fe1edd6646ee6efd552fb7b0921dec83/cffi-2.0.0-cp310-cp310-macosx_10_13_x86_64.whl", hash = "sha256:0cf2d91ecc3fcc0625c2c530fe004f82c110405f101548512cce44322fa8ac44", size = 184283, upload-time = "2025-09-08T23:22:08.01Z" },
    { url = "https://files.pythonhosted.org/packages/9e/84/ad6a0b408daa859246f57c03efd28e5dd1b33c21737c2db84cae8c237aa5/cffi-2.0.0-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:f73b96c41e3b2adedc34a7356e64c8eb96e03a3782b535e043a986276ce12a49", size = 180504, upload-time = "2025-09-08T23:22:10.637Z" },
    { url = "https://files.pythonhosted.org/packages/50/bd/b1a6362b80628111e6653c961f987faa55262b4002fcec42308cad1db680/cffi-2.0.0-cp310-cp310-manylinux1_i686.manylinux2014_i686.manylinux_2_17_i686.manylinux_2_5_i686.whl", hash = "sha256:53f77cbe57044e88bbd5ed26ac1d0514d2acf0591dd6bb02a3ae37f76811b80c", size = 208811, upload-time = "2025-09-08T23:22:12.267Z" },
    { url = "https://files.pythonhosted.org/packages/4f/27/6933a8b2562d7bd1fb595074cf99cc81fc3789f6a6c05cdabb46284a3188/cffi-2.0.0-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.whl", hash = "sha256:3e837e369566884707ddaf85fc1744b47575005c0a229de3327f8f9a20f4efeb", size = 216402, upload-time = "2025-09-08T23:22:13.455Z" },
    { url = "https://files.pythonhosted.org/packages/05/eb/b86f2a2645b62adcfff53b0dd97e8dfafb5c8aa864bd0d9a2c2049a0d551/cffi-2.0.0-cp310-cp310-manylinux2014_ppc64le.manylinux_2_17_ppc64le.whl", hash = "sha256:5eda85d6d1879e692d546a078b44251cdd08dd1cfb98dfb77b670c97cee49ea0", size = 203217, upload-time = "2025-09-08T23:22:14.596Z" },
    { url = "https://files.pythonhosted.org/packages/9f/e0/6cbe77a53acf5acc7c08cc186c9928864bd7c005f9efd0d126884858a5fe/cffi-2.0.0-cp310-cp310-manylinux2014_s390x.manylinux_2_17_s390x.whl", hash = "sha256:9332088d75dc3241c702d852d4671613136d90fa6881da7d770a483fd05248b4", size = 203079, upload-time = "2025-09-08T23:22:15.769Z" },
    { url = "https://files.pythonhosted.org/packages/98/29/9b366e70e243eb3d14a5cb488dfd3a0b6b2f1fb001a203f653b93ccfac88/cffi-2.0.0-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:fc7de24befaeae77ba923797c7c87834c73648a05a4bde34b3b7e5588973a453", size = 216475, upload-time = "2025-09-08T23:22:17.427Z" },
    { url = "https://files.pythonhosted.org/packages/21/7a/13b24e70d2f90a322f2900c5d8e1f14fa7e2a6b3332b7309ba7b2ba51a5a/cffi-2.0.0-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:cf364028c016c03078a23b503f02058f1814320a56ad535686f90565636a9495", size = 218829, upload-time = "2025-09-08T23:22:19.069Z" },
    { url = "https://files.pythonhosted.org/packages/60/99/c9dc110974c59cc981b1f5b66e1d8af8af764e00f0293266824d9c4254bc/cffi-2.0.0-cp310-cp310-musllinux_1_2_i686.whl", hash = "sha256:e11e82b744887154b182fd3e7e8512418446501191994dbf9c9fc1f32cc8efd5", size = 211211, upload-time = "2025-09-08T23:22:20.588Z" },
    { url = "https://files.pythonhosted.org/packages/49/72/ff2d12dbf21aca1b32a40ed792ee6b40f6dc3a9cf1644bd7ef6e95e0ac5e/cffi-2.0.0-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:8ea985900c5c95ce9db1745f7933eeef5d314f0565b27625d9a10ec9881e1bfb", size = 218036, upload-time = "2025-09-08T23:22:22.143Z" },
    { url = "https://files.pythonhosted.org/packages/e2/cc/027d7fb82e58c48ea717149b03bcadcbdc293553edb283af792bd4bcbb3f/cffi-2.0.0-cp310-cp310-win32.whl", hash = "sha256:1f72fb8906754ac8a2cc3f9f5aaa298070652a0ffae577e0ea9bd480dc3c931a", size = 172184, upload-time = "2025-09-08T23:22:23.328Z" },
    { url = "https://files.pythonhosted.org/packages/33/fa/072dd15ae27fbb4e06b437eb6e944e75b068deb09e2a2826039e49ee2045/cffi-2.0.0-cp310-cp310-win_amd64.whl", hash = "sha256:b18a3ed7d5b3bd8d9ef7a8cb226502c6bf8308df1525e1cc676c3680e7176739", size = 182790, upload-time = "2025-09-08T23:22:24.752Z" },
    { url = "https://files.pythonhosted.org/packages/12/4a/3dfd5f7850cbf0d06dc84ba9aa00db766b52ca38d8b86e3a38314d52498c/cffi-2.0.0-cp311-cp311-macosx_10_13_x86_64.whl", hash = "sha256:b4c854ef3adc177950a8dfc81a86f5115d2abd545751a304c5bcf2c2c7283cfe", size = 184344, upload-time = "2025-09-08T23:22:26.456Z" },
    { url = "https://files.pythonhosted.org/packages/4f/8b/f0e4c441227ba756aafbe78f117485b25bb26b1c059d01f137fa6d14896b/cffi-2.0.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:2de9a304e27f7596cd03d16f1b7c72219bd944e99cc52b84d0145aefb07cbd3c", size = 180560, upload-time = "2025-09-08T23:22:28.197Z" },
    { url = "https://files.pythonhosted.org/packages/b1/b7/1200d354378ef52ec227395d95c2576330fd22a869f7a70e88e1447eb234/cffi-2.0.0-cp311-cp311-manylinux1_i686.manylinux2014_i686.manylinux_2_17_i686.manylinux_2_5_i686.whl", hash = "sha256:baf5215e0ab74c16e2dd324e8ec067ef59e41125d3eade2b863d294fd5035c92", size = 209613, upload-time = "2025-09-08T23:22:29.475Z" },
    { url = "https://files.pythonhosted.org/packages/b8/56/6033f5e86e8cc9bb629f0077ba71679508bdf54a9a5e112a3c0b91870332/cffi-2.0.0-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.whl", hash = "sha256:730cacb21e1bdff3ce90babf007d0a0917cc3e6492f336c2f0134101e0944f93", size = 216476, upload-time = "2025-09-08T23:22:31.063Z" },
    { url = "https://files.pythonhosted.org/packages/dc/7f/55fecd70f7ece178db2f26128ec41430d8720f2d12ca97bf8f0a628207d5/cffi-2.0.0-cp311-cp311-manylinux2014_ppc64le.manylinux_2_17_ppc64le.whl", hash = "sha256:6824f87845e3396029f3820c206e459ccc91760e8fa24422f8b0c3d1731cbec5", size = 203374, upload-time = "2025-09-08T23:22:32.507Z" },
    { url = "https://files.pythonhosted.org/packages/84/ef/a7b77c8bdc0f77adc3b46888f1ad54be8f3b7821697a7b89126e829e676a/cffi-2.0.0-cp311-cp311-manylinux2014_s390x.manylinux_2_17_s390x.whl", hash = "sha256:9de40a7b0323d889cf8d23d1ef214f565ab154443c42737dfe52ff82cf857664", size = 202597, upload-time = "2025-09-08T23:22:34.132Z" },
    { url = "https://files.pythonhosted.org/packages/d7/91/500d892b2bf36529a75b77958edfcd5ad8e2ce4064ce2ecfeab2125d72d1/cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:8941aaadaf67246224cee8c3803777eed332a19d909b47e29c9842ef1e79ac26", size = 215574, upload-time = "2025-09-08T23:22:35.443Z" },
    { url = "https://files.pythonhosted.org/packages/44/64/58f6255b62b101093d5df22dcb752596066c7e89dd725e0afaed242a61be/cffi-2.0.0-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:a05d0c237b3349096d3981b727493e22147f934b20f6f125a3eba8f994bec4a9", size = 218971, upload-time = "2025-09-08T23:22:36.805Z" },
    { url = "https://files.pythonhosted.org/packages/ab/49/fa72cebe2fd8a55fbe14956f9970fe8eb1ac59e5df042f603ef7c8ba0adc/cffi-2.0.0-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:94698a9c5f91f9d138526b48fe26a199609544591f859c870d477351dc7b2414", size = 211972, upload-time = "2025-09-08T23:22:38.436Z" },
    { url = "https://files.pythonhosted.org/packages/0b/28/dd0967a76aab36731b6ebfe64dec4e981aff7e0608f60c2d46b46982607d/cffi-2.0.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:5fed36fccc0612a53f1d4d9a816b50a36702c28a2aa880cb8a122b3466638743", size = 217078, upload-time = "2025-09-08T23:22:39.776Z" },
    { url = "https://files.pythonhosted.org/packages/2b/c0/015b25184413d7ab0a410775fdb4a50fca20f5589b5dab1dbbfa3baad8ce/cffi-2.0.0-cp311-cp311-win32.whl", hash = "sha256:c649e3a33450ec82378822b3dad03cc228b8f5963c0c12fc3b1e0ab940f768a5", size = 172076, upload-time = "2025-09-08T23:22:40.95Z" },
    { url = "https://files.pythonhosted.org/packages/ae/8f/dc5531155e7070361eb1b7e4c1a9d896d0cb21c49f807a6c03fd63fc877e/cffi-2.0.0-cp311-cp311-win_amd64.whl", hash = "sha256:66f011380d0e49ed280c789fbd08ff0d40968ee7b665575489afa95c98196ab5", size = 182820, upload-time = "2025-09-08T23:22:42.463Z" },
    { url = "https://files.pythonhosted.org/packages/95/5c/1b493356429f9aecfd56bc171285a4c4ac8697f76e9bbbbb105e537853a1/cffi-2.0.0-cp311-cp311-win_arm64.whl", hash = "sha256:c6638687455baf640e37344fe26d37c404db8b80d037c3d29f58fe8d1c3b194d", size = 177635, upload-time = "2025-09-08T23:22:43.623Z" },
    { url = "https://files.pythonhosted.org/packages/ea/47/4f61023ea636104d4f16ab488e268b93008c3d0bb76893b1b31db1f96802/cffi-2.0.0-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:6d02d6655b0e54f54c4ef0b94eb6be0607b70853c45ce98bd278dc7de718be5d", size = 185271, upload-time = "2025-09-08T23:22:44.795Z" },
    { url = "https://files.pythonhosted.org/packages/df/a2/781b623f57358e360d62cdd7a8c681f074a71d445418a776eef0aadb4ab4/cffi-2.0.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:8eca2a813c1cb7ad4fb74d368c2ffbbb4789d377ee5bb8df98373c2cc0dee76c", size = 181048, upload-time = "2025-09-08T23:22:45.938Z" },
    { url = "https://files.pythonhosted.org/packages/ff/df/a4f0fbd47331ceeba3d37c2e51e9dfc9722498becbeec2bd8bc856c9538a/cffi-2.0.0-cp312-cp312-manylinux1_i686.manylinux2014_i686.manylinux_2_17_i686.manylinux_2_5_i686.whl", hash = "sha256:21d1152871b019407d8ac3985f6775c079416c282e431a4da6afe7aefd2bccbe", size = 212529, upload-time = "2025-09-08T23:22:47.349Z" },
    { url = "https://files.pythonhosted.org/packages/d5/72/12b5f8d3865bf0f87cf1404d8c374e7487dcf097a1c91c436e72e6badd83/cffi-2.0.0-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.whl", hash = "sha256:b21e08af67b8a103c71a250401c78d5e0893beff75e28c53c98f4de42f774062", size = 220097, upload-time = "2025-09-08T23:22:48.677Z" },
    { url = "https://files.pythonhosted.org/packages/c2/95/7a135d52a50dfa7c882ab0ac17e8dc11cec9d55d2c18dda414c051c5e69e/cffi-2.0.0-cp312-cp312-manylinux2014_ppc64le.manylinux_2_17_ppc64le.whl", hash = "sha256:1e3a615586f05fc4065a8b22b8152f0c1b00cdbc60596d187c2a74f9e3036e4e", size = 207983, upload-time = "2025-09-08T23:22:50.06Z" },
    { url = "https://files.pythonhosted.org/packages/3a/c8/15cb9ada8895957ea171c62dc78ff3e99159ee7adb13c0123c001a2546c1/cffi-2.0.0-cp312-cp312-manylinux2014_s390x.manylinux_2_17_s390x.whl", hash = "sha256:81afed14892743bbe14dacb9e36d9e0e504cd204e0b165062c488942b9718037", size = 206519, upload-time = "2025-09-08T23:22:51.364Z" },
    { url = "https://files.pythonhosted.org/packages/78/2d/7fa73dfa841b5ac06c7b8855cfc18622132e365f5b81d02230333ff26e9e/cffi-2.0.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:3e17ed538242334bf70832644a32a7aae3d83b57567f9fd60a26257e992b79ba", size = 219572, upload-time = "2025-09-08T23:22:52.902Z" },
    { url = "https://files.pythonhosted.org/packages/07/e0/267e57e387b4ca276b90f0434ff88b2c2241ad72b16d31836adddfd6031b/cffi-2.0.0-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:3925dd22fa2b7699ed2617149842d2e6adde22b262fcbfada50e3d195e4b3a94", size = 222963, upload-time = "2025-09-08T23:22:54.518Z" },
    { url = "https://files.pythonhosted.org/packages/b6/75/1f2747525e06f53efbd878f4d03bac5b859cbc11c633d0fb81432d98a795/cffi-2.0.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:2c8f814d84194c9ea681642fd164267891702542f028a15fc97d4674b6206187", size = 221361, upload-time = "2025-09-08T23:22:55.867Z" },
    { url = "https://files.pythonhosted.org/packages/7b/2b/2b6435f76bfeb6bbf055596976da087377ede68df465419d192acf00c437/cffi-2.0.0-cp312-cp312-win32.whl", hash = "sha256:da902562c3e9c550df360bfa53c035b2f241fed6d9aef119048073680ace4a18", size = 172932, upload-time = "2025-09-08T23:22:57.188Z" },
    { url = "https://files.pythonhosted.org/packages/f8/ed/13bd4418627013bec4ed6e54283b1959cf6db888048c7cf4b4c3b5b36002/cffi-2.0.0-cp312-cp312-win_amd64.whl", hash = "sha256:da68248800ad6320861f129cd9c1bf96ca849a2771a59e0344e88681905916f5", size = 183557, upload-time = "2025-09-08T23:22:58.351Z" },
    { url = "https://files.pythonhosted.org/packages/95/31/9f7f93ad2f8eff1dbc1c3656d7ca5bfd8fb52c9d786b4dcf19b2d02217fa/cffi-2.0.0-cp312-cp312-win_arm64.whl", hash = "sha256:4671d9dd5ec934cb9a73e7ee9676f9362aba54f7f34910956b84d727b0d73fb6", size = 177762, upload-time = "2025-09-08T23:22:59.668Z" },
    { url = "https://files.pythonhosted.org/packages/4b/8d/a0a47a0c9e413a658623d014e91e74a50cdd2c423f7ccfd44086ef767f90/cffi-2.0.0-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:00bdf7acc5f795150faa6957054fbbca2439db2f775ce831222b66f192f03beb", size = 185230, upload-time = "2025-09-08T23:23:00.879Z" },
    { url = "https://files.pythonhosted.org/packages/4a/d2/a6c0296814556c68ee32009d9c2ad4f85f2707cdecfd7727951ec228005d/cffi-2.0.0-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:45d5e886156860dc35862657e1494b9bae8dfa63bf56796f2fb56e1679fc0bca", size = 181043, upload-time = "2025-09-08T23:23:02.231Z" },
    { url = "https://files.pythonhosted.org/packages/b0/1e/d22cc63332bd59b06481ceaac49d6c507598642e2230f201649058a7e704/cffi-2.0.0-cp313-cp313-manylinux1_i686.manylinux2014_i686.manylinux_2_17_i686.manylinux_2_5_i686.whl", hash = "sha256:07b271772c100085dd28b74fa0cd81c8fb1a3ba18b21e03d7c27f3436a10606b", size = 212446, upload-time = "2025-09-08T23:23:03.472Z" },
    { url = "https://files.pythonhosted.org/packages/a9/f5/a2c23eb03b61a0b8747f211eb716446c826ad66818ddc7810cc2cc19b3f2/cffi-2.0.0-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.whl", hash = "sha256:d48a880098c96020b02d5a1f7d9251308510ce8858940e6fa99ece33f610838b", size = 220101, upload-time = "2025-09-08T23:23:04.792Z" },
    { url = "https://files.pythonhosted.org/packages/f2/7f/e6647792fc5850d634695bc0e6ab4111ae88e89981d35ac269956605feba/cffi-2.0.0-cp313-cp313-manylinux2014_ppc64le.manylinux_2_17_ppc64le.whl", hash = "sha256:f93fd8e5c8c0a4aa1f424d6173f14a892044054871c771f8566e4008eaa359d2", size = 207948, upload-time = "2025-09-08T23:23:06.127Z" },
    { url = "https://files.pythonhosted.org/packages/cb/1e/a5a1bd6f1fb30f22573f76533de12a00bf274abcdc55c8edab639078abb6/cffi-2.0.0-cp313-cp313-manylinux2014_s390x.manylinux_2_17_s390x.whl", hash = "sha256:dd4f05f54a52fb558f1ba9f528228066954fee3ebe629fc1660d874d040ae5a3", size = 206422, upload-time = "2025-09-08T23:23:07.753Z" },
    { url = "https://files.pythonhosted.org/packages/98/df/0a1755e750013a2081e863e7cd37e0cdd02664372c754e5560099eb7aa44/cffi-2.0.0-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:c8d3b5532fc71b7a77c09192b4a5a200ea992702734a2e9279a37f2478236f26", size = 219499, upload-time = "2025-09-08T23:23:09.648Z" },
    { url = "https://files.pythonhosted.org/packages/50/e1/a969e687fcf9ea58e6e2a928ad5e2dd88cc12f6f0ab477e9971f2309b57c/cffi-2.0.0-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:d9b29c1f0ae438d5ee9acb31cadee00a58c46cc9c0b2f9038c6b0b3470877a8c", size = 222928, upload-time = "2025-09-08T23:23:10.928Z" },
    { url = "https://files.pythonhosted.org/packages/36/54/0362578dd2c9e557a28ac77698ed67323ed5b9775ca9d3fe73fe191bb5d8/cffi-2.0.0-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:6d50360be4546678fc1b79ffe7a66265e28667840010348dd69a314145807a1b", size = 221302, upload-time = "2025-09-08T23:23:12.42Z" },
    { url = "https://files.pythonhosted.org/packages/eb/6d/bf9bda840d5f1dfdbf0feca87fbdb64a918a69bca42cfa0ba7b137c48cb8/cffi-2.0.0-cp313-cp313-win32.whl", hash = "sha256:74a03b9698e198d47562765773b4a8309919089150a0bb17d829ad7b44b60d27", size = 172909, upload-time = "2025-09-08T23:23:14.32Z" },
    { url = "https://files.pythonhosted.org/packages/37/18/6519e1ee6f5a1e579e04b9ddb6f1676c17368a7aba48299c3759bbc3c8b3/cffi-2.0.0-cp313-cp313-win_amd64.whl", hash = "sha256:19f705ada2530c1167abacb171925dd886168931e0a7b78f5bffcae5c6b5be75", size = 183402, upload-time = "2025-09-08T23:23:15.535Z" },
    { url = "https://files.pythonhosted.org/packages/cb/0e/02ceeec9a7d6ee63bb596121c2c8e9b3a9e150936f4fbef6ca1943e6137c/cffi-2.0.0-cp313-cp313-win_arm64.whl", hash = "sha256:256f80b80ca3853f90c21b23ee78cd008713787b1b1e93eae9f3d6a7134abd91", size = 177780, upload-time = "2025-09-08T23:23:16.761Z" },
    { url = "https://files.pythonhosted.org/packages/92/c4/3ce07396253a83250ee98564f8d7e9789fab8e58858f35d07a9a2c78de9f/cffi-2.0.0-cp314-cp314-macosx_10_13_x86_64.whl", hash = "sha256:fc33c5141b55ed366cfaad382df24fe7dcbc686de5be719b207bb248e3053dc5", size = 185320, upload-time = "2025-09-08T23:23:18.087Z" },
    { url = "https://files.pythonhosted.org/packages/59/dd/27e9fa567a23931c838c6b02d0764611c62290062a6d4e8ff7863daf9730/cffi-2.0.0-cp314-cp314-macosx_11_0_arm64.whl", hash = "sha256:c654de545946e0db659b3400168c9ad31b5d29593291482c43e3564effbcee13", size = 181487, upload-time = "2025-09-08T23:23:19.622Z" },
    { url = "https://files.pythonhosted.org/packages/d6/43/0e822876f87ea8a4ef95442c3d766a06a51fc5298823f884ef87aaad168c/cffi-2.0.0-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.whl", hash = "sha256:24b6f81f1983e6df8db3adc38562c83f7d4a0c36162885ec7f7b77c7dcbec97b", size = 220049, upload-time = "2025-09-08T23:23:20.853Z" },
    { url = "https://files.pythonhosted.org/packages/b4/89/76799151d9c2d2d1ead63c2429da9ea9d7aac304603de0c6e8764e6e8e70/cffi-2.0.0-cp314-cp314-manylinux2014_ppc64le.manylinux_2_17_ppc64le.whl", hash = "sha256:12873ca6cb9b0f0d3a0da705d6086fe911591737a59f28b7936bdfed27c0d47c", size = 207793, upload-time = "2025-09-08T23:23:22.08Z" },
    { url = "https://files.pythonhosted.org/packages/bb/dd/3465b14bb9e24ee24cb88c9e3730f6de63111fffe513492bf8c808a3547e/cffi-2.0.0-cp314-cp314-manylinux2014_s390x.manylinux_2_17_s390x.whl", hash = "sha256:d9b97165e8aed9272a6bb17c01e3cc5871a594a446ebedc996e2397a1c1ea8ef", size = 206300, upload-time = "2025-09-08T23:23:23.314Z" },
    { url = "https://files.pythonhosted.org/packages/47/d9/d83e293854571c877a92da46fdec39158f8d7e68da75bf73581225d28e90/cffi-2.0.0-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:afb8db5439b81cf9c9d0c80404b60c3cc9c3add93e114dcae767f1477cb53775", size = 219244, upload-time = "2025-09-08T23:23:24.541Z" },
    { url = "https://files.pythonhosted.org/packages/2b/0f/1f177e3683aead2bb00f7679a16451d302c436b5cbf2505f0ea8146ef59e/cffi-2.0.0-cp314-cp314-musllinux_1_2_aarch64.whl", hash = "sha256:737fe7d37e1a1bffe70bd5754ea763a62a066dc5913ca57e957824b72a85e205", size = 222828, upload-time = "2025-09-08T23:23:26.143Z" },
    { url = "https://files.pythonhosted.org/packages/c6/0f/cafacebd4b040e3119dcb32fed8bdef8dfe94da653155f9d0b9dc660166e/cffi-2.0.0-cp314-cp314-musllinux_1_2_x86_64.whl", hash = "sha256:38100abb9d1b1435bc4cc340bb4489635dc2f0da7456590877030c9b3d40b0c1", size = 220926, upload-time = "2025-09-08T23:23:27.873Z" },
    { url = "https://files.pythonhosted.org/packages/3e/aa/df335faa45b395396fcbc03de2dfcab242cd61a9900e914fe682a59170b1/cffi-2.0.0-cp314-cp314-win32.whl", hash = "sha256:087067fa8953339c723661eda6b54bc98c5625757ea62e95eb4898ad5e776e9f", size = 175328, upload-time = "2025-09-08T23:23:44.61Z" },
    { url = "https://files.pythonhosted.org/packages/bb/92/882c2d30831744296ce713f0feb4c1cd30f346ef747b530b5318715cc367/cffi-2.0.0-cp314-cp314-win_amd64.whl", hash = "sha256:203a48d1fb583fc7d78a4c6655692963b860a417c0528492a6bc21f1aaefab25", size = 185650, upload-time = "2025-09-08T23:23:45.848Z" },
    { url = "https://files.pythonhosted.org/packages/9f/2c/98ece204b9d35a7366b5b2c6539c350313ca13932143e79dc133ba757104/cffi-2.0.0-cp314-cp314-win_arm64.whl", hash = "sha256:dbd5c7a25a7cb98f5ca55d258b103a2054f859a46ae11aaf23134f9cc0d356ad", size = 180687, upload-time = "2025-09-08T23:23:47.105Z" },
    { url = "https://files.pythonhosted.org/packages/3e/61/c768e4d548bfa607abcda77423448df8c471f25dbe64fb2ef6d555eae006/cffi-2.0.0-cp314-cp314t-macosx_10_13_x86_64.whl", hash = "sha256:9a67fc9e8eb39039280526379fb3a70023d77caec1852002b4da7e8b270c4dd9", size = 188773, upload-time = "2025-09-08T23:23:29.347Z" },
    { url = "https://files.pythonhosted.org/packages/2c/ea/5f76bce7cf6fcd0ab1a1058b5af899bfbef198bea4d5686da88471ea0336/cffi-2.0.0-cp314-cp314t-macosx_11_0_arm64.whl", hash = "sha256:7a66c7204d8869299919db4d5069a82f1561581af12b11b3c9f48c584eb8743d", size = 185013, upload-time = "2025-09-08T23:23:30.63Z" },
    { url = "https://files.pythonhosted.org/packages/be/b4/c56878d0d1755cf9caa54ba71e5d049479c52f9e4afc230f06822162ab2f/cffi-2.0.0-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.whl", hash = "sha256:7cc09976e8b56f8cebd752f7113ad07752461f48a58cbba644139015ac24954c", size = 221593, upload-time = "2025-09-08T23:23:31.91Z" },
    { url = "https://files.pythonhosted.org/packages/e0/0d/eb704606dfe8033e7128df5e90fee946bbcb64a04fcdaa97321309004000/cffi-2.0.0-cp314-cp314t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.whl", hash = "sha256:92b68146a71df78564e4ef48af17551a5ddd142e5190cdf2c5624d0c3ff5b2e8", size = 209354, upload-time = "2025-09-08T23:23:33.214Z" },
    { url = "https://files.pythonhosted.org/packages/d8/19/3c435d727b368ca475fb8742ab97c9cb13a0de600ce86f62eab7fa3eea60/cffi-2.0.0-cp314-cp314t-manylinux2014_s390x.manylinux_2_17_s390x.whl", hash = "sha256:b1e74d11748e7e98e2f426ab176d4ed720a64412b6a15054378afdb71e0f37dc", size = 208480, upload-time = "2025-09-08T23:23:34.495Z" },
    { url = "https://files.pythonhosted.org/packages/d0/44/681604464ed9541673e486521497406fadcc15b5217c3e326b061696899a/cffi-2.0.0-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:28a3a209b96630bca57cce802da70c266eb08c6e97e5afd61a75611ee6c64592", size = 221584, upload-time = "2025-09-08T23:23:36.096Z" },
    { url = "https://files.pythonhosted.org/packages/25/8e/342a504ff018a2825d395d44d63a767dd8ebc927ebda557fecdaca3ac33a/cffi-2.0.0-cp314-cp314t-musllinux_1_2_aarch64.whl", hash = "sha256:7553fb2090d71822f02c629afe6042c299edf91ba1bf94951165613553984512", size = 224443, upload-time = "2025-09-08T23:23:37.328Z" },
    { url = "https://files.pythonhosted.org/packages/e1/5e/b666bacbbc60fbf415ba9988324a132c9a7a0448a9a8f125074671c0f2c3/cffi-2.0.0-cp314-cp314t-musllinux_1_2_x86_64.whl", hash = "sha256:6c6c373cfc5c83a975506110d17457138c8c63016b563cc9ed6e056a82f13ce4", size = 223437, upload-time = "2025-09-08T23:23:38.945Z" },
    { url = "https://files.pythonhosted.org/packages/a0/1d/ec1a60bd1a10daa292d3cd6bb0b359a81607154fb8165f3ec95fe003b85c/cffi-2.0.0-cp314-cp314t-win32.whl", hash = "sha256:1fc9ea04857caf665289b7a75923f2c6ed559b8298a1b8c49e59f7dd95c8481e", size = 180487, upload-time = "2025-09-08T23:23:40.423Z" },
    { url = "https://files.pythonhosted.org/packages/bf/41/4c1168c74fac325c0c8156f04b6749c8b6a8f405bbf91413ba088359f60d/cffi-2.0.0-cp314-cp314t-win_amd64.whl", hash = "sha256:d68b6cef7827e8641e8ef16f4494edda8b36104d79773a334beaa1e3521430f6", size = 191726, upload-time = "2025-09-08T23:23:41.742Z" },
    { url = "https://files.pythonhosted.org/packages/ae/3a/dbeec9d1ee0844c679f6bb5d6ad4e9f198b1224f4e7a32825f47f6192b0c/cffi-2.0.0-cp314-cp314t-win_arm64.whl", hash = "sha256:0a1527a803f0a659de1af2e1fd700213caba79377e27e4693648c2923da066f9", size = 184195, upload-time = "2025-09-08T23:23:43.004Z" },
]

[[package]]
name = "click"
version = "8.3.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "colorama", marker = "sys_platform == 'win32'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/3d/fa/656b739db8587d7b5dfa22e22ed02566950fbfbcdc20311993483657a5c0/click-8.3.1.tar.gz", hash = "sha256:12ff4785d337a1bb490bb7e9c2b1ee5da3112e94a8622f26a6c77f5d2fc6842a", size = 295065, upload-time = "2025-11-15T20:45:42.706Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/98/78/01c019cdb5d6498122777c1a43056ebb3ebfeef2076d9d026bfe15583b2b/click-8.3.1-py3-none-any.whl", hash = "sha256:981153a64e25f12d547d3426c367a4857371575ee7ad18df2a6183ab0545b2a6", size = 108274, upload-time = "2025-11-15T20:45:41.139Z" },
]

[[package]]
name = "colorama"
version = "0.4.6"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/d8/53/6f443c9a4a8358a93a6792e2acffb9d9d5cb0a5cfd8802644b7b1c9a02e4/colorama-0.4.6.tar.gz", hash = "sha256:08695f5cb7ed6e0531a20572697297273c47b8cae5a63ffc6d6ed5c201be6e44", size = 27697, upload-time = "2022-10-25T02:36:22.414Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/d1/d6/3965ed04c63042e047cb6a3e6ed1a63a35087b6a609aa3a15ed8ac56c221/colorama-0.4.6-py2.py3-none-any.whl", hash = "sha256:4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6", size = 25335, upload-time = "2022-10-25T02:36:20.889Z" },
]

[[package]]
name = "cryptography"
version = "46.0.3"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "cffi", marker = "platform_python_implementation != 'PyPy'" },
    { name = "typing-extensions", marker = "python_full_version < '3.11'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/9f/33/c00162f49c0e2fe8064a62cb92b93e50c74a72bc370ab92f86112b33ff62/cryptography-46.0.3.tar.gz", hash = "sha256:a8b17438104fed022ce745b362294d9ce35b4c2e45c1d958ad4a4b019285f4a1", size = 749258, upload-time = "2025-10-15T23:18:31.74Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/1d/42/9c391dd801d6cf0d561b5890549d4b27bafcc53b39c31a817e69d87c625b/cryptography-46.0.3-cp311-abi3-macosx_10_9_universal2.whl", hash = "sha256:109d4ddfadf17e8e7779c39f9b18111a09efb969a301a31e987416a0191ed93a", size = 7225004, upload-time = "2025-10-15T23:16:52.239Z" },
    { url = "https://files.pythonhosted.org/packages/1c/67/38769ca6b65f07461eb200e85fc1639b438bdc667be02cf7f2cd6a64601c/cryptography-46.0.3-cp311-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl", hash = "sha256:09859af8466b69bc3c27bdf4f5d84a665e0f7ab5088412e9e2ec49758eca5cbc", size = 4296667, upload-time = "2025-10-15T23:16:54.369Z" },
    { url = "https://files.pythonhosted.org/packages/5c/49/498c86566a1d80e978b42f0d702795f69887005548c041636df6ae1ca64c/cryptography-46.0.3-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:01ca9ff2885f3acc98c29f1860552e37f6d7c7d013d7334ff2a9de43a449315d", size = 4450807, upload-time = "2025-10-15T23:16:56.414Z" },
    { url = "https://files.pythonhosted.org/packages/4b/0a/863a3604112174c8624a2ac3c038662d9e59970c7f926acdcfaed8d61142/cryptography-46.0.3-cp311-abi3-manylinux_2_28_aarch64.whl", hash = "sha256:6eae65d4c3d33da080cff9c4ab1f711b15c1d9760809dad6ea763f3812d254cb", size = 4299615, upload-time = "2025-10-15T23:16:58.442Z" },
    { url = "https://files.pythonhosted.org/packages/64/02/b73a533f6b64a69f3cd3872acb6ebc12aef924d8d103133bb3ea750dc703/cryptography-46.0.3-cp311-abi3-manylinux_2_28_armv7l.manylinux_2_31_armv7l.whl", hash = "sha256:e5bf0ed4490068a2e72ac03d786693adeb909981cc596425d09032d372bcc849", size = 4016800, upload-time = "2025-10-15T23:17:00.378Z" },
    { url = "https://files.pythonhosted.org/packages/25/d5/16e41afbfa450cde85a3b7ec599bebefaef16b5c6ba4ec49a3532336ed72/cryptography-46.0.3-cp311-abi3-manylinux_2_28_ppc64le.whl", hash = "sha256:5ecfccd2329e37e9b7112a888e76d9feca2347f12f37918facbb893d7bb88ee8", size = 4984707, upload-time = "2025-10-15T23:17:01.98Z" },
    { url = "https://files.pythonhosted.org/packages/c9/56/e7e69b427c3878352c2fb9b450bd0e19ed552753491d39d7d0a2f5226d41/cryptography-46.0.3-cp311-abi3-manylinux_2_28_x86_64.whl", hash = "sha256:a2c0cd47381a3229c403062f764160d57d4d175e022c1df84e168c6251a22eec", size = 4482541, upload-time = "2025-10-15T23:17:04.078Z" },
    { url = "https://files.pythonhosted.org/packages/78/f6/50736d40d97e8483172f1bb6e698895b92a223dba513b0ca6f06b2365339/cryptography-46.0.3-cp311-abi3-manylinux_2_34_aarch64.whl", hash = "sha256:549e234ff32571b1f4076ac269fcce7a808d3bf98b76c8dd560e42dbc66d7d91", size = 4299464, upload-time = "2025-10-15T23:17:05.483Z" },
    { url = "https://files.pythonhosted.org/packages/00/de/d8e26b1a855f19d9994a19c702fa2e93b0456beccbcfe437eda00e0701f2/cryptography-46.0.3-cp311-abi3-manylinux_2_34_ppc64le.whl", hash = "sha256:c0a7bb1a68a5d3471880e264621346c48665b3bf1c3759d682fc0864c540bd9e", size = 4950838, upload-time = "2025-10-15T23:17:07.425Z" },
    { url = "https://files.pythonhosted.org/packages/8f/29/798fc4ec461a1c9e9f735f2fc58741b0daae30688f41b2497dcbc9ed1355/cryptography-46.0.3-cp311-abi3-manylinux_2_34_x86_64.whl", hash = "sha256:10b01676fc208c3e6feeb25a8b83d81767e8059e1fe86e1dc62d10a3018fa926", size = 4481596, upload-time = "2025-10-15T23:17:09.343Z" },
    { url = "https://files.pythonhosted.org/packages/15/8d/03cd48b20a573adfff7652b76271078e3045b9f49387920e7f1f631d125e/cryptography-46.0.3-cp311-abi3-musllinux_1_2_aarch64.whl", hash = "sha256:0abf1ffd6e57c67e92af68330d05760b7b7efb243aab8377e583284dbab72c71", size = 4426782, upload-time = "2025-10-15T23:17:11.22Z" },
    { url = "https://files.pythonhosted.org/packages/fa/b1/ebacbfe53317d55cf33165bda24c86523497a6881f339f9aae5c2e13e57b/cryptography-46.0.3-cp311-abi3-musllinux_1_2_x86_64.whl", hash = "sha256:a04bee9ab6a4da801eb9b51f1b708a1b5b5c9eb48c03f74198464c66f0d344ac", size = 4698381, upload-time = "2025-10-15T23:17:12.829Z" },
    { url = "https://files.pythonhosted.org/packages/96/92/8a6a9525893325fc057a01f654d7efc2c64b9de90413adcf605a85744ff4/cryptography-46.0.3-cp311-abi3-win32.whl", hash = "sha256:f260d0d41e9b4da1ed1e0f1ce571f97fe370b152ab18778e9e8f67d6af432018", size = 3055988, upload-time = "2025-10-15T23:17:14.65Z" },
    { url = "https://files.pythonhosted.org/packages/7e/bf/80fbf45253ea585a1e492a6a17efcb93467701fa79e71550a430c5e60df0/cryptography-46.0.3-cp311-abi3-win_amd64.whl", hash = "sha256:a9a3008438615669153eb86b26b61e09993921ebdd75385ddd748702c5adfddb", size = 3514451, upload-time = "2025-10-15T23:17:16.142Z" },
    { url = "https://files.pythonhosted.org/packages/2e/af/9b302da4c87b0beb9db4e756386a7c6c5b8003cd0e742277888d352ae91d/cryptography-46.0.3-cp311-abi3-win_arm64.whl", hash = "sha256:5d7f93296ee28f68447397bf5198428c9aeeab45705a55d53a6343455dcb2c3c", size = 2928007, upload-time = "2025-10-15T23:17:18.04Z" },
    { url = "https://files.pythonhosted.org/packages/f5/e2/a510aa736755bffa9d2f75029c229111a1d02f8ecd5de03078f4c18d91a3/cryptography-46.0.3-cp314-cp314t-macosx_10_9_universal2.whl", hash = "sha256:00a5e7e87938e5ff9ff5447ab086a5706a957137e6e433841e9d24f38a065217", size = 7158012, upload-time = "2025-10-15T23:17:19.982Z" },
    { url = "https://files.pythonhosted.org/packages/73/dc/9aa866fbdbb95b02e7f9d086f1fccfeebf8953509b87e3f28fff927ff8a0/cryptography-46.0.3-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.whl", hash = "sha256:c8daeb2d2174beb4575b77482320303f3d39b8e81153da4f0fb08eb5fe86a6c5", size = 4288728, upload-time = "2025-10-15T23:17:21.527Z" },
    { url = "https://files.pythonhosted.org/packages/c5/fd/bc1daf8230eaa075184cbbf5f8cd00ba9db4fd32d63fb83da4671b72ed8a/cryptography-46.0.3-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:39b6755623145ad5eff1dab323f4eae2a32a77a7abef2c5089a04a3d04366715", size = 4435078, upload-time = "2025-10-15T23:17:23.042Z" },
    { url = "https://files.pythonhosted.org/packages/82/98/d3bd5407ce4c60017f8ff9e63ffee4200ab3e23fe05b765cab805a7db008/cryptography-46.0.3-cp314-cp314t-manylinux_2_28_aarch64.whl", hash = "sha256:db391fa7c66df6762ee3f00c95a89e6d428f4d60e7abc8328f4fe155b5ac6e54", size = 4293460, upload-time = "2025-10-15T23:17:24.885Z" },
    { url = "https://files.pythonhosted.org/packages/26/e9/e23e7900983c2b8af7a08098db406cf989d7f09caea7897e347598d4cd5b/cryptography-46.0.3-cp314-cp314t-manylinux_2_28_armv7l.manylinux_2_31_armv7l.whl", hash = "sha256:78a97cf6a8839a48c49271cdcbd5cf37ca2c1d6b7fdd86cc864f302b5e9bf459", size = 3995237, upload-time = "2025-10-15T23:17:26.449Z" },
    { url = "https://files.pythonhosted.org/packages/91/15/af68c509d4a138cfe299d0d7ddb14afba15233223ebd933b4bbdbc7155d3/cryptography-46.0.3-cp314-cp314t-manylinux_2_28_ppc64le.whl", hash = "sha256:dfb781ff7eaa91a6f7fd41776ec37c5853c795d3b358d4896fdbb5df168af422", size = 4967344, upload-time = "2025-10-15T23:17:28.06Z" },
    { url = "https://files.pythonhosted.org/packages/ca/e3/8643d077c53868b681af077edf6b3cb58288b5423610f21c62aadcbe99f4/cryptography-46.0.3-cp314-cp314t-manylinux_2_28_x86_64.whl", hash = "sha256:6f61efb26e76c45c4a227835ddeae96d83624fb0d29eb5df5b96e14ed1a0afb7", size = 4466564, upload-time = "2025-10-15T23:17:29.665Z" },
    { url = "https://files.pythonhosted.org/packages/0e/43/c1e8726fa59c236ff477ff2b5dc071e54b21e5a1e51aa2cee1676f1c986f/cryptography-46.0.3-cp314-cp314t-manylinux_2_34_aarch64.whl", hash = "sha256:23b1a8f26e43f47ceb6d6a43115f33a5a37d57df4ea0ca295b780ae8546e8044", size = 4292415, upload-time = "2025-10-15T23:17:31.686Z" },
    { url = "https://files.pythonhosted.org/packages/42/f9/2f8fefdb1aee8a8e3256a0568cffc4e6d517b256a2fe97a029b3f1b9fe7e/cryptography-46.0.3-cp314-cp314t-manylinux_2_34_ppc64le.whl", hash = "sha256:b419ae593c86b87014b9be7396b385491ad7f320bde96826d0dd174459e54665", size = 4931457, upload-time = "2025-10-15T23:17:33.478Z" },
    { url = "https://files.pythonhosted.org/packages/79/30/9b54127a9a778ccd6d27c3da7563e9f2d341826075ceab89ae3b41bf5be2/cryptography-46.0.3-cp314-cp314t-manylinux_2_34_x86_64.whl", hash = "sha256:50fc3343ac490c6b08c0cf0d704e881d0d660be923fd3076db3e932007e726e3", size = 4466074, upload-time = "2025-10-15T23:17:35.158Z" },
    { url = "https://files.pythonhosted.org/packages/ac/68/b4f4a10928e26c941b1b6a179143af9f4d27d88fe84a6a3c53592d2e76bf/cryptography-46.0.3-cp314-cp314t-musllinux_1_2_aarch64.whl", hash = "sha256:22d7e97932f511d6b0b04f2bfd818d73dcd5928db509460aaf48384778eb6d20", size = 4420569, upload-time = "2025-10-15T23:17:37.188Z" },
    { url = "https://files.pythonhosted.org/packages/a3/49/3746dab4c0d1979888f125226357d3262a6dd40e114ac29e3d2abdf1ec55/cryptography-46.0.3-cp314-cp314t-musllinux_1_2_x86_64.whl", hash = "sha256:d55f3dffadd674514ad19451161118fd010988540cee43d8bc20675e775925de", size = 4681941, upload-time = "2025-10-15T23:17:39.236Z" },
    { url = "https://files.pythonhosted.org/packages/fd/30/27654c1dbaf7e4a3531fa1fc77986d04aefa4d6d78259a62c9dc13d7ad36/cryptography-46.0.3-cp314-cp314t-win32.whl", hash = "sha256:8a6e050cb6164d3f830453754094c086ff2d0b2f3a897a1d9820f6139a1f0914", size = 3022339, upload-time = "2025-10-15T23:17:40.888Z" },
    { url = "https://files.pythonhosted.org/packages/f6/30/640f34ccd4d2a1bc88367b54b926b781b5a018d65f404d409aba76a84b1c/cryptography-46.0.3-cp314-cp314t-win_amd64.whl", hash = "sha256:760f83faa07f8b64e9c33fc963d790a2edb24efb479e3520c14a45741cd9b2db", size = 3494315, upload-time = "2025-10-15T23:17:42.769Z" },
    { url = "https://files.pythonhosted.org/packages/ba/8b/88cc7e3bd0a8e7b861f26981f7b820e1f46aa9d26cc482d0feba0ecb4919/cryptography-46.0.3-cp314-cp314t-win_arm64.whl", hash = "sha256:516ea134e703e9fe26bcd1277a4b59ad30586ea90c365a87781d7887a646fe21", size = 2919331, upload-time = "2025-10-15T23:17:44.468Z" },
    { url = "https://files.pythonhosted.org/packages/fd/23/45fe7f376a7df8daf6da3556603b36f53475a99ce4faacb6ba2cf3d82021/cryptography-46.0.3-cp38-abi3-macosx_10_9_universal2.whl", hash = "sha256:cb3d760a6117f621261d662bccc8ef5bc32ca673e037c83fbe565324f5c46936", size = 7218248, upload-time = "2025-10-15T23:17:46.294Z" },
    { url = "https://files.pythonhosted.org/packages/27/32/b68d27471372737054cbd34c84981f9edbc24fe67ca225d389799614e27f/cryptography-46.0.3-cp38-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl", hash = "sha256:4b7387121ac7d15e550f5cb4a43aef2559ed759c35df7336c402bb8275ac9683", size = 4294089, upload-time = "2025-10-15T23:17:48.269Z" },
    { url = "https://files.pythonhosted.org/packages/26/42/fa8389d4478368743e24e61eea78846a0006caffaf72ea24a15159215a14/cryptography-46.0.3-cp38-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:15ab9b093e8f09daab0f2159bb7e47532596075139dd74365da52ecc9cb46c5d", size = 4440029, upload-time = "2025-10-15T23:17:49.837Z" },
    { url = "https://files.pythonhosted.org/packages/5f/eb/f483db0ec5ac040824f269e93dd2bd8a21ecd1027e77ad7bdf6914f2fd80/cryptography-46.0.3-cp38-abi3-manylinux_2_28_aarch64.whl", hash = "sha256:46acf53b40ea38f9c6c229599a4a13f0d46a6c3fa9ef19fc1a124d62e338dfa0", size = 4297222, upload-time = "2025-10-15T23:17:51.357Z" },
    { url = "https://files.pythonhosted.org/packages/fd/cf/da9502c4e1912cb1da3807ea3618a6829bee8207456fbbeebc361ec38ba3/cryptography-46.0.3-cp38-abi3-manylinux_2_28_armv7l.manylinux_2_31_armv7l.whl", hash = "sha256:10ca84c4668d066a9878890047f03546f3ae0a6b8b39b697457b7757aaf18dbc", size = 4012280, upload-time = "2025-10-15T23:17:52.964Z" },
    { url = "https://files.pythonhosted.org/packages/6b/8f/9adb86b93330e0df8b3dcf03eae67c33ba89958fc2e03862ef1ac2b42465/cryptography-46.0.3-cp38-abi3-manylinux_2_28_ppc64le.whl", hash = "sha256:36e627112085bb3b81b19fed209c05ce2a52ee8b15d161b7c643a7d5a88491f3", size = 4978958, upload-time = "2025-10-15T23:17:54.965Z" },
    { url = "https://files.pythonhosted.org/packages/d1/a0/5fa77988289c34bdb9f913f5606ecc9ada1adb5ae870bd0d1054a7021cc4/cryptography-46.0.3-cp38-abi3-manylinux_2_28_x86_64.whl", hash = "sha256:1000713389b75c449a6e979ffc7dcc8ac90b437048766cef052d4d30b8220971", size = 4473714, upload-time = "2025-10-15T23:17:56.754Z" },
    { url = "https://files.pythonhosted.org/packages/14/e5/fc82d72a58d41c393697aa18c9abe5ae1214ff6f2a5c18ac470f92777895/cryptography-46.0.3-cp38-abi3-manylinux_2_34_aarch64.whl", hash = "sha256:b02cf04496f6576afffef5ddd04a0cb7d49cf6be16a9059d793a30b035f6b6ac", size = 4296970, upload-time = "2025-10-15T23:17:58.588Z" },
    { url = "https://files.pythonhosted.org/packages/78/06/5663ed35438d0b09056973994f1aec467492b33bd31da36e468b01ec1097/cryptography-46.0.3-cp38-abi3-manylinux_2_34_ppc64le.whl", hash = "sha256:71e842ec9bc7abf543b47cf86b9a743baa95f4677d22baa4c7d5c69e49e9bc04", size = 4940236, upload-time = "2025-10-15T23:18:00.897Z" },
    { url = "https://files.pythonhosted.org/packages/fc/59/873633f3f2dcd8a053b8dd1d38f783043b5fce589c0f6988bf55ef57e43e/cryptography-46.0.3-cp38-abi3-manylinux_2_34_x86_64.whl", hash = "sha256:402b58fc32614f00980b66d6e56a5b4118e6cb362ae8f3fda141ba4689bd4506", size = 4472642, upload-time = "2025-10-15T23:18:02.749Z" },
    { url = "https://files.pythonhosted.org/packages/3d/39/8e71f3930e40f6877737d6f69248cf74d4e34b886a3967d32f919cc50d3b/cryptography-46.0.3-cp38-abi3-musllinux_1_2_aarch64.whl", hash = "sha256:ef639cb3372f69ec44915fafcd6698b6cc78fbe0c2ea41be867f6ed612811963", size = 4423126, upload-time = "2025-10-15T23:18:04.85Z" },
    { url = "https://files.pythonhosted.org/packages/cd/c7/f65027c2810e14c3e7268353b1681932b87e5a48e65505d8cc17c99e36ae/cryptography-46.0.3-cp38-abi3-musllinux_1_2_x86_64.whl", hash = "sha256:3b51b8ca4f1c6453d8829e1eb7299499ca7f313900dd4d89a24b8b87c0a780d4", size = 4686573, upload-time = "2025-10-15T23:18:06.908Z" },
    { url = "https://files.pythonhosted.org/packages/0a/6e/1c8331ddf91ca4730ab3086a0f1be19c65510a33b5a441cb334e7a2d2560/cryptography-46.0.3-cp38-abi3-win32.whl", hash = "sha256:6276eb85ef938dc035d59b87c8a7dc559a232f954962520137529d77b18ff1df", size = 3036695, upload-time = "2025-10-15T23:18:08.672Z" },
    { url = "https://files.pythonhosted.org/packages/90/45/b0d691df20633eff80955a0fc7695ff9051ffce8b69741444bd9ed7bd0db/cryptography-46.0.3-cp38-abi3-win_amd64.whl", hash = "sha256:416260257577718c05135c55958b674000baef9a1c7d9e8f306ec60d71db850f", size = 3501720, upload-time = "2025-10-15T23:18:10.632Z" },
    { url = "https://files.pythonhosted.org/packages/e8/cb/2da4cc83f5edb9c3257d09e1e7ab7b23f049c7962cae8d842bbef0a9cec9/cryptography-46.0.3-cp38-abi3-win_arm64.whl", hash = "sha256:d89c3468de4cdc4f08a57e214384d0471911a3830fcdaf7a8cc587e42a866372", size = 2918740, upload-time = "2025-10-15T23:18:12.277Z" },
    { url = "https://files.pythonhosted.org/packages/d9/cd/1a8633802d766a0fa46f382a77e096d7e209e0817892929655fe0586ae32/cryptography-46.0.3-pp310-pypy310_pp73-macosx_10_9_x86_64.whl", hash = "sha256:a23582810fedb8c0bc47524558fb6c56aac3fc252cb306072fd2815da2a47c32", size = 3689163, upload-time = "2025-10-15T23:18:13.821Z" },
    { url = "https://files.pythonhosted.org/packages/4c/59/6b26512964ace6480c3e54681a9859c974172fb141c38df11eadd8416947/cryptography-46.0.3-pp310-pypy310_pp73-win_amd64.whl", hash = "sha256:e7aec276d68421f9574040c26e2a7c3771060bc0cff408bae1dcb19d3ab1e63c", size = 3429474, upload-time = "2025-10-15T23:18:15.477Z" },
    { url = "https://files.pythonhosted.org/packages/06/8a/e60e46adab4362a682cf142c7dcb5bf79b782ab2199b0dcb81f55970807f/cryptography-46.0.3-pp311-pypy311_pp73-macosx_10_9_x86_64.whl", hash = "sha256:7ce938a99998ed3c8aa7e7272dca1a610401ede816d36d0693907d863b10d9ea", size = 3698132, upload-time = "2025-10-15T23:18:17.056Z" },
    { url = "https://files.pythonhosted.org/packages/da/38/f59940ec4ee91e93d3311f7532671a5cef5570eb04a144bf203b58552d11/cryptography-46.0.3-pp311-pypy311_pp73-manylinux_2_28_aarch64.whl", hash = "sha256:191bb60a7be5e6f54e30ba16fdfae78ad3a342a0599eb4193ba88e3f3d6e185b", size = 4243992, upload-time = "2025-10-15T23:18:18.695Z" },
    { url = "https://files.pythonhosted.org/packages/b0/0c/35b3d92ddebfdfda76bb485738306545817253d0a3ded0bfe80ef8e67aa5/cryptography-46.0.3-pp311-pypy311_pp73-manylinux_2_28_x86_64.whl", hash = "sha256:c70cc23f12726be8f8bc72e41d5065d77e4515efae3690326764ea1b07845cfb", size = 4409944, upload-time = "2025-10-15T23:18:20.597Z" },
    { url = "https://files.pythonhosted.org/packages/99/55/181022996c4063fc0e7666a47049a1ca705abb9c8a13830f074edb347495/cryptography-46.0.3-pp311-pypy311_pp73-manylinux_2_34_aarch64.whl", hash = "sha256:9394673a9f4de09e28b5356e7fff97d778f8abad85c9d5ac4a4b7e25a0de7717", size = 4242957, upload-time = "2025-10-15T23:18:22.18Z" },
    { url = "https://files.pythonhosted.org/packages/ba/af/72cd6ef29f9c5f731251acadaeb821559fe25f10852f44a63374c9ca08c1/cryptography-46.0.3-pp311-pypy311_pp73-manylinux_2_34_x86_64.whl", hash = "sha256:94cd0549accc38d1494e1f8de71eca837d0509d0d44bf11d158524b0e12cebf9", size = 4409447, upload-time = "2025-10-15T23:18:24.209Z" },
    { url = "https://files.pythonhosted.org/packages/0d/c3/e90f4a4feae6410f914f8ebac129b9ae7a8c92eb60a638012dde42030a9d/cryptography-46.0.3-pp311-pypy311_pp73-win_amd64.whl", hash = "sha256:6b5063083824e5509fdba180721d55909ffacccc8adbec85268b48439423d78c", size = 3438528, upload-time = "2025-10-15T23:18:26.227Z" },
]

[[package]]
name = "cyclopts"
version = "4.8.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "attrs" },
    { name = "docstring-parser" },
    { name = "rich" },
    { name = "rich-rst" },
    { name = "tomli", marker = "python_full_version < '3.11'" },
    { name = "typing-extensions", marker = "python_full_version < '3.11'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/33/7a/3c3623755561c7f283dd769470e99ae36c46810bf3b3f264d69006f6c97a/cyclopts-4.8.0.tar.gz", hash = "sha256:92cc292d18d8be372e58d8bce1aa966d30f819a5fb3fee02bd2ad4a6bb403f29", size = 164066, upload-time = "2026-03-07T19:39:18.122Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/87/01/6ec7210775ea5e4989a10d89eda6c5ea7ff06caa614231ad533d74fecac8/cyclopts-4.8.0-py3-none-any.whl", hash = "sha256:ef353da05fec36587d4ebce7a6e4b27515d775d184a23bab4b01426f93ddc8d4", size = 201948, upload-time = "2026-03-07T19:39:19.307Z" },
]

[[package]]
name = "dnspython"
version = "2.8.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/8c/8b/57666417c0f90f08bcafa776861060426765fdb422eb10212086fb811d26/dnspython-2.8.0.tar.gz", hash = "sha256:181d3c6996452cb1189c4046c61599b84a5a86e099562ffde77d26984ff26d0f", size = 368251, upload-time = "2025-09-07T18:58:00.022Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/ba/5a/18ad964b0086c6e62e2e7500f7edc89e3faa45033c71c1893d34eed2b2de/dnspython-2.8.0-py3-none-any.whl", hash = "sha256:01d9bbc4a2d76bf0db7c1f729812ded6d912bd318d3b1cf81d30c0f845dbf3af", size = 331094, upload-time = "2025-09-07T18:57:58.071Z" },
]

[[package]]
name = "docstring-parser"
version = "0.17.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/b2/9d/c3b43da9515bd270df0f80548d9944e389870713cc1fe2b8fb35fe2bcefd/docstring_parser-0.17.0.tar.gz", hash = "sha256:583de4a309722b3315439bb31d64ba3eebada841f2e2cee23b99df001434c912", size = 27442, upload-time = "2025-07-21T07:35:01.868Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/55/e2/2537ebcff11c1ee1ff17d8d0b6f4db75873e3b0fb32c2d4a2ee31ecb310a/docstring_parser-0.17.0-py3-none-any.whl", hash = "sha256:cf2569abd23dce8099b300f9b4fa8191e9582dda731fd533daf54c4551658708", size = 36896, upload-time = "2025-07-21T07:35:00.684Z" },
]

[[package]]
name = "docutils"
version = "0.22.4"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/ae/b6/03bb70946330e88ffec97aefd3ea75ba575cb2e762061e0e62a213befee8/docutils-0.22.4.tar.gz", hash = "sha256:4db53b1fde9abecbb74d91230d32ab626d94f6badfc575d6db9194a49df29968", size = 2291750, upload-time = "2025-12-18T19:00:26.443Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/02/10/5da547df7a391dcde17f59520a231527b8571e6f46fc8efb02ccb370ab12/docutils-0.22.4-py3-none-any.whl", hash = "sha256:d0013f540772d1420576855455d050a2180186c91c15779301ac2ccb3eeb68de", size = 633196, upload-time = "2025-12-18T19:00:18.077Z" },
]

[[package]]
name = "email-validator"
version = "2.3.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "dnspython" },
    { name = "idna" },
]
sdist = { url = "https://files.pythonhosted.org/packages/f5/22/900cb125c76b7aaa450ce02fd727f452243f2e91a61af068b40adba60ea9/email_validator-2.3.0.tar.gz", hash = "sha256:9fc05c37f2f6cf439ff414f8fc46d917929974a82244c20eb10231ba60c54426", size = 51238, upload-time = "2025-08-26T13:09:06.831Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/de/15/545e2b6cf2e3be84bc1ed85613edd75b8aea69807a71c26f4ca6a9258e82/email_validator-2.3.0-py3-none-any.whl", hash = "sha256:80f13f623413e6b197ae73bb10bf4eb0908faf509ad8362c5edeb0be7fd450b4", size = 35604, upload-time = "2025-08-26T13:09:05.858Z" },
]

[[package]]
name = "exceptiongroup"
version = "1.3.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "typing-extensions", marker = "python_full_version < '3.13'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/50/79/66800aadf48771f6b62f7eb014e352e5d06856655206165d775e675a02c9/exceptiongroup-1.3.1.tar.gz", hash = "sha256:8b412432c6055b0b7d14c310000ae93352ed6754f70fa8f7c34141f91c4e3219", size = 30371, upload-time = "2025-11-21T23:01:54.787Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/8a/0e/97c33bf5009bdbac74fd2beace167cab3f978feb69cc36f1ef79360d6c4e/exceptiongroup-1.3.1-py3-none-any.whl", hash = "sha256:a7a39a3bd276781e98394987d3a5701d0c4edffb633bb7a5144577f82c773598", size = 16740, upload-time = "2025-11-21T23:01:53.443Z" },
]

[[package]]
name = "fastmcp"
version = "3.1.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "authlib" },
    { name = "cyclopts" },
    { name = "exceptiongroup" },
    { name = "httpx" },
    { name = "jsonref" },
    { name = "jsonschema-path" },
    { name = "mcp" },
    { name = "openapi-pydantic" },
    { name = "opentelemetry-api" },
    { name = "packaging" },
    { name = "platformdirs" },
    { name = "py-key-value-aio", extra = ["filetree", "keyring", "memory"] },
    { name = "pydantic", extra = ["email"] },
    { name = "pyperclip" },
    { name = "python-dotenv" },
    { name = "pyyaml" },
    { name = "rich" },
    { name = "uncalled-for" },
    { name = "uvicorn" },
    { name = "watchfiles" },
    { name = "websockets" },
]
sdist = { url = "https://files.pythonhosted.org/packages/0a/70/862026c4589441f86ad3108f05bfb2f781c6b322ad60a982f40b303b47d7/fastmcp-3.1.0.tar.gz", hash = "sha256:e25264794c734b9977502a51466961eeecff92a0c2f3b49c40c070993628d6d0", size = 17347083, upload-time = "2026-03-03T02:43:11.283Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/17/07/516f5b20d88932e5a466c2216b628e5358a71b3a9f522215607c3281de05/fastmcp-3.1.0-py3-none-any.whl", hash = "sha256:b1f73b56fd3b0cb2bd9e2a144fc650d5cc31587ed129d996db7710e464ae8010", size = 633749, upload-time = "2026-03-03T02:43:09.06Z" },
]

[[package]]
name = "h11"
version = "0.16.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/01/ee/02a2c011bdab74c6fb3c75474d40b3052059d95df7e73351460c8588d963/h11-0.16.0.tar.gz", hash = "sha256:4e35b956cf45792e4caa5885e69fba00bdbc6ffafbfa020300e549b208ee5ff1", size = 101250, upload-time = "2025-04-24T03:35:25.427Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/04/4b/29cac41a4d98d144bf5f6d33995617b185d14b22401f75ca86f384e87ff1/h11-0.16.0-py3-none-any.whl", hash = "sha256:63cf8bbe7522de3bf65932fda1d9c2772064ffb3dae62d55932da54b31cb6c86", size = 37515, upload-time = "2025-04-24T03:35:24.344Z" },
]

[[package]]
name = "httpcore"
version = "1.0.9"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "certifi" },
    { name = "h11" },
]
sdist = { url = "https://files.pythonhosted.org/packages/06/94/82699a10bca87a5556c9c59b5963f2d039dbd239f25bc2a63907a05a14cb/httpcore-1.0.9.tar.gz", hash = "sha256:6e34463af53fd2ab5d807f399a9b45ea31c3dfa2276f15a2c3f00afff6e176e8", size = 85484, upload-time = "2025-04-24T22:06:22.219Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/7e/f5/f66802a942d491edb555dd61e3a9961140fd64c90bce1eafd741609d334d/httpcore-1.0.9-py3-none-any.whl", hash = "sha256:2d400746a40668fc9dec9810239072b40b4484b640a8c38fd654a024c7a1bf55", size = 78784, upload-time = "2025-04-24T22:06:20.566Z" },
]

[[package]]
name = "httpx"
version = "0.28.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "anyio" },
    { name = "certifi" },
    { name = "httpcore" },
    { name = "idna" },
]
sdist = { url = "https://files.pythonhosted.org/packages/b1/df/48c586a5fe32a0f01324ee087459e112ebb7224f646c0b5023f5e79e9956/httpx-0.28.1.tar.gz", hash = "sha256:75e98c5f16b0f35b567856f597f06ff2270a374470a5c2392242528e3e3e42fc", size = 141406, upload-time = "2024-12-06T15:37:23.222Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/2a/39/e50c7c3a983047577ee07d2a9e53faf5a69493943ec3f6a384bdc792deb2/httpx-0.28.1-py3-none-any.whl", hash = "sha256:d909fcccc110f8c7faf814ca82a9a4d816bc5a6dbfea25d6591d6985b8ba59ad", size = 73517, upload-time = "2024-12-06T15:37:21.509Z" },
]

[[package]]
name = "httpx-sse"
version = "0.4.3"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/0f/4c/751061ffa58615a32c31b2d82e8482be8dd4a89154f003147acee90f2be9/httpx_sse-0.4.3.tar.gz", hash = "sha256:9b1ed0127459a66014aec3c56bebd93da3c1bc8bb6618c8082039a44889a755d", size = 15943, upload-time = "2025-10-10T21:48:22.271Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/d2/fd/6668e5aec43ab844de6fc74927e155a3b37bf40d7c3790e49fc0406b6578/httpx_sse-0.4.3-py3-none-any.whl", hash = "sha256:0ac1c9fe3c0afad2e0ebb25a934a59f4c7823b60792691f779fad2c5568830fc", size = 8960, upload-time = "2025-10-10T21:48:21.158Z" },
]

[[package]]
name = "idna"
version = "3.11"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/6f/6d/0703ccc57f3a7233505399edb88de3cbd678da106337b9fcde432b65ed60/idna-3.11.tar.gz", hash = "sha256:795dafcc9c04ed0c1fb032c2aa73654d8e8c5023a7df64a53f39190ada629902", size = 194582, upload-time = "2025-10-12T14:55:20.501Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/0e/61/66938bbb5fc52dbdf84594873d5b51fb1f7c7794e9c0f5bd885f30bc507b/idna-3.11-py3-none-any.whl", hash = "sha256:771a87f49d9defaf64091e6e6fe9c18d4833f140bd19464795bc32d966ca37ea", size = 71008, upload-time = "2025-10-12T14:55:18.883Z" },
]

[[package]]
name = "importlib-metadata"
version = "8.7.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "zipp" },
]
sdist = { url = "https://files.pythonhosted.org/packages/f3/49/3b30cad09e7771a4982d9975a8cbf64f00d4a1ececb53297f1d9a7be1b10/importlib_metadata-8.7.1.tar.gz", hash = "sha256:49fef1ae6440c182052f407c8d34a68f72efc36db9ca90dc0113398f2fdde8bb", size = 57107, upload-time = "2025-12-21T10:00:19.278Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/fa/5e/f8e9a1d23b9c20a551a8a02ea3637b4642e22c2626e3a13a9a29cdea99eb/importlib_metadata-8.7.1-py3-none-any.whl", hash = "sha256:5a1f80bf1daa489495071efbb095d75a634cf28a8bc299581244063b53176151", size = 27865, upload-time = "2025-12-21T10:00:18.329Z" },
]

[[package]]
name = "iniconfig"
version = "2.3.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/72/34/14ca021ce8e5dfedc35312d08ba8bf51fdd999c576889fc2c24cb97f4f10/iniconfig-2.3.0.tar.gz", hash = "sha256:c76315c77db068650d49c5b56314774a7804df16fee4402c1f19d6d15d8c4730", size = 20503, upload-time = "2025-10-18T21:55:43.219Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/cb/b1/3846dd7f199d53cb17f49cba7e651e9ce294d8497c8c150530ed11865bb8/iniconfig-2.3.0-py3-none-any.whl", hash = "sha256:f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12", size = 7484, upload-time = "2025-10-18T21:55:41.639Z" },
]

[[package]]
name = "jaraco-classes"
version = "3.4.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "more-itertools" },
]
sdist = { url = "https://files.pythonhosted.org/packages/06/c0/ed4a27bc5571b99e3cff68f8a9fa5b56ff7df1c2251cc715a652ddd26402/jaraco.classes-3.4.0.tar.gz", hash = "sha256:47a024b51d0239c0dd8c8540c6c7f484be3b8fcf0b2d85c13825780d3b3f3acd", size = 11780, upload-time = "2024-03-31T07:27:36.643Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/7f/66/b15ce62552d84bbfcec9a4873ab79d993a1dd4edb922cbfccae192bd5b5f/jaraco.classes-3.4.0-py3-none-any.whl", hash = "sha256:f662826b6bed8cace05e7ff873ce0f9283b5c924470fe664fff1c2f00f581790", size = 6777, upload-time = "2024-03-31T07:27:34.792Z" },
]

[[package]]
name = "jaraco-context"
version = "6.1.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "backports-tarfile", marker = "python_full_version < '3.12'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/27/7b/c3081ff1af947915503121c649f26a778e1a2101fd525f74aef997d75b7e/jaraco_context-6.1.1.tar.gz", hash = "sha256:bc046b2dc94f1e5532bd02402684414575cc11f565d929b6563125deb0a6e581", size = 15832, upload-time = "2026-03-07T15:46:04.63Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/f4/49/c152890d49102b280ecf86ba5f80a8c111c3a155dafa3bd24aeb64fde9e1/jaraco_context-6.1.1-py3-none-any.whl", hash = "sha256:0df6a0287258f3e364072c3e40d5411b20cafa30cb28c4839d24319cecf9f808", size = 7005, upload-time = "2026-03-07T15:46:03.515Z" },
]

[[package]]
name = "jaraco-functools"
version = "4.4.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "more-itertools" },
]
sdist = { url = "https://files.pythonhosted.org/packages/0f/27/056e0638a86749374d6f57d0b0db39f29509cce9313cf91bdc0ac4d91084/jaraco_functools-4.4.0.tar.gz", hash = "sha256:da21933b0417b89515562656547a77b4931f98176eb173644c0d35032a33d6bb", size = 19943, upload-time = "2025-12-21T09:29:43.6Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/fd/c4/813bb09f0985cb21e959f21f2464169eca882656849adf727ac7bb7e1767/jaraco_functools-4.4.0-py3-none-any.whl", hash = "sha256:9eec1e36f45c818d9bf307c8948eb03b2b56cd44087b3cdc989abca1f20b9176", size = 10481, upload-time = "2025-12-21T09:29:42.27Z" },
]

[[package]]
name = "jeepney"
version = "0.9.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/7b/6f/357efd7602486741aa73ffc0617fb310a29b588ed0fd69c2399acbb85b0c/jeepney-0.9.0.tar.gz", hash = "sha256:cf0e9e845622b81e4a28df94c40345400256ec608d0e55bb8a3feaa9163f5732", size = 106758, upload-time = "2025-02-27T18:51:01.684Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b2/a3/e137168c9c44d18eff0376253da9f1e9234d0239e0ee230d2fee6cea8e55/jeepney-0.9.0-py3-none-any.whl", hash = "sha256:97e5714520c16fc0a45695e5365a2e11b81ea79bba796e26f9f1d178cb182683", size = 49010, upload-time = "2025-02-27T18:51:00.104Z" },
]

[[package]]
name = "jsonref"
version = "1.1.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/aa/0d/c1f3277e90ccdb50d33ed5ba1ec5b3f0a242ed8c1b1a85d3afeb68464dca/jsonref-1.1.0.tar.gz", hash = "sha256:32fe8e1d85af0fdefbebce950af85590b22b60f9e95443176adbde4e1ecea552", size = 8814, upload-time = "2023-01-16T16:10:04.455Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/0c/ec/e1db9922bceb168197a558a2b8c03a7963f1afe93517ddd3cf99f202f996/jsonref-1.1.0-py3-none-any.whl", hash = "sha256:590dc7773df6c21cbf948b5dac07a72a251db28b0238ceecce0a2abfa8ec30a9", size = 9425, upload-time = "2023-01-16T16:10:02.255Z" },
]

[[package]]
name = "jsonschema"
version = "4.25.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "attrs" },
    { name = "jsonschema-specifications" },
    { name = "referencing" },
    { name = "rpds-py" },
]
sdist = { url = "https://files.pythonhosted.org/packages/74/69/f7185de793a29082a9f3c7728268ffb31cb5095131a9c139a74078e27336/jsonschema-4.25.1.tar.gz", hash = "sha256:e4a9655ce0da0c0b67a085847e00a3a51449e1157f4f75e9fb5aa545e122eb85", size = 357342, upload-time = "2025-08-18T17:03:50.038Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/bf/9c/8c95d856233c1f82500c2450b8c68576b4cf1c871db3afac5c34ff84e6fd/jsonschema-4.25.1-py3-none-any.whl", hash = "sha256:3fba0169e345c7175110351d456342c364814cfcf3b964ba4587f22915230a63", size = 90040, upload-time = "2025-08-18T17:03:48.373Z" },
]

[[package]]
name = "jsonschema-path"
version = "0.4.5"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "pathable" },
    { name = "pyyaml" },
    { name = "referencing" },
]
sdist = { url = "https://files.pythonhosted.org/packages/5b/8a/7e6102f2b8bdc6705a9eb5294f8f6f9ccd3a8420e8e8e19671d1dd773251/jsonschema_path-0.4.5.tar.gz", hash = "sha256:c6cd7d577ae290c7defd4f4029e86fdb248ca1bd41a07557795b3c95e5144918", size = 15113, upload-time = "2026-03-03T09:56:46.87Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/04/d5/4e96c44f6c1ea3d812cf5391d81a4f5abaa540abf8d04ecd7f66e0ed11df/jsonschema_path-0.4.5-py3-none-any.whl", hash = "sha256:7d77a2c3f3ec569a40efe5c5f942c44c1af2a6f96fe0866794c9ef5b8f87fd65", size = 19368, upload-time = "2026-03-03T09:56:45.39Z" },
]

[[package]]
name = "jsonschema-specifications"
version = "2025.9.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "referencing" },
]
sdist = { url = "https://files.pythonhosted.org/packages/19/74/a633ee74eb36c44aa6d1095e7cc5569bebf04342ee146178e2d36600708b/jsonschema_specifications-2025.9.1.tar.gz", hash = "sha256:b540987f239e745613c7a9176f3edb72b832a4ac465cf02712288397832b5e8d", size = 32855, upload-time = "2025-09-08T01:34:59.186Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/41/45/1a4ed80516f02155c51f51e8cedb3c1902296743db0bbc66608a0db2814f/jsonschema_specifications-2025.9.1-py3-none-any.whl", hash = "sha256:98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe", size = 18437, upload-time = "2025-09-08T01:34:57.871Z" },
]

[[package]]
name = "keyring"
version = "25.7.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "importlib-metadata", marker = "python_full_version < '3.12'" },
    { name = "jaraco-classes" },
    { name = "jaraco-context" },
    { name = "jaraco-functools" },
    { name = "jeepney", marker = "sys_platform == 'linux'" },
    { name = "pywin32-ctypes", marker = "sys_platform == 'win32'" },
    { name = "secretstorage", marker = "sys_platform == 'linux'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/43/4b/674af6ef2f97d56f0ab5153bf0bfa28ccb6c3ed4d1babf4305449668807b/keyring-25.7.0.tar.gz", hash = "sha256:fe01bd85eb3f8fb3dd0405defdeac9a5b4f6f0439edbb3149577f244a2e8245b", size = 63516, upload-time = "2025-11-16T16:26:09.482Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/81/db/e655086b7f3a705df045bf0933bdd9c2f79bb3c97bfef1384598bb79a217/keyring-25.7.0-py3-none-any.whl", hash = "sha256:be4a0b195f149690c166e850609a477c532ddbfbaed96a404d4e43f8d5e2689f", size = 39160, upload-time = "2025-11-16T16:26:08.402Z" },
]

[[package]]
name = "librt"
version = "0.7.3"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/b3/d9/6f3d3fcf5e5543ed8a60cc70fa7d50508ed60b8a10e9af6d2058159ab54e/librt-0.7.3.tar.gz", hash = "sha256:3ec50cf65235ff5c02c5b747748d9222e564ad48597122a361269dd3aa808798", size = 144549, upload-time = "2025-12-06T19:04:45.553Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/4d/66/79a14e672256ef58144a24eb49adb338ec02de67ff4b45320af6504682ab/librt-0.7.3-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:2682162855a708e3270eba4b92026b93f8257c3e65278b456c77631faf0f4f7a", size = 54707, upload-time = "2025-12-06T19:03:10.881Z" },
    { url = "https://files.pythonhosted.org/packages/58/fa/b709c65a9d5eab85f7bcfe0414504d9775aaad6e78727a0327e175474caa/librt-0.7.3-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:440c788f707c061d237c1e83edf6164ff19f5c0f823a3bf054e88804ebf971ec", size = 56670, upload-time = "2025-12-06T19:03:12.107Z" },
    { url = "https://files.pythonhosted.org/packages/3a/56/0685a0772ec89ddad4c00e6b584603274c3d818f9a68e2c43c4eb7b39ee9/librt-0.7.3-cp310-cp310-manylinux1_i686.manylinux_2_28_i686.manylinux_2_5_i686.whl", hash = "sha256:399938edbd3d78339f797d685142dd8a623dfaded023cf451033c85955e4838a", size = 161045, upload-time = "2025-12-06T19:03:13.444Z" },
    { url = "https://files.pythonhosted.org/packages/4e/d9/863ada0c5ce48aefb89df1555e392b2209fcb6daee4c153c031339b9a89b/librt-0.7.3-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:1975eda520957c6e0eb52d12968dd3609ffb7eef05d4223d097893d6daf1d8a7", size = 169532, upload-time = "2025-12-06T19:03:14.699Z" },
    { url = "https://files.pythonhosted.org/packages/68/a0/71da6c8724fd16c31749905ef1c9e11de206d9301b5be984bf2682b4efb3/librt-0.7.3-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:f9da128d0edf990cf0d2ca011b02cd6f639e79286774bd5b0351245cbb5a6e51", size = 183277, upload-time = "2025-12-06T19:03:16.446Z" },
    { url = "https://files.pythonhosted.org/packages/8c/bf/9c97bf2f8338ba1914de233ea312bba2bbd7c59f43f807b3e119796bab18/librt-0.7.3-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:e19acfde38cb532a560b98f473adc741c941b7a9bc90f7294bc273d08becb58b", size = 179045, upload-time = "2025-12-06T19:03:17.838Z" },
    { url = "https://files.pythonhosted.org/packages/b3/b1/ceea067f489e904cb4ddcca3c9b06ba20229bc3fa7458711e24a5811f162/librt-0.7.3-cp310-cp310-musllinux_1_2_i686.whl", hash = "sha256:7b4f57f7a0c65821c5441d98c47ff7c01d359b1e12328219709bdd97fdd37f90", size = 173521, upload-time = "2025-12-06T19:03:19.17Z" },
    { url = "https://files.pythonhosted.org/packages/7a/41/6cb18f5da9c89ed087417abb0127a445a50ad4eaf1282ba5b52588187f47/librt-0.7.3-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:256793988bff98040de23c57cf36e1f4c2f2dc3dcd17537cdac031d3b681db71", size = 193592, upload-time = "2025-12-06T19:03:20.637Z" },
    { url = "https://files.pythonhosted.org/packages/4c/3c/fcef208746584e7c78584b7aedc617130c4a4742cb8273361bbda8b183b5/librt-0.7.3-cp310-cp310-win32.whl", hash = "sha256:fcb72249ac4ea81a7baefcbff74df7029c3cb1cf01a711113fa052d563639c9c", size = 47201, upload-time = "2025-12-06T19:03:21.764Z" },
    { url = "https://files.pythonhosted.org/packages/c4/bf/d8a6c35d1b2b789a4df9b3ddb1c8f535ea373fde2089698965a8f0d62138/librt-0.7.3-cp310-cp310-win_amd64.whl", hash = "sha256:4887c29cadbdc50640179e3861c276325ff2986791e6044f73136e6e798ff806", size = 54371, upload-time = "2025-12-06T19:03:23.231Z" },
    { url = "https://files.pythonhosted.org/packages/21/e6/f6391f5c6f158d31ed9af6bd1b1bcd3ffafdea1d816bc4219d0d90175a7f/librt-0.7.3-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:687403cced6a29590e6be6964463835315905221d797bc5c934a98750fe1a9af", size = 54711, upload-time = "2025-12-06T19:03:24.6Z" },
    { url = "https://files.pythonhosted.org/packages/ab/1b/53c208188c178987c081560a0fcf36f5ca500d5e21769596c845ef2f40d4/librt-0.7.3-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:24d70810f6e2ea853ff79338001533716b373cc0f63e2a0be5bc96129edb5fb5", size = 56664, upload-time = "2025-12-06T19:03:25.969Z" },
    { url = "https://files.pythonhosted.org/packages/cb/5c/d9da832b9a1e5f8366e8a044ec80217945385b26cb89fd6f94bfdc7d80b0/librt-0.7.3-cp311-cp311-manylinux1_i686.manylinux_2_28_i686.manylinux_2_5_i686.whl", hash = "sha256:bf8c7735fbfc0754111f00edda35cf9e98a8d478de6c47b04eaa9cef4300eaa7", size = 161701, upload-time = "2025-12-06T19:03:27.035Z" },
    { url = "https://files.pythonhosted.org/packages/20/aa/1e0a7aba15e78529dd21f233076b876ee58c8b8711b1793315bdd3b263b0/librt-0.7.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:e32d43610dff472eab939f4d7fbdd240d1667794192690433672ae22d7af8445", size = 171040, upload-time = "2025-12-06T19:03:28.482Z" },
    { url = "https://files.pythonhosted.org/packages/69/46/3cfa325c1c2bc25775ec6ec1718cfbec9cff4ac767d37d2d3a2d1cc6f02c/librt-0.7.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:adeaa886d607fb02563c1f625cf2ee58778a2567c0c109378da8f17ec3076ad7", size = 184720, upload-time = "2025-12-06T19:03:29.599Z" },
    { url = "https://files.pythonhosted.org/packages/99/bb/e4553433d7ac47f4c75d0a7e59b13aee0e08e88ceadbee356527a9629b0a/librt-0.7.3-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:572a24fc5958c61431da456a0ef1eeea6b4989d81eeb18b8e5f1f3077592200b", size = 180731, upload-time = "2025-12-06T19:03:31.201Z" },
    { url = "https://files.pythonhosted.org/packages/35/89/51cd73006232981a3106d4081fbaa584ac4e27b49bc02266468d3919db03/librt-0.7.3-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:6488e69d408b492e08bfb68f20c4a899a354b4386a446ecd490baff8d0862720", size = 174565, upload-time = "2025-12-06T19:03:32.818Z" },
    { url = "https://files.pythonhosted.org/packages/42/54/0578a78b587e5aa22486af34239a052c6366835b55fc307bc64380229e3f/librt-0.7.3-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:ed028fc3d41adda916320712838aec289956c89b4f0a361ceadf83a53b4c047a", size = 195247, upload-time = "2025-12-06T19:03:34.434Z" },
    { url = "https://files.pythonhosted.org/packages/b5/0a/ee747cd999753dd9447e50b98fc36ee433b6c841a42dbf6d47b64b32a56e/librt-0.7.3-cp311-cp311-win32.whl", hash = "sha256:2cf9d73499486ce39eebbff5f42452518cc1f88d8b7ea4a711ab32962b176ee2", size = 47514, upload-time = "2025-12-06T19:03:35.959Z" },
    { url = "https://files.pythonhosted.org/packages/ec/af/8b13845178dec488e752878f8e290f8f89e7e34ae1528b70277aa1a6dd1e/librt-0.7.3-cp311-cp311-win_amd64.whl", hash = "sha256:35f1609e3484a649bb80431310ddbec81114cd86648f1d9482bc72a3b86ded2e", size = 54695, upload-time = "2025-12-06T19:03:36.956Z" },
    { url = "https://files.pythonhosted.org/packages/02/7a/ae59578501b1a25850266778f59279f4f3e726acc5c44255bfcb07b4bc57/librt-0.7.3-cp311-cp311-win_arm64.whl", hash = "sha256:550fdbfbf5bba6a2960b27376ca76d6aaa2bd4b1a06c4255edd8520c306fcfc0", size = 48142, upload-time = "2025-12-06T19:03:38.263Z" },
    { url = "https://files.pythonhosted.org/packages/29/90/ed8595fa4e35b6020317b5ea8d226a782dcbac7a997c19ae89fb07a41c66/librt-0.7.3-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:0fa9ac2e49a6bee56e47573a6786cb635e128a7b12a0dc7851090037c0d397a3", size = 55687, upload-time = "2025-12-06T19:03:39.245Z" },
    { url = "https://files.pythonhosted.org/packages/dd/f6/6a20702a07b41006cb001a759440cb6b5362530920978f64a2b2ae2bf729/librt-0.7.3-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:2e980cf1ed1a2420a6424e2ed884629cdead291686f1048810a817de07b5eb18", size = 57127, upload-time = "2025-12-06T19:03:40.3Z" },
    { url = "https://files.pythonhosted.org/packages/79/f3/b0c4703d5ffe9359b67bb2ccb86c42d4e930a363cfc72262ac3ba53cff3e/librt-0.7.3-cp312-cp312-manylinux1_i686.manylinux_2_28_i686.manylinux_2_5_i686.whl", hash = "sha256:e094e445c37c57e9ec612847812c301840239d34ccc5d153a982fa9814478c60", size = 165336, upload-time = "2025-12-06T19:03:41.369Z" },
    { url = "https://files.pythonhosted.org/packages/02/69/3ba05b73ab29ccbe003856232cea4049769be5942d799e628d1470ed1694/librt-0.7.3-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:aca73d70c3f553552ba9133d4a09e767dcfeee352d8d8d3eb3f77e38a3beb3ed", size = 174237, upload-time = "2025-12-06T19:03:42.44Z" },
    { url = "https://files.pythonhosted.org/packages/22/ad/d7c2671e7bf6c285ef408aa435e9cd3fdc06fd994601e1f2b242df12034f/librt-0.7.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:c634a0a6db395fdaba0361aa78395597ee72c3aad651b9a307a3a7eaf5efd67e", size = 189017, upload-time = "2025-12-06T19:03:44.01Z" },
    { url = "https://files.pythonhosted.org/packages/f4/94/d13f57193148004592b618555f296b41d2d79b1dc814ff8b3273a0bf1546/librt-0.7.3-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:a59a69deeb458c858b8fea6acf9e2acd5d755d76cd81a655256bc65c20dfff5b", size = 183983, upload-time = "2025-12-06T19:03:45.834Z" },
    { url = "https://files.pythonhosted.org/packages/02/10/b612a9944ebd39fa143c7e2e2d33f2cb790205e025ddd903fb509a3a3bb3/librt-0.7.3-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:d91e60ac44bbe3a77a67af4a4c13114cbe9f6d540337ce22f2c9eaf7454ca71f", size = 177602, upload-time = "2025-12-06T19:03:46.944Z" },
    { url = "https://files.pythonhosted.org/packages/1f/48/77bc05c4cc232efae6c5592c0095034390992edbd5bae8d6cf1263bb7157/librt-0.7.3-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:703456146dc2bf430f7832fd1341adac5c893ec3c1430194fdcefba00012555c", size = 199282, upload-time = "2025-12-06T19:03:48.069Z" },
    { url = "https://files.pythonhosted.org/packages/12/aa/05916ccd864227db1ffec2a303ae34f385c6b22d4e7ce9f07054dbcf083c/librt-0.7.3-cp312-cp312-win32.whl", hash = "sha256:b7c1239b64b70be7759554ad1a86288220bbb04d68518b527783c4ad3fb4f80b", size = 47879, upload-time = "2025-12-06T19:03:49.289Z" },
    { url = "https://files.pythonhosted.org/packages/50/92/7f41c42d31ea818b3c4b9cc1562e9714bac3c676dd18f6d5dd3d0f2aa179/librt-0.7.3-cp312-cp312-win_amd64.whl", hash = "sha256:ef59c938f72bdbc6ab52dc50f81d0637fde0f194b02d636987cea2ab30f8f55a", size = 54972, upload-time = "2025-12-06T19:03:50.335Z" },
    { url = "https://files.pythonhosted.org/packages/3f/dc/53582bbfb422311afcbc92adb75711f04e989cec052f08ec0152fbc36c9c/librt-0.7.3-cp312-cp312-win_arm64.whl", hash = "sha256:ff21c554304e8226bf80c3a7754be27c6c3549a9fec563a03c06ee8f494da8fc", size = 48338, upload-time = "2025-12-06T19:03:51.431Z" },
    { url = "https://files.pythonhosted.org/packages/93/7d/e0ce1837dfb452427db556e6d4c5301ba3b22fe8de318379fbd0593759b9/librt-0.7.3-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:56f2a47beda8409061bc1c865bef2d4bd9ff9255219402c0817e68ab5ad89aed", size = 55742, upload-time = "2025-12-06T19:03:52.459Z" },
    { url = "https://files.pythonhosted.org/packages/be/c0/3564262301e507e1d5cf31c7d84cb12addf0d35e05ba53312494a2eba9a4/librt-0.7.3-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:14569ac5dd38cfccf0a14597a88038fb16811a6fede25c67b79c6d50fc2c8fdc", size = 57163, upload-time = "2025-12-06T19:03:53.516Z" },
    { url = "https://files.pythonhosted.org/packages/be/ac/245e72b7e443d24a562f6047563c7f59833384053073ef9410476f68505b/librt-0.7.3-cp313-cp313-manylinux1_i686.manylinux_2_28_i686.manylinux_2_5_i686.whl", hash = "sha256:6038ccbd5968325a5d6fd393cf6e00b622a8de545f0994b89dd0f748dcf3e19e", size = 165840, upload-time = "2025-12-06T19:03:54.918Z" },
    { url = "https://files.pythonhosted.org/packages/98/af/587e4491f40adba066ba39a450c66bad794c8d92094f936a201bfc7c2b5f/librt-0.7.3-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:d39079379a9a28e74f4d57dc6357fa310a1977b51ff12239d7271ec7e71d67f5", size = 174827, upload-time = "2025-12-06T19:03:56.082Z" },
    { url = "https://files.pythonhosted.org/packages/78/21/5b8c60ea208bc83dd00421022a3874330685d7e856404128dc3728d5d1af/librt-0.7.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:8837d5a52a2d7aa9f4c3220a8484013aed1d8ad75240d9a75ede63709ef89055", size = 189612, upload-time = "2025-12-06T19:03:57.507Z" },
    { url = "https://files.pythonhosted.org/packages/da/2f/8b819169ef696421fb81cd04c6cdf225f6e96f197366001e9d45180d7e9e/librt-0.7.3-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:399bbd7bcc1633c3e356ae274a1deb8781c7bf84d9c7962cc1ae0c6e87837292", size = 184584, upload-time = "2025-12-06T19:03:58.686Z" },
    { url = "https://files.pythonhosted.org/packages/6c/fc/af9d225a9395b77bd7678362cb055d0b8139c2018c37665de110ca388022/librt-0.7.3-cp313-cp313-musllinux_1_2_i686.whl", hash = "sha256:8d8cf653e798ee4c4e654062b633db36984a1572f68c3aa25e364a0ddfbbb910", size = 178269, upload-time = "2025-12-06T19:03:59.769Z" },
    { url = "https://files.pythonhosted.org/packages/6c/d8/7b4fa1683b772966749d5683aa3fd605813defffe157833a8fa69cc89207/librt-0.7.3-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:2f03484b54bf4ae80ab2e504a8d99d20d551bfe64a7ec91e218010b467d77093", size = 199852, upload-time = "2025-12-06T19:04:00.901Z" },
    { url = "https://files.pythonhosted.org/packages/77/e8/4598413aece46ca38d9260ef6c51534bd5f34b5c21474fcf210ce3a02123/librt-0.7.3-cp313-cp313-win32.whl", hash = "sha256:44b3689b040df57f492e02cd4f0bacd1b42c5400e4b8048160c9d5e866de8abe", size = 47936, upload-time = "2025-12-06T19:04:02.054Z" },
    { url = "https://files.pythonhosted.org/packages/af/80/ac0e92d5ef8c6791b3e2c62373863827a279265e0935acdf807901353b0e/librt-0.7.3-cp313-cp313-win_amd64.whl", hash = "sha256:6b407c23f16ccc36614c136251d6b32bf30de7a57f8e782378f1107be008ddb0", size = 54965, upload-time = "2025-12-06T19:04:03.224Z" },
    { url = "https://files.pythonhosted.org/packages/f1/fd/042f823fcbff25c1449bb4203a29919891ca74141b68d3a5f6612c4ce283/librt-0.7.3-cp313-cp313-win_arm64.whl", hash = "sha256:abfc57cab3c53c4546aee31859ef06753bfc136c9d208129bad23e2eca39155a", size = 48350, upload-time = "2025-12-06T19:04:04.234Z" },
    { url = "https://files.pythonhosted.org/packages/3e/ae/c6ecc7bb97134a71b5241e8855d39964c0e5f4d96558f0d60593892806d2/librt-0.7.3-cp314-cp314-macosx_10_13_x86_64.whl", hash = "sha256:120dd21d46ff875e849f1aae19346223cf15656be489242fe884036b23d39e93", size = 55175, upload-time = "2025-12-06T19:04:05.308Z" },
    { url = "https://files.pythonhosted.org/packages/cf/bc/2cc0cb0ab787b39aa5c7645cd792433c875982bdf12dccca558b89624594/librt-0.7.3-cp314-cp314-macosx_11_0_arm64.whl", hash = "sha256:1617bea5ab31266e152871208502ee943cb349c224846928a1173c864261375e", size = 56881, upload-time = "2025-12-06T19:04:06.674Z" },
    { url = "https://files.pythonhosted.org/packages/8e/87/397417a386190b70f5bf26fcedbaa1515f19dce33366e2684c6b7ee83086/librt-0.7.3-cp314-cp314-manylinux1_i686.manylinux_2_28_i686.manylinux_2_5_i686.whl", hash = "sha256:93b2a1f325fefa1482516ced160c8c7b4b8d53226763fa6c93d151fa25164207", size = 163710, upload-time = "2025-12-06T19:04:08.437Z" },
    { url = "https://files.pythonhosted.org/packages/c9/37/7338f85b80e8a17525d941211451199845093ca242b32efbf01df8531e72/librt-0.7.3-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:f3d4801db8354436fd3936531e7f0e4feb411f62433a6b6cb32bb416e20b529f", size = 172471, upload-time = "2025-12-06T19:04:10.124Z" },
    { url = "https://files.pythonhosted.org/packages/3b/e0/741704edabbfae2c852fedc1b40d9ed5a783c70ed3ed8e4fe98f84b25d13/librt-0.7.3-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:11ad45122bbed42cfc8b0597450660126ef28fd2d9ae1a219bc5af8406f95678", size = 186804, upload-time = "2025-12-06T19:04:11.586Z" },
    { url = "https://files.pythonhosted.org/packages/f4/d1/0a82129d6ba242f3be9af34815be089f35051bc79619f5c27d2c449ecef6/librt-0.7.3-cp314-cp314-musllinux_1_2_aarch64.whl", hash = "sha256:6b4e7bff1d76dd2b46443078519dc75df1b5e01562345f0bb740cea5266d8218", size = 181817, upload-time = "2025-12-06T19:04:12.802Z" },
    { url = "https://files.pythonhosted.org/packages/4f/32/704f80bcf9979c68d4357c46f2af788fbf9d5edda9e7de5786ed2255e911/librt-0.7.3-cp314-cp314-musllinux_1_2_i686.whl", hash = "sha256:d86f94743a11873317094326456b23f8a5788bad9161fd2f0e52088c33564620", size = 175602, upload-time = "2025-12-06T19:04:14.004Z" },
    { url = "https://files.pythonhosted.org/packages/f7/6d/4355cfa0fae0c062ba72f541d13db5bc575770125a7ad3d4f46f4109d305/librt-0.7.3-cp314-cp314-musllinux_1_2_x86_64.whl", hash = "sha256:754a0d09997095ad764ccef050dd5bf26cbf457aab9effcba5890dad081d879e", size = 196497, upload-time = "2025-12-06T19:04:15.487Z" },
    { url = "https://files.pythonhosted.org/packages/2e/eb/ac6d8517d44209e5a712fde46f26d0055e3e8969f24d715f70bd36056230/librt-0.7.3-cp314-cp314-win32.whl", hash = "sha256:fbd7351d43b80d9c64c3cfcb50008f786cc82cba0450e8599fdd64f264320bd3", size = 44678, upload-time = "2025-12-06T19:04:16.688Z" },
    { url = "https://files.pythonhosted.org/packages/e9/93/238f026d141faf9958da588c761a0812a1a21c98cc54a76f3608454e4e59/librt-0.7.3-cp314-cp314-win_amd64.whl", hash = "sha256:d376a35c6561e81d2590506804b428fc1075fcc6298fc5bb49b771534c0ba010", size = 51689, upload-time = "2025-12-06T19:04:17.726Z" },
    { url = "https://files.pythonhosted.org/packages/52/44/43f462ad9dcf9ed7d3172fe2e30d77b980956250bd90e9889a9cca93df2a/librt-0.7.3-cp314-cp314-win_arm64.whl", hash = "sha256:cbdb3f337c88b43c3b49ca377731912c101178be91cb5071aac48faa898e6f8e", size = 44662, upload-time = "2025-12-06T19:04:18.771Z" },
    { url = "https://files.pythonhosted.org/packages/1d/35/fed6348915f96b7323241de97f26e2af481e95183b34991df12fd5ce31b1/librt-0.7.3-cp314-cp314t-macosx_10_13_x86_64.whl", hash = "sha256:9f0e0927efe87cd42ad600628e595a1a0aa1c64f6d0b55f7e6059079a428641a", size = 57347, upload-time = "2025-12-06T19:04:19.812Z" },
    { url = "https://files.pythonhosted.org/packages/9a/f2/045383ccc83e3fea4fba1b761796584bc26817b6b2efb6b8a6731431d16f/librt-0.7.3-cp314-cp314t-macosx_11_0_arm64.whl", hash = "sha256:020c6db391268bcc8ce75105cb572df8cb659a43fd347366aaa407c366e5117a", size = 59223, upload-time = "2025-12-06T19:04:20.862Z" },
    { url = "https://files.pythonhosted.org/packages/77/3f/c081f8455ab1d7f4a10dbe58463ff97119272ff32494f21839c3b9029c2c/librt-0.7.3-cp314-cp314t-manylinux1_i686.manylinux_2_28_i686.manylinux_2_5_i686.whl", hash = "sha256:7af7785f5edd1f418da09a8cdb9ec84b0213e23d597413e06525340bcce1ea4f", size = 183861, upload-time = "2025-12-06T19:04:21.963Z" },
    { url = "https://files.pythonhosted.org/packages/1d/f5/73c5093c22c31fbeaebc25168837f05ebfd8bf26ce00855ef97a5308f36f/librt-0.7.3-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:8ccadf260bb46a61b9c7e89e2218f6efea9f3eeaaab4e3d1f58571890e54858e", size = 194594, upload-time = "2025-12-06T19:04:23.14Z" },
    { url = "https://files.pythonhosted.org/packages/78/b8/d5f17d4afe16612a4a94abfded94c16c5a033f183074fb130dfe56fc1a42/librt-0.7.3-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:d9883b2d819ce83f87ba82a746c81d14ada78784db431e57cc9719179847376e", size = 206759, upload-time = "2025-12-06T19:04:24.328Z" },
    { url = "https://files.pythonhosted.org/packages/36/2e/021765c1be85ee23ffd5b5b968bb4cba7526a4db2a0fc27dcafbdfc32da7/librt-0.7.3-cp314-cp314t-musllinux_1_2_aarch64.whl", hash = "sha256:59cb0470612d21fa1efddfa0dd710756b50d9c7fb6c1236bbf8ef8529331dc70", size = 203210, upload-time = "2025-12-06T19:04:25.544Z" },
    { url = "https://files.pythonhosted.org/packages/77/f0/9923656e42da4fd18c594bd08cf6d7e152d4158f8b808e210d967f0dcceb/librt-0.7.3-cp314-cp314t-musllinux_1_2_i686.whl", hash = "sha256:1fe603877e1865b5fd047a5e40379509a4a60204aa7aa0f72b16f7a41c3f0712", size = 196708, upload-time = "2025-12-06T19:04:26.725Z" },
    { url = "https://files.pythonhosted.org/packages/fc/0b/0708b886ac760e64d6fbe7e16024e4be3ad1a3629d19489a97e9cf4c3431/librt-0.7.3-cp314-cp314t-musllinux_1_2_x86_64.whl", hash = "sha256:5460d99ed30f043595bbdc888f542bad2caeb6226b01c33cda3ae444e8f82d42", size = 217212, upload-time = "2025-12-06T19:04:27.892Z" },
    { url = "https://files.pythonhosted.org/packages/5d/7f/12a73ff17bca4351e73d585dd9ebf46723c4a8622c4af7fe11a2e2d011ff/librt-0.7.3-cp314-cp314t-win32.whl", hash = "sha256:d09f677693328503c9e492e33e9601464297c01f9ebd966ea8fc5308f3069bfd", size = 45586, upload-time = "2025-12-06T19:04:29.116Z" },
    { url = "https://files.pythonhosted.org/packages/e2/df/8decd032ac9b995e4f5606cde783711a71094128d88d97a52e397daf2c89/librt-0.7.3-cp314-cp314t-win_amd64.whl", hash = "sha256:25711f364c64cab2c910a0247e90b51421e45dbc8910ceeb4eac97a9e132fc6f", size = 53002, upload-time = "2025-12-06T19:04:30.173Z" },
    { url = "https://files.pythonhosted.org/packages/de/0c/6605b6199de8178afe7efc77ca1d8e6db00453bc1d3349d27605c0f42104/librt-0.7.3-cp314-cp314t-win_arm64.whl", hash = "sha256:a9f9b661f82693eb56beb0605156c7fca57f535704ab91837405913417d6990b", size = 45647, upload-time = "2025-12-06T19:04:31.302Z" },
]

[[package]]
name = "markdown-it-py"
version = "4.0.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "mdurl" },
]
sdist = { url = "https://files.pythonhosted.org/packages/5b/f5/4ec618ed16cc4f8fb3b701563655a69816155e79e24a17b651541804721d/markdown_it_py-4.0.0.tar.gz", hash = "sha256:cb0a2b4aa34f932c007117b194e945bd74e0ec24133ceb5bac59009cda1cb9f3", size = 73070, upload-time = "2025-08-11T12:57:52.854Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/94/54/e7d793b573f298e1c9013b8c4dade17d481164aa517d1d7148619c2cedbf/markdown_it_py-4.0.0-py3-none-any.whl", hash = "sha256:87327c59b172c5011896038353a81343b6754500a08cd7a4973bb48c6d578147", size = 87321, upload-time = "2025-08-11T12:57:51.923Z" },
]

[[package]]
name = "mcp"
version = "1.26.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "anyio" },
    { name = "httpx" },
    { name = "httpx-sse" },
    { name = "jsonschema" },
    { name = "pydantic" },
    { name = "pydantic-settings" },
    { name = "pyjwt", extra = ["crypto"] },
    { name = "python-multipart" },
    { name = "pywin32", marker = "sys_platform == 'win32'" },
    { name = "sse-starlette" },
    { name = "starlette" },
    { name = "typing-extensions" },
    { name = "typing-inspection" },
    { name = "uvicorn", marker = "sys_platform != 'emscripten'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/fc/6d/62e76bbb8144d6ed86e202b5edd8a4cb631e7c8130f3f4893c3f90262b10/mcp-1.26.0.tar.gz", hash = "sha256:db6e2ef491eecc1a0d93711a76f28dec2e05999f93afd48795da1c1137142c66", size = 608005, upload-time = "2026-01-24T19:40:32.468Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/fd/d9/eaa1f80170d2b7c5ba23f3b59f766f3a0bb41155fbc32a69adfa1adaaef9/mcp-1.26.0-py3-none-any.whl", hash = "sha256:904a21c33c25aa98ddbeb47273033c435e595bbacfdb177f4bd87f6dceebe1ca", size = 233615, upload-time = "2026-01-24T19:40:30.652Z" },
]

[[package]]
name = "mdurl"
version = "0.1.2"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/d6/54/cfe61301667036ec958cb99bd3efefba235e65cdeb9c84d24a8293ba1d90/mdurl-0.1.2.tar.gz", hash = "sha256:bb413d29f5eea38f31dd4754dd7377d4465116fb207585f97bf925588687c1ba", size = 8729, upload-time = "2022-08-14T12:40:10.846Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b3/38/89ba8ad64ae25be8de66a6d463314cf1eb366222074cfda9ee839c56a4b4/mdurl-0.1.2-py3-none-any.whl", hash = "sha256:84008a41e51615a49fc9966191ff91509e3c40b939176e643fd50a5c2196b8f8", size = 9979, upload-time = "2022-08-14T12:40:09.779Z" },
]

[[package]]
name = "more-itertools"
version = "10.8.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/ea/5d/38b681d3fce7a266dd9ab73c66959406d565b3e85f21d5e66e1181d93721/more_itertools-10.8.0.tar.gz", hash = "sha256:f638ddf8a1a0d134181275fb5d58b086ead7c6a72429ad725c67503f13ba30bd", size = 137431, upload-time = "2025-09-02T15:23:11.018Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/a4/8e/469e5a4a2f5855992e425f3cb33804cc07bf18d48f2db061aec61ce50270/more_itertools-10.8.0-py3-none-any.whl", hash = "sha256:52d4362373dcf7c52546bc4af9a86ee7c4579df9a8dc268be0a2f949d376cc9b", size = 69667, upload-time = "2025-09-02T15:23:09.635Z" },
]

[[package]]
name = "mypy"
version = "1.19.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "librt" },
    { name = "mypy-extensions" },
    { name = "pathspec" },
    { name = "tomli", marker = "python_full_version < '3.11'" },
    { name = "typing-extensions" },
]
sdist = { url = "https://files.pythonhosted.org/packages/f9/b5/b58cdc25fadd424552804bf410855d52324183112aa004f0732c5f6324cf/mypy-1.19.0.tar.gz", hash = "sha256:f6b874ca77f733222641e5c46e4711648c4037ea13646fd0cdc814c2eaec2528", size = 3579025, upload-time = "2025-11-28T15:49:01.26Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/98/8f/55fb488c2b7dabd76e3f30c10f7ab0f6190c1fcbc3e97b1e588ec625bbe2/mypy-1.19.0-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:6148ede033982a8c5ca1143de34c71836a09f105068aaa8b7d5edab2b053e6c8", size = 13093239, upload-time = "2025-11-28T15:45:11.342Z" },
    { url = "https://files.pythonhosted.org/packages/72/1b/278beea978456c56b3262266274f335c3ba5ff2c8108b3b31bec1ffa4c1d/mypy-1.19.0-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:a9ac09e52bb0f7fb912f5d2a783345c72441a08ef56ce3e17c1752af36340a39", size = 12156128, upload-time = "2025-11-28T15:46:02.566Z" },
    { url = "https://files.pythonhosted.org/packages/21/f8/e06f951902e136ff74fd7a4dc4ef9d884faeb2f8eb9c49461235714f079f/mypy-1.19.0-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:11f7254c15ab3f8ed68f8e8f5cbe88757848df793e31c36aaa4d4f9783fd08ab", size = 12753508, upload-time = "2025-11-28T15:44:47.538Z" },
    { url = "https://files.pythonhosted.org/packages/67/5a/d035c534ad86e09cee274d53cf0fd769c0b29ca6ed5b32e205be3c06878c/mypy-1.19.0-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:318ba74f75899b0e78b847d8c50821e4c9637c79d9a59680fc1259f29338cb3e", size = 13507553, upload-time = "2025-11-28T15:44:39.26Z" },
    { url = "https://files.pythonhosted.org/packages/6a/17/c4a5498e00071ef29e483a01558b285d086825b61cf1fb2629fbdd019d94/mypy-1.19.0-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:cf7d84f497f78b682edd407f14a7b6e1a2212b433eedb054e2081380b7395aa3", size = 13792898, upload-time = "2025-11-28T15:44:31.102Z" },
    { url = "https://files.pythonhosted.org/packages/67/f6/bb542422b3ee4399ae1cdc463300d2d91515ab834c6233f2fd1d52fa21e0/mypy-1.19.0-cp310-cp310-win_amd64.whl", hash = "sha256:c3385246593ac2b97f155a0e9639be906e73534630f663747c71908dfbf26134", size = 10048835, upload-time = "2025-11-28T15:48:15.744Z" },
    { url = "https://files.pythonhosted.org/packages/0f/d2/010fb171ae5ac4a01cc34fbacd7544531e5ace95c35ca166dd8fd1b901d0/mypy-1.19.0-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:a31e4c28e8ddb042c84c5e977e28a21195d086aaffaf08b016b78e19c9ef8106", size = 13010563, upload-time = "2025-11-28T15:48:23.975Z" },
    { url = "https://files.pythonhosted.org/packages/41/6b/63f095c9f1ce584fdeb595d663d49e0980c735a1d2004720ccec252c5d47/mypy-1.19.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:34ec1ac66d31644f194b7c163d7f8b8434f1b49719d403a5d26c87fff7e913f7", size = 12077037, upload-time = "2025-11-28T15:47:51.582Z" },
    { url = "https://files.pythonhosted.org/packages/d7/83/6cb93d289038d809023ec20eb0b48bbb1d80af40511fa077da78af6ff7c7/mypy-1.19.0-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:cb64b0ba5980466a0f3f9990d1c582bcab8db12e29815ecb57f1408d99b4bff7", size = 12680255, upload-time = "2025-11-28T15:46:57.628Z" },
    { url = "https://files.pythonhosted.org/packages/99/db/d217815705987d2cbace2edd9100926196d6f85bcb9b5af05058d6e3c8ad/mypy-1.19.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:120cffe120cca5c23c03c77f84abc0c14c5d2e03736f6c312480020082f1994b", size = 13421472, upload-time = "2025-11-28T15:47:59.655Z" },
    { url = "https://files.pythonhosted.org/packages/4e/51/d2beaca7c497944b07594f3f8aad8d2f0e8fc53677059848ae5d6f4d193e/mypy-1.19.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:7a500ab5c444268a70565e374fc803972bfd1f09545b13418a5174e29883dab7", size = 13651823, upload-time = "2025-11-28T15:45:29.318Z" },
    { url = "https://files.pythonhosted.org/packages/aa/d1/7883dcf7644db3b69490f37b51029e0870aac4a7ad34d09ceae709a3df44/mypy-1.19.0-cp311-cp311-win_amd64.whl", hash = "sha256:c14a98bc63fd867530e8ec82f217dae29d0550c86e70debc9667fff1ec83284e", size = 10049077, upload-time = "2025-11-28T15:45:39.818Z" },
    { url = "https://files.pythonhosted.org/packages/11/7e/1afa8fb188b876abeaa14460dc4983f909aaacaa4bf5718c00b2c7e0b3d5/mypy-1.19.0-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:0fb3115cb8fa7c5f887c8a8d81ccdcb94cff334684980d847e5a62e926910e1d", size = 13207728, upload-time = "2025-11-28T15:46:26.463Z" },
    { url = "https://files.pythonhosted.org/packages/b2/13/f103d04962bcbefb1644f5ccb235998b32c337d6c13145ea390b9da47f3e/mypy-1.19.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:f3e19e3b897562276bb331074d64c076dbdd3e79213f36eed4e592272dabd760", size = 12202945, upload-time = "2025-11-28T15:48:49.143Z" },
    { url = "https://files.pythonhosted.org/packages/e4/93/a86a5608f74a22284a8ccea8592f6e270b61f95b8588951110ad797c2ddd/mypy-1.19.0-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:b9d491295825182fba01b6ffe2c6fe4e5a49dbf4e2bb4d1217b6ced3b4797bc6", size = 12718673, upload-time = "2025-11-28T15:47:37.193Z" },
    { url = "https://files.pythonhosted.org/packages/3d/58/cf08fff9ced0423b858f2a7495001fda28dc058136818ee9dffc31534ea9/mypy-1.19.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:6016c52ab209919b46169651b362068f632efcd5eb8ef9d1735f6f86da7853b2", size = 13608336, upload-time = "2025-11-28T15:48:32.625Z" },
    { url = "https://files.pythonhosted.org/packages/64/ed/9c509105c5a6d4b73bb08733102a3ea62c25bc02c51bca85e3134bf912d3/mypy-1.19.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:f188dcf16483b3e59f9278c4ed939ec0254aa8a60e8fc100648d9ab5ee95a431", size = 13833174, upload-time = "2025-11-28T15:45:48.091Z" },
    { url = "https://files.pythonhosted.org/packages/cd/71/01939b66e35c6f8cb3e6fdf0b657f0fd24de2f8ba5e523625c8e72328208/mypy-1.19.0-cp312-cp312-win_amd64.whl", hash = "sha256:0e3c3d1e1d62e678c339e7ade72746a9e0325de42cd2cccc51616c7b2ed1a018", size = 10112208, upload-time = "2025-11-28T15:46:41.702Z" },
    { url = "https://files.pythonhosted.org/packages/cb/0d/a1357e6bb49e37ce26fcf7e3cc55679ce9f4ebee0cd8b6ee3a0e301a9210/mypy-1.19.0-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:7686ed65dbabd24d20066f3115018d2dce030d8fa9db01aa9f0a59b6813e9f9e", size = 13191993, upload-time = "2025-11-28T15:47:22.336Z" },
    { url = "https://files.pythonhosted.org/packages/5d/75/8e5d492a879ec4490e6ba664b5154e48c46c85b5ac9785792a5ec6a4d58f/mypy-1.19.0-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:fd4a985b2e32f23bead72e2fb4bbe5d6aceee176be471243bd831d5b2644672d", size = 12174411, upload-time = "2025-11-28T15:44:55.492Z" },
    { url = "https://files.pythonhosted.org/packages/71/31/ad5dcee9bfe226e8eaba777e9d9d251c292650130f0450a280aec3485370/mypy-1.19.0-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:fc51a5b864f73a3a182584b1ac75c404396a17eced54341629d8bdcb644a5bba", size = 12727751, upload-time = "2025-11-28T15:44:14.169Z" },
    { url = "https://files.pythonhosted.org/packages/77/06/b6b8994ce07405f6039701f4b66e9d23f499d0b41c6dd46ec28f96d57ec3/mypy-1.19.0-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:37af5166f9475872034b56c5efdcf65ee25394e9e1d172907b84577120714364", size = 13593323, upload-time = "2025-11-28T15:46:34.699Z" },
    { url = "https://files.pythonhosted.org/packages/68/b1/126e274484cccdf099a8e328d4fda1c7bdb98a5e888fa6010b00e1bbf330/mypy-1.19.0-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:510c014b722308c9bd377993bcbf9a07d7e0692e5fa8fc70e639c1eb19fc6bee", size = 13818032, upload-time = "2025-11-28T15:46:18.286Z" },
    { url = "https://files.pythonhosted.org/packages/f8/56/53a8f70f562dfc466c766469133a8a4909f6c0012d83993143f2a9d48d2d/mypy-1.19.0-cp313-cp313-win_amd64.whl", hash = "sha256:cabbee74f29aa9cd3b444ec2f1e4fa5a9d0d746ce7567a6a609e224429781f53", size = 10120644, upload-time = "2025-11-28T15:47:43.99Z" },
    { url = "https://files.pythonhosted.org/packages/b0/f4/7751f32f56916f7f8c229fe902cbdba3e4dd3f3ea9e8b872be97e7fc546d/mypy-1.19.0-cp314-cp314-macosx_10_15_x86_64.whl", hash = "sha256:f2e36bed3c6d9b5f35d28b63ca4b727cb0228e480826ffc8953d1892ddc8999d", size = 13185236, upload-time = "2025-11-28T15:45:20.696Z" },
    { url = "https://files.pythonhosted.org/packages/35/31/871a9531f09e78e8d145032355890384f8a5b38c95a2c7732d226b93242e/mypy-1.19.0-cp314-cp314-macosx_11_0_arm64.whl", hash = "sha256:a18d8abdda14035c5718acb748faec09571432811af129bf0d9e7b2d6699bf18", size = 12213902, upload-time = "2025-11-28T15:46:10.117Z" },
    { url = "https://files.pythonhosted.org/packages/58/b8/af221910dd40eeefa2077a59107e611550167b9994693fc5926a0b0f87c0/mypy-1.19.0-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:f75e60aca3723a23511948539b0d7ed514dda194bc3755eae0bfc7a6b4887aa7", size = 12738600, upload-time = "2025-11-28T15:44:22.521Z" },
    { url = "https://files.pythonhosted.org/packages/11/9f/c39e89a3e319c1d9c734dedec1183b2cc3aefbab066ec611619002abb932/mypy-1.19.0-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:8f44f2ae3c58421ee05fe609160343c25f70e3967f6e32792b5a78006a9d850f", size = 13592639, upload-time = "2025-11-28T15:48:08.55Z" },
    { url = "https://files.pythonhosted.org/packages/97/6d/ffaf5f01f5e284d9033de1267e6c1b8f3783f2cf784465378a86122e884b/mypy-1.19.0-cp314-cp314-musllinux_1_2_x86_64.whl", hash = "sha256:63ea6a00e4bd6822adbfc75b02ab3653a17c02c4347f5bb0cf1d5b9df3a05835", size = 13799132, upload-time = "2025-11-28T15:47:06.032Z" },
    { url = "https://files.pythonhosted.org/packages/fe/b0/c33921e73aaa0106224e5a34822411bea38046188eb781637f5a5b07e269/mypy-1.19.0-cp314-cp314-win_amd64.whl", hash = "sha256:3ad925b14a0bb99821ff6f734553294aa6a3440a8cb082fe1f5b84dfb662afb1", size = 10269832, upload-time = "2025-11-28T15:47:29.392Z" },
    { url = "https://files.pythonhosted.org/packages/09/0e/fe228ed5aeab470c6f4eb82481837fadb642a5aa95cc8215fd2214822c10/mypy-1.19.0-py3-none-any.whl", hash = "sha256:0c01c99d626380752e527d5ce8e69ffbba2046eb8a060db0329690849cf9b6f9", size = 2469714, upload-time = "2025-11-28T15:45:33.22Z" },
]

[[package]]
name = "mypy-extensions"
version = "1.1.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/a2/6e/371856a3fb9d31ca8dac321cda606860fa4548858c0cc45d9d1d4ca2628b/mypy_extensions-1.1.0.tar.gz", hash = "sha256:52e68efc3284861e772bbcd66823fde5ae21fd2fdb51c62a211403730b916558", size = 6343, upload-time = "2025-04-22T14:54:24.164Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/79/7b/2c79738432f5c924bef5071f933bcc9efd0473bac3b4aa584a6f7c1c8df8/mypy_extensions-1.1.0-py3-none-any.whl", hash = "sha256:1be4cccdb0f2482337c4743e60421de3a356cd97508abadd57d47403e94f5505", size = 4963, upload-time = "2025-04-22T14:54:22.983Z" },
]

[[package]]
name = "openapi-pydantic"
version = "0.5.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "pydantic" },
]
sdist = { url = "https://files.pythonhosted.org/packages/02/2e/58d83848dd1a79cb92ed8e63f6ba901ca282c5f09d04af9423ec26c56fd7/openapi_pydantic-0.5.1.tar.gz", hash = "sha256:ff6835af6bde7a459fb93eb93bb92b8749b754fc6e51b2f1590a19dc3005ee0d", size = 60892, upload-time = "2025-01-08T19:29:27.083Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/12/cf/03675d8bd8ecbf4445504d8071adab19f5f993676795708e36402ab38263/openapi_pydantic-0.5.1-py3-none-any.whl", hash = "sha256:a3a09ef4586f5bd760a8df7f43028b60cafb6d9f61de2acba9574766255ab146", size = 96381, upload-time = "2025-01-08T19:29:25.275Z" },
]

[[package]]
name = "opentelemetry-api"
version = "1.40.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "importlib-metadata" },
    { name = "typing-extensions" },
]
sdist = { url = "https://files.pythonhosted.org/packages/2c/1d/4049a9e8698361cc1a1aa03a6c59e4fa4c71e0c0f94a30f988a6876a2ae6/opentelemetry_api-1.40.0.tar.gz", hash = "sha256:159be641c0b04d11e9ecd576906462773eb97ae1b657730f0ecf64d32071569f", size = 70851, upload-time = "2026-03-04T14:17:21.555Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/5f/bf/93795954016c522008da367da292adceed71cca6ee1717e1d64c83089099/opentelemetry_api-1.40.0-py3-none-any.whl", hash = "sha256:82dd69331ae74b06f6a874704be0cfaa49a1650e1537d4a813b86ecef7d0ecf9", size = 68676, upload-time = "2026-03-04T14:17:01.24Z" },
]

[[package]]
name = "packaging"
version = "25.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/a1/d4/1fc4078c65507b51b96ca8f8c3ba19e6a61c8253c72794544580a7b6c24d/packaging-25.0.tar.gz", hash = "sha256:d443872c98d677bf60f6a1f2f8c1cb748e8fe762d2bf9d3148b5599295b0fc4f", size = 165727, upload-time = "2025-04-19T11:48:59.673Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/20/12/38679034af332785aac8774540895e234f4d07f7545804097de4b666afd8/packaging-25.0-py3-none-any.whl", hash = "sha256:29572ef2b1f17581046b3a2227d5c611fb25ec70ca1ba8554b24b0e69331a484", size = 66469, upload-time = "2025-04-19T11:48:57.875Z" },
]

[[package]]
name = "pathable"
version = "0.5.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/72/55/b748445cb4ea6b125626f15379be7c96d1035d4fa3e8fee362fa92298abf/pathable-0.5.0.tar.gz", hash = "sha256:d81938348a1cacb525e7c75166270644782c0fb9c8cecc16be033e71427e0ef1", size = 16655, upload-time = "2026-02-20T08:47:00.748Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/52/96/5a770e5c461462575474468e5af931cff9de036e7c2b4fea23c1c58d2cbe/pathable-0.5.0-py3-none-any.whl", hash = "sha256:646e3d09491a6351a0c82632a09c02cdf70a252e73196b36d8a15ba0a114f0a6", size = 16867, upload-time = "2026-02-20T08:46:59.536Z" },
]

[[package]]
name = "pathspec"
version = "0.12.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/ca/bc/f35b8446f4531a7cb215605d100cd88b7ac6f44ab3fc94870c120ab3adbf/pathspec-0.12.1.tar.gz", hash = "sha256:a482d51503a1ab33b1c67a6c3813a26953dbdc71c31dacaef9a838c4e29f5712", size = 51043, upload-time = "2023-12-10T22:30:45Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/cc/20/ff623b09d963f88bfde16306a54e12ee5ea43e9b597108672ff3a408aad6/pathspec-0.12.1-py3-none-any.whl", hash = "sha256:a0d503e138a4c123b27490a4f7beda6a01c6f288df0e4a8b79c7eb0dc7b4cc08", size = 31191, upload-time = "2023-12-10T22:30:43.14Z" },
]

[[package]]
name = "platformdirs"
version = "4.9.4"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/19/56/8d4c30c8a1d07013911a8fdbd8f89440ef9f08d07a1b50ab8ca8be5a20f9/platformdirs-4.9.4.tar.gz", hash = "sha256:1ec356301b7dc906d83f371c8f487070e99d3ccf9e501686456394622a01a934", size = 28737, upload-time = "2026-03-05T18:34:13.271Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/63/d7/97f7e3a6abb67d8080dd406fd4df842c2be0efaf712d1c899c32a075027c/platformdirs-4.9.4-py3-none-any.whl", hash = "sha256:68a9a4619a666ea6439f2ff250c12a853cd1cbd5158d258bd824a7df6be2f868", size = 21216, upload-time = "2026-03-05T18:34:12.172Z" },
]

[[package]]
name = "pluggy"
version = "1.6.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/f9/e2/3e91f31a7d2b083fe6ef3fa267035b518369d9511ffab804f839851d2779/pluggy-1.6.0.tar.gz", hash = "sha256:7dcc130b76258d33b90f61b658791dede3486c3e6bfb003ee5c9bfb396dd22f3", size = 69412, upload-time = "2025-05-15T12:30:07.975Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/54/20/4d324d65cc6d9205fabedc306948156824eb9f0ee1633355a8f7ec5c66bf/pluggy-1.6.0-py3-none-any.whl", hash = "sha256:e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746", size = 20538, upload-time = "2025-05-15T12:30:06.134Z" },
]

[[package]]
name = "py-key-value-aio"
version = "0.4.4"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "beartype" },
    { name = "typing-extensions" },
]
sdist = { url = "https://files.pythonhosted.org/packages/04/3c/0397c072a38d4bc580994b42e0c90c5f44f679303489e4376289534735e5/py_key_value_aio-0.4.4.tar.gz", hash = "sha256:e3012e6243ed7cc09bb05457bd4d03b1ba5c2b1ca8700096b3927db79ffbbe55", size = 92300, upload-time = "2026-02-16T21:21:43.245Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/32/69/f1b537ee70b7def42d63124a539ed3026a11a3ffc3086947a1ca6e861868/py_key_value_aio-0.4.4-py3-none-any.whl", hash = "sha256:18e17564ecae61b987f909fc2cd41ee2012c84b4b1dcb8c055cf8b4bc1bf3f5d", size = 152291, upload-time = "2026-02-16T21:21:44.241Z" },
]

[package.optional-dependencies]
filetree = [
    { name = "aiofile" },
    { name = "anyio" },
]
keyring = [
    { name = "keyring" },
]
memory = [
    { name = "cachetools" },
]

[[package]]
name = "pycparser"
version = "2.23"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/fe/cf/d2d3b9f5699fb1e4615c8e32ff220203e43b248e1dfcc6736ad9057731ca/pycparser-2.23.tar.gz", hash = "sha256:78816d4f24add8f10a06d6f05b4d424ad9e96cfebf68a4ddc99c65c0720d00c2", size = 173734, upload-time = "2025-09-09T13:23:47.91Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/a0/e3/59cd50310fc9b59512193629e1984c1f95e5c8ae6e5d8c69532ccc65a7fe/pycparser-2.23-py3-none-any.whl", hash = "sha256:e5c6e8d3fbad53479cab09ac03729e0a9faf2bee3db8208a550daf5af81a5934", size = 118140, upload-time = "2025-09-09T13:23:46.651Z" },
]

[[package]]
name = "pydantic"
version = "2.12.5"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "annotated-types" },
    { name = "pydantic-core" },
    { name = "typing-extensions" },
    { name = "typing-inspection" },
]
sdist = { url = "https://files.pythonhosted.org/packages/69/44/36f1a6e523abc58ae5f928898e4aca2e0ea509b5aa6f6f392a5d882be928/pydantic-2.12.5.tar.gz", hash = "sha256:4d351024c75c0f085a9febbb665ce8c0c6ec5d30e903bdb6394b7ede26aebb49", size = 821591, upload-time = "2025-11-26T15:11:46.471Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/5a/87/b70ad306ebb6f9b585f114d0ac2137d792b48be34d732d60e597c2f8465a/pydantic-2.12.5-py3-none-any.whl", hash = "sha256:e561593fccf61e8a20fc46dfc2dfe075b8be7d0188df33f221ad1f0139180f9d", size = 463580, upload-time = "2025-11-26T15:11:44.605Z" },
]

[package.optional-dependencies]
email = [
    { name = "email-validator" },
]

[[package]]
name = "pydantic-core"
version = "2.41.5"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "typing-extensions" },
]
sdist = { url = "https://files.pythonhosted.org/packages/71/70/23b021c950c2addd24ec408e9ab05d59b035b39d97cdc1130e1bce647bb6/pydantic_core-2.41.5.tar.gz", hash = "sha256:08daa51ea16ad373ffd5e7606252cc32f07bc72b28284b6bc9c6df804816476e", size = 460952, upload-time = "2025-11-04T13:43:49.098Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/c6/90/32c9941e728d564b411d574d8ee0cf09b12ec978cb22b294995bae5549a5/pydantic_core-2.41.5-cp310-cp310-macosx_10_12_x86_64.whl", hash = "sha256:77b63866ca88d804225eaa4af3e664c5faf3568cea95360d21f4725ab6e07146", size = 2107298, upload-time = "2025-11-04T13:39:04.116Z" },
    { url = "https://files.pythonhosted.org/packages/fb/a8/61c96a77fe28993d9a6fb0f4127e05430a267b235a124545d79fea46dd65/pydantic_core-2.41.5-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:dfa8a0c812ac681395907e71e1274819dec685fec28273a28905df579ef137e2", size = 1901475, upload-time = "2025-11-04T13:39:06.055Z" },
    { url = "https://files.pythonhosted.org/packages/5d/b6/338abf60225acc18cdc08b4faef592d0310923d19a87fba1faf05af5346e/pydantic_core-2.41.5-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:5921a4d3ca3aee735d9fd163808f5e8dd6c6972101e4adbda9a4667908849b97", size = 1918815, upload-time = "2025-11-04T13:39:10.41Z" },
    { url = "https://files.pythonhosted.org/packages/d1/1c/2ed0433e682983d8e8cba9c8d8ef274d4791ec6a6f24c58935b90e780e0a/pydantic_core-2.41.5-cp310-cp310-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:e25c479382d26a2a41b7ebea1043564a937db462816ea07afa8a44c0866d52f9", size = 2065567, upload-time = "2025-11-04T13:39:12.244Z" },
    { url = "https://files.pythonhosted.org/packages/b3/24/cf84974ee7d6eae06b9e63289b7b8f6549d416b5c199ca2d7ce13bbcf619/pydantic_core-2.41.5-cp310-cp310-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:f547144f2966e1e16ae626d8ce72b4cfa0caedc7fa28052001c94fb2fcaa1c52", size = 2230442, upload-time = "2025-11-04T13:39:13.962Z" },
    { url = "https://files.pythonhosted.org/packages/fd/21/4e287865504b3edc0136c89c9c09431be326168b1eb7841911cbc877a995/pydantic_core-2.41.5-cp310-cp310-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:6f52298fbd394f9ed112d56f3d11aabd0d5bd27beb3084cc3d8ad069483b8941", size = 2350956, upload-time = "2025-11-04T13:39:15.889Z" },
    { url = "https://files.pythonhosted.org/packages/a8/76/7727ef2ffa4b62fcab916686a68a0426b9b790139720e1934e8ba797e238/pydantic_core-2.41.5-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:100baa204bb412b74fe285fb0f3a385256dad1d1879f0a5cb1499ed2e83d132a", size = 2068253, upload-time = "2025-11-04T13:39:17.403Z" },
    { url = "https://files.pythonhosted.org/packages/d5/8c/a4abfc79604bcb4c748e18975c44f94f756f08fb04218d5cb87eb0d3a63e/pydantic_core-2.41.5-cp310-cp310-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:05a2c8852530ad2812cb7914dc61a1125dc4e06252ee98e5638a12da6cc6fb6c", size = 2177050, upload-time = "2025-11-04T13:39:19.351Z" },
    { url = "https://files.pythonhosted.org/packages/67/b1/de2e9a9a79b480f9cb0b6e8b6ba4c50b18d4e89852426364c66aa82bb7b3/pydantic_core-2.41.5-cp310-cp310-musllinux_1_1_aarch64.whl", hash = "sha256:29452c56df2ed968d18d7e21f4ab0ac55e71dc59524872f6fc57dcf4a3249ed2", size = 2147178, upload-time = "2025-11-04T13:39:21Z" },
    { url = "https://files.pythonhosted.org/packages/16/c1/dfb33f837a47b20417500efaa0378adc6635b3c79e8369ff7a03c494b4ac/pydantic_core-2.41.5-cp310-cp310-musllinux_1_1_armv7l.whl", hash = "sha256:d5160812ea7a8a2ffbe233d8da666880cad0cbaf5d4de74ae15c313213d62556", size = 2341833, upload-time = "2025-11-04T13:39:22.606Z" },
    { url = "https://files.pythonhosted.org/packages/47/36/00f398642a0f4b815a9a558c4f1dca1b4020a7d49562807d7bc9ff279a6c/pydantic_core-2.41.5-cp310-cp310-musllinux_1_1_x86_64.whl", hash = "sha256:df3959765b553b9440adfd3c795617c352154e497a4eaf3752555cfb5da8fc49", size = 2321156, upload-time = "2025-11-04T13:39:25.843Z" },
    { url = "https://files.pythonhosted.org/packages/7e/70/cad3acd89fde2010807354d978725ae111ddf6d0ea46d1ea1775b5c1bd0c/pydantic_core-2.41.5-cp310-cp310-win32.whl", hash = "sha256:1f8d33a7f4d5a7889e60dc39856d76d09333d8a6ed0f5f1190635cbec70ec4ba", size = 1989378, upload-time = "2025-11-04T13:39:27.92Z" },
    { url = "https://files.pythonhosted.org/packages/76/92/d338652464c6c367e5608e4488201702cd1cbb0f33f7b6a85a60fe5f3720/pydantic_core-2.41.5-cp310-cp310-win_amd64.whl", hash = "sha256:62de39db01b8d593e45871af2af9e497295db8d73b085f6bfd0b18c83c70a8f9", size = 2013622, upload-time = "2025-11-04T13:39:29.848Z" },
    { url = "https://files.pythonhosted.org/packages/e8/72/74a989dd9f2084b3d9530b0915fdda64ac48831c30dbf7c72a41a5232db8/pydantic_core-2.41.5-cp311-cp311-macosx_10_12_x86_64.whl", hash = "sha256:a3a52f6156e73e7ccb0f8cced536adccb7042be67cb45f9562e12b319c119da6", size = 2105873, upload-time = "2025-11-04T13:39:31.373Z" },
    { url = "https://files.pythonhosted.org/packages/12/44/37e403fd9455708b3b942949e1d7febc02167662bf1a7da5b78ee1ea2842/pydantic_core-2.41.5-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:7f3bf998340c6d4b0c9a2f02d6a400e51f123b59565d74dc60d252ce888c260b", size = 1899826, upload-time = "2025-11-04T13:39:32.897Z" },
    { url = "https://files.pythonhosted.org/packages/33/7f/1d5cab3ccf44c1935a359d51a8a2a9e1a654b744b5e7f80d41b88d501eec/pydantic_core-2.41.5-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:378bec5c66998815d224c9ca994f1e14c0c21cb95d2f52b6021cc0b2a58f2a5a", size = 1917869, upload-time = "2025-11-04T13:39:34.469Z" },
    { url = "https://files.pythonhosted.org/packages/6e/6a/30d94a9674a7fe4f4744052ed6c5e083424510be1e93da5bc47569d11810/pydantic_core-2.41.5-cp311-cp311-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:e7b576130c69225432866fe2f4a469a85a54ade141d96fd396dffcf607b558f8", size = 2063890, upload-time = "2025-11-04T13:39:36.053Z" },
    { url = "https://files.pythonhosted.org/packages/50/be/76e5d46203fcb2750e542f32e6c371ffa9b8ad17364cf94bb0818dbfb50c/pydantic_core-2.41.5-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:6cb58b9c66f7e4179a2d5e0f849c48eff5c1fca560994d6eb6543abf955a149e", size = 2229740, upload-time = "2025-11-04T13:39:37.753Z" },
    { url = "https://files.pythonhosted.org/packages/d3/ee/fed784df0144793489f87db310a6bbf8118d7b630ed07aa180d6067e653a/pydantic_core-2.41.5-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:88942d3a3dff3afc8288c21e565e476fc278902ae4d6d134f1eeda118cc830b1", size = 2350021, upload-time = "2025-11-04T13:39:40.94Z" },
    { url = "https://files.pythonhosted.org/packages/c8/be/8fed28dd0a180dca19e72c233cbf58efa36df055e5b9d90d64fd1740b828/pydantic_core-2.41.5-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:f31d95a179f8d64d90f6831d71fa93290893a33148d890ba15de25642c5d075b", size = 2066378, upload-time = "2025-11-04T13:39:42.523Z" },
    { url = "https://files.pythonhosted.org/packages/b0/3b/698cf8ae1d536a010e05121b4958b1257f0b5522085e335360e53a6b1c8b/pydantic_core-2.41.5-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:c1df3d34aced70add6f867a8cf413e299177e0c22660cc767218373d0779487b", size = 2175761, upload-time = "2025-11-04T13:39:44.553Z" },
    { url = "https://files.pythonhosted.org/packages/b8/ba/15d537423939553116dea94ce02f9c31be0fa9d0b806d427e0308ec17145/pydantic_core-2.41.5-cp311-cp311-musllinux_1_1_aarch64.whl", hash = "sha256:4009935984bd36bd2c774e13f9a09563ce8de4abaa7226f5108262fa3e637284", size = 2146303, upload-time = "2025-11-04T13:39:46.238Z" },
    { url = "https://files.pythonhosted.org/packages/58/7f/0de669bf37d206723795f9c90c82966726a2ab06c336deba4735b55af431/pydantic_core-2.41.5-cp311-cp311-musllinux_1_1_armv7l.whl", hash = "sha256:34a64bc3441dc1213096a20fe27e8e128bd3ff89921706e83c0b1ac971276594", size = 2340355, upload-time = "2025-11-04T13:39:48.002Z" },
    { url = "https://files.pythonhosted.org/packages/e5/de/e7482c435b83d7e3c3ee5ee4451f6e8973cff0eb6007d2872ce6383f6398/pydantic_core-2.41.5-cp311-cp311-musllinux_1_1_x86_64.whl", hash = "sha256:c9e19dd6e28fdcaa5a1de679aec4141f691023916427ef9bae8584f9c2fb3b0e", size = 2319875, upload-time = "2025-11-04T13:39:49.705Z" },
    { url = "https://files.pythonhosted.org/packages/fe/e6/8c9e81bb6dd7560e33b9053351c29f30c8194b72f2d6932888581f503482/pydantic_core-2.41.5-cp311-cp311-win32.whl", hash = "sha256:2c010c6ded393148374c0f6f0bf89d206bf3217f201faa0635dcd56bd1520f6b", size = 1987549, upload-time = "2025-11-04T13:39:51.842Z" },
    { url = "https://files.pythonhosted.org/packages/11/66/f14d1d978ea94d1bc21fc98fcf570f9542fe55bfcc40269d4e1a21c19bf7/pydantic_core-2.41.5-cp311-cp311-win_amd64.whl", hash = "sha256:76ee27c6e9c7f16f47db7a94157112a2f3a00e958bc626e2f4ee8bec5c328fbe", size = 2011305, upload-time = "2025-11-04T13:39:53.485Z" },
    { url = "https://files.pythonhosted.org/packages/56/d8/0e271434e8efd03186c5386671328154ee349ff0354d83c74f5caaf096ed/pydantic_core-2.41.5-cp311-cp311-win_arm64.whl", hash = "sha256:4bc36bbc0b7584de96561184ad7f012478987882ebf9f9c389b23f432ea3d90f", size = 1972902, upload-time = "2025-11-04T13:39:56.488Z" },
    { url = "https://files.pythonhosted.org/packages/5f/5d/5f6c63eebb5afee93bcaae4ce9a898f3373ca23df3ccaef086d0233a35a7/pydantic_core-2.41.5-cp312-cp312-macosx_10_12_x86_64.whl", hash = "sha256:f41a7489d32336dbf2199c8c0a215390a751c5b014c2c1c5366e817202e9cdf7", size = 2110990, upload-time = "2025-11-04T13:39:58.079Z" },
    { url = "https://files.pythonhosted.org/packages/aa/32/9c2e8ccb57c01111e0fd091f236c7b371c1bccea0fa85247ac55b1e2b6b6/pydantic_core-2.41.5-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:070259a8818988b9a84a449a2a7337c7f430a22acc0859c6b110aa7212a6d9c0", size = 1896003, upload-time = "2025-11-04T13:39:59.956Z" },
    { url = "https://files.pythonhosted.org/packages/68/b8/a01b53cb0e59139fbc9e4fda3e9724ede8de279097179be4ff31f1abb65a/pydantic_core-2.41.5-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:e96cea19e34778f8d59fe40775a7a574d95816eb150850a85a7a4c8f4b94ac69", size = 1919200, upload-time = "2025-11-04T13:40:02.241Z" },
    { url = "https://files.pythonhosted.org/packages/38/de/8c36b5198a29bdaade07b5985e80a233a5ac27137846f3bc2d3b40a47360/pydantic_core-2.41.5-cp312-cp312-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:ed2e99c456e3fadd05c991f8f437ef902e00eedf34320ba2b0842bd1c3ca3a75", size = 2052578, upload-time = "2025-11-04T13:40:04.401Z" },
    { url = "https://files.pythonhosted.org/packages/00/b5/0e8e4b5b081eac6cb3dbb7e60a65907549a1ce035a724368c330112adfdd/pydantic_core-2.41.5-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:65840751b72fbfd82c3c640cff9284545342a4f1eb1586ad0636955b261b0b05", size = 2208504, upload-time = "2025-11-04T13:40:06.072Z" },
    { url = "https://files.pythonhosted.org/packages/77/56/87a61aad59c7c5b9dc8caad5a41a5545cba3810c3e828708b3d7404f6cef/pydantic_core-2.41.5-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:e536c98a7626a98feb2d3eaf75944ef6f3dbee447e1f841eae16f2f0a72d8ddc", size = 2335816, upload-time = "2025-11-04T13:40:07.835Z" },
    { url = "https://files.pythonhosted.org/packages/0d/76/941cc9f73529988688a665a5c0ecff1112b3d95ab48f81db5f7606f522d3/pydantic_core-2.41.5-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:eceb81a8d74f9267ef4081e246ffd6d129da5d87e37a77c9bde550cb04870c1c", size = 2075366, upload-time = "2025-11-04T13:40:09.804Z" },
    { url = "https://files.pythonhosted.org/packages/d3/43/ebef01f69baa07a482844faaa0a591bad1ef129253ffd0cdaa9d8a7f72d3/pydantic_core-2.41.5-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:d38548150c39b74aeeb0ce8ee1d8e82696f4a4e16ddc6de7b1d8823f7de4b9b5", size = 2171698, upload-time = "2025-11-04T13:40:12.004Z" },
    { url = "https://files.pythonhosted.org/packages/b1/87/41f3202e4193e3bacfc2c065fab7706ebe81af46a83d3e27605029c1f5a6/pydantic_core-2.41.5-cp312-cp312-musllinux_1_1_aarch64.whl", hash = "sha256:c23e27686783f60290e36827f9c626e63154b82b116d7fe9adba1fda36da706c", size = 2132603, upload-time = "2025-11-04T13:40:13.868Z" },
    { url = "https://files.pythonhosted.org/packages/49/7d/4c00df99cb12070b6bccdef4a195255e6020a550d572768d92cc54dba91a/pydantic_core-2.41.5-cp312-cp312-musllinux_1_1_armv7l.whl", hash = "sha256:482c982f814460eabe1d3bb0adfdc583387bd4691ef00b90575ca0d2b6fe2294", size = 2329591, upload-time = "2025-11-04T13:40:15.672Z" },
    { url = "https://files.pythonhosted.org/packages/cc/6a/ebf4b1d65d458f3cda6a7335d141305dfa19bdc61140a884d165a8a1bbc7/pydantic_core-2.41.5-cp312-cp312-musllinux_1_1_x86_64.whl", hash = "sha256:bfea2a5f0b4d8d43adf9d7b8bf019fb46fdd10a2e5cde477fbcb9d1fa08c68e1", size = 2319068, upload-time = "2025-11-04T13:40:17.532Z" },
    { url = "https://files.pythonhosted.org/packages/49/3b/774f2b5cd4192d5ab75870ce4381fd89cf218af999515baf07e7206753f0/pydantic_core-2.41.5-cp312-cp312-win32.whl", hash = "sha256:b74557b16e390ec12dca509bce9264c3bbd128f8a2c376eaa68003d7f327276d", size = 1985908, upload-time = "2025-11-04T13:40:19.309Z" },
    { url = "https://files.pythonhosted.org/packages/86/45/00173a033c801cacf67c190fef088789394feaf88a98a7035b0e40d53dc9/pydantic_core-2.41.5-cp312-cp312-win_amd64.whl", hash = "sha256:1962293292865bca8e54702b08a4f26da73adc83dd1fcf26fbc875b35d81c815", size = 2020145, upload-time = "2025-11-04T13:40:21.548Z" },
    { url = "https://files.pythonhosted.org/packages/f9/22/91fbc821fa6d261b376a3f73809f907cec5ca6025642c463d3488aad22fb/pydantic_core-2.41.5-cp312-cp312-win_arm64.whl", hash = "sha256:1746d4a3d9a794cacae06a5eaaccb4b8643a131d45fbc9af23e353dc0a5ba5c3", size = 1976179, upload-time = "2025-11-04T13:40:23.393Z" },
    { url = "https://files.pythonhosted.org/packages/87/06/8806241ff1f70d9939f9af039c6c35f2360cf16e93c2ca76f184e76b1564/pydantic_core-2.41.5-cp313-cp313-macosx_10_12_x86_64.whl", hash = "sha256:941103c9be18ac8daf7b7adca8228f8ed6bb7a1849020f643b3a14d15b1924d9", size = 2120403, upload-time = "2025-11-04T13:40:25.248Z" },
    { url = "https://files.pythonhosted.org/packages/94/02/abfa0e0bda67faa65fef1c84971c7e45928e108fe24333c81f3bfe35d5f5/pydantic_core-2.41.5-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:112e305c3314f40c93998e567879e887a3160bb8689ef3d2c04b6cc62c33ac34", size = 1896206, upload-time = "2025-11-04T13:40:27.099Z" },
    { url = "https://files.pythonhosted.org/packages/15/df/a4c740c0943e93e6500f9eb23f4ca7ec9bf71b19e608ae5b579678c8d02f/pydantic_core-2.41.5-cp313-cp313-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:0cbaad15cb0c90aa221d43c00e77bb33c93e8d36e0bf74760cd00e732d10a6a0", size = 1919307, upload-time = "2025-11-04T13:40:29.806Z" },
    { url = "https://files.pythonhosted.org/packages/9a/e3/6324802931ae1d123528988e0e86587c2072ac2e5394b4bc2bc34b61ff6e/pydantic_core-2.41.5-cp313-cp313-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:03ca43e12fab6023fc79d28ca6b39b05f794ad08ec2feccc59a339b02f2b3d33", size = 2063258, upload-time = "2025-11-04T13:40:33.544Z" },
    { url = "https://files.pythonhosted.org/packages/c9/d4/2230d7151d4957dd79c3044ea26346c148c98fbf0ee6ebd41056f2d62ab5/pydantic_core-2.41.5-cp313-cp313-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:dc799088c08fa04e43144b164feb0c13f9a0bc40503f8df3e9fde58a3c0c101e", size = 2214917, upload-time = "2025-11-04T13:40:35.479Z" },
    { url = "https://files.pythonhosted.org/packages/e6/9f/eaac5df17a3672fef0081b6c1bb0b82b33ee89aa5cec0d7b05f52fd4a1fa/pydantic_core-2.41.5-cp313-cp313-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:97aeba56665b4c3235a0e52b2c2f5ae9cd071b8a8310ad27bddb3f7fb30e9aa2", size = 2332186, upload-time = "2025-11-04T13:40:37.436Z" },
    { url = "https://files.pythonhosted.org/packages/cf/4e/35a80cae583a37cf15604b44240e45c05e04e86f9cfd766623149297e971/pydantic_core-2.41.5-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:406bf18d345822d6c21366031003612b9c77b3e29ffdb0f612367352aab7d586", size = 2073164, upload-time = "2025-11-04T13:40:40.289Z" },
    { url = "https://files.pythonhosted.org/packages/bf/e3/f6e262673c6140dd3305d144d032f7bd5f7497d3871c1428521f19f9efa2/pydantic_core-2.41.5-cp313-cp313-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:b93590ae81f7010dbe380cdeab6f515902ebcbefe0b9327cc4804d74e93ae69d", size = 2179146, upload-time = "2025-11-04T13:40:42.809Z" },
    { url = "https://files.pythonhosted.org/packages/75/c7/20bd7fc05f0c6ea2056a4565c6f36f8968c0924f19b7d97bbfea55780e73/pydantic_core-2.41.5-cp313-cp313-musllinux_1_1_aarch64.whl", hash = "sha256:01a3d0ab748ee531f4ea6c3e48ad9dac84ddba4b0d82291f87248f2f9de8d740", size = 2137788, upload-time = "2025-11-04T13:40:44.752Z" },
    { url = "https://files.pythonhosted.org/packages/3a/8d/34318ef985c45196e004bc46c6eab2eda437e744c124ef0dbe1ff2c9d06b/pydantic_core-2.41.5-cp313-cp313-musllinux_1_1_armv7l.whl", hash = "sha256:6561e94ba9dacc9c61bce40e2d6bdc3bfaa0259d3ff36ace3b1e6901936d2e3e", size = 2340133, upload-time = "2025-11-04T13:40:46.66Z" },
    { url = "https://files.pythonhosted.org/packages/9c/59/013626bf8c78a5a5d9350d12e7697d3d4de951a75565496abd40ccd46bee/pydantic_core-2.41.5-cp313-cp313-musllinux_1_1_x86_64.whl", hash = "sha256:915c3d10f81bec3a74fbd4faebe8391013ba61e5a1a8d48c4455b923bdda7858", size = 2324852, upload-time = "2025-11-04T13:40:48.575Z" },
    { url = "https://files.pythonhosted.org/packages/1a/d9/c248c103856f807ef70c18a4f986693a46a8ffe1602e5d361485da502d20/pydantic_core-2.41.5-cp313-cp313-win32.whl", hash = "sha256:650ae77860b45cfa6e2cdafc42618ceafab3a2d9a3811fcfbd3bbf8ac3c40d36", size = 1994679, upload-time = "2025-11-04T13:40:50.619Z" },
    { url = "https://files.pythonhosted.org/packages/9e/8b/341991b158ddab181cff136acd2552c9f35bd30380422a639c0671e99a91/pydantic_core-2.41.5-cp313-cp313-win_amd64.whl", hash = "sha256:79ec52ec461e99e13791ec6508c722742ad745571f234ea6255bed38c6480f11", size = 2019766, upload-time = "2025-11-04T13:40:52.631Z" },
    { url = "https://files.pythonhosted.org/packages/73/7d/f2f9db34af103bea3e09735bb40b021788a5e834c81eedb541991badf8f5/pydantic_core-2.41.5-cp313-cp313-win_arm64.whl", hash = "sha256:3f84d5c1b4ab906093bdc1ff10484838aca54ef08de4afa9de0f5f14d69639cd", size = 1981005, upload-time = "2025-11-04T13:40:54.734Z" },
    { url = "https://files.pythonhosted.org/packages/ea/28/46b7c5c9635ae96ea0fbb779e271a38129df2550f763937659ee6c5dbc65/pydantic_core-2.41.5-cp314-cp314-macosx_10_12_x86_64.whl", hash = "sha256:3f37a19d7ebcdd20b96485056ba9e8b304e27d9904d233d7b1015db320e51f0a", size = 2119622, upload-time = "2025-11-04T13:40:56.68Z" },
    { url = "https://files.pythonhosted.org/packages/74/1a/145646e5687e8d9a1e8d09acb278c8535ebe9e972e1f162ed338a622f193/pydantic_core-2.41.5-cp314-cp314-macosx_11_0_arm64.whl", hash = "sha256:1d1d9764366c73f996edd17abb6d9d7649a7eb690006ab6adbda117717099b14", size = 1891725, upload-time = "2025-11-04T13:40:58.807Z" },
    { url = "https://files.pythonhosted.org/packages/23/04/e89c29e267b8060b40dca97bfc64a19b2a3cf99018167ea1677d96368273/pydantic_core-2.41.5-cp314-cp314-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:25e1c2af0fce638d5f1988b686f3b3ea8cd7de5f244ca147c777769e798a9cd1", size = 1915040, upload-time = "2025-11-04T13:41:00.853Z" },
    { url = "https://files.pythonhosted.org/packages/84/a3/15a82ac7bd97992a82257f777b3583d3e84bdb06ba6858f745daa2ec8a85/pydantic_core-2.41.5-cp314-cp314-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:506d766a8727beef16b7adaeb8ee6217c64fc813646b424d0804d67c16eddb66", size = 2063691, upload-time = "2025-11-04T13:41:03.504Z" },
    { url = "https://files.pythonhosted.org/packages/74/9b/0046701313c6ef08c0c1cf0e028c67c770a4e1275ca73131563c5f2a310a/pydantic_core-2.41.5-cp314-cp314-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:4819fa52133c9aa3c387b3328f25c1facc356491e6135b459f1de698ff64d869", size = 2213897, upload-time = "2025-11-04T13:41:05.804Z" },
    { url = "https://files.pythonhosted.org/packages/8a/cd/6bac76ecd1b27e75a95ca3a9a559c643b3afcd2dd62086d4b7a32a18b169/pydantic_core-2.41.5-cp314-cp314-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:2b761d210c9ea91feda40d25b4efe82a1707da2ef62901466a42492c028553a2", size = 2333302, upload-time = "2025-11-04T13:41:07.809Z" },
    { url = "https://files.pythonhosted.org/packages/4c/d2/ef2074dc020dd6e109611a8be4449b98cd25e1b9b8a303c2f0fca2f2bcf7/pydantic_core-2.41.5-cp314-cp314-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:22f0fb8c1c583a3b6f24df2470833b40207e907b90c928cc8d3594b76f874375", size = 2064877, upload-time = "2025-11-04T13:41:09.827Z" },
    { url = "https://files.pythonhosted.org/packages/18/66/e9db17a9a763d72f03de903883c057b2592c09509ccfe468187f2a2eef29/pydantic_core-2.41.5-cp314-cp314-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:2782c870e99878c634505236d81e5443092fba820f0373997ff75f90f68cd553", size = 2180680, upload-time = "2025-11-04T13:41:12.379Z" },
    { url = "https://files.pythonhosted.org/packages/d3/9e/3ce66cebb929f3ced22be85d4c2399b8e85b622db77dad36b73c5387f8f8/pydantic_core-2.41.5-cp314-cp314-musllinux_1_1_aarch64.whl", hash = "sha256:0177272f88ab8312479336e1d777f6b124537d47f2123f89cb37e0accea97f90", size = 2138960, upload-time = "2025-11-04T13:41:14.627Z" },
    { url = "https://files.pythonhosted.org/packages/a6/62/205a998f4327d2079326b01abee48e502ea739d174f0a89295c481a2272e/pydantic_core-2.41.5-cp314-cp314-musllinux_1_1_armv7l.whl", hash = "sha256:63510af5e38f8955b8ee5687740d6ebf7c2a0886d15a6d65c32814613681bc07", size = 2339102, upload-time = "2025-11-04T13:41:16.868Z" },
    { url = "https://files.pythonhosted.org/packages/3c/0d/f05e79471e889d74d3d88f5bd20d0ed189ad94c2423d81ff8d0000aab4ff/pydantic_core-2.41.5-cp314-cp314-musllinux_1_1_x86_64.whl", hash = "sha256:e56ba91f47764cc14f1daacd723e3e82d1a89d783f0f5afe9c364b8bb491ccdb", size = 2326039, upload-time = "2025-11-04T13:41:18.934Z" },
    { url = "https://files.pythonhosted.org/packages/ec/e1/e08a6208bb100da7e0c4b288eed624a703f4d129bde2da475721a80cab32/pydantic_core-2.41.5-cp314-cp314-win32.whl", hash = "sha256:aec5cf2fd867b4ff45b9959f8b20ea3993fc93e63c7363fe6851424c8a7e7c23", size = 1995126, upload-time = "2025-11-04T13:41:21.418Z" },
    { url = "https://files.pythonhosted.org/packages/48/5d/56ba7b24e9557f99c9237e29f5c09913c81eeb2f3217e40e922353668092/pydantic_core-2.41.5-cp314-cp314-win_amd64.whl", hash = "sha256:8e7c86f27c585ef37c35e56a96363ab8de4e549a95512445b85c96d3e2f7c1bf", size = 2015489, upload-time = "2025-11-04T13:41:24.076Z" },
    { url = "https://files.pythonhosted.org/packages/4e/bb/f7a190991ec9e3e0ba22e4993d8755bbc4a32925c0b5b42775c03e8148f9/pydantic_core-2.41.5-cp314-cp314-win_arm64.whl", hash = "sha256:e672ba74fbc2dc8eea59fb6d4aed6845e6905fc2a8afe93175d94a83ba2a01a0", size = 1977288, upload-time = "2025-11-04T13:41:26.33Z" },
    { url = "https://files.pythonhosted.org/packages/92/ed/77542d0c51538e32e15afe7899d79efce4b81eee631d99850edc2f5e9349/pydantic_core-2.41.5-cp314-cp314t-macosx_10_12_x86_64.whl", hash = "sha256:8566def80554c3faa0e65ac30ab0932b9e3a5cd7f8323764303d468e5c37595a", size = 2120255, upload-time = "2025-11-04T13:41:28.569Z" },
    { url = "https://files.pythonhosted.org/packages/bb/3d/6913dde84d5be21e284439676168b28d8bbba5600d838b9dca99de0fad71/pydantic_core-2.41.5-cp314-cp314t-macosx_11_0_arm64.whl", hash = "sha256:b80aa5095cd3109962a298ce14110ae16b8c1aece8b72f9dafe81cf597ad80b3", size = 1863760, upload-time = "2025-11-04T13:41:31.055Z" },
    { url = "https://files.pythonhosted.org/packages/5a/f0/e5e6b99d4191da102f2b0eb9687aaa7f5bea5d9964071a84effc3e40f997/pydantic_core-2.41.5-cp314-cp314t-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:3006c3dd9ba34b0c094c544c6006cc79e87d8612999f1a5d43b769b89181f23c", size = 1878092, upload-time = "2025-11-04T13:41:33.21Z" },
    { url = "https://files.pythonhosted.org/packages/71/48/36fb760642d568925953bcc8116455513d6e34c4beaa37544118c36aba6d/pydantic_core-2.41.5-cp314-cp314t-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:72f6c8b11857a856bcfa48c86f5368439f74453563f951e473514579d44aa612", size = 2053385, upload-time = "2025-11-04T13:41:35.508Z" },
    { url = "https://files.pythonhosted.org/packages/20/25/92dc684dd8eb75a234bc1c764b4210cf2646479d54b47bf46061657292a8/pydantic_core-2.41.5-cp314-cp314t-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:5cb1b2f9742240e4bb26b652a5aeb840aa4b417c7748b6f8387927bc6e45e40d", size = 2218832, upload-time = "2025-11-04T13:41:37.732Z" },
    { url = "https://files.pythonhosted.org/packages/e2/09/f53e0b05023d3e30357d82eb35835d0f6340ca344720a4599cd663dca599/pydantic_core-2.41.5-cp314-cp314t-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:bd3d54f38609ff308209bd43acea66061494157703364ae40c951f83ba99a1a9", size = 2327585, upload-time = "2025-11-04T13:41:40Z" },
    { url = "https://files.pythonhosted.org/packages/aa/4e/2ae1aa85d6af35a39b236b1b1641de73f5a6ac4d5a7509f77b814885760c/pydantic_core-2.41.5-cp314-cp314t-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:2ff4321e56e879ee8d2a879501c8e469414d948f4aba74a2d4593184eb326660", size = 2041078, upload-time = "2025-11-04T13:41:42.323Z" },
    { url = "https://files.pythonhosted.org/packages/cd/13/2e215f17f0ef326fc72afe94776edb77525142c693767fc347ed6288728d/pydantic_core-2.41.5-cp314-cp314t-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:d0d2568a8c11bf8225044aa94409e21da0cb09dcdafe9ecd10250b2baad531a9", size = 2173914, upload-time = "2025-11-04T13:41:45.221Z" },
    { url = "https://files.pythonhosted.org/packages/02/7a/f999a6dcbcd0e5660bc348a3991c8915ce6599f4f2c6ac22f01d7a10816c/pydantic_core-2.41.5-cp314-cp314t-musllinux_1_1_aarch64.whl", hash = "sha256:a39455728aabd58ceabb03c90e12f71fd30fa69615760a075b9fec596456ccc3", size = 2129560, upload-time = "2025-11-04T13:41:47.474Z" },
    { url = "https://files.pythonhosted.org/packages/3a/b1/6c990ac65e3b4c079a4fb9f5b05f5b013afa0f4ed6780a3dd236d2cbdc64/pydantic_core-2.41.5-cp314-cp314t-musllinux_1_1_armv7l.whl", hash = "sha256:239edca560d05757817c13dc17c50766136d21f7cd0fac50295499ae24f90fdf", size = 2329244, upload-time = "2025-11-04T13:41:49.992Z" },
    { url = "https://files.pythonhosted.org/packages/d9/02/3c562f3a51afd4d88fff8dffb1771b30cfdfd79befd9883ee094f5b6c0d8/pydantic_core-2.41.5-cp314-cp314t-musllinux_1_1_x86_64.whl", hash = "sha256:2a5e06546e19f24c6a96a129142a75cee553cc018ffee48a460059b1185f4470", size = 2331955, upload-time = "2025-11-04T13:41:54.079Z" },
    { url = "https://files.pythonhosted.org/packages/5c/96/5fb7d8c3c17bc8c62fdb031c47d77a1af698f1d7a406b0f79aaa1338f9ad/pydantic_core-2.41.5-cp314-cp314t-win32.whl", hash = "sha256:b4ececa40ac28afa90871c2cc2b9ffd2ff0bf749380fbdf57d165fd23da353aa", size = 1988906, upload-time = "2025-11-04T13:41:56.606Z" },
    { url = "https://files.pythonhosted.org/packages/22/ed/182129d83032702912c2e2d8bbe33c036f342cc735737064668585dac28f/pydantic_core-2.41.5-cp314-cp314t-win_amd64.whl", hash = "sha256:80aa89cad80b32a912a65332f64a4450ed00966111b6615ca6816153d3585a8c", size = 1981607, upload-time = "2025-11-04T13:41:58.889Z" },
    { url = "https://files.pythonhosted.org/packages/9f/ed/068e41660b832bb0b1aa5b58011dea2a3fe0ba7861ff38c4d4904c1c1a99/pydantic_core-2.41.5-cp314-cp314t-win_arm64.whl", hash = "sha256:35b44f37a3199f771c3eaa53051bc8a70cd7b54f333531c59e29fd4db5d15008", size = 1974769, upload-time = "2025-11-04T13:42:01.186Z" },
    { url = "https://files.pythonhosted.org/packages/11/72/90fda5ee3b97e51c494938a4a44c3a35a9c96c19bba12372fb9c634d6f57/pydantic_core-2.41.5-graalpy311-graalpy242_311_native-macosx_10_12_x86_64.whl", hash = "sha256:b96d5f26b05d03cc60f11a7761a5ded1741da411e7fe0909e27a5e6a0cb7b034", size = 2115441, upload-time = "2025-11-04T13:42:39.557Z" },
    { url = "https://files.pythonhosted.org/packages/1f/53/8942f884fa33f50794f119012dc6a1a02ac43a56407adaac20463df8e98f/pydantic_core-2.41.5-graalpy311-graalpy242_311_native-macosx_11_0_arm64.whl", hash = "sha256:634e8609e89ceecea15e2d61bc9ac3718caaaa71963717bf3c8f38bfde64242c", size = 1930291, upload-time = "2025-11-04T13:42:42.169Z" },
    { url = "https://files.pythonhosted.org/packages/79/c8/ecb9ed9cd942bce09fc888ee960b52654fbdbede4ba6c2d6e0d3b1d8b49c/pydantic_core-2.41.5-graalpy311-graalpy242_311_native-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:93e8740d7503eb008aa2df04d3b9735f845d43ae845e6dcd2be0b55a2da43cd2", size = 1948632, upload-time = "2025-11-04T13:42:44.564Z" },
    { url = "https://files.pythonhosted.org/packages/2e/1b/687711069de7efa6af934e74f601e2a4307365e8fdc404703afc453eab26/pydantic_core-2.41.5-graalpy311-graalpy242_311_native-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:f15489ba13d61f670dcc96772e733aad1a6f9c429cc27574c6cdaed82d0146ad", size = 2138905, upload-time = "2025-11-04T13:42:47.156Z" },
    { url = "https://files.pythonhosted.org/packages/09/32/59b0c7e63e277fa7911c2fc70ccfb45ce4b98991e7ef37110663437005af/pydantic_core-2.41.5-graalpy312-graalpy250_312_native-macosx_10_12_x86_64.whl", hash = "sha256:7da7087d756b19037bc2c06edc6c170eeef3c3bafcb8f532ff17d64dc427adfd", size = 2110495, upload-time = "2025-11-04T13:42:49.689Z" },
    { url = "https://files.pythonhosted.org/packages/aa/81/05e400037eaf55ad400bcd318c05bb345b57e708887f07ddb2d20e3f0e98/pydantic_core-2.41.5-graalpy312-graalpy250_312_native-macosx_11_0_arm64.whl", hash = "sha256:aabf5777b5c8ca26f7824cb4a120a740c9588ed58df9b2d196ce92fba42ff8dc", size = 1915388, upload-time = "2025-11-04T13:42:52.215Z" },
    { url = "https://files.pythonhosted.org/packages/6e/0d/e3549b2399f71d56476b77dbf3cf8937cec5cd70536bdc0e374a421d0599/pydantic_core-2.41.5-graalpy312-graalpy250_312_native-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:c007fe8a43d43b3969e8469004e9845944f1a80e6acd47c150856bb87f230c56", size = 1942879, upload-time = "2025-11-04T13:42:56.483Z" },
    { url = "https://files.pythonhosted.org/packages/f7/07/34573da085946b6a313d7c42f82f16e8920bfd730665de2d11c0c37a74b5/pydantic_core-2.41.5-graalpy312-graalpy250_312_native-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:76d0819de158cd855d1cbb8fcafdf6f5cf1eb8e470abe056d5d161106e38062b", size = 2139017, upload-time = "2025-11-04T13:42:59.471Z" },
    { url = "https://files.pythonhosted.org/packages/e6/b0/1a2aa41e3b5a4ba11420aba2d091b2d17959c8d1519ece3627c371951e73/pydantic_core-2.41.5-pp310-pypy310_pp73-macosx_10_12_x86_64.whl", hash = "sha256:b5819cd790dbf0c5eb9f82c73c16b39a65dd6dd4d1439dcdea7816ec9adddab8", size = 2103351, upload-time = "2025-11-04T13:43:02.058Z" },
    { url = "https://files.pythonhosted.org/packages/a4/ee/31b1f0020baaf6d091c87900ae05c6aeae101fa4e188e1613c80e4f1ea31/pydantic_core-2.41.5-pp310-pypy310_pp73-macosx_11_0_arm64.whl", hash = "sha256:5a4e67afbc95fa5c34cf27d9089bca7fcab4e51e57278d710320a70b956d1b9a", size = 1925363, upload-time = "2025-11-04T13:43:05.159Z" },
    { url = "https://files.pythonhosted.org/packages/e1/89/ab8e86208467e467a80deaca4e434adac37b10a9d134cd2f99b28a01e483/pydantic_core-2.41.5-pp310-pypy310_pp73-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:ece5c59f0ce7d001e017643d8d24da587ea1f74f6993467d85ae8a5ef9d4f42b", size = 2135615, upload-time = "2025-11-04T13:43:08.116Z" },
    { url = "https://files.pythonhosted.org/packages/99/0a/99a53d06dd0348b2008f2f30884b34719c323f16c3be4e6cc1203b74a91d/pydantic_core-2.41.5-pp310-pypy310_pp73-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:16f80f7abe3351f8ea6858914ddc8c77e02578544a0ebc15b4c2e1a0e813b0b2", size = 2175369, upload-time = "2025-11-04T13:43:12.49Z" },
    { url = "https://files.pythonhosted.org/packages/6d/94/30ca3b73c6d485b9bb0bc66e611cff4a7138ff9736b7e66bcf0852151636/pydantic_core-2.41.5-pp310-pypy310_pp73-musllinux_1_1_aarch64.whl", hash = "sha256:33cb885e759a705b426baada1fe68cbb0a2e68e34c5d0d0289a364cf01709093", size = 2144218, upload-time = "2025-11-04T13:43:15.431Z" },
    { url = "https://files.pythonhosted.org/packages/87/57/31b4f8e12680b739a91f472b5671294236b82586889ef764b5fbc6669238/pydantic_core-2.41.5-pp310-pypy310_pp73-musllinux_1_1_armv7l.whl", hash = "sha256:c8d8b4eb992936023be7dee581270af5c6e0697a8559895f527f5b7105ecd36a", size = 2329951, upload-time = "2025-11-04T13:43:18.062Z" },
    { url = "https://files.pythonhosted.org/packages/7d/73/3c2c8edef77b8f7310e6fb012dbc4b8551386ed575b9eb6fb2506e28a7eb/pydantic_core-2.41.5-pp310-pypy310_pp73-musllinux_1_1_x86_64.whl", hash = "sha256:242a206cd0318f95cd21bdacff3fcc3aab23e79bba5cac3db5a841c9ef9c6963", size = 2318428, upload-time = "2025-11-04T13:43:20.679Z" },
    { url = "https://files.pythonhosted.org/packages/2f/02/8559b1f26ee0d502c74f9cca5c0d2fd97e967e083e006bbbb4e97f3a043a/pydantic_core-2.41.5-pp310-pypy310_pp73-win_amd64.whl", hash = "sha256:d3a978c4f57a597908b7e697229d996d77a6d3c94901e9edee593adada95ce1a", size = 2147009, upload-time = "2025-11-04T13:43:23.286Z" },
    { url = "https://files.pythonhosted.org/packages/5f/9b/1b3f0e9f9305839d7e84912f9e8bfbd191ed1b1ef48083609f0dabde978c/pydantic_core-2.41.5-pp311-pypy311_pp73-macosx_10_12_x86_64.whl", hash = "sha256:b2379fa7ed44ddecb5bfe4e48577d752db9fc10be00a6b7446e9663ba143de26", size = 2101980, upload-time = "2025-11-04T13:43:25.97Z" },
    { url = "https://files.pythonhosted.org/packages/a4/ed/d71fefcb4263df0da6a85b5d8a7508360f2f2e9b3bf5814be9c8bccdccc1/pydantic_core-2.41.5-pp311-pypy311_pp73-macosx_11_0_arm64.whl", hash = "sha256:266fb4cbf5e3cbd0b53669a6d1b039c45e3ce651fd5442eff4d07c2cc8d66808", size = 1923865, upload-time = "2025-11-04T13:43:28.763Z" },
    { url = "https://files.pythonhosted.org/packages/ce/3a/626b38db460d675f873e4444b4bb030453bbe7b4ba55df821d026a0493c4/pydantic_core-2.41.5-pp311-pypy311_pp73-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:58133647260ea01e4d0500089a8c4f07bd7aa6ce109682b1426394988d8aaacc", size = 2134256, upload-time = "2025-11-04T13:43:31.71Z" },
    { url = "https://files.pythonhosted.org/packages/83/d9/8412d7f06f616bbc053d30cb4e5f76786af3221462ad5eee1f202021eb4e/pydantic_core-2.41.5-pp311-pypy311_pp73-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:287dad91cfb551c363dc62899a80e9e14da1f0e2b6ebde82c806612ca2a13ef1", size = 2174762, upload-time = "2025-11-04T13:43:34.744Z" },
    { url = "https://files.pythonhosted.org/packages/55/4c/162d906b8e3ba3a99354e20faa1b49a85206c47de97a639510a0e673f5da/pydantic_core-2.41.5-pp311-pypy311_pp73-musllinux_1_1_aarch64.whl", hash = "sha256:03b77d184b9eb40240ae9fd676ca364ce1085f203e1b1256f8ab9984dca80a84", size = 2143141, upload-time = "2025-11-04T13:43:37.701Z" },
    { url = "https://files.pythonhosted.org/packages/1f/f2/f11dd73284122713f5f89fc940f370d035fa8e1e078d446b3313955157fe/pydantic_core-2.41.5-pp311-pypy311_pp73-musllinux_1_1_armv7l.whl", hash = "sha256:a668ce24de96165bb239160b3d854943128f4334822900534f2fe947930e5770", size = 2330317, upload-time = "2025-11-04T13:43:40.406Z" },
    { url = "https://files.pythonhosted.org/packages/88/9d/b06ca6acfe4abb296110fb1273a4d848a0bfb2ff65f3ee92127b3244e16b/pydantic_core-2.41.5-pp311-pypy311_pp73-musllinux_1_1_x86_64.whl", hash = "sha256:f14f8f046c14563f8eb3f45f499cc658ab8d10072961e07225e507adb700e93f", size = 2316992, upload-time = "2025-11-04T13:43:43.602Z" },
    { url = "https://files.pythonhosted.org/packages/36/c7/cfc8e811f061c841d7990b0201912c3556bfeb99cdcb7ed24adc8d6f8704/pydantic_core-2.41.5-pp311-pypy311_pp73-win_amd64.whl", hash = "sha256:56121965f7a4dc965bff783d70b907ddf3d57f6eba29b6d2e5dabfaf07799c51", size = 2145302, upload-time = "2025-11-04T13:43:46.64Z" },
]

[[package]]
name = "pydantic-settings"
version = "2.12.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "pydantic" },
    { name = "python-dotenv" },
    { name = "typing-inspection" },
]
sdist = { url = "https://files.pythonhosted.org/packages/43/4b/ac7e0aae12027748076d72a8764ff1c9d82ca75a7a52622e67ed3f765c54/pydantic_settings-2.12.0.tar.gz", hash = "sha256:005538ef951e3c2a68e1c08b292b5f2e71490def8589d4221b95dab00dafcfd0", size = 194184, upload-time = "2025-11-10T14:25:47.013Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/c1/60/5d4751ba3f4a40a6891f24eec885f51afd78d208498268c734e256fb13c4/pydantic_settings-2.12.0-py3-none-any.whl", hash = "sha256:fddb9fd99a5b18da837b29710391e945b1e30c135477f484084ee513adb93809", size = 51880, upload-time = "2025-11-10T14:25:45.546Z" },
]

[[package]]
name = "pygments"
version = "2.19.2"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/b0/77/a5b8c569bf593b0140bde72ea885a803b82086995367bf2037de0159d924/pygments-2.19.2.tar.gz", hash = "sha256:636cb2477cec7f8952536970bc533bc43743542f70392ae026374600add5b887", size = 4968631, upload-time = "2025-06-21T13:39:12.283Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/c7/21/705964c7812476f378728bdf590ca4b771ec72385c533964653c68e86bdc/pygments-2.19.2-py3-none-any.whl", hash = "sha256:86540386c03d588bb81d44bc3928634ff26449851e99741617ecb9037ee5ec0b", size = 1225217, upload-time = "2025-06-21T13:39:07.939Z" },
]

[[package]]
name = "pyjwt"
version = "2.10.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/e7/46/bd74733ff231675599650d3e47f361794b22ef3e3770998dda30d3b63726/pyjwt-2.10.1.tar.gz", hash = "sha256:3cc5772eb20009233caf06e9d8a0577824723b44e6648ee0a2aedb6cf9381953", size = 87785, upload-time = "2024-11-28T03:43:29.933Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/61/ad/689f02752eeec26aed679477e80e632ef1b682313be70793d798c1d5fc8f/PyJWT-2.10.1-py3-none-any.whl", hash = "sha256:dcdd193e30abefd5debf142f9adfcdd2b58004e644f25406ffaebd50bd98dacb", size = 22997, upload-time = "2024-11-28T03:43:27.893Z" },
]

[package.optional-dependencies]
crypto = [
    { name = "cryptography" },
]

[[package]]
name = "pyperclip"
version = "1.11.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/e8/52/d87eba7cb129b81563019d1679026e7a112ef76855d6159d24754dbd2a51/pyperclip-1.11.0.tar.gz", hash = "sha256:244035963e4428530d9e3a6101a1ef97209c6825edab1567beac148ccc1db1b6", size = 12185, upload-time = "2025-09-26T14:40:37.245Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/df/80/fc9d01d5ed37ba4c42ca2b55b4339ae6e200b456be3a1aaddf4a9fa99b8c/pyperclip-1.11.0-py3-none-any.whl", hash = "sha256:299403e9ff44581cb9ba2ffeed69c7aa96a008622ad0c46cb575ca75b5b84273", size = 11063, upload-time = "2025-09-26T14:40:36.069Z" },
]

[[package]]
name = "pytest"
version = "9.0.2"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "colorama", marker = "sys_platform == 'win32'" },
    { name = "exceptiongroup", marker = "python_full_version < '3.11'" },
    { name = "iniconfig" },
    { name = "packaging" },
    { name = "pluggy" },
    { name = "pygments" },
    { name = "tomli", marker = "python_full_version < '3.11'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/d1/db/7ef3487e0fb0049ddb5ce41d3a49c235bf9ad299b6a25d5780a89f19230f/pytest-9.0.2.tar.gz", hash = "sha256:75186651a92bd89611d1d9fc20f0b4345fd827c41ccd5c299a868a05d70edf11", size = 1568901, upload-time = "2025-12-06T21:30:51.014Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/3b/ab/b3226f0bd7cdcf710fbede2b3548584366da3b19b5021e74f5bde2a8fa3f/pytest-9.0.2-py3-none-any.whl", hash = "sha256:711ffd45bf766d5264d487b917733b453d917afd2b0ad65223959f59089f875b", size = 374801, upload-time = "2025-12-06T21:30:49.154Z" },
]

[[package]]
name = "pytest-asyncio"
version = "1.3.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "backports-asyncio-runner", marker = "python_full_version < '3.11'" },
    { name = "pytest" },
    { name = "typing-extensions", marker = "python_full_version < '3.13'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/90/2c/8af215c0f776415f3590cac4f9086ccefd6fd463befeae41cd4d3f193e5a/pytest_asyncio-1.3.0.tar.gz", hash = "sha256:d7f52f36d231b80ee124cd216ffb19369aa168fc10095013c6b014a34d3ee9e5", size = 50087, upload-time = "2025-11-10T16:07:47.256Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/e5/35/f8b19922b6a25bc0880171a2f1a003eaeb93657475193ab516fd87cac9da/pytest_asyncio-1.3.0-py3-none-any.whl", hash = "sha256:611e26147c7f77640e6d0a92a38ed17c3e9848063698d5c93d5aa7aa11cebff5", size = 15075, upload-time = "2025-11-10T16:07:45.537Z" },
]

[[package]]
name = "python-dotenv"
version = "1.2.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/f0/26/19cadc79a718c5edbec86fd4919a6b6d3f681039a2f6d66d14be94e75fb9/python_dotenv-1.2.1.tar.gz", hash = "sha256:42667e897e16ab0d66954af0e60a9caa94f0fd4ecf3aaf6d2d260eec1aa36ad6", size = 44221, upload-time = "2025-10-26T15:12:10.434Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/14/1b/a298b06749107c305e1fe0f814c6c74aea7b2f1e10989cb30f544a1b3253/python_dotenv-1.2.1-py3-none-any.whl", hash = "sha256:b81ee9561e9ca4004139c6cbba3a238c32b03e4894671e181b671e8cb8425d61", size = 21230, upload-time = "2025-10-26T15:12:09.109Z" },
]

[[package]]
name = "python-multipart"
version = "0.0.22"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/94/01/979e98d542a70714b0cb2b6728ed0b7c46792b695e3eaec3e20711271ca3/python_multipart-0.0.22.tar.gz", hash = "sha256:7340bef99a7e0032613f56dc36027b959fd3b30a787ed62d310e951f7c3a3a58", size = 37612, upload-time = "2026-01-25T10:15:56.219Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/1b/d0/397f9626e711ff749a95d96b7af99b9c566a9bb5129b8e4c10fc4d100304/python_multipart-0.0.22-py3-none-any.whl", hash = "sha256:2b2cd894c83d21bf49d702499531c7bafd057d730c201782048f7945d82de155", size = 24579, upload-time = "2026-01-25T10:15:54.811Z" },
]

[[package]]
name = "pywin32"
version = "311"
source = { registry = "https://pypi.org/simple" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/7b/40/44efbb0dfbd33aca6a6483191dae0716070ed99e2ecb0c53683f400a0b4f/pywin32-311-cp310-cp310-win32.whl", hash = "sha256:d03ff496d2a0cd4a5893504789d4a15399133fe82517455e78bad62efbb7f0a3", size = 8760432, upload-time = "2025-07-14T20:13:05.9Z" },
    { url = "https://files.pythonhosted.org/packages/5e/bf/360243b1e953bd254a82f12653974be395ba880e7ec23e3731d9f73921cc/pywin32-311-cp310-cp310-win_amd64.whl", hash = "sha256:797c2772017851984b97180b0bebe4b620bb86328e8a884bb626156295a63b3b", size = 9590103, upload-time = "2025-07-14T20:13:07.698Z" },
    { url = "https://files.pythonhosted.org/packages/57/38/d290720e6f138086fb3d5ffe0b6caa019a791dd57866940c82e4eeaf2012/pywin32-311-cp310-cp310-win_arm64.whl", hash = "sha256:0502d1facf1fed4839a9a51ccbcc63d952cf318f78ffc00a7e78528ac27d7a2b", size = 8778557, upload-time = "2025-07-14T20:13:11.11Z" },
    { url = "https://files.pythonhosted.org/packages/7c/af/449a6a91e5d6db51420875c54f6aff7c97a86a3b13a0b4f1a5c13b988de3/pywin32-311-cp311-cp311-win32.whl", hash = "sha256:184eb5e436dea364dcd3d2316d577d625c0351bf237c4e9a5fabbcfa5a58b151", size = 8697031, upload-time = "2025-07-14T20:13:13.266Z" },
    { url = "https://files.pythonhosted.org/packages/51/8f/9bb81dd5bb77d22243d33c8397f09377056d5c687aa6d4042bea7fbf8364/pywin32-311-cp311-cp311-win_amd64.whl", hash = "sha256:3ce80b34b22b17ccbd937a6e78e7225d80c52f5ab9940fe0506a1a16f3dab503", size = 9508308, upload-time = "2025-07-14T20:13:15.147Z" },
    { url = "https://files.pythonhosted.org/packages/44/7b/9c2ab54f74a138c491aba1b1cd0795ba61f144c711daea84a88b63dc0f6c/pywin32-311-cp311-cp311-win_arm64.whl", hash = "sha256:a733f1388e1a842abb67ffa8e7aad0e70ac519e09b0f6a784e65a136ec7cefd2", size = 8703930, upload-time = "2025-07-14T20:13:16.945Z" },
    { url = "https://files.pythonhosted.org/packages/e7/ab/01ea1943d4eba0f850c3c61e78e8dd59757ff815ff3ccd0a84de5f541f42/pywin32-311-cp312-cp312-win32.whl", hash = "sha256:750ec6e621af2b948540032557b10a2d43b0cee2ae9758c54154d711cc852d31", size = 8706543, upload-time = "2025-07-14T20:13:20.765Z" },
    { url = "https://files.pythonhosted.org/packages/d1/a8/a0e8d07d4d051ec7502cd58b291ec98dcc0c3fff027caad0470b72cfcc2f/pywin32-311-cp312-cp312-win_amd64.whl", hash = "sha256:b8c095edad5c211ff31c05223658e71bf7116daa0ecf3ad85f3201ea3190d067", size = 9495040, upload-time = "2025-07-14T20:13:22.543Z" },
    { url = "https://files.pythonhosted.org/packages/ba/3a/2ae996277b4b50f17d61f0603efd8253cb2d79cc7ae159468007b586396d/pywin32-311-cp312-cp312-win_arm64.whl", hash = "sha256:e286f46a9a39c4a18b319c28f59b61de793654af2f395c102b4f819e584b5852", size = 8710102, upload-time = "2025-07-14T20:13:24.682Z" },
    { url = "https://files.pythonhosted.org/packages/a5/be/3fd5de0979fcb3994bfee0d65ed8ca9506a8a1260651b86174f6a86f52b3/pywin32-311-cp313-cp313-win32.whl", hash = "sha256:f95ba5a847cba10dd8c4d8fefa9f2a6cf283b8b88ed6178fa8a6c1ab16054d0d", size = 8705700, upload-time = "2025-07-14T20:13:26.471Z" },
    { url = "https://files.pythonhosted.org/packages/e3/28/e0a1909523c6890208295a29e05c2adb2126364e289826c0a8bc7297bd5c/pywin32-311-cp313-cp313-win_amd64.whl", hash = "sha256:718a38f7e5b058e76aee1c56ddd06908116d35147e133427e59a3983f703a20d", size = 9494700, upload-time = "2025-07-14T20:13:28.243Z" },
    { url = "https://files.pythonhosted.org/packages/04/bf/90339ac0f55726dce7d794e6d79a18a91265bdf3aa70b6b9ca52f35e022a/pywin32-311-cp313-cp313-win_arm64.whl", hash = "sha256:7b4075d959648406202d92a2310cb990fea19b535c7f4a78d3f5e10b926eeb8a", size = 8709318, upload-time = "2025-07-14T20:13:30.348Z" },
    { url = "https://files.pythonhosted.org/packages/c9/31/097f2e132c4f16d99a22bfb777e0fd88bd8e1c634304e102f313af69ace5/pywin32-311-cp314-cp314-win32.whl", hash = "sha256:b7a2c10b93f8986666d0c803ee19b5990885872a7de910fc460f9b0c2fbf92ee", size = 8840714, upload-time = "2025-07-14T20:13:32.449Z" },
    { url = "https://files.pythonhosted.org/packages/90/4b/07c77d8ba0e01349358082713400435347df8426208171ce297da32c313d/pywin32-311-cp314-cp314-win_amd64.whl", hash = "sha256:3aca44c046bd2ed8c90de9cb8427f581c479e594e99b5c0bb19b29c10fd6cb87", size = 9656800, upload-time = "2025-07-14T20:13:34.312Z" },
    { url = "https://files.pythonhosted.org/packages/c0/d2/21af5c535501a7233e734b8af901574572da66fcc254cb35d0609c9080dd/pywin32-311-cp314-cp314-win_arm64.whl", hash = "sha256:a508e2d9025764a8270f93111a970e1d0fbfc33f4153b388bb649b7eec4f9b42", size = 8932540, upload-time = "2025-07-14T20:13:36.379Z" },
]

[[package]]
name = "pywin32-ctypes"
version = "0.2.3"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/85/9f/01a1a99704853cb63f253eea009390c88e7131c67e66a0a02099a8c917cb/pywin32-ctypes-0.2.3.tar.gz", hash = "sha256:d162dc04946d704503b2edc4d55f3dba5c1d539ead017afa00142c38b9885755", size = 29471, upload-time = "2024-08-14T10:15:34.626Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/de/3d/8161f7711c017e01ac9f008dfddd9410dff3674334c233bde66e7ba65bbf/pywin32_ctypes-0.2.3-py3-none-any.whl", hash = "sha256:8a1513379d709975552d202d942d9837758905c8d01eb82b8bcc30918929e7b8", size = 30756, upload-time = "2024-08-14T10:15:33.187Z" },
]

[[package]]
name = "pyyaml"
version = "6.0.3"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/05/8e/961c0007c59b8dd7729d542c61a4d537767a59645b82a0b521206e1e25c2/pyyaml-6.0.3.tar.gz", hash = "sha256:d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f", size = 130960, upload-time = "2025-09-25T21:33:16.546Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/f4/a0/39350dd17dd6d6c6507025c0e53aef67a9293a6d37d3511f23ea510d5800/pyyaml-6.0.3-cp310-cp310-macosx_10_13_x86_64.whl", hash = "sha256:214ed4befebe12df36bcc8bc2b64b396ca31be9304b8f59e25c11cf94a4c033b", size = 184227, upload-time = "2025-09-25T21:31:46.04Z" },
    { url = "https://files.pythonhosted.org/packages/05/14/52d505b5c59ce73244f59c7a50ecf47093ce4765f116cdb98286a71eeca2/pyyaml-6.0.3-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:02ea2dfa234451bbb8772601d7b8e426c2bfa197136796224e50e35a78777956", size = 174019, upload-time = "2025-09-25T21:31:47.706Z" },
    { url = "https://files.pythonhosted.org/packages/43/f7/0e6a5ae5599c838c696adb4e6330a59f463265bfa1e116cfd1fbb0abaaae/pyyaml-6.0.3-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:b30236e45cf30d2b8e7b3e85881719e98507abed1011bf463a8fa23e9c3e98a8", size = 740646, upload-time = "2025-09-25T21:31:49.21Z" },
    { url = "https://files.pythonhosted.org/packages/2f/3a/61b9db1d28f00f8fd0ae760459a5c4bf1b941baf714e207b6eb0657d2578/pyyaml-6.0.3-cp310-cp310-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:66291b10affd76d76f54fad28e22e51719ef9ba22b29e1d7d03d6777a9174198", size = 840793, upload-time = "2025-09-25T21:31:50.735Z" },
    { url = "https://files.pythonhosted.org/packages/7a/1e/7acc4f0e74c4b3d9531e24739e0ab832a5edf40e64fbae1a9c01941cabd7/pyyaml-6.0.3-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:9c7708761fccb9397fe64bbc0395abcae8c4bf7b0eac081e12b809bf47700d0b", size = 770293, upload-time = "2025-09-25T21:31:51.828Z" },
    { url = "https://files.pythonhosted.org/packages/8b/ef/abd085f06853af0cd59fa5f913d61a8eab65d7639ff2a658d18a25d6a89d/pyyaml-6.0.3-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:418cf3f2111bc80e0933b2cd8cd04f286338bb88bdc7bc8e6dd775ebde60b5e0", size = 732872, upload-time = "2025-09-25T21:31:53.282Z" },
    { url = "https://files.pythonhosted.org/packages/1f/15/2bc9c8faf6450a8b3c9fc5448ed869c599c0a74ba2669772b1f3a0040180/pyyaml-6.0.3-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:5e0b74767e5f8c593e8c9b5912019159ed0533c70051e9cce3e8b6aa699fcd69", size = 758828, upload-time = "2025-09-25T21:31:54.807Z" },
    { url = "https://files.pythonhosted.org/packages/a3/00/531e92e88c00f4333ce359e50c19b8d1de9fe8d581b1534e35ccfbc5f393/pyyaml-6.0.3-cp310-cp310-win32.whl", hash = "sha256:28c8d926f98f432f88adc23edf2e6d4921ac26fb084b028c733d01868d19007e", size = 142415, upload-time = "2025-09-25T21:31:55.885Z" },
    { url = "https://files.pythonhosted.org/packages/2a/fa/926c003379b19fca39dd4634818b00dec6c62d87faf628d1394e137354d4/pyyaml-6.0.3-cp310-cp310-win_amd64.whl", hash = "sha256:bdb2c67c6c1390b63c6ff89f210c8fd09d9a1217a465701eac7316313c915e4c", size = 158561, upload-time = "2025-09-25T21:31:57.406Z" },
    { url = "https://files.pythonhosted.org/packages/6d/16/a95b6757765b7b031c9374925bb718d55e0a9ba8a1b6a12d25962ea44347/pyyaml-6.0.3-cp311-cp311-macosx_10_13_x86_64.whl", hash = "sha256:44edc647873928551a01e7a563d7452ccdebee747728c1080d881d68af7b997e", size = 185826, upload-time = "2025-09-25T21:31:58.655Z" },
    { url = "https://files.pythonhosted.org/packages/16/19/13de8e4377ed53079ee996e1ab0a9c33ec2faf808a4647b7b4c0d46dd239/pyyaml-6.0.3-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:652cb6edd41e718550aad172851962662ff2681490a8a711af6a4d288dd96824", size = 175577, upload-time = "2025-09-25T21:32:00.088Z" },
    { url = "https://files.pythonhosted.org/packages/0c/62/d2eb46264d4b157dae1275b573017abec435397aa59cbcdab6fc978a8af4/pyyaml-6.0.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:10892704fc220243f5305762e276552a0395f7beb4dbf9b14ec8fd43b57f126c", size = 775556, upload-time = "2025-09-25T21:32:01.31Z" },
    { url = "https://files.pythonhosted.org/packages/10/cb/16c3f2cf3266edd25aaa00d6c4350381c8b012ed6f5276675b9eba8d9ff4/pyyaml-6.0.3-cp311-cp311-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:850774a7879607d3a6f50d36d04f00ee69e7fc816450e5f7e58d7f17f1ae5c00", size = 882114, upload-time = "2025-09-25T21:32:03.376Z" },
    { url = "https://files.pythonhosted.org/packages/71/60/917329f640924b18ff085ab889a11c763e0b573da888e8404ff486657602/pyyaml-6.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:b8bb0864c5a28024fac8a632c443c87c5aa6f215c0b126c449ae1a150412f31d", size = 806638, upload-time = "2025-09-25T21:32:04.553Z" },
    { url = "https://files.pythonhosted.org/packages/dd/6f/529b0f316a9fd167281a6c3826b5583e6192dba792dd55e3203d3f8e655a/pyyaml-6.0.3-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:1d37d57ad971609cf3c53ba6a7e365e40660e3be0e5175fa9f2365a379d6095a", size = 767463, upload-time = "2025-09-25T21:32:06.152Z" },
    { url = "https://files.pythonhosted.org/packages/f2/6a/b627b4e0c1dd03718543519ffb2f1deea4a1e6d42fbab8021936a4d22589/pyyaml-6.0.3-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:37503bfbfc9d2c40b344d06b2199cf0e96e97957ab1c1b546fd4f87e53e5d3e4", size = 794986, upload-time = "2025-09-25T21:32:07.367Z" },
    { url = "https://files.pythonhosted.org/packages/45/91/47a6e1c42d9ee337c4839208f30d9f09caa9f720ec7582917b264defc875/pyyaml-6.0.3-cp311-cp311-win32.whl", hash = "sha256:8098f252adfa6c80ab48096053f512f2321f0b998f98150cea9bd23d83e1467b", size = 142543, upload-time = "2025-09-25T21:32:08.95Z" },
    { url = "https://files.pythonhosted.org/packages/da/e3/ea007450a105ae919a72393cb06f122f288ef60bba2dc64b26e2646fa315/pyyaml-6.0.3-cp311-cp311-win_amd64.whl", hash = "sha256:9f3bfb4965eb874431221a3ff3fdcddc7e74e3b07799e0e84ca4a0f867d449bf", size = 158763, upload-time = "2025-09-25T21:32:09.96Z" },
    { url = "https://files.pythonhosted.org/packages/d1/33/422b98d2195232ca1826284a76852ad5a86fe23e31b009c9886b2d0fb8b2/pyyaml-6.0.3-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:7f047e29dcae44602496db43be01ad42fc6f1cc0d8cd6c83d342306c32270196", size = 182063, upload-time = "2025-09-25T21:32:11.445Z" },
    { url = "https://files.pythonhosted.org/packages/89/a0/6cf41a19a1f2f3feab0e9c0b74134aa2ce6849093d5517a0c550fe37a648/pyyaml-6.0.3-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:fc09d0aa354569bc501d4e787133afc08552722d3ab34836a80547331bb5d4a0", size = 173973, upload-time = "2025-09-25T21:32:12.492Z" },
    { url = "https://files.pythonhosted.org/packages/ed/23/7a778b6bd0b9a8039df8b1b1d80e2e2ad78aa04171592c8a5c43a56a6af4/pyyaml-6.0.3-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:9149cad251584d5fb4981be1ecde53a1ca46c891a79788c0df828d2f166bda28", size = 775116, upload-time = "2025-09-25T21:32:13.652Z" },
    { url = "https://files.pythonhosted.org/packages/65/30/d7353c338e12baef4ecc1b09e877c1970bd3382789c159b4f89d6a70dc09/pyyaml-6.0.3-cp312-cp312-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:5fdec68f91a0c6739b380c83b951e2c72ac0197ace422360e6d5a959d8d97b2c", size = 844011, upload-time = "2025-09-25T21:32:15.21Z" },
    { url = "https://files.pythonhosted.org/packages/8b/9d/b3589d3877982d4f2329302ef98a8026e7f4443c765c46cfecc8858c6b4b/pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:ba1cc08a7ccde2d2ec775841541641e4548226580ab850948cbfda66a1befcdc", size = 807870, upload-time = "2025-09-25T21:32:16.431Z" },
    { url = "https://files.pythonhosted.org/packages/05/c0/b3be26a015601b822b97d9149ff8cb5ead58c66f981e04fedf4e762f4bd4/pyyaml-6.0.3-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:8dc52c23056b9ddd46818a57b78404882310fb473d63f17b07d5c40421e47f8e", size = 761089, upload-time = "2025-09-25T21:32:17.56Z" },
    { url = "https://files.pythonhosted.org/packages/be/8e/98435a21d1d4b46590d5459a22d88128103f8da4c2d4cb8f14f2a96504e1/pyyaml-6.0.3-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:41715c910c881bc081f1e8872880d3c650acf13dfa8214bad49ed4cede7c34ea", size = 790181, upload-time = "2025-09-25T21:32:18.834Z" },
    { url = "https://files.pythonhosted.org/packages/74/93/7baea19427dcfbe1e5a372d81473250b379f04b1bd3c4c5ff825e2327202/pyyaml-6.0.3-cp312-cp312-win32.whl", hash = "sha256:96b533f0e99f6579b3d4d4995707cf36df9100d67e0c8303a0c55b27b5f99bc5", size = 137658, upload-time = "2025-09-25T21:32:20.209Z" },
    { url = "https://files.pythonhosted.org/packages/86/bf/899e81e4cce32febab4fb42bb97dcdf66bc135272882d1987881a4b519e9/pyyaml-6.0.3-cp312-cp312-win_amd64.whl", hash = "sha256:5fcd34e47f6e0b794d17de1b4ff496c00986e1c83f7ab2fb8fcfe9616ff7477b", size = 154003, upload-time = "2025-09-25T21:32:21.167Z" },
    { url = "https://files.pythonhosted.org/packages/1a/08/67bd04656199bbb51dbed1439b7f27601dfb576fb864099c7ef0c3e55531/pyyaml-6.0.3-cp312-cp312-win_arm64.whl", hash = "sha256:64386e5e707d03a7e172c0701abfb7e10f0fb753ee1d773128192742712a98fd", size = 140344, upload-time = "2025-09-25T21:32:22.617Z" },
    { url = "https://files.pythonhosted.org/packages/d1/11/0fd08f8192109f7169db964b5707a2f1e8b745d4e239b784a5a1dd80d1db/pyyaml-6.0.3-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:8da9669d359f02c0b91ccc01cac4a67f16afec0dac22c2ad09f46bee0697eba8", size = 181669, upload-time = "2025-09-25T21:32:23.673Z" },
    { url = "https://files.pythonhosted.org/packages/b1/16/95309993f1d3748cd644e02e38b75d50cbc0d9561d21f390a76242ce073f/pyyaml-6.0.3-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:2283a07e2c21a2aa78d9c4442724ec1eb15f5e42a723b99cb3d822d48f5f7ad1", size = 173252, upload-time = "2025-09-25T21:32:25.149Z" },
    { url = "https://files.pythonhosted.org/packages/50/31/b20f376d3f810b9b2371e72ef5adb33879b25edb7a6d072cb7ca0c486398/pyyaml-6.0.3-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:ee2922902c45ae8ccada2c5b501ab86c36525b883eff4255313a253a3160861c", size = 767081, upload-time = "2025-09-25T21:32:26.575Z" },
    { url = "https://files.pythonhosted.org/packages/49/1e/a55ca81e949270d5d4432fbbd19dfea5321eda7c41a849d443dc92fd1ff7/pyyaml-6.0.3-cp313-cp313-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:a33284e20b78bd4a18c8c2282d549d10bc8408a2a7ff57653c0cf0b9be0afce5", size = 841159, upload-time = "2025-09-25T21:32:27.727Z" },
    { url = "https://files.pythonhosted.org/packages/74/27/e5b8f34d02d9995b80abcef563ea1f8b56d20134d8f4e5e81733b1feceb2/pyyaml-6.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:0f29edc409a6392443abf94b9cf89ce99889a1dd5376d94316ae5145dfedd5d6", size = 801626, upload-time = "2025-09-25T21:32:28.878Z" },
    { url = "https://files.pythonhosted.org/packages/f9/11/ba845c23988798f40e52ba45f34849aa8a1f2d4af4b798588010792ebad6/pyyaml-6.0.3-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:f7057c9a337546edc7973c0d3ba84ddcdf0daa14533c2065749c9075001090e6", size = 753613, upload-time = "2025-09-25T21:32:30.178Z" },
    { url = "https://files.pythonhosted.org/packages/3d/e0/7966e1a7bfc0a45bf0a7fb6b98ea03fc9b8d84fa7f2229e9659680b69ee3/pyyaml-6.0.3-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:eda16858a3cab07b80edaf74336ece1f986ba330fdb8ee0d6c0d68fe82bc96be", size = 794115, upload-time = "2025-09-25T21:32:31.353Z" },
    { url = "https://files.pythonhosted.org/packages/de/94/980b50a6531b3019e45ddeada0626d45fa85cbe22300844a7983285bed3b/pyyaml-6.0.3-cp313-cp313-win32.whl", hash = "sha256:d0eae10f8159e8fdad514efdc92d74fd8d682c933a6dd088030f3834bc8e6b26", size = 137427, upload-time = "2025-09-25T21:32:32.58Z" },
    { url = "https://files.pythonhosted.org/packages/97/c9/39d5b874e8b28845e4ec2202b5da735d0199dbe5b8fb85f91398814a9a46/pyyaml-6.0.3-cp313-cp313-win_amd64.whl", hash = "sha256:79005a0d97d5ddabfeeea4cf676af11e647e41d81c9a7722a193022accdb6b7c", size = 154090, upload-time = "2025-09-25T21:32:33.659Z" },
    { url = "https://files.pythonhosted.org/packages/73/e8/2bdf3ca2090f68bb3d75b44da7bbc71843b19c9f2b9cb9b0f4ab7a5a4329/pyyaml-6.0.3-cp313-cp313-win_arm64.whl", hash = "sha256:5498cd1645aa724a7c71c8f378eb29ebe23da2fc0d7a08071d89469bf1d2defb", size = 140246, upload-time = "2025-09-25T21:32:34.663Z" },
    { url = "https://files.pythonhosted.org/packages/9d/8c/f4bd7f6465179953d3ac9bc44ac1a8a3e6122cf8ada906b4f96c60172d43/pyyaml-6.0.3-cp314-cp314-macosx_10_13_x86_64.whl", hash = "sha256:8d1fab6bb153a416f9aeb4b8763bc0f22a5586065f86f7664fc23339fc1c1fac", size = 181814, upload-time = "2025-09-25T21:32:35.712Z" },
    { url = "https://files.pythonhosted.org/packages/bd/9c/4d95bb87eb2063d20db7b60faa3840c1b18025517ae857371c4dd55a6b3a/pyyaml-6.0.3-cp314-cp314-macosx_11_0_arm64.whl", hash = "sha256:34d5fcd24b8445fadc33f9cf348c1047101756fd760b4dacb5c3e99755703310", size = 173809, upload-time = "2025-09-25T21:32:36.789Z" },
    { url = "https://files.pythonhosted.org/packages/92/b5/47e807c2623074914e29dabd16cbbdd4bf5e9b2db9f8090fa64411fc5382/pyyaml-6.0.3-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:501a031947e3a9025ed4405a168e6ef5ae3126c59f90ce0cd6f2bfc477be31b7", size = 766454, upload-time = "2025-09-25T21:32:37.966Z" },
    { url = "https://files.pythonhosted.org/packages/02/9e/e5e9b168be58564121efb3de6859c452fccde0ab093d8438905899a3a483/pyyaml-6.0.3-cp314-cp314-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:b3bc83488de33889877a0f2543ade9f70c67d66d9ebb4ac959502e12de895788", size = 836355, upload-time = "2025-09-25T21:32:39.178Z" },
    { url = "https://files.pythonhosted.org/packages/88/f9/16491d7ed2a919954993e48aa941b200f38040928474c9e85ea9e64222c3/pyyaml-6.0.3-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:c458b6d084f9b935061bc36216e8a69a7e293a2f1e68bf956dcd9e6cbcd143f5", size = 794175, upload-time = "2025-09-25T21:32:40.865Z" },
    { url = "https://files.pythonhosted.org/packages/dd/3f/5989debef34dc6397317802b527dbbafb2b4760878a53d4166579111411e/pyyaml-6.0.3-cp314-cp314-musllinux_1_2_aarch64.whl", hash = "sha256:7c6610def4f163542a622a73fb39f534f8c101d690126992300bf3207eab9764", size = 755228, upload-time = "2025-09-25T21:32:42.084Z" },
    { url = "https://files.pythonhosted.org/packages/d7/ce/af88a49043cd2e265be63d083fc75b27b6ed062f5f9fd6cdc223ad62f03e/pyyaml-6.0.3-cp314-cp314-musllinux_1_2_x86_64.whl", hash = "sha256:5190d403f121660ce8d1d2c1bb2ef1bd05b5f68533fc5c2ea899bd15f4399b35", size = 789194, upload-time = "2025-09-25T21:32:43.362Z" },
    { url = "https://files.pythonhosted.org/packages/23/20/bb6982b26a40bb43951265ba29d4c246ef0ff59c9fdcdf0ed04e0687de4d/pyyaml-6.0.3-cp314-cp314-win_amd64.whl", hash = "sha256:4a2e8cebe2ff6ab7d1050ecd59c25d4c8bd7e6f400f5f82b96557ac0abafd0ac", size = 156429, upload-time = "2025-09-25T21:32:57.844Z" },
    { url = "https://files.pythonhosted.org/packages/f4/f4/a4541072bb9422c8a883ab55255f918fa378ecf083f5b85e87fc2b4eda1b/pyyaml-6.0.3-cp314-cp314-win_arm64.whl", hash = "sha256:93dda82c9c22deb0a405ea4dc5f2d0cda384168e466364dec6255b293923b2f3", size = 143912, upload-time = "2025-09-25T21:32:59.247Z" },
    { url = "https://files.pythonhosted.org/packages/7c/f9/07dd09ae774e4616edf6cda684ee78f97777bdd15847253637a6f052a62f/pyyaml-6.0.3-cp314-cp314t-macosx_10_13_x86_64.whl", hash = "sha256:02893d100e99e03eda1c8fd5c441d8c60103fd175728e23e431db1b589cf5ab3", size = 189108, upload-time = "2025-09-25T21:32:44.377Z" },
    { url = "https://files.pythonhosted.org/packages/4e/78/8d08c9fb7ce09ad8c38ad533c1191cf27f7ae1effe5bb9400a46d9437fcf/pyyaml-6.0.3-cp314-cp314t-macosx_11_0_arm64.whl", hash = "sha256:c1ff362665ae507275af2853520967820d9124984e0f7466736aea23d8611fba", size = 183641, upload-time = "2025-09-25T21:32:45.407Z" },
    { url = "https://files.pythonhosted.org/packages/7b/5b/3babb19104a46945cf816d047db2788bcaf8c94527a805610b0289a01c6b/pyyaml-6.0.3-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:6adc77889b628398debc7b65c073bcb99c4a0237b248cacaf3fe8a557563ef6c", size = 831901, upload-time = "2025-09-25T21:32:48.83Z" },
    { url = "https://files.pythonhosted.org/packages/8b/cc/dff0684d8dc44da4d22a13f35f073d558c268780ce3c6ba1b87055bb0b87/pyyaml-6.0.3-cp314-cp314t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:a80cb027f6b349846a3bf6d73b5e95e782175e52f22108cfa17876aaeff93702", size = 861132, upload-time = "2025-09-25T21:32:50.149Z" },
    { url = "https://files.pythonhosted.org/packages/b1/5e/f77dc6b9036943e285ba76b49e118d9ea929885becb0a29ba8a7c75e29fe/pyyaml-6.0.3-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:00c4bdeba853cc34e7dd471f16b4114f4162dc03e6b7afcc2128711f0eca823c", size = 839261, upload-time = "2025-09-25T21:32:51.808Z" },
    { url = "https://files.pythonhosted.org/packages/ce/88/a9db1376aa2a228197c58b37302f284b5617f56a5d959fd1763fb1675ce6/pyyaml-6.0.3-cp314-cp314t-musllinux_1_2_aarch64.whl", hash = "sha256:66e1674c3ef6f541c35191caae2d429b967b99e02040f5ba928632d9a7f0f065", size = 805272, upload-time = "2025-09-25T21:32:52.941Z" },
    { url = "https://files.pythonhosted.org/packages/da/92/1446574745d74df0c92e6aa4a7b0b3130706a4142b2d1a5869f2eaa423c6/pyyaml-6.0.3-cp314-cp314t-musllinux_1_2_x86_64.whl", hash = "sha256:16249ee61e95f858e83976573de0f5b2893b3677ba71c9dd36b9cf8be9ac6d65", size = 829923, upload-time = "2025-09-25T21:32:54.537Z" },
    { url = "https://files.pythonhosted.org/packages/f0/7a/1c7270340330e575b92f397352af856a8c06f230aa3e76f86b39d01b416a/pyyaml-6.0.3-cp314-cp314t-win_amd64.whl", hash = "sha256:4ad1906908f2f5ae4e5a8ddfce73c320c2a1429ec52eafd27138b7f1cbe341c9", size = 174062, upload-time = "2025-09-25T21:32:55.767Z" },
    { url = "https://files.pythonhosted.org/packages/f1/12/de94a39c2ef588c7e6455cfbe7343d3b2dc9d6b6b2f40c4c6565744c873d/pyyaml-6.0.3-cp314-cp314t-win_arm64.whl", hash = "sha256:ebc55a14a21cb14062aa4162f906cd962b28e2e9ea38f9b4391244cd8de4ae0b", size = 149341, upload-time = "2025-09-25T21:32:56.828Z" },
]

[[package]]
name = "referencing"
version = "0.37.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "attrs" },
    { name = "rpds-py" },
    { name = "typing-extensions", marker = "python_full_version < '3.13'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/22/f5/df4e9027acead3ecc63e50fe1e36aca1523e1719559c499951bb4b53188f/referencing-0.37.0.tar.gz", hash = "sha256:44aefc3142c5b842538163acb373e24cce6632bd54bdb01b21ad5863489f50d8", size = 78036, upload-time = "2025-10-13T15:30:48.871Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/2c/58/ca301544e1fa93ed4f80d724bf5b194f6e4b945841c5bfd555878eea9fcb/referencing-0.37.0-py3-none-any.whl", hash = "sha256:381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231", size = 26766, upload-time = "2025-10-13T15:30:47.625Z" },
]

[[package]]
name = "rich"
version = "14.3.3"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "markdown-it-py" },
    { name = "pygments" },
]
sdist = { url = "https://files.pythonhosted.org/packages/b3/c6/f3b320c27991c46f43ee9d856302c70dc2d0fb2dba4842ff739d5f46b393/rich-14.3.3.tar.gz", hash = "sha256:b8daa0b9e4eef54dd8cf7c86c03713f53241884e814f4e2f5fb342fe520f639b", size = 230582, upload-time = "2026-02-19T17:23:12.474Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/14/25/b208c5683343959b670dc001595f2f3737e051da617f66c31f7c4fa93abc/rich-14.3.3-py3-none-any.whl", hash = "sha256:793431c1f8619afa7d3b52b2cdec859562b950ea0d4b6b505397612db8d5362d", size = 310458, upload-time = "2026-02-19T17:23:13.732Z" },
]

[[package]]
name = "rich-rst"
version = "1.3.2"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "docutils" },
    { name = "rich" },
]
sdist = { url = "https://files.pythonhosted.org/packages/bc/6d/a506aaa4a9eaa945ed8ab2b7347859f53593864289853c5d6d62b77246e0/rich_rst-1.3.2.tar.gz", hash = "sha256:a1196fdddf1e364b02ec68a05e8ff8f6914fee10fbca2e6b6735f166bb0da8d4", size = 14936, upload-time = "2025-10-14T16:49:45.332Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/13/2f/b4530fbf948867702d0a3f27de4a6aab1d156f406d72852ab902c4d04de9/rich_rst-1.3.2-py3-none-any.whl", hash = "sha256:a99b4907cbe118cf9d18b0b44de272efa61f15117c61e39ebdc431baf5df722a", size = 12567, upload-time = "2025-10-14T16:49:42.953Z" },
]

[[package]]
name = "rpds-py"
version = "0.30.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/20/af/3f2f423103f1113b36230496629986e0ef7e199d2aa8392452b484b38ced/rpds_py-0.30.0.tar.gz", hash = "sha256:dd8ff7cf90014af0c0f787eea34794ebf6415242ee1d6fa91eaba725cc441e84", size = 69469, upload-time = "2025-11-30T20:24:38.837Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/06/0c/0c411a0ec64ccb6d104dcabe0e713e05e153a9a2c3c2bd2b32ce412166fe/rpds_py-0.30.0-cp310-cp310-macosx_10_12_x86_64.whl", hash = "sha256:679ae98e00c0e8d68a7fda324e16b90fd5260945b45d3b824c892cec9eea3288", size = 370490, upload-time = "2025-11-30T20:21:33.256Z" },
    { url = "https://files.pythonhosted.org/packages/19/6a/4ba3d0fb7297ebae71171822554abe48d7cab29c28b8f9f2c04b79988c05/rpds_py-0.30.0-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:4cc2206b76b4f576934f0ed374b10d7ca5f457858b157ca52064bdfc26b9fc00", size = 359751, upload-time = "2025-11-30T20:21:34.591Z" },
    { url = "https://files.pythonhosted.org/packages/cd/7c/e4933565ef7f7a0818985d87c15d9d273f1a649afa6a52ea35ad011195ea/rpds_py-0.30.0-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:389a2d49eded1896c3d48b0136ead37c48e221b391c052fba3f4055c367f60a6", size = 389696, upload-time = "2025-11-30T20:21:36.122Z" },
    { url = "https://files.pythonhosted.org/packages/5e/01/6271a2511ad0815f00f7ed4390cf2567bec1d4b1da39e2c27a41e6e3b4de/rpds_py-0.30.0-cp310-cp310-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:32c8528634e1bf7121f3de08fa85b138f4e0dc47657866630611b03967f041d7", size = 403136, upload-time = "2025-11-30T20:21:37.728Z" },
    { url = "https://files.pythonhosted.org/packages/55/64/c857eb7cd7541e9b4eee9d49c196e833128a55b89a9850a9c9ac33ccf897/rpds_py-0.30.0-cp310-cp310-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:f207f69853edd6f6700b86efb84999651baf3789e78a466431df1331608e5324", size = 524699, upload-time = "2025-11-30T20:21:38.92Z" },
    { url = "https://files.pythonhosted.org/packages/9c/ed/94816543404078af9ab26159c44f9e98e20fe47e2126d5d32c9d9948d10a/rpds_py-0.30.0-cp310-cp310-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:67b02ec25ba7a9e8fa74c63b6ca44cf5707f2fbfadae3ee8e7494297d56aa9df", size = 412022, upload-time = "2025-11-30T20:21:40.407Z" },
    { url = "https://files.pythonhosted.org/packages/61/b5/707f6cf0066a6412aacc11d17920ea2e19e5b2f04081c64526eb35b5c6e7/rpds_py-0.30.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:0c0e95f6819a19965ff420f65578bacb0b00f251fefe2c8b23347c37174271f3", size = 390522, upload-time = "2025-11-30T20:21:42.17Z" },
    { url = "https://files.pythonhosted.org/packages/13/4e/57a85fda37a229ff4226f8cbcf09f2a455d1ed20e802ce5b2b4a7f5ed053/rpds_py-0.30.0-cp310-cp310-manylinux_2_31_riscv64.whl", hash = "sha256:a452763cc5198f2f98898eb98f7569649fe5da666c2dc6b5ddb10fde5a574221", size = 404579, upload-time = "2025-11-30T20:21:43.769Z" },
    { url = "https://files.pythonhosted.org/packages/f9/da/c9339293513ec680a721e0e16bf2bac3db6e5d7e922488de471308349bba/rpds_py-0.30.0-cp310-cp310-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:e0b65193a413ccc930671c55153a03ee57cecb49e6227204b04fae512eb657a7", size = 421305, upload-time = "2025-11-30T20:21:44.994Z" },
    { url = "https://files.pythonhosted.org/packages/f9/be/522cb84751114f4ad9d822ff5a1aa3c98006341895d5f084779b99596e5c/rpds_py-0.30.0-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:858738e9c32147f78b3ac24dc0edb6610000e56dc0f700fd5f651d0a0f0eb9ff", size = 572503, upload-time = "2025-11-30T20:21:46.91Z" },
    { url = "https://files.pythonhosted.org/packages/a2/9b/de879f7e7ceddc973ea6e4629e9b380213a6938a249e94b0cdbcc325bb66/rpds_py-0.30.0-cp310-cp310-musllinux_1_2_i686.whl", hash = "sha256:da279aa314f00acbb803da1e76fa18666778e8a8f83484fba94526da5de2cba7", size = 598322, upload-time = "2025-11-30T20:21:48.709Z" },
    { url = "https://files.pythonhosted.org/packages/48/ac/f01fc22efec3f37d8a914fc1b2fb9bcafd56a299edbe96406f3053edea5a/rpds_py-0.30.0-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:7c64d38fb49b6cdeda16ab49e35fe0da2e1e9b34bc38bd78386530f218b37139", size = 560792, upload-time = "2025-11-30T20:21:50.024Z" },
    { url = "https://files.pythonhosted.org/packages/e2/da/4e2b19d0f131f35b6146425f846563d0ce036763e38913d917187307a671/rpds_py-0.30.0-cp310-cp310-win32.whl", hash = "sha256:6de2a32a1665b93233cde140ff8b3467bdb9e2af2b91079f0333a0974d12d464", size = 221901, upload-time = "2025-11-30T20:21:51.32Z" },
    { url = "https://files.pythonhosted.org/packages/96/cb/156d7a5cf4f78a7cc571465d8aec7a3c447c94f6749c5123f08438bcf7bc/rpds_py-0.30.0-cp310-cp310-win_amd64.whl", hash = "sha256:1726859cd0de969f88dc8673bdd954185b9104e05806be64bcd87badbe313169", size = 235823, upload-time = "2025-11-30T20:21:52.505Z" },
    { url = "https://files.pythonhosted.org/packages/4d/6e/f964e88b3d2abee2a82c1ac8366da848fce1c6d834dc2132c3fda3970290/rpds_py-0.30.0-cp311-cp311-macosx_10_12_x86_64.whl", hash = "sha256:a2bffea6a4ca9f01b3f8e548302470306689684e61602aa3d141e34da06cf425", size = 370157, upload-time = "2025-11-30T20:21:53.789Z" },
    { url = "https://files.pythonhosted.org/packages/94/ba/24e5ebb7c1c82e74c4e4f33b2112a5573ddc703915b13a073737b59b86e0/rpds_py-0.30.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:dc4f992dfe1e2bc3ebc7444f6c7051b4bc13cd8e33e43511e8ffd13bf407010d", size = 359676, upload-time = "2025-11-30T20:21:55.475Z" },
    { url = "https://files.pythonhosted.org/packages/84/86/04dbba1b087227747d64d80c3b74df946b986c57af0a9f0c98726d4d7a3b/rpds_py-0.30.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:422c3cb9856d80b09d30d2eb255d0754b23e090034e1deb4083f8004bd0761e4", size = 389938, upload-time = "2025-11-30T20:21:57.079Z" },
    { url = "https://files.pythonhosted.org/packages/42/bb/1463f0b1722b7f45431bdd468301991d1328b16cffe0b1c2918eba2c4eee/rpds_py-0.30.0-cp311-cp311-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:07ae8a593e1c3c6b82ca3292efbe73c30b61332fd612e05abee07c79359f292f", size = 402932, upload-time = "2025-11-30T20:21:58.47Z" },
    { url = "https://files.pythonhosted.org/packages/99/ee/2520700a5c1f2d76631f948b0736cdf9b0acb25abd0ca8e889b5c62ac2e3/rpds_py-0.30.0-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:12f90dd7557b6bd57f40abe7747e81e0c0b119bef015ea7726e69fe550e394a4", size = 525830, upload-time = "2025-11-30T20:21:59.699Z" },
    { url = "https://files.pythonhosted.org/packages/e0/ad/bd0331f740f5705cc555a5e17fdf334671262160270962e69a2bdef3bf76/rpds_py-0.30.0-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:99b47d6ad9a6da00bec6aabe5a6279ecd3c06a329d4aa4771034a21e335c3a97", size = 412033, upload-time = "2025-11-30T20:22:00.991Z" },
    { url = "https://files.pythonhosted.org/packages/f8/1e/372195d326549bb51f0ba0f2ecb9874579906b97e08880e7a65c3bef1a99/rpds_py-0.30.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:33f559f3104504506a44bb666b93a33f5d33133765b0c216a5bf2f1e1503af89", size = 390828, upload-time = "2025-11-30T20:22:02.723Z" },
    { url = "https://files.pythonhosted.org/packages/ab/2b/d88bb33294e3e0c76bc8f351a3721212713629ffca1700fa94979cb3eae8/rpds_py-0.30.0-cp311-cp311-manylinux_2_31_riscv64.whl", hash = "sha256:946fe926af6e44f3697abbc305ea168c2c31d3e3ef1058cf68f379bf0335a78d", size = 404683, upload-time = "2025-11-30T20:22:04.367Z" },
    { url = "https://files.pythonhosted.org/packages/50/32/c759a8d42bcb5289c1fac697cd92f6fe01a018dd937e62ae77e0e7f15702/rpds_py-0.30.0-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:495aeca4b93d465efde585977365187149e75383ad2684f81519f504f5c13038", size = 421583, upload-time = "2025-11-30T20:22:05.814Z" },
    { url = "https://files.pythonhosted.org/packages/2b/81/e729761dbd55ddf5d84ec4ff1f47857f4374b0f19bdabfcf929164da3e24/rpds_py-0.30.0-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:d9a0ca5da0386dee0655b4ccdf46119df60e0f10da268d04fe7cc87886872ba7", size = 572496, upload-time = "2025-11-30T20:22:07.713Z" },
    { url = "https://files.pythonhosted.org/packages/14/f6/69066a924c3557c9c30baa6ec3a0aa07526305684c6f86c696b08860726c/rpds_py-0.30.0-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:8d6d1cc13664ec13c1b84241204ff3b12f9bb82464b8ad6e7a5d3486975c2eed", size = 598669, upload-time = "2025-11-30T20:22:09.312Z" },
    { url = "https://files.pythonhosted.org/packages/5f/48/905896b1eb8a05630d20333d1d8ffd162394127b74ce0b0784ae04498d32/rpds_py-0.30.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:3896fa1be39912cf0757753826bc8bdc8ca331a28a7c4ae46b7a21280b06bb85", size = 561011, upload-time = "2025-11-30T20:22:11.309Z" },
    { url = "https://files.pythonhosted.org/packages/22/16/cd3027c7e279d22e5eb431dd3c0fbc677bed58797fe7581e148f3f68818b/rpds_py-0.30.0-cp311-cp311-win32.whl", hash = "sha256:55f66022632205940f1827effeff17c4fa7ae1953d2b74a8581baaefb7d16f8c", size = 221406, upload-time = "2025-11-30T20:22:13.101Z" },
    { url = "https://files.pythonhosted.org/packages/fa/5b/e7b7aa136f28462b344e652ee010d4de26ee9fd16f1bfd5811f5153ccf89/rpds_py-0.30.0-cp311-cp311-win_amd64.whl", hash = "sha256:a51033ff701fca756439d641c0ad09a41d9242fa69121c7d8769604a0a629825", size = 236024, upload-time = "2025-11-30T20:22:14.853Z" },
    { url = "https://files.pythonhosted.org/packages/14/a6/364bba985e4c13658edb156640608f2c9e1d3ea3c81b27aa9d889fff0e31/rpds_py-0.30.0-cp311-cp311-win_arm64.whl", hash = "sha256:47b0ef6231c58f506ef0b74d44e330405caa8428e770fec25329ed2cb971a229", size = 229069, upload-time = "2025-11-30T20:22:16.577Z" },
    { url = "https://files.pythonhosted.org/packages/03/e7/98a2f4ac921d82f33e03f3835f5bf3a4a40aa1bfdc57975e74a97b2b4bdd/rpds_py-0.30.0-cp312-cp312-macosx_10_12_x86_64.whl", hash = "sha256:a161f20d9a43006833cd7068375a94d035714d73a172b681d8881820600abfad", size = 375086, upload-time = "2025-11-30T20:22:17.93Z" },
    { url = "https://files.pythonhosted.org/packages/4d/a1/bca7fd3d452b272e13335db8d6b0b3ecde0f90ad6f16f3328c6fb150c889/rpds_py-0.30.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:6abc8880d9d036ecaafe709079969f56e876fcf107f7a8e9920ba6d5a3878d05", size = 359053, upload-time = "2025-11-30T20:22:19.297Z" },
    { url = "https://files.pythonhosted.org/packages/65/1c/ae157e83a6357eceff62ba7e52113e3ec4834a84cfe07fa4b0757a7d105f/rpds_py-0.30.0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:ca28829ae5f5d569bb62a79512c842a03a12576375d5ece7d2cadf8abe96ec28", size = 390763, upload-time = "2025-11-30T20:22:21.661Z" },
    { url = "https://files.pythonhosted.org/packages/d4/36/eb2eb8515e2ad24c0bd43c3ee9cd74c33f7ca6430755ccdb240fd3144c44/rpds_py-0.30.0-cp312-cp312-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:a1010ed9524c73b94d15919ca4d41d8780980e1765babf85f9a2f90d247153dd", size = 408951, upload-time = "2025-11-30T20:22:23.408Z" },
    { url = "https://files.pythonhosted.org/packages/d6/65/ad8dc1784a331fabbd740ef6f71ce2198c7ed0890dab595adb9ea2d775a1/rpds_py-0.30.0-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:f8d1736cfb49381ba528cd5baa46f82fdc65c06e843dab24dd70b63d09121b3f", size = 514622, upload-time = "2025-11-30T20:22:25.16Z" },
    { url = "https://files.pythonhosted.org/packages/63/8e/0cfa7ae158e15e143fe03993b5bcd743a59f541f5952e1546b1ac1b5fd45/rpds_py-0.30.0-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:d948b135c4693daff7bc2dcfc4ec57237a29bd37e60c2fabf5aff2bbacf3e2f1", size = 414492, upload-time = "2025-11-30T20:22:26.505Z" },
    { url = "https://files.pythonhosted.org/packages/60/1b/6f8f29f3f995c7ffdde46a626ddccd7c63aefc0efae881dc13b6e5d5bb16/rpds_py-0.30.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:47f236970bccb2233267d89173d3ad2703cd36a0e2a6e92d0560d333871a3d23", size = 394080, upload-time = "2025-11-30T20:22:27.934Z" },
    { url = "https://files.pythonhosted.org/packages/6d/d5/a266341051a7a3ca2f4b750a3aa4abc986378431fc2da508c5034d081b70/rpds_py-0.30.0-cp312-cp312-manylinux_2_31_riscv64.whl", hash = "sha256:2e6ecb5a5bcacf59c3f912155044479af1d0b6681280048b338b28e364aca1f6", size = 408680, upload-time = "2025-11-30T20:22:29.341Z" },
    { url = "https://files.pythonhosted.org/packages/10/3b/71b725851df9ab7a7a4e33cf36d241933da66040d195a84781f49c50490c/rpds_py-0.30.0-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:a8fa71a2e078c527c3e9dc9fc5a98c9db40bcc8a92b4e8858e36d329f8684b51", size = 423589, upload-time = "2025-11-30T20:22:31.469Z" },
    { url = "https://files.pythonhosted.org/packages/00/2b/e59e58c544dc9bd8bd8384ecdb8ea91f6727f0e37a7131baeff8d6f51661/rpds_py-0.30.0-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:73c67f2db7bc334e518d097c6d1e6fed021bbc9b7d678d6cc433478365d1d5f5", size = 573289, upload-time = "2025-11-30T20:22:32.997Z" },
    { url = "https://files.pythonhosted.org/packages/da/3e/a18e6f5b460893172a7d6a680e86d3b6bc87a54c1f0b03446a3c8c7b588f/rpds_py-0.30.0-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:5ba103fb455be00f3b1c2076c9d4264bfcb037c976167a6047ed82f23153f02e", size = 599737, upload-time = "2025-11-30T20:22:34.419Z" },
    { url = "https://files.pythonhosted.org/packages/5c/e2/714694e4b87b85a18e2c243614974413c60aa107fd815b8cbc42b873d1d7/rpds_py-0.30.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:7cee9c752c0364588353e627da8a7e808a66873672bcb5f52890c33fd965b394", size = 563120, upload-time = "2025-11-30T20:22:35.903Z" },
    { url = "https://files.pythonhosted.org/packages/6f/ab/d5d5e3bcedb0a77f4f613706b750e50a5a3ba1c15ccd3665ecc636c968fd/rpds_py-0.30.0-cp312-cp312-win32.whl", hash = "sha256:1ab5b83dbcf55acc8b08fc62b796ef672c457b17dbd7820a11d6c52c06839bdf", size = 223782, upload-time = "2025-11-30T20:22:37.271Z" },
    { url = "https://files.pythonhosted.org/packages/39/3b/f786af9957306fdc38a74cef405b7b93180f481fb48453a114bb6465744a/rpds_py-0.30.0-cp312-cp312-win_amd64.whl", hash = "sha256:a090322ca841abd453d43456ac34db46e8b05fd9b3b4ac0c78bcde8b089f959b", size = 240463, upload-time = "2025-11-30T20:22:39.021Z" },
    { url = "https://files.pythonhosted.org/packages/f3/d2/b91dc748126c1559042cfe41990deb92c4ee3e2b415f6b5234969ffaf0cc/rpds_py-0.30.0-cp312-cp312-win_arm64.whl", hash = "sha256:669b1805bd639dd2989b281be2cfd951c6121b65e729d9b843e9639ef1fd555e", size = 230868, upload-time = "2025-11-30T20:22:40.493Z" },
    { url = "https://files.pythonhosted.org/packages/ed/dc/d61221eb88ff410de3c49143407f6f3147acf2538c86f2ab7ce65ae7d5f9/rpds_py-0.30.0-cp313-cp313-macosx_10_12_x86_64.whl", hash = "sha256:f83424d738204d9770830d35290ff3273fbb02b41f919870479fab14b9d303b2", size = 374887, upload-time = "2025-11-30T20:22:41.812Z" },
    { url = "https://files.pythonhosted.org/packages/fd/32/55fb50ae104061dbc564ef15cc43c013dc4a9f4527a1f4d99baddf56fe5f/rpds_py-0.30.0-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:e7536cd91353c5273434b4e003cbda89034d67e7710eab8761fd918ec6c69cf8", size = 358904, upload-time = "2025-11-30T20:22:43.479Z" },
    { url = "https://files.pythonhosted.org/packages/58/70/faed8186300e3b9bdd138d0273109784eea2396c68458ed580f885dfe7ad/rpds_py-0.30.0-cp313-cp313-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:2771c6c15973347f50fece41fc447c054b7ac2ae0502388ce3b6738cd366e3d4", size = 389945, upload-time = "2025-11-30T20:22:44.819Z" },
    { url = "https://files.pythonhosted.org/packages/bd/a8/073cac3ed2c6387df38f71296d002ab43496a96b92c823e76f46b8af0543/rpds_py-0.30.0-cp313-cp313-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:0a59119fc6e3f460315fe9d08149f8102aa322299deaa5cab5b40092345c2136", size = 407783, upload-time = "2025-11-30T20:22:46.103Z" },
    { url = "https://files.pythonhosted.org/packages/77/57/5999eb8c58671f1c11eba084115e77a8899d6e694d2a18f69f0ba471ec8b/rpds_py-0.30.0-cp313-cp313-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:76fec018282b4ead0364022e3c54b60bf368b9d926877957a8624b58419169b7", size = 515021, upload-time = "2025-11-30T20:22:47.458Z" },
    { url = "https://files.pythonhosted.org/packages/e0/af/5ab4833eadc36c0a8ed2bc5c0de0493c04f6c06de223170bd0798ff98ced/rpds_py-0.30.0-cp313-cp313-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:692bef75a5525db97318e8cd061542b5a79812d711ea03dbc1f6f8dbb0c5f0d2", size = 414589, upload-time = "2025-11-30T20:22:48.872Z" },
    { url = "https://files.pythonhosted.org/packages/b7/de/f7192e12b21b9e9a68a6d0f249b4af3fdcdff8418be0767a627564afa1f1/rpds_py-0.30.0-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:9027da1ce107104c50c81383cae773ef5c24d296dd11c99e2629dbd7967a20c6", size = 394025, upload-time = "2025-11-30T20:22:50.196Z" },
    { url = "https://files.pythonhosted.org/packages/91/c4/fc70cd0249496493500e7cc2de87504f5aa6509de1e88623431fec76d4b6/rpds_py-0.30.0-cp313-cp313-manylinux_2_31_riscv64.whl", hash = "sha256:9cf69cdda1f5968a30a359aba2f7f9aa648a9ce4b580d6826437f2b291cfc86e", size = 408895, upload-time = "2025-11-30T20:22:51.87Z" },
    { url = "https://files.pythonhosted.org/packages/58/95/d9275b05ab96556fefff73a385813eb66032e4c99f411d0795372d9abcea/rpds_py-0.30.0-cp313-cp313-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:a4796a717bf12b9da9d3ad002519a86063dcac8988b030e405704ef7d74d2d9d", size = 422799, upload-time = "2025-11-30T20:22:53.341Z" },
    { url = "https://files.pythonhosted.org/packages/06/c1/3088fc04b6624eb12a57eb814f0d4997a44b0d208d6cace713033ff1a6ba/rpds_py-0.30.0-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:5d4c2aa7c50ad4728a094ebd5eb46c452e9cb7edbfdb18f9e1221f597a73e1e7", size = 572731, upload-time = "2025-11-30T20:22:54.778Z" },
    { url = "https://files.pythonhosted.org/packages/d8/42/c612a833183b39774e8ac8fecae81263a68b9583ee343db33ab571a7ce55/rpds_py-0.30.0-cp313-cp313-musllinux_1_2_i686.whl", hash = "sha256:ba81a9203d07805435eb06f536d95a266c21e5b2dfbf6517748ca40c98d19e31", size = 599027, upload-time = "2025-11-30T20:22:56.212Z" },
    { url = "https://files.pythonhosted.org/packages/5f/60/525a50f45b01d70005403ae0e25f43c0384369ad24ffe46e8d9068b50086/rpds_py-0.30.0-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:945dccface01af02675628334f7cf49c2af4c1c904748efc5cf7bbdf0b579f95", size = 563020, upload-time = "2025-11-30T20:22:58.2Z" },
    { url = "https://files.pythonhosted.org/packages/0b/5d/47c4655e9bcd5ca907148535c10e7d489044243cc9941c16ed7cd53be91d/rpds_py-0.30.0-cp313-cp313-win32.whl", hash = "sha256:b40fb160a2db369a194cb27943582b38f79fc4887291417685f3ad693c5a1d5d", size = 223139, upload-time = "2025-11-30T20:23:00.209Z" },
    { url = "https://files.pythonhosted.org/packages/f2/e1/485132437d20aa4d3e1d8b3fb5a5e65aa8139f1e097080c2a8443201742c/rpds_py-0.30.0-cp313-cp313-win_amd64.whl", hash = "sha256:806f36b1b605e2d6a72716f321f20036b9489d29c51c91f4dd29a3e3afb73b15", size = 240224, upload-time = "2025-11-30T20:23:02.008Z" },
    { url = "https://files.pythonhosted.org/packages/24/95/ffd128ed1146a153d928617b0ef673960130be0009c77d8fbf0abe306713/rpds_py-0.30.0-cp313-cp313-win_arm64.whl", hash = "sha256:d96c2086587c7c30d44f31f42eae4eac89b60dabbac18c7669be3700f13c3ce1", size = 230645, upload-time = "2025-11-30T20:23:03.43Z" },
    { url = "https://files.pythonhosted.org/packages/ff/1b/b10de890a0def2a319a2626334a7f0ae388215eb60914dbac8a3bae54435/rpds_py-0.30.0-cp313-cp313t-macosx_10_12_x86_64.whl", hash = "sha256:eb0b93f2e5c2189ee831ee43f156ed34e2a89a78a66b98cadad955972548be5a", size = 364443, upload-time = "2025-11-30T20:23:04.878Z" },
    { url = "https://files.pythonhosted.org/packages/0d/bf/27e39f5971dc4f305a4fb9c672ca06f290f7c4e261c568f3dea16a410d47/rpds_py-0.30.0-cp313-cp313t-macosx_11_0_arm64.whl", hash = "sha256:922e10f31f303c7c920da8981051ff6d8c1a56207dbdf330d9047f6d30b70e5e", size = 353375, upload-time = "2025-11-30T20:23:06.342Z" },
    { url = "https://files.pythonhosted.org/packages/40/58/442ada3bba6e8e6615fc00483135c14a7538d2ffac30e2d933ccf6852232/rpds_py-0.30.0-cp313-cp313t-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:cdc62c8286ba9bf7f47befdcea13ea0e26bf294bda99758fd90535cbaf408000", size = 383850, upload-time = "2025-11-30T20:23:07.825Z" },
    { url = "https://files.pythonhosted.org/packages/14/14/f59b0127409a33c6ef6f5c1ebd5ad8e32d7861c9c7adfa9a624fc3889f6c/rpds_py-0.30.0-cp313-cp313t-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:47f9a91efc418b54fb8190a6b4aa7813a23fb79c51f4bb84e418f5476c38b8db", size = 392812, upload-time = "2025-11-30T20:23:09.228Z" },
    { url = "https://files.pythonhosted.org/packages/b3/66/e0be3e162ac299b3a22527e8913767d869e6cc75c46bd844aa43fb81ab62/rpds_py-0.30.0-cp313-cp313t-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:1f3587eb9b17f3789ad50824084fa6f81921bbf9a795826570bda82cb3ed91f2", size = 517841, upload-time = "2025-11-30T20:23:11.186Z" },
    { url = "https://files.pythonhosted.org/packages/3d/55/fa3b9cf31d0c963ecf1ba777f7cf4b2a2c976795ac430d24a1f43d25a6ba/rpds_py-0.30.0-cp313-cp313t-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:39c02563fc592411c2c61d26b6c5fe1e51eaa44a75aa2c8735ca88b0d9599daa", size = 408149, upload-time = "2025-11-30T20:23:12.864Z" },
    { url = "https://files.pythonhosted.org/packages/60/ca/780cf3b1a32b18c0f05c441958d3758f02544f1d613abf9488cd78876378/rpds_py-0.30.0-cp313-cp313t-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:51a1234d8febafdfd33a42d97da7a43f5dcb120c1060e352a3fbc0c6d36e2083", size = 383843, upload-time = "2025-11-30T20:23:14.638Z" },
    { url = "https://files.pythonhosted.org/packages/82/86/d5f2e04f2aa6247c613da0c1dd87fcd08fa17107e858193566048a1e2f0a/rpds_py-0.30.0-cp313-cp313t-manylinux_2_31_riscv64.whl", hash = "sha256:eb2c4071ab598733724c08221091e8d80e89064cd472819285a9ab0f24bcedb9", size = 396507, upload-time = "2025-11-30T20:23:16.105Z" },
    { url = "https://files.pythonhosted.org/packages/4b/9a/453255d2f769fe44e07ea9785c8347edaf867f7026872e76c1ad9f7bed92/rpds_py-0.30.0-cp313-cp313t-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:6bdfdb946967d816e6adf9a3d8201bfad269c67efe6cefd7093ef959683c8de0", size = 414949, upload-time = "2025-11-30T20:23:17.539Z" },
    { url = "https://files.pythonhosted.org/packages/a3/31/622a86cdc0c45d6df0e9ccb6becdba5074735e7033c20e401a6d9d0e2ca0/rpds_py-0.30.0-cp313-cp313t-musllinux_1_2_aarch64.whl", hash = "sha256:c77afbd5f5250bf27bf516c7c4a016813eb2d3e116139aed0096940c5982da94", size = 565790, upload-time = "2025-11-30T20:23:19.029Z" },
    { url = "https://files.pythonhosted.org/packages/1c/5d/15bbf0fb4a3f58a3b1c67855ec1efcc4ceaef4e86644665fff03e1b66d8d/rpds_py-0.30.0-cp313-cp313t-musllinux_1_2_i686.whl", hash = "sha256:61046904275472a76c8c90c9ccee9013d70a6d0f73eecefd38c1ae7c39045a08", size = 590217, upload-time = "2025-11-30T20:23:20.885Z" },
    { url = "https://files.pythonhosted.org/packages/6d/61/21b8c41f68e60c8cc3b2e25644f0e3681926020f11d06ab0b78e3c6bbff1/rpds_py-0.30.0-cp313-cp313t-musllinux_1_2_x86_64.whl", hash = "sha256:4c5f36a861bc4b7da6516dbdf302c55313afa09b81931e8280361a4f6c9a2d27", size = 555806, upload-time = "2025-11-30T20:23:22.488Z" },
    { url = "https://files.pythonhosted.org/packages/f9/39/7e067bb06c31de48de3eb200f9fc7c58982a4d3db44b07e73963e10d3be9/rpds_py-0.30.0-cp313-cp313t-win32.whl", hash = "sha256:3d4a69de7a3e50ffc214ae16d79d8fbb0922972da0356dcf4d0fdca2878559c6", size = 211341, upload-time = "2025-11-30T20:23:24.449Z" },
    { url = "https://files.pythonhosted.org/packages/0a/4d/222ef0b46443cf4cf46764d9c630f3fe4abaa7245be9417e56e9f52b8f65/rpds_py-0.30.0-cp313-cp313t-win_amd64.whl", hash = "sha256:f14fc5df50a716f7ece6a80b6c78bb35ea2ca47c499e422aa4463455dd96d56d", size = 225768, upload-time = "2025-11-30T20:23:25.908Z" },
    { url = "https://files.pythonhosted.org/packages/86/81/dad16382ebbd3d0e0328776d8fd7ca94220e4fa0798d1dc5e7da48cb3201/rpds_py-0.30.0-cp314-cp314-macosx_10_12_x86_64.whl", hash = "sha256:68f19c879420aa08f61203801423f6cd5ac5f0ac4ac82a2368a9fcd6a9a075e0", size = 362099, upload-time = "2025-11-30T20:23:27.316Z" },
    { url = "https://files.pythonhosted.org/packages/2b/60/19f7884db5d5603edf3c6bce35408f45ad3e97e10007df0e17dd57af18f8/rpds_py-0.30.0-cp314-cp314-macosx_11_0_arm64.whl", hash = "sha256:ec7c4490c672c1a0389d319b3a9cfcd098dcdc4783991553c332a15acf7249be", size = 353192, upload-time = "2025-11-30T20:23:29.151Z" },
    { url = "https://files.pythonhosted.org/packages/bf/c4/76eb0e1e72d1a9c4703c69607cec123c29028bff28ce41588792417098ac/rpds_py-0.30.0-cp314-cp314-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:f251c812357a3fed308d684a5079ddfb9d933860fc6de89f2b7ab00da481e65f", size = 384080, upload-time = "2025-11-30T20:23:30.785Z" },
    { url = "https://files.pythonhosted.org/packages/72/87/87ea665e92f3298d1b26d78814721dc39ed8d2c74b86e83348d6b48a6f31/rpds_py-0.30.0-cp314-cp314-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:ac98b175585ecf4c0348fd7b29c3864bda53b805c773cbf7bfdaffc8070c976f", size = 394841, upload-time = "2025-11-30T20:23:32.209Z" },
    { url = "https://files.pythonhosted.org/packages/77/ad/7783a89ca0587c15dcbf139b4a8364a872a25f861bdb88ed99f9b0dec985/rpds_py-0.30.0-cp314-cp314-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:3e62880792319dbeb7eb866547f2e35973289e7d5696c6e295476448f5b63c87", size = 516670, upload-time = "2025-11-30T20:23:33.742Z" },
    { url = "https://files.pythonhosted.org/packages/5b/3c/2882bdac942bd2172f3da574eab16f309ae10a3925644e969536553cb4ee/rpds_py-0.30.0-cp314-cp314-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:4e7fc54e0900ab35d041b0601431b0a0eb495f0851a0639b6ef90f7741b39a18", size = 408005, upload-time = "2025-11-30T20:23:35.253Z" },
    { url = "https://files.pythonhosted.org/packages/ce/81/9a91c0111ce1758c92516a3e44776920b579d9a7c09b2b06b642d4de3f0f/rpds_py-0.30.0-cp314-cp314-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:47e77dc9822d3ad616c3d5759ea5631a75e5809d5a28707744ef79d7a1bcfcad", size = 382112, upload-time = "2025-11-30T20:23:36.842Z" },
    { url = "https://files.pythonhosted.org/packages/cf/8e/1da49d4a107027e5fbc64daeab96a0706361a2918da10cb41769244b805d/rpds_py-0.30.0-cp314-cp314-manylinux_2_31_riscv64.whl", hash = "sha256:b4dc1a6ff022ff85ecafef7979a2c6eb423430e05f1165d6688234e62ba99a07", size = 399049, upload-time = "2025-11-30T20:23:38.343Z" },
    { url = "https://files.pythonhosted.org/packages/df/5a/7ee239b1aa48a127570ec03becbb29c9d5a9eb092febbd1699d567cae859/rpds_py-0.30.0-cp314-cp314-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:4559c972db3a360808309e06a74628b95eaccbf961c335c8fe0d590cf587456f", size = 415661, upload-time = "2025-11-30T20:23:40.263Z" },
    { url = "https://files.pythonhosted.org/packages/70/ea/caa143cf6b772f823bc7929a45da1fa83569ee49b11d18d0ada7f5ee6fd6/rpds_py-0.30.0-cp314-cp314-musllinux_1_2_aarch64.whl", hash = "sha256:0ed177ed9bded28f8deb6ab40c183cd1192aa0de40c12f38be4d59cd33cb5c65", size = 565606, upload-time = "2025-11-30T20:23:42.186Z" },
    { url = "https://files.pythonhosted.org/packages/64/91/ac20ba2d69303f961ad8cf55bf7dbdb4763f627291ba3d0d7d67333cced9/rpds_py-0.30.0-cp314-cp314-musllinux_1_2_i686.whl", hash = "sha256:ad1fa8db769b76ea911cb4e10f049d80bf518c104f15b3edb2371cc65375c46f", size = 591126, upload-time = "2025-11-30T20:23:44.086Z" },
    { url = "https://files.pythonhosted.org/packages/21/20/7ff5f3c8b00c8a95f75985128c26ba44503fb35b8e0259d812766ea966c7/rpds_py-0.30.0-cp314-cp314-musllinux_1_2_x86_64.whl", hash = "sha256:46e83c697b1f1c72b50e5ee5adb4353eef7406fb3f2043d64c33f20ad1c2fc53", size = 553371, upload-time = "2025-11-30T20:23:46.004Z" },
    { url = "https://files.pythonhosted.org/packages/72/c7/81dadd7b27c8ee391c132a6b192111ca58d866577ce2d9b0ca157552cce0/rpds_py-0.30.0-cp314-cp314-win32.whl", hash = "sha256:ee454b2a007d57363c2dfd5b6ca4a5d7e2c518938f8ed3b706e37e5d470801ed", size = 215298, upload-time = "2025-11-30T20:23:47.696Z" },
    { url = "https://files.pythonhosted.org/packages/3e/d2/1aaac33287e8cfb07aab2e6b8ac1deca62f6f65411344f1433c55e6f3eb8/rpds_py-0.30.0-cp314-cp314-win_amd64.whl", hash = "sha256:95f0802447ac2d10bcc69f6dc28fe95fdf17940367b21d34e34c737870758950", size = 228604, upload-time = "2025-11-30T20:23:49.501Z" },
    { url = "https://files.pythonhosted.org/packages/e8/95/ab005315818cc519ad074cb7784dae60d939163108bd2b394e60dc7b5461/rpds_py-0.30.0-cp314-cp314-win_arm64.whl", hash = "sha256:613aa4771c99f03346e54c3f038e4cc574ac09a3ddfb0e8878487335e96dead6", size = 222391, upload-time = "2025-11-30T20:23:50.96Z" },
    { url = "https://files.pythonhosted.org/packages/9e/68/154fe0194d83b973cdedcdcc88947a2752411165930182ae41d983dcefa6/rpds_py-0.30.0-cp314-cp314t-macosx_10_12_x86_64.whl", hash = "sha256:7e6ecfcb62edfd632e56983964e6884851786443739dbfe3582947e87274f7cb", size = 364868, upload-time = "2025-11-30T20:23:52.494Z" },
    { url = "https://files.pythonhosted.org/packages/83/69/8bbc8b07ec854d92a8b75668c24d2abcb1719ebf890f5604c61c9369a16f/rpds_py-0.30.0-cp314-cp314t-macosx_11_0_arm64.whl", hash = "sha256:a1d0bc22a7cdc173fedebb73ef81e07faef93692b8c1ad3733b67e31e1b6e1b8", size = 353747, upload-time = "2025-11-30T20:23:54.036Z" },
    { url = "https://files.pythonhosted.org/packages/ab/00/ba2e50183dbd9abcce9497fa5149c62b4ff3e22d338a30d690f9af970561/rpds_py-0.30.0-cp314-cp314t-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:0d08f00679177226c4cb8c5265012eea897c8ca3b93f429e546600c971bcbae7", size = 383795, upload-time = "2025-11-30T20:23:55.556Z" },
    { url = "https://files.pythonhosted.org/packages/05/6f/86f0272b84926bcb0e4c972262f54223e8ecc556b3224d281e6598fc9268/rpds_py-0.30.0-cp314-cp314t-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:5965af57d5848192c13534f90f9dd16464f3c37aaf166cc1da1cae1fd5a34898", size = 393330, upload-time = "2025-11-30T20:23:57.033Z" },
    { url = "https://files.pythonhosted.org/packages/cb/e9/0e02bb2e6dc63d212641da45df2b0bf29699d01715913e0d0f017ee29438/rpds_py-0.30.0-cp314-cp314t-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:9a4e86e34e9ab6b667c27f3211ca48f73dba7cd3d90f8d5b11be56e5dbc3fb4e", size = 518194, upload-time = "2025-11-30T20:23:58.637Z" },
    { url = "https://files.pythonhosted.org/packages/ee/ca/be7bca14cf21513bdf9c0606aba17d1f389ea2b6987035eb4f62bd923f25/rpds_py-0.30.0-cp314-cp314t-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:e5d3e6b26f2c785d65cc25ef1e5267ccbe1b069c5c21b8cc724efee290554419", size = 408340, upload-time = "2025-11-30T20:24:00.2Z" },
    { url = "https://files.pythonhosted.org/packages/c2/c7/736e00ebf39ed81d75544c0da6ef7b0998f8201b369acf842f9a90dc8fce/rpds_py-0.30.0-cp314-cp314t-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:626a7433c34566535b6e56a1b39a7b17ba961e97ce3b80ec62e6f1312c025551", size = 383765, upload-time = "2025-11-30T20:24:01.759Z" },
    { url = "https://files.pythonhosted.org/packages/4a/3f/da50dfde9956aaf365c4adc9533b100008ed31aea635f2b8d7b627e25b49/rpds_py-0.30.0-cp314-cp314t-manylinux_2_31_riscv64.whl", hash = "sha256:acd7eb3f4471577b9b5a41baf02a978e8bdeb08b4b355273994f8b87032000a8", size = 396834, upload-time = "2025-11-30T20:24:03.687Z" },
    { url = "https://files.pythonhosted.org/packages/4e/00/34bcc2565b6020eab2623349efbdec810676ad571995911f1abdae62a3a0/rpds_py-0.30.0-cp314-cp314t-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:fe5fa731a1fa8a0a56b0977413f8cacac1768dad38d16b3a296712709476fbd5", size = 415470, upload-time = "2025-11-30T20:24:05.232Z" },
    { url = "https://files.pythonhosted.org/packages/8c/28/882e72b5b3e6f718d5453bd4d0d9cf8df36fddeb4ddbbab17869d5868616/rpds_py-0.30.0-cp314-cp314t-musllinux_1_2_aarch64.whl", hash = "sha256:74a3243a411126362712ee1524dfc90c650a503502f135d54d1b352bd01f2404", size = 565630, upload-time = "2025-11-30T20:24:06.878Z" },
    { url = "https://files.pythonhosted.org/packages/3b/97/04a65539c17692de5b85c6e293520fd01317fd878ea1995f0367d4532fb1/rpds_py-0.30.0-cp314-cp314t-musllinux_1_2_i686.whl", hash = "sha256:3e8eeb0544f2eb0d2581774be4c3410356eba189529a6b3e36bbbf9696175856", size = 591148, upload-time = "2025-11-30T20:24:08.445Z" },
    { url = "https://files.pythonhosted.org/packages/85/70/92482ccffb96f5441aab93e26c4d66489eb599efdcf96fad90c14bbfb976/rpds_py-0.30.0-cp314-cp314t-musllinux_1_2_x86_64.whl", hash = "sha256:dbd936cde57abfee19ab3213cf9c26be06d60750e60a8e4dd85d1ab12c8b1f40", size = 556030, upload-time = "2025-11-30T20:24:10.956Z" },
    { url = "https://files.pythonhosted.org/packages/20/53/7c7e784abfa500a2b6b583b147ee4bb5a2b3747a9166bab52fec4b5b5e7d/rpds_py-0.30.0-cp314-cp314t-win32.whl", hash = "sha256:dc824125c72246d924f7f796b4f63c1e9dc810c7d9e2355864b3c3a73d59ade0", size = 211570, upload-time = "2025-11-30T20:24:12.735Z" },
    { url = "https://files.pythonhosted.org/packages/d0/02/fa464cdfbe6b26e0600b62c528b72d8608f5cc49f96b8d6e38c95d60c676/rpds_py-0.30.0-cp314-cp314t-win_amd64.whl", hash = "sha256:27f4b0e92de5bfbc6f86e43959e6edd1425c33b5e69aab0984a72047f2bcf1e3", size = 226532, upload-time = "2025-11-30T20:24:14.634Z" },
    { url = "https://files.pythonhosted.org/packages/69/71/3f34339ee70521864411f8b6992e7ab13ac30d8e4e3309e07c7361767d91/rpds_py-0.30.0-pp311-pypy311_pp73-macosx_10_12_x86_64.whl", hash = "sha256:c2262bdba0ad4fc6fb5545660673925c2d2a5d9e2e0fb603aad545427be0fc58", size = 372292, upload-time = "2025-11-30T20:24:16.537Z" },
    { url = "https://files.pythonhosted.org/packages/57/09/f183df9b8f2d66720d2ef71075c59f7e1b336bec7ee4c48f0a2b06857653/rpds_py-0.30.0-pp311-pypy311_pp73-macosx_11_0_arm64.whl", hash = "sha256:ee6af14263f25eedc3bb918a3c04245106a42dfd4f5c2285ea6f997b1fc3f89a", size = 362128, upload-time = "2025-11-30T20:24:18.086Z" },
    { url = "https://files.pythonhosted.org/packages/7a/68/5c2594e937253457342e078f0cc1ded3dd7b2ad59afdbf2d354869110a02/rpds_py-0.30.0-pp311-pypy311_pp73-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:3adbb8179ce342d235c31ab8ec511e66c73faa27a47e076ccc92421add53e2bb", size = 391542, upload-time = "2025-11-30T20:24:20.092Z" },
    { url = "https://files.pythonhosted.org/packages/49/5c/31ef1afd70b4b4fbdb2800249f34c57c64beb687495b10aec0365f53dfc4/rpds_py-0.30.0-pp311-pypy311_pp73-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:250fa00e9543ac9b97ac258bd37367ff5256666122c2d0f2bc97577c60a1818c", size = 404004, upload-time = "2025-11-30T20:24:22.231Z" },
    { url = "https://files.pythonhosted.org/packages/e3/63/0cfbea38d05756f3440ce6534d51a491d26176ac045e2707adc99bb6e60a/rpds_py-0.30.0-pp311-pypy311_pp73-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:9854cf4f488b3d57b9aaeb105f06d78e5529d3145b1e4a41750167e8c213c6d3", size = 527063, upload-time = "2025-11-30T20:24:24.302Z" },
    { url = "https://files.pythonhosted.org/packages/42/e6/01e1f72a2456678b0f618fc9a1a13f882061690893c192fcad9f2926553a/rpds_py-0.30.0-pp311-pypy311_pp73-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:993914b8e560023bc0a8bf742c5f303551992dcb85e247b1e5c7f4a7d145bda5", size = 413099, upload-time = "2025-11-30T20:24:25.916Z" },
    { url = "https://files.pythonhosted.org/packages/b8/25/8df56677f209003dcbb180765520c544525e3ef21ea72279c98b9aa7c7fb/rpds_py-0.30.0-pp311-pypy311_pp73-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:58edca431fb9b29950807e301826586e5bbf24163677732429770a697ffe6738", size = 392177, upload-time = "2025-11-30T20:24:27.834Z" },
    { url = "https://files.pythonhosted.org/packages/4a/b4/0a771378c5f16f8115f796d1f437950158679bcd2a7c68cf251cfb00ed5b/rpds_py-0.30.0-pp311-pypy311_pp73-manylinux_2_31_riscv64.whl", hash = "sha256:dea5b552272a944763b34394d04577cf0f9bd013207bc32323b5a89a53cf9c2f", size = 406015, upload-time = "2025-11-30T20:24:29.457Z" },
    { url = "https://files.pythonhosted.org/packages/36/d8/456dbba0af75049dc6f63ff295a2f92766b9d521fa00de67a2bd6427d57a/rpds_py-0.30.0-pp311-pypy311_pp73-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:ba3af48635eb83d03f6c9735dfb21785303e73d22ad03d489e88adae6eab8877", size = 423736, upload-time = "2025-11-30T20:24:31.22Z" },
    { url = "https://files.pythonhosted.org/packages/13/64/b4d76f227d5c45a7e0b796c674fd81b0a6c4fbd48dc29271857d8219571c/rpds_py-0.30.0-pp311-pypy311_pp73-musllinux_1_2_aarch64.whl", hash = "sha256:dff13836529b921e22f15cb099751209a60009731a68519630a24d61f0b1b30a", size = 573981, upload-time = "2025-11-30T20:24:32.934Z" },
    { url = "https://files.pythonhosted.org/packages/20/91/092bacadeda3edf92bf743cc96a7be133e13a39cdbfd7b5082e7ab638406/rpds_py-0.30.0-pp311-pypy311_pp73-musllinux_1_2_i686.whl", hash = "sha256:1b151685b23929ab7beec71080a8889d4d6d9fa9a983d213f07121205d48e2c4", size = 599782, upload-time = "2025-11-30T20:24:35.169Z" },
    { url = "https://files.pythonhosted.org/packages/d1/b7/b95708304cd49b7b6f82fdd039f1748b66ec2b21d6a45180910802f1abf1/rpds_py-0.30.0-pp311-pypy311_pp73-musllinux_1_2_x86_64.whl", hash = "sha256:ac37f9f516c51e5753f27dfdef11a88330f04de2d564be3991384b2f3535d02e", size = 562191, upload-time = "2025-11-30T20:24:36.853Z" },
]

[[package]]
name = "ruff"
version = "0.14.9"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/f6/1b/ab712a9d5044435be8e9a2beb17cbfa4c241aa9b5e4413febac2a8b79ef2/ruff-0.14.9.tar.gz", hash = "sha256:35f85b25dd586381c0cc053f48826109384c81c00ad7ef1bd977bfcc28119d5b", size = 5809165, upload-time = "2025-12-11T21:39:47.381Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b8/1c/d1b1bba22cffec02351c78ab9ed4f7d7391876e12720298448b29b7229c1/ruff-0.14.9-py3-none-linux_armv6l.whl", hash = "sha256:f1ec5de1ce150ca6e43691f4a9ef5c04574ad9ca35c8b3b0e18877314aba7e75", size = 13576541, upload-time = "2025-12-11T21:39:14.806Z" },
    { url = "https://files.pythonhosted.org/packages/94/ab/ffe580e6ea1fca67f6337b0af59fc7e683344a43642d2d55d251ff83ceae/ruff-0.14.9-py3-none-macosx_10_12_x86_64.whl", hash = "sha256:ed9d7417a299fc6030b4f26333bf1117ed82a61ea91238558c0268c14e00d0c2", size = 13779363, upload-time = "2025-12-11T21:39:20.29Z" },
    { url = "https://files.pythonhosted.org/packages/7d/f8/2be49047f929d6965401855461e697ab185e1a6a683d914c5c19c7962d9e/ruff-0.14.9-py3-none-macosx_11_0_arm64.whl", hash = "sha256:d5dc3473c3f0e4a1008d0ef1d75cee24a48e254c8bed3a7afdd2b4392657ed2c", size = 12925292, upload-time = "2025-12-11T21:39:38.757Z" },
    { url = "https://files.pythonhosted.org/packages/9e/e9/08840ff5127916bb989c86f18924fd568938b06f58b60e206176f327c0fe/ruff-0.14.9-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:84bf7c698fc8f3cb8278830fb6b5a47f9bcc1ed8cb4f689b9dd02698fa840697", size = 13362894, upload-time = "2025-12-11T21:39:02.524Z" },
    { url = "https://files.pythonhosted.org/packages/31/1c/5b4e8e7750613ef43390bb58658eaf1d862c0cc3352d139cd718a2cea164/ruff-0.14.9-py3-none-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:aa733093d1f9d88a5d98988d8834ef5d6f9828d03743bf5e338bf980a19fce27", size = 13311482, upload-time = "2025-12-11T21:39:17.51Z" },
    { url = "https://files.pythonhosted.org/packages/5b/3a/459dce7a8cb35ba1ea3e9c88f19077667a7977234f3b5ab197fad240b404/ruff-0.14.9-py3-none-manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:6a1cfb04eda979b20c8c19550c8b5f498df64ff8da151283311ce3199e8b3648", size = 14016100, upload-time = "2025-12-11T21:39:41.948Z" },
    { url = "https://files.pythonhosted.org/packages/a6/31/f064f4ec32524f9956a0890fc6a944e5cf06c63c554e39957d208c0ffc45/ruff-0.14.9-py3-none-manylinux_2_17_ppc64.manylinux2014_ppc64.whl", hash = "sha256:1e5cb521e5ccf0008bd74d5595a4580313844a42b9103b7388eca5a12c970743", size = 15477729, upload-time = "2025-12-11T21:39:23.279Z" },
    { url = "https://files.pythonhosted.org/packages/7a/6d/f364252aad36ccd443494bc5f02e41bf677f964b58902a17c0b16c53d890/ruff-0.14.9-py3-none-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:cd429a8926be6bba4befa8cdcf3f4dd2591c413ea5066b1e99155ed245ae42bb", size = 15122386, upload-time = "2025-12-11T21:39:33.125Z" },
    { url = "https://files.pythonhosted.org/packages/20/02/e848787912d16209aba2799a4d5a1775660b6a3d0ab3944a4ccc13e64a02/ruff-0.14.9-py3-none-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:ab208c1b7a492e37caeaf290b1378148f75e13c2225af5d44628b95fd7834273", size = 14497124, upload-time = "2025-12-11T21:38:59.33Z" },
    { url = "https://files.pythonhosted.org/packages/f3/51/0489a6a5595b7760b5dbac0dd82852b510326e7d88d51dbffcd2e07e3ff3/ruff-0.14.9-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:72034534e5b11e8a593f517b2f2f2b273eb68a30978c6a2d40473ad0aaa4cb4a", size = 14195343, upload-time = "2025-12-11T21:39:44.866Z" },
    { url = "https://files.pythonhosted.org/packages/f6/53/3bb8d2fa73e4c2f80acc65213ee0830fa0c49c6479313f7a68a00f39e208/ruff-0.14.9-py3-none-manylinux_2_31_riscv64.whl", hash = "sha256:712ff04f44663f1b90a1195f51525836e3413c8a773574a7b7775554269c30ed", size = 14346425, upload-time = "2025-12-11T21:39:05.927Z" },
    { url = "https://files.pythonhosted.org/packages/ad/04/bdb1d0ab876372da3e983896481760867fc84f969c5c09d428e8f01b557f/ruff-0.14.9-py3-none-musllinux_1_2_aarch64.whl", hash = "sha256:a111fee1db6f1d5d5810245295527cda1d367c5aa8f42e0fca9a78ede9b4498b", size = 13258768, upload-time = "2025-12-11T21:39:08.691Z" },
    { url = "https://files.pythonhosted.org/packages/40/d9/8bf8e1e41a311afd2abc8ad12be1b6c6c8b925506d9069b67bb5e9a04af3/ruff-0.14.9-py3-none-musllinux_1_2_armv7l.whl", hash = "sha256:8769efc71558fecc25eb295ddec7d1030d41a51e9dcf127cbd63ec517f22d567", size = 13326939, upload-time = "2025-12-11T21:39:53.842Z" },
    { url = "https://files.pythonhosted.org/packages/f4/56/a213fa9edb6dd849f1cfbc236206ead10913693c72a67fb7ddc1833bf95d/ruff-0.14.9-py3-none-musllinux_1_2_i686.whl", hash = "sha256:347e3bf16197e8a2de17940cd75fd6491e25c0aa7edf7d61aa03f146a1aa885a", size = 13578888, upload-time = "2025-12-11T21:39:35.988Z" },
    { url = "https://files.pythonhosted.org/packages/33/09/6a4a67ffa4abae6bf44c972a4521337ffce9cbc7808faadede754ef7a79c/ruff-0.14.9-py3-none-musllinux_1_2_x86_64.whl", hash = "sha256:7715d14e5bccf5b660f54516558aa94781d3eb0838f8e706fb60e3ff6eff03a8", size = 14314473, upload-time = "2025-12-11T21:39:50.78Z" },
    { url = "https://files.pythonhosted.org/packages/12/0d/15cc82da5d83f27a3c6b04f3a232d61bc8c50d38a6cd8da79228e5f8b8d6/ruff-0.14.9-py3-none-win32.whl", hash = "sha256:df0937f30aaabe83da172adaf8937003ff28172f59ca9f17883b4213783df197", size = 13202651, upload-time = "2025-12-11T21:39:26.628Z" },
    { url = "https://files.pythonhosted.org/packages/32/f7/c78b060388eefe0304d9d42e68fab8cffd049128ec466456cef9b8d4f06f/ruff-0.14.9-py3-none-win_amd64.whl", hash = "sha256:c0b53a10e61df15a42ed711ec0bda0c582039cf6c754c49c020084c55b5b0bc2", size = 14702079, upload-time = "2025-12-11T21:39:11.954Z" },
    { url = "https://files.pythonhosted.org/packages/26/09/7a9520315decd2334afa65ed258fed438f070e31f05a2e43dd480a5e5911/ruff-0.14.9-py3-none-win_arm64.whl", hash = "sha256:8e821c366517a074046d92f0e9213ed1c13dbc5b37a7fc20b07f79b64d62cc84", size = 13744730, upload-time = "2025-12-11T21:39:29.659Z" },
]

[[package]]
name = "secretstorage"
version = "3.5.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "cryptography" },
    { name = "jeepney" },
]
sdist = { url = "https://files.pythonhosted.org/packages/1c/03/e834bcd866f2f8a49a85eaff47340affa3bfa391ee9912a952a1faa68c7b/secretstorage-3.5.0.tar.gz", hash = "sha256:f04b8e4689cbce351744d5537bf6b1329c6fc68f91fa666f60a380edddcd11be", size = 19884, upload-time = "2025-11-23T19:02:53.191Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b7/46/f5af3402b579fd5e11573ce652019a67074317e18c1935cc0b4ba9b35552/secretstorage-3.5.0-py3-none-any.whl", hash = "sha256:0ce65888c0725fcb2c5bc0fdb8e5438eece02c523557ea40ce0703c266248137", size = 15554, upload-time = "2025-11-23T19:02:51.545Z" },
]

[[package]]
name = "sse-starlette"
version = "3.0.4"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "anyio" },
    { name = "starlette" },
]
sdist = { url = "https://files.pythonhosted.org/packages/17/8b/54651ad49bce99a50fd61a7f19c2b6a79fbb072e693101fbb1194c362054/sse_starlette-3.0.4.tar.gz", hash = "sha256:5e34286862e96ead0eb70f5ddd0bd21ab1f6473a8f44419dd267f431611383dd", size = 22576, upload-time = "2025-12-14T16:22:52.493Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/71/22/8ab1066358601163e1ac732837adba3672f703818f693e179b24e0d3b65c/sse_starlette-3.0.4-py3-none-any.whl", hash = "sha256:32c80ef0d04506ced4b0b6ab8fe300925edc37d26f666afb1874c754895f5dc3", size = 11764, upload-time = "2025-12-14T16:22:51.453Z" },
]

[[package]]
name = "starlette"
version = "0.50.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "anyio" },
    { name = "typing-extensions", marker = "python_full_version < '3.13'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/ba/b8/73a0e6a6e079a9d9cfa64113d771e421640b6f679a52eeb9b32f72d871a1/starlette-0.50.0.tar.gz", hash = "sha256:a2a17b22203254bcbc2e1f926d2d55f3f9497f769416b3190768befe598fa3ca", size = 2646985, upload-time = "2025-11-01T15:25:27.516Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/d9/52/1064f510b141bd54025f9b55105e26d1fa970b9be67ad766380a3c9b74b0/starlette-0.50.0-py3-none-any.whl", hash = "sha256:9e5391843ec9b6e472eed1365a78c8098cfceb7a74bfd4d6b1c0c0095efb3bca", size = 74033, upload-time = "2025-11-01T15:25:25.461Z" },
]

[[package]]
name = "tomli"
version = "2.3.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/52/ed/3f73f72945444548f33eba9a87fc7a6e969915e7b1acc8260b30e1f76a2f/tomli-2.3.0.tar.gz", hash = "sha256:64be704a875d2a59753d80ee8a533c3fe183e3f06807ff7dc2232938ccb01549", size = 17392, upload-time = "2025-10-08T22:01:47.119Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b3/2e/299f62b401438d5fe1624119c723f5d877acc86a4c2492da405626665f12/tomli-2.3.0-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:88bd15eb972f3664f5ed4b57c1634a97153b4bac4479dcb6a495f41921eb7f45", size = 153236, upload-time = "2025-10-08T22:01:00.137Z" },
    { url = "https://files.pythonhosted.org/packages/86/7f/d8fffe6a7aefdb61bced88fcb5e280cfd71e08939da5894161bd71bea022/tomli-2.3.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:883b1c0d6398a6a9d29b508c331fa56adbcdff647f6ace4dfca0f50e90dfd0ba", size = 148084, upload-time = "2025-10-08T22:01:01.63Z" },
    { url = "https://files.pythonhosted.org/packages/47/5c/24935fb6a2ee63e86d80e4d3b58b222dafaf438c416752c8b58537c8b89a/tomli-2.3.0-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:d1381caf13ab9f300e30dd8feadb3de072aeb86f1d34a8569453ff32a7dea4bf", size = 234832, upload-time = "2025-10-08T22:01:02.543Z" },
    { url = "https://files.pythonhosted.org/packages/89/da/75dfd804fc11e6612846758a23f13271b76d577e299592b4371a4ca4cd09/tomli-2.3.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:a0e285d2649b78c0d9027570d4da3425bdb49830a6156121360b3f8511ea3441", size = 242052, upload-time = "2025-10-08T22:01:03.836Z" },
    { url = "https://files.pythonhosted.org/packages/70/8c/f48ac899f7b3ca7eb13af73bacbc93aec37f9c954df3c08ad96991c8c373/tomli-2.3.0-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:0a154a9ae14bfcf5d8917a59b51ffd5a3ac1fd149b71b47a3a104ca4edcfa845", size = 239555, upload-time = "2025-10-08T22:01:04.834Z" },
    { url = "https://files.pythonhosted.org/packages/ba/28/72f8afd73f1d0e7829bfc093f4cb98ce0a40ffc0cc997009ee1ed94ba705/tomli-2.3.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:74bf8464ff93e413514fefd2be591c3b0b23231a77f901db1eb30d6f712fc42c", size = 245128, upload-time = "2025-10-08T22:01:05.84Z" },
    { url = "https://files.pythonhosted.org/packages/b6/eb/a7679c8ac85208706d27436e8d421dfa39d4c914dcf5fa8083a9305f58d9/tomli-2.3.0-cp311-cp311-win32.whl", hash = "sha256:00b5f5d95bbfc7d12f91ad8c593a1659b6387b43f054104cda404be6bda62456", size = 96445, upload-time = "2025-10-08T22:01:06.896Z" },
    { url = "https://files.pythonhosted.org/packages/0a/fe/3d3420c4cb1ad9cb462fb52967080575f15898da97e21cb6f1361d505383/tomli-2.3.0-cp311-cp311-win_amd64.whl", hash = "sha256:4dc4ce8483a5d429ab602f111a93a6ab1ed425eae3122032db7e9acf449451be", size = 107165, upload-time = "2025-10-08T22:01:08.107Z" },
    { url = "https://files.pythonhosted.org/packages/ff/b7/40f36368fcabc518bb11c8f06379a0fd631985046c038aca08c6d6a43c6e/tomli-2.3.0-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:d7d86942e56ded512a594786a5ba0a5e521d02529b3826e7761a05138341a2ac", size = 154891, upload-time = "2025-10-08T22:01:09.082Z" },
    { url = "https://files.pythonhosted.org/packages/f9/3f/d9dd692199e3b3aab2e4e4dd948abd0f790d9ded8cd10cbaae276a898434/tomli-2.3.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:73ee0b47d4dad1c5e996e3cd33b8a76a50167ae5f96a2607cbe8cc773506ab22", size = 148796, upload-time = "2025-10-08T22:01:10.266Z" },
    { url = "https://files.pythonhosted.org/packages/60/83/59bff4996c2cf9f9387a0f5a3394629c7efa5ef16142076a23a90f1955fa/tomli-2.3.0-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:792262b94d5d0a466afb5bc63c7daa9d75520110971ee269152083270998316f", size = 242121, upload-time = "2025-10-08T22:01:11.332Z" },
    { url = "https://files.pythonhosted.org/packages/45/e5/7c5119ff39de8693d6baab6c0b6dcb556d192c165596e9fc231ea1052041/tomli-2.3.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:4f195fe57ecceac95a66a75ac24d9d5fbc98ef0962e09b2eddec5d39375aae52", size = 250070, upload-time = "2025-10-08T22:01:12.498Z" },
    { url = "https://files.pythonhosted.org/packages/45/12/ad5126d3a278f27e6701abde51d342aa78d06e27ce2bb596a01f7709a5a2/tomli-2.3.0-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:e31d432427dcbf4d86958c184b9bfd1e96b5b71f8eb17e6d02531f434fd335b8", size = 245859, upload-time = "2025-10-08T22:01:13.551Z" },
    { url = "https://files.pythonhosted.org/packages/fb/a1/4d6865da6a71c603cfe6ad0e6556c73c76548557a8d658f9e3b142df245f/tomli-2.3.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:7b0882799624980785240ab732537fcfc372601015c00f7fc367c55308c186f6", size = 250296, upload-time = "2025-10-08T22:01:14.614Z" },
    { url = "https://files.pythonhosted.org/packages/a0/b7/a7a7042715d55c9ba6e8b196d65d2cb662578b4d8cd17d882d45322b0d78/tomli-2.3.0-cp312-cp312-win32.whl", hash = "sha256:ff72b71b5d10d22ecb084d345fc26f42b5143c5533db5e2eaba7d2d335358876", size = 97124, upload-time = "2025-10-08T22:01:15.629Z" },
    { url = "https://files.pythonhosted.org/packages/06/1e/f22f100db15a68b520664eb3328fb0ae4e90530887928558112c8d1f4515/tomli-2.3.0-cp312-cp312-win_amd64.whl", hash = "sha256:1cb4ed918939151a03f33d4242ccd0aa5f11b3547d0cf30f7c74a408a5b99878", size = 107698, upload-time = "2025-10-08T22:01:16.51Z" },
    { url = "https://files.pythonhosted.org/packages/89/48/06ee6eabe4fdd9ecd48bf488f4ac783844fd777f547b8d1b61c11939974e/tomli-2.3.0-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:5192f562738228945d7b13d4930baffda67b69425a7f0da96d360b0a3888136b", size = 154819, upload-time = "2025-10-08T22:01:17.964Z" },
    { url = "https://files.pythonhosted.org/packages/f1/01/88793757d54d8937015c75dcdfb673c65471945f6be98e6a0410fba167ed/tomli-2.3.0-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:be71c93a63d738597996be9528f4abe628d1adf5e6eb11607bc8fe1a510b5dae", size = 148766, upload-time = "2025-10-08T22:01:18.959Z" },
    { url = "https://files.pythonhosted.org/packages/42/17/5e2c956f0144b812e7e107f94f1cc54af734eb17b5191c0bbfb72de5e93e/tomli-2.3.0-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:c4665508bcbac83a31ff8ab08f424b665200c0e1e645d2bd9ab3d3e557b6185b", size = 240771, upload-time = "2025-10-08T22:01:20.106Z" },
    { url = "https://files.pythonhosted.org/packages/d5/f4/0fbd014909748706c01d16824eadb0307115f9562a15cbb012cd9b3512c5/tomli-2.3.0-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:4021923f97266babc6ccab9f5068642a0095faa0a51a246a6a02fccbb3514eaf", size = 248586, upload-time = "2025-10-08T22:01:21.164Z" },
    { url = "https://files.pythonhosted.org/packages/30/77/fed85e114bde5e81ecf9bc5da0cc69f2914b38f4708c80ae67d0c10180c5/tomli-2.3.0-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:a4ea38c40145a357d513bffad0ed869f13c1773716cf71ccaa83b0fa0cc4e42f", size = 244792, upload-time = "2025-10-08T22:01:22.417Z" },
    { url = "https://files.pythonhosted.org/packages/55/92/afed3d497f7c186dc71e6ee6d4fcb0acfa5f7d0a1a2878f8beae379ae0cc/tomli-2.3.0-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:ad805ea85eda330dbad64c7ea7a4556259665bdf9d2672f5dccc740eb9d3ca05", size = 248909, upload-time = "2025-10-08T22:01:23.859Z" },
    { url = "https://files.pythonhosted.org/packages/f8/84/ef50c51b5a9472e7265ce1ffc7f24cd4023d289e109f669bdb1553f6a7c2/tomli-2.3.0-cp313-cp313-win32.whl", hash = "sha256:97d5eec30149fd3294270e889b4234023f2c69747e555a27bd708828353ab606", size = 96946, upload-time = "2025-10-08T22:01:24.893Z" },
    { url = "https://files.pythonhosted.org/packages/b2/b7/718cd1da0884f281f95ccfa3a6cc572d30053cba64603f79d431d3c9b61b/tomli-2.3.0-cp313-cp313-win_amd64.whl", hash = "sha256:0c95ca56fbe89e065c6ead5b593ee64b84a26fca063b5d71a1122bf26e533999", size = 107705, upload-time = "2025-10-08T22:01:26.153Z" },
    { url = "https://files.pythonhosted.org/packages/19/94/aeafa14a52e16163008060506fcb6aa1949d13548d13752171a755c65611/tomli-2.3.0-cp314-cp314-macosx_10_13_x86_64.whl", hash = "sha256:cebc6fe843e0733ee827a282aca4999b596241195f43b4cc371d64fc6639da9e", size = 154244, upload-time = "2025-10-08T22:01:27.06Z" },
    { url = "https://files.pythonhosted.org/packages/db/e4/1e58409aa78eefa47ccd19779fc6f36787edbe7d4cd330eeeedb33a4515b/tomli-2.3.0-cp314-cp314-macosx_11_0_arm64.whl", hash = "sha256:4c2ef0244c75aba9355561272009d934953817c49f47d768070c3c94355c2aa3", size = 148637, upload-time = "2025-10-08T22:01:28.059Z" },
    { url = "https://files.pythonhosted.org/packages/26/b6/d1eccb62f665e44359226811064596dd6a366ea1f985839c566cd61525ae/tomli-2.3.0-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:c22a8bf253bacc0cf11f35ad9808b6cb75ada2631c2d97c971122583b129afbc", size = 241925, upload-time = "2025-10-08T22:01:29.066Z" },
    { url = "https://files.pythonhosted.org/packages/70/91/7cdab9a03e6d3d2bb11beae108da5bdc1c34bdeb06e21163482544ddcc90/tomli-2.3.0-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:0eea8cc5c5e9f89c9b90c4896a8deefc74f518db5927d0e0e8d4a80953d774d0", size = 249045, upload-time = "2025-10-08T22:01:31.98Z" },
    { url = "https://files.pythonhosted.org/packages/15/1b/8c26874ed1f6e4f1fcfeb868db8a794cbe9f227299402db58cfcc858766c/tomli-2.3.0-cp314-cp314-musllinux_1_2_aarch64.whl", hash = "sha256:b74a0e59ec5d15127acdabd75ea17726ac4c5178ae51b85bfe39c4f8a278e879", size = 245835, upload-time = "2025-10-08T22:01:32.989Z" },
    { url = "https://files.pythonhosted.org/packages/fd/42/8e3c6a9a4b1a1360c1a2a39f0b972cef2cc9ebd56025168c4137192a9321/tomli-2.3.0-cp314-cp314-musllinux_1_2_x86_64.whl", hash = "sha256:b5870b50c9db823c595983571d1296a6ff3e1b88f734a4c8f6fc6188397de005", size = 253109, upload-time = "2025-10-08T22:01:34.052Z" },
    { url = "https://files.pythonhosted.org/packages/22/0c/b4da635000a71b5f80130937eeac12e686eefb376b8dee113b4a582bba42/tomli-2.3.0-cp314-cp314-win32.whl", hash = "sha256:feb0dacc61170ed7ab602d3d972a58f14ee3ee60494292d384649a3dc38ef463", size = 97930, upload-time = "2025-10-08T22:01:35.082Z" },
    { url = "https://files.pythonhosted.org/packages/b9/74/cb1abc870a418ae99cd5c9547d6bce30701a954e0e721821df483ef7223c/tomli-2.3.0-cp314-cp314-win_amd64.whl", hash = "sha256:b273fcbd7fc64dc3600c098e39136522650c49bca95df2d11cf3b626422392c8", size = 107964, upload-time = "2025-10-08T22:01:36.057Z" },
    { url = "https://files.pythonhosted.org/packages/54/78/5c46fff6432a712af9f792944f4fcd7067d8823157949f4e40c56b8b3c83/tomli-2.3.0-cp314-cp314t-macosx_10_13_x86_64.whl", hash = "sha256:940d56ee0410fa17ee1f12b817b37a4d4e4dc4d27340863cc67236c74f582e77", size = 163065, upload-time = "2025-10-08T22:01:37.27Z" },
    { url = "https://files.pythonhosted.org/packages/39/67/f85d9bd23182f45eca8939cd2bc7050e1f90c41f4a2ecbbd5963a1d1c486/tomli-2.3.0-cp314-cp314t-macosx_11_0_arm64.whl", hash = "sha256:f85209946d1fe94416debbb88d00eb92ce9cd5266775424ff81bc959e001acaf", size = 159088, upload-time = "2025-10-08T22:01:38.235Z" },
    { url = "https://files.pythonhosted.org/packages/26/5a/4b546a0405b9cc0659b399f12b6adb750757baf04250b148d3c5059fc4eb/tomli-2.3.0-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:a56212bdcce682e56b0aaf79e869ba5d15a6163f88d5451cbde388d48b13f530", size = 268193, upload-time = "2025-10-08T22:01:39.712Z" },
    { url = "https://files.pythonhosted.org/packages/42/4f/2c12a72ae22cf7b59a7fe75b3465b7aba40ea9145d026ba41cb382075b0e/tomli-2.3.0-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:c5f3ffd1e098dfc032d4d3af5c0ac64f6d286d98bc148698356847b80fa4de1b", size = 275488, upload-time = "2025-10-08T22:01:40.773Z" },
    { url = "https://files.pythonhosted.org/packages/92/04/a038d65dbe160c3aa5a624e93ad98111090f6804027d474ba9c37c8ae186/tomli-2.3.0-cp314-cp314t-musllinux_1_2_aarch64.whl", hash = "sha256:5e01decd096b1530d97d5d85cb4dff4af2d8347bd35686654a004f8dea20fc67", size = 272669, upload-time = "2025-10-08T22:01:41.824Z" },
    { url = "https://files.pythonhosted.org/packages/be/2f/8b7c60a9d1612a7cbc39ffcca4f21a73bf368a80fc25bccf8253e2563267/tomli-2.3.0-cp314-cp314t-musllinux_1_2_x86_64.whl", hash = "sha256:8a35dd0e643bb2610f156cca8db95d213a90015c11fee76c946aa62b7ae7e02f", size = 279709, upload-time = "2025-10-08T22:01:43.177Z" },
    { url = "https://files.pythonhosted.org/packages/7e/46/cc36c679f09f27ded940281c38607716c86cf8ba4a518d524e349c8b4874/tomli-2.3.0-cp314-cp314t-win32.whl", hash = "sha256:a1f7f282fe248311650081faafa5f4732bdbfef5d45fe3f2e702fbc6f2d496e0", size = 107563, upload-time = "2025-10-08T22:01:44.233Z" },
    { url = "https://files.pythonhosted.org/packages/84/ff/426ca8683cf7b753614480484f6437f568fd2fda2edbdf57a2d3d8b27a0b/tomli-2.3.0-cp314-cp314t-win_amd64.whl", hash = "sha256:70a251f8d4ba2d9ac2542eecf008b3c8a9fc5c3f9f02c56a9d7952612be2fdba", size = 119756, upload-time = "2025-10-08T22:01:45.234Z" },
    { url = "https://files.pythonhosted.org/packages/77/b8/0135fadc89e73be292b473cb820b4f5a08197779206b33191e801feeae40/tomli-2.3.0-py3-none-any.whl", hash = "sha256:e95b1af3c5b07d9e643909b5abbec77cd9f1217e6d0bca72b0234736b9fb1f1b", size = 14408, upload-time = "2025-10-08T22:01:46.04Z" },
]

[[package]]
name = "typing-extensions"
version = "4.15.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/72/94/1a15dd82efb362ac84269196e94cf00f187f7ed21c242792a923cdb1c61f/typing_extensions-4.15.0.tar.gz", hash = "sha256:0cea48d173cc12fa28ecabc3b837ea3cf6f38c6d1136f85cbaaf598984861466", size = 109391, upload-time = "2025-08-25T13:49:26.313Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/18/67/36e9267722cc04a6b9f15c7f3441c2363321a3ea07da7ae0c0707beb2a9c/typing_extensions-4.15.0-py3-none-any.whl", hash = "sha256:f0fa19c6845758ab08074a0cfa8b7aecb71c999ca73d62883bc25cc018c4e548", size = 44614, upload-time = "2025-08-25T13:49:24.86Z" },
]

[[package]]
name = "typing-inspection"
version = "0.4.2"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "typing-extensions" },
]
sdist = { url = "https://files.pythonhosted.org/packages/55/e3/70399cb7dd41c10ac53367ae42139cf4b1ca5f36bb3dc6c9d33acdb43655/typing_inspection-0.4.2.tar.gz", hash = "sha256:ba561c48a67c5958007083d386c3295464928b01faa735ab8547c5692e87f464", size = 75949, upload-time = "2025-10-01T02:14:41.687Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/dc/9b/47798a6c91d8bdb567fe2698fe81e0c6b7cb7ef4d13da4114b41d239f65d/typing_inspection-0.4.2-py3-none-any.whl", hash = "sha256:4ed1cacbdc298c220f1bd249ed5287caa16f34d44ef4e9c3d0cbad5b521545e7", size = 14611, upload-time = "2025-10-01T02:14:40.154Z" },
]

[[package]]
name = "uncalled-for"
version = "0.2.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/02/7c/b5b7d8136f872e3f13b0584e576886de0489d7213a12de6bebf29ff6ebfc/uncalled_for-0.2.0.tar.gz", hash = "sha256:b4f8fdbcec328c5a113807d653e041c5094473dd4afa7c34599ace69ccb7e69f", size = 49488, upload-time = "2026-02-27T17:40:58.137Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/ff/7f/4320d9ce3be404e6310b915c3629fe27bf1e2f438a1a7a3cb0396e32e9a9/uncalled_for-0.2.0-py3-none-any.whl", hash = "sha256:2c0bd338faff5f930918f79e7eb9ff48290df2cb05fcc0b40a7f334e55d4d85f", size = 11351, upload-time = "2026-02-27T17:40:56.804Z" },
]

[[package]]
name = "uvicorn"
version = "0.38.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "click" },
    { name = "h11" },
    { name = "typing-extensions", marker = "python_full_version < '3.11'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/cb/ce/f06b84e2697fef4688ca63bdb2fdf113ca0a3be33f94488f2cadb690b0cf/uvicorn-0.38.0.tar.gz", hash = "sha256:fd97093bdd120a2609fc0d3afe931d4d4ad688b6e75f0f929fde1bc36fe0e91d", size = 80605, upload-time = "2025-10-18T13:46:44.63Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/ee/d9/d88e73ca598f4f6ff671fb5fde8a32925c2e08a637303a1d12883c7305fa/uvicorn-0.38.0-py3-none-any.whl", hash = "sha256:48c0afd214ceb59340075b4a052ea1ee91c16fbc2a9b1469cca0e54566977b02", size = 68109, upload-time = "2025-10-18T13:46:42.958Z" },
]

[[package]]
name = "watchfiles"
version = "1.1.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "anyio" },
]
sdist = { url = "https://files.pythonhosted.org/packages/c2/c9/8869df9b2a2d6c59d79220a4db37679e74f807c559ffe5265e08b227a210/watchfiles-1.1.1.tar.gz", hash = "sha256:a173cb5c16c4f40ab19cecf48a534c409f7ea983ab8fed0741304a1c0a31b3f2", size = 94440, upload-time = "2025-10-14T15:06:21.08Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/a7/1a/206e8cf2dd86fddf939165a57b4df61607a1e0add2785f170a3f616b7d9f/watchfiles-1.1.1-cp310-cp310-macosx_10_12_x86_64.whl", hash = "sha256:eef58232d32daf2ac67f42dea51a2c80f0d03379075d44a587051e63cc2e368c", size = 407318, upload-time = "2025-10-14T15:04:18.753Z" },
    { url = "https://files.pythonhosted.org/packages/b3/0f/abaf5262b9c496b5dad4ed3c0e799cbecb1f8ea512ecb6ddd46646a9fca3/watchfiles-1.1.1-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:03fa0f5237118a0c5e496185cafa92878568b652a2e9a9382a5151b1a0380a43", size = 394478, upload-time = "2025-10-14T15:04:20.297Z" },
    { url = "https://files.pythonhosted.org/packages/b1/04/9cc0ba88697b34b755371f5ace8d3a4d9a15719c07bdc7bd13d7d8c6a341/watchfiles-1.1.1-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:8ca65483439f9c791897f7db49202301deb6e15fe9f8fe2fed555bf986d10c31", size = 449894, upload-time = "2025-10-14T15:04:21.527Z" },
    { url = "https://files.pythonhosted.org/packages/d2/9c/eda4615863cd8621e89aed4df680d8c3ec3da6a4cf1da113c17decd87c7f/watchfiles-1.1.1-cp310-cp310-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:f0ab1c1af0cb38e3f598244c17919fb1a84d1629cc08355b0074b6d7f53138ac", size = 459065, upload-time = "2025-10-14T15:04:22.795Z" },
    { url = "https://files.pythonhosted.org/packages/84/13/f28b3f340157d03cbc8197629bc109d1098764abe1e60874622a0be5c112/watchfiles-1.1.1-cp310-cp310-manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:3bc570d6c01c206c46deb6e935a260be44f186a2f05179f52f7fcd2be086a94d", size = 488377, upload-time = "2025-10-14T15:04:24.138Z" },
    { url = "https://files.pythonhosted.org/packages/86/93/cfa597fa9389e122488f7ffdbd6db505b3b915ca7435ecd7542e855898c2/watchfiles-1.1.1-cp310-cp310-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:e84087b432b6ac94778de547e08611266f1f8ffad28c0ee4c82e028b0fc5966d", size = 595837, upload-time = "2025-10-14T15:04:25.057Z" },
    { url = "https://files.pythonhosted.org/packages/57/1e/68c1ed5652b48d89fc24d6af905d88ee4f82fa8bc491e2666004e307ded1/watchfiles-1.1.1-cp310-cp310-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:620bae625f4cb18427b1bb1a2d9426dc0dd5a5ba74c7c2cdb9de405f7b129863", size = 473456, upload-time = "2025-10-14T15:04:26.497Z" },
    { url = "https://files.pythonhosted.org/packages/d5/dc/1a680b7458ffa3b14bb64878112aefc8f2e4f73c5af763cbf0bd43100658/watchfiles-1.1.1-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:544364b2b51a9b0c7000a4b4b02f90e9423d97fbbf7e06689236443ebcad81ab", size = 455614, upload-time = "2025-10-14T15:04:27.539Z" },
    { url = "https://files.pythonhosted.org/packages/61/a5/3d782a666512e01eaa6541a72ebac1d3aae191ff4a31274a66b8dd85760c/watchfiles-1.1.1-cp310-cp310-musllinux_1_1_aarch64.whl", hash = "sha256:bbe1ef33d45bc71cf21364df962af171f96ecaeca06bd9e3d0b583efb12aec82", size = 630690, upload-time = "2025-10-14T15:04:28.495Z" },
    { url = "https://files.pythonhosted.org/packages/9b/73/bb5f38590e34687b2a9c47a244aa4dd50c56a825969c92c9c5fc7387cea1/watchfiles-1.1.1-cp310-cp310-musllinux_1_1_x86_64.whl", hash = "sha256:1a0bb430adb19ef49389e1ad368450193a90038b5b752f4ac089ec6942c4dff4", size = 622459, upload-time = "2025-10-14T15:04:29.491Z" },
    { url = "https://files.pythonhosted.org/packages/f1/ac/c9bb0ec696e07a20bd58af5399aeadaef195fb2c73d26baf55180fe4a942/watchfiles-1.1.1-cp310-cp310-win32.whl", hash = "sha256:3f6d37644155fb5beca5378feb8c1708d5783145f2a0f1c4d5a061a210254844", size = 272663, upload-time = "2025-10-14T15:04:30.435Z" },
    { url = "https://files.pythonhosted.org/packages/11/a0/a60c5a7c2ec59fa062d9a9c61d02e3b6abd94d32aac2d8344c4bdd033326/watchfiles-1.1.1-cp310-cp310-win_amd64.whl", hash = "sha256:a36d8efe0f290835fd0f33da35042a1bb5dc0e83cbc092dcf69bce442579e88e", size = 287453, upload-time = "2025-10-14T15:04:31.53Z" },
    { url = "https://files.pythonhosted.org/packages/1f/f8/2c5f479fb531ce2f0564eda479faecf253d886b1ab3630a39b7bf7362d46/watchfiles-1.1.1-cp311-cp311-macosx_10_12_x86_64.whl", hash = "sha256:f57b396167a2565a4e8b5e56a5a1c537571733992b226f4f1197d79e94cf0ae5", size = 406529, upload-time = "2025-10-14T15:04:32.899Z" },
    { url = "https://files.pythonhosted.org/packages/fe/cd/f515660b1f32f65df671ddf6f85bfaca621aee177712874dc30a97397977/watchfiles-1.1.1-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:421e29339983e1bebc281fab40d812742268ad057db4aee8c4d2bce0af43b741", size = 394384, upload-time = "2025-10-14T15:04:33.761Z" },
    { url = "https://files.pythonhosted.org/packages/7b/c3/28b7dc99733eab43fca2d10f55c86e03bd6ab11ca31b802abac26b23d161/watchfiles-1.1.1-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:6e43d39a741e972bab5d8100b5cdacf69db64e34eb19b6e9af162bccf63c5cc6", size = 448789, upload-time = "2025-10-14T15:04:34.679Z" },
    { url = "https://files.pythonhosted.org/packages/4a/24/33e71113b320030011c8e4316ccca04194bf0cbbaeee207f00cbc7d6b9f5/watchfiles-1.1.1-cp311-cp311-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:f537afb3276d12814082a2e9b242bdcf416c2e8fd9f799a737990a1dbe906e5b", size = 460521, upload-time = "2025-10-14T15:04:35.963Z" },
    { url = "https://files.pythonhosted.org/packages/f4/c3/3c9a55f255aa57b91579ae9e98c88704955fa9dac3e5614fb378291155df/watchfiles-1.1.1-cp311-cp311-manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:b2cd9e04277e756a2e2d2543d65d1e2166d6fd4c9b183f8808634fda23f17b14", size = 488722, upload-time = "2025-10-14T15:04:37.091Z" },
    { url = "https://files.pythonhosted.org/packages/49/36/506447b73eb46c120169dc1717fe2eff07c234bb3232a7200b5f5bd816e9/watchfiles-1.1.1-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:5f3f58818dc0b07f7d9aa7fe9eb1037aecb9700e63e1f6acfed13e9fef648f5d", size = 596088, upload-time = "2025-10-14T15:04:38.39Z" },
    { url = "https://files.pythonhosted.org/packages/82/ab/5f39e752a9838ec4d52e9b87c1e80f1ee3ccdbe92e183c15b6577ab9de16/watchfiles-1.1.1-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:9bb9f66367023ae783551042d31b1d7fd422e8289eedd91f26754a66f44d5cff", size = 472923, upload-time = "2025-10-14T15:04:39.666Z" },
    { url = "https://files.pythonhosted.org/packages/af/b9/a419292f05e302dea372fa7e6fda5178a92998411f8581b9830d28fb9edb/watchfiles-1.1.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:aebfd0861a83e6c3d1110b78ad54704486555246e542be3e2bb94195eabb2606", size = 456080, upload-time = "2025-10-14T15:04:40.643Z" },
    { url = "https://files.pythonhosted.org/packages/b0/c3/d5932fd62bde1a30c36e10c409dc5d54506726f08cb3e1d8d0ba5e2bc8db/watchfiles-1.1.1-cp311-cp311-musllinux_1_1_aarch64.whl", hash = "sha256:5fac835b4ab3c6487b5dbad78c4b3724e26bcc468e886f8ba8cc4306f68f6701", size = 629432, upload-time = "2025-10-14T15:04:41.789Z" },
    { url = "https://files.pythonhosted.org/packages/f7/77/16bddd9779fafb795f1a94319dc965209c5641db5bf1edbbccace6d1b3c0/watchfiles-1.1.1-cp311-cp311-musllinux_1_1_x86_64.whl", hash = "sha256:399600947b170270e80134ac854e21b3ccdefa11a9529a3decc1327088180f10", size = 623046, upload-time = "2025-10-14T15:04:42.718Z" },
    { url = "https://files.pythonhosted.org/packages/46/ef/f2ecb9a0f342b4bfad13a2787155c6ee7ce792140eac63a34676a2feeef2/watchfiles-1.1.1-cp311-cp311-win32.whl", hash = "sha256:de6da501c883f58ad50db3a32ad397b09ad29865b5f26f64c24d3e3281685849", size = 271473, upload-time = "2025-10-14T15:04:43.624Z" },
    { url = "https://files.pythonhosted.org/packages/94/bc/f42d71125f19731ea435c3948cad148d31a64fccde3867e5ba4edee901f9/watchfiles-1.1.1-cp311-cp311-win_amd64.whl", hash = "sha256:35c53bd62a0b885bf653ebf6b700d1bf05debb78ad9292cf2a942b23513dc4c4", size = 287598, upload-time = "2025-10-14T15:04:44.516Z" },
    { url = "https://files.pythonhosted.org/packages/57/c9/a30f897351f95bbbfb6abcadafbaca711ce1162f4db95fc908c98a9165f3/watchfiles-1.1.1-cp311-cp311-win_arm64.whl", hash = "sha256:57ca5281a8b5e27593cb7d82c2ac927ad88a96ed406aa446f6344e4328208e9e", size = 277210, upload-time = "2025-10-14T15:04:45.883Z" },
    { url = "https://files.pythonhosted.org/packages/74/d5/f039e7e3c639d9b1d09b07ea412a6806d38123f0508e5f9b48a87b0a76cc/watchfiles-1.1.1-cp312-cp312-macosx_10_12_x86_64.whl", hash = "sha256:8c89f9f2f740a6b7dcc753140dd5e1ab9215966f7a3530d0c0705c83b401bd7d", size = 404745, upload-time = "2025-10-14T15:04:46.731Z" },
    { url = "https://files.pythonhosted.org/packages/a5/96/a881a13aa1349827490dab2d363c8039527060cfcc2c92cc6d13d1b1049e/watchfiles-1.1.1-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:bd404be08018c37350f0d6e34676bd1e2889990117a2b90070b3007f172d0610", size = 391769, upload-time = "2025-10-14T15:04:48.003Z" },
    { url = "https://files.pythonhosted.org/packages/4b/5b/d3b460364aeb8da471c1989238ea0e56bec24b6042a68046adf3d9ddb01c/watchfiles-1.1.1-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:8526e8f916bb5b9a0a777c8317c23ce65de259422bba5b31325a6fa6029d33af", size = 449374, upload-time = "2025-10-14T15:04:49.179Z" },
    { url = "https://files.pythonhosted.org/packages/b9/44/5769cb62d4ed055cb17417c0a109a92f007114a4e07f30812a73a4efdb11/watchfiles-1.1.1-cp312-cp312-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:2edc3553362b1c38d9f06242416a5d8e9fe235c204a4072e988ce2e5bb1f69f6", size = 459485, upload-time = "2025-10-14T15:04:50.155Z" },
    { url = "https://files.pythonhosted.org/packages/19/0c/286b6301ded2eccd4ffd0041a1b726afda999926cf720aab63adb68a1e36/watchfiles-1.1.1-cp312-cp312-manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:30f7da3fb3f2844259cba4720c3fc7138eb0f7b659c38f3bfa65084c7fc7abce", size = 488813, upload-time = "2025-10-14T15:04:51.059Z" },
    { url = "https://files.pythonhosted.org/packages/c7/2b/8530ed41112dd4a22f4dcfdb5ccf6a1baad1ff6eed8dc5a5f09e7e8c41c7/watchfiles-1.1.1-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:f8979280bdafff686ba5e4d8f97840f929a87ed9cdf133cbbd42f7766774d2aa", size = 594816, upload-time = "2025-10-14T15:04:52.031Z" },
    { url = "https://files.pythonhosted.org/packages/ce/d2/f5f9fb49489f184f18470d4f99f4e862a4b3e9ac2865688eb2099e3d837a/watchfiles-1.1.1-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:dcc5c24523771db3a294c77d94771abcfcb82a0e0ee8efd910c37c59ec1b31bb", size = 475186, upload-time = "2025-10-14T15:04:53.064Z" },
    { url = "https://files.pythonhosted.org/packages/cf/68/5707da262a119fb06fbe214d82dd1fe4a6f4af32d2d14de368d0349eb52a/watchfiles-1.1.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:1db5d7ae38ff20153d542460752ff397fcf5c96090c1230803713cf3147a6803", size = 456812, upload-time = "2025-10-14T15:04:55.174Z" },
    { url = "https://files.pythonhosted.org/packages/66/ab/3cbb8756323e8f9b6f9acb9ef4ec26d42b2109bce830cc1f3468df20511d/watchfiles-1.1.1-cp312-cp312-musllinux_1_1_aarch64.whl", hash = "sha256:28475ddbde92df1874b6c5c8aaeb24ad5be47a11f87cde5a28ef3835932e3e94", size = 630196, upload-time = "2025-10-14T15:04:56.22Z" },
    { url = "https://files.pythonhosted.org/packages/78/46/7152ec29b8335f80167928944a94955015a345440f524d2dfe63fc2f437b/watchfiles-1.1.1-cp312-cp312-musllinux_1_1_x86_64.whl", hash = "sha256:36193ed342f5b9842edd3532729a2ad55c4160ffcfa3700e0d54be496b70dd43", size = 622657, upload-time = "2025-10-14T15:04:57.521Z" },
    { url = "https://files.pythonhosted.org/packages/0a/bf/95895e78dd75efe9a7f31733607f384b42eb5feb54bd2eb6ed57cc2e94f4/watchfiles-1.1.1-cp312-cp312-win32.whl", hash = "sha256:859e43a1951717cc8de7f4c77674a6d389b106361585951d9e69572823f311d9", size = 272042, upload-time = "2025-10-14T15:04:59.046Z" },
    { url = "https://files.pythonhosted.org/packages/87/0a/90eb755f568de2688cb220171c4191df932232c20946966c27a59c400850/watchfiles-1.1.1-cp312-cp312-win_amd64.whl", hash = "sha256:91d4c9a823a8c987cce8fa2690923b069966dabb196dd8d137ea2cede885fde9", size = 288410, upload-time = "2025-10-14T15:05:00.081Z" },
    { url = "https://files.pythonhosted.org/packages/36/76/f322701530586922fbd6723c4f91ace21364924822a8772c549483abed13/watchfiles-1.1.1-cp312-cp312-win_arm64.whl", hash = "sha256:a625815d4a2bdca61953dbba5a39d60164451ef34c88d751f6c368c3ea73d404", size = 278209, upload-time = "2025-10-14T15:05:01.168Z" },
    { url = "https://files.pythonhosted.org/packages/bb/f4/f750b29225fe77139f7ae5de89d4949f5a99f934c65a1f1c0b248f26f747/watchfiles-1.1.1-cp313-cp313-macosx_10_12_x86_64.whl", hash = "sha256:130e4876309e8686a5e37dba7d5e9bc77e6ed908266996ca26572437a5271e18", size = 404321, upload-time = "2025-10-14T15:05:02.063Z" },
    { url = "https://files.pythonhosted.org/packages/2b/f9/f07a295cde762644aa4c4bb0f88921d2d141af45e735b965fb2e87858328/watchfiles-1.1.1-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:5f3bde70f157f84ece3765b42b4a52c6ac1a50334903c6eaf765362f6ccca88a", size = 391783, upload-time = "2025-10-14T15:05:03.052Z" },
    { url = "https://files.pythonhosted.org/packages/bc/11/fc2502457e0bea39a5c958d86d2cb69e407a4d00b85735ca724bfa6e0d1a/watchfiles-1.1.1-cp313-cp313-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:14e0b1fe858430fc0251737ef3824c54027bedb8c37c38114488b8e131cf8219", size = 449279, upload-time = "2025-10-14T15:05:04.004Z" },
    { url = "https://files.pythonhosted.org/packages/e3/1f/d66bc15ea0b728df3ed96a539c777acfcad0eb78555ad9efcaa1274688f0/watchfiles-1.1.1-cp313-cp313-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:f27db948078f3823a6bb3b465180db8ebecf26dd5dae6f6180bd87383b6b4428", size = 459405, upload-time = "2025-10-14T15:05:04.942Z" },
    { url = "https://files.pythonhosted.org/packages/be/90/9f4a65c0aec3ccf032703e6db02d89a157462fbb2cf20dd415128251cac0/watchfiles-1.1.1-cp313-cp313-manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:059098c3a429f62fc98e8ec62b982230ef2c8df68c79e826e37b895bc359a9c0", size = 488976, upload-time = "2025-10-14T15:05:05.905Z" },
    { url = "https://files.pythonhosted.org/packages/37/57/ee347af605d867f712be7029bb94c8c071732a4b44792e3176fa3c612d39/watchfiles-1.1.1-cp313-cp313-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:bfb5862016acc9b869bb57284e6cb35fdf8e22fe59f7548858e2f971d045f150", size = 595506, upload-time = "2025-10-14T15:05:06.906Z" },
    { url = "https://files.pythonhosted.org/packages/a8/78/cc5ab0b86c122047f75e8fc471c67a04dee395daf847d3e59381996c8707/watchfiles-1.1.1-cp313-cp313-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:319b27255aacd9923b8a276bb14d21a5f7ff82564c744235fc5eae58d95422ae", size = 474936, upload-time = "2025-10-14T15:05:07.906Z" },
    { url = "https://files.pythonhosted.org/packages/62/da/def65b170a3815af7bd40a3e7010bf6ab53089ef1b75d05dd5385b87cf08/watchfiles-1.1.1-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:c755367e51db90e75b19454b680903631d41f9e3607fbd941d296a020c2d752d", size = 456147, upload-time = "2025-10-14T15:05:09.138Z" },
    { url = "https://files.pythonhosted.org/packages/57/99/da6573ba71166e82d288d4df0839128004c67d2778d3b566c138695f5c0b/watchfiles-1.1.1-cp313-cp313-musllinux_1_1_aarch64.whl", hash = "sha256:c22c776292a23bfc7237a98f791b9ad3144b02116ff10d820829ce62dff46d0b", size = 630007, upload-time = "2025-10-14T15:05:10.117Z" },
    { url = "https://files.pythonhosted.org/packages/a8/51/7439c4dd39511368849eb1e53279cd3454b4a4dbace80bab88feeb83c6b5/watchfiles-1.1.1-cp313-cp313-musllinux_1_1_x86_64.whl", hash = "sha256:3a476189be23c3686bc2f4321dd501cb329c0a0469e77b7b534ee10129ae6374", size = 622280, upload-time = "2025-10-14T15:05:11.146Z" },
    { url = "https://files.pythonhosted.org/packages/95/9c/8ed97d4bba5db6fdcdb2b298d3898f2dd5c20f6b73aee04eabe56c59677e/watchfiles-1.1.1-cp313-cp313-win32.whl", hash = "sha256:bf0a91bfb5574a2f7fc223cf95eeea79abfefa404bf1ea5e339c0c1560ae99a0", size = 272056, upload-time = "2025-10-14T15:05:12.156Z" },
    { url = "https://files.pythonhosted.org/packages/1f/f3/c14e28429f744a260d8ceae18bf58c1d5fa56b50d006a7a9f80e1882cb0d/watchfiles-1.1.1-cp313-cp313-win_amd64.whl", hash = "sha256:52e06553899e11e8074503c8e716d574adeeb7e68913115c4b3653c53f9bae42", size = 288162, upload-time = "2025-10-14T15:05:13.208Z" },
    { url = "https://files.pythonhosted.org/packages/dc/61/fe0e56c40d5cd29523e398d31153218718c5786b5e636d9ae8ae79453d27/watchfiles-1.1.1-cp313-cp313-win_arm64.whl", hash = "sha256:ac3cc5759570cd02662b15fbcd9d917f7ecd47efe0d6b40474eafd246f91ea18", size = 277909, upload-time = "2025-10-14T15:05:14.49Z" },
    { url = "https://files.pythonhosted.org/packages/79/42/e0a7d749626f1e28c7108a99fb9bf524b501bbbeb9b261ceecde644d5a07/watchfiles-1.1.1-cp313-cp313t-macosx_10_12_x86_64.whl", hash = "sha256:563b116874a9a7ce6f96f87cd0b94f7faf92d08d0021e837796f0a14318ef8da", size = 403389, upload-time = "2025-10-14T15:05:15.777Z" },
    { url = "https://files.pythonhosted.org/packages/15/49/08732f90ce0fbbc13913f9f215c689cfc9ced345fb1bcd8829a50007cc8d/watchfiles-1.1.1-cp313-cp313t-macosx_11_0_arm64.whl", hash = "sha256:3ad9fe1dae4ab4212d8c91e80b832425e24f421703b5a42ef2e4a1e215aff051", size = 389964, upload-time = "2025-10-14T15:05:16.85Z" },
    { url = "https://files.pythonhosted.org/packages/27/0d/7c315d4bd5f2538910491a0393c56bf70d333d51bc5b34bee8e68e8cea19/watchfiles-1.1.1-cp313-cp313t-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:ce70f96a46b894b36eba678f153f052967a0d06d5b5a19b336ab0dbbd029f73e", size = 448114, upload-time = "2025-10-14T15:05:17.876Z" },
    { url = "https://files.pythonhosted.org/packages/c3/24/9e096de47a4d11bc4df41e9d1e61776393eac4cb6eb11b3e23315b78b2cc/watchfiles-1.1.1-cp313-cp313t-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:cb467c999c2eff23a6417e58d75e5828716f42ed8289fe6b77a7e5a91036ca70", size = 460264, upload-time = "2025-10-14T15:05:18.962Z" },
    { url = "https://files.pythonhosted.org/packages/cc/0f/e8dea6375f1d3ba5fcb0b3583e2b493e77379834c74fd5a22d66d85d6540/watchfiles-1.1.1-cp313-cp313t-manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:836398932192dae4146c8f6f737d74baeac8b70ce14831a239bdb1ca882fc261", size = 487877, upload-time = "2025-10-14T15:05:20.094Z" },
    { url = "https://files.pythonhosted.org/packages/ac/5b/df24cfc6424a12deb41503b64d42fbea6b8cb357ec62ca84a5a3476f654a/watchfiles-1.1.1-cp313-cp313t-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:743185e7372b7bc7c389e1badcc606931a827112fbbd37f14c537320fca08620", size = 595176, upload-time = "2025-10-14T15:05:21.134Z" },
    { url = "https://files.pythonhosted.org/packages/8f/b5/853b6757f7347de4e9b37e8cc3289283fb983cba1ab4d2d7144694871d9c/watchfiles-1.1.1-cp313-cp313t-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:afaeff7696e0ad9f02cbb8f56365ff4686ab205fcf9c4c5b6fdfaaa16549dd04", size = 473577, upload-time = "2025-10-14T15:05:22.306Z" },
    { url = "https://files.pythonhosted.org/packages/e1/f7/0a4467be0a56e80447c8529c9fce5b38eab4f513cb3d9bf82e7392a5696b/watchfiles-1.1.1-cp313-cp313t-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:3f7eb7da0eb23aa2ba036d4f616d46906013a68caf61b7fdbe42fc8b25132e77", size = 455425, upload-time = "2025-10-14T15:05:23.348Z" },
    { url = "https://files.pythonhosted.org/packages/8e/e0/82583485ea00137ddf69bc84a2db88bd92ab4a6e3c405e5fb878ead8d0e7/watchfiles-1.1.1-cp313-cp313t-musllinux_1_1_aarch64.whl", hash = "sha256:831a62658609f0e5c64178211c942ace999517f5770fe9436be4c2faeba0c0ef", size = 628826, upload-time = "2025-10-14T15:05:24.398Z" },
    { url = "https://files.pythonhosted.org/packages/28/9a/a785356fccf9fae84c0cc90570f11702ae9571036fb25932f1242c82191c/watchfiles-1.1.1-cp313-cp313t-musllinux_1_1_x86_64.whl", hash = "sha256:f9a2ae5c91cecc9edd47e041a930490c31c3afb1f5e6d71de3dc671bfaca02bf", size = 622208, upload-time = "2025-10-14T15:05:25.45Z" },
    { url = "https://files.pythonhosted.org/packages/c3/f4/0872229324ef69b2c3edec35e84bd57a1289e7d3fe74588048ed8947a323/watchfiles-1.1.1-cp314-cp314-macosx_10_12_x86_64.whl", hash = "sha256:d1715143123baeeaeadec0528bb7441103979a1d5f6fd0e1f915383fea7ea6d5", size = 404315, upload-time = "2025-10-14T15:05:26.501Z" },
    { url = "https://files.pythonhosted.org/packages/7b/22/16d5331eaed1cb107b873f6ae1b69e9ced582fcf0c59a50cd84f403b1c32/watchfiles-1.1.1-cp314-cp314-macosx_11_0_arm64.whl", hash = "sha256:39574d6370c4579d7f5d0ad940ce5b20db0e4117444e39b6d8f99db5676c52fd", size = 390869, upload-time = "2025-10-14T15:05:27.649Z" },
    { url = "https://files.pythonhosted.org/packages/b2/7e/5643bfff5acb6539b18483128fdc0ef2cccc94a5b8fbda130c823e8ed636/watchfiles-1.1.1-cp314-cp314-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:7365b92c2e69ee952902e8f70f3ba6360d0d596d9299d55d7d386df84b6941fb", size = 449919, upload-time = "2025-10-14T15:05:28.701Z" },
    { url = "https://files.pythonhosted.org/packages/51/2e/c410993ba5025a9f9357c376f48976ef0e1b1aefb73b97a5ae01a5972755/watchfiles-1.1.1-cp314-cp314-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:bfff9740c69c0e4ed32416f013f3c45e2ae42ccedd1167ef2d805c000b6c71a5", size = 460845, upload-time = "2025-10-14T15:05:30.064Z" },
    { url = "https://files.pythonhosted.org/packages/8e/a4/2df3b404469122e8680f0fcd06079317e48db58a2da2950fb45020947734/watchfiles-1.1.1-cp314-cp314-manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:b27cf2eb1dda37b2089e3907d8ea92922b673c0c427886d4edc6b94d8dfe5db3", size = 489027, upload-time = "2025-10-14T15:05:31.064Z" },
    { url = "https://files.pythonhosted.org/packages/ea/84/4587ba5b1f267167ee715b7f66e6382cca6938e0a4b870adad93e44747e6/watchfiles-1.1.1-cp314-cp314-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:526e86aced14a65a5b0ec50827c745597c782ff46b571dbfe46192ab9e0b3c33", size = 595615, upload-time = "2025-10-14T15:05:32.074Z" },
    { url = "https://files.pythonhosted.org/packages/6a/0f/c6988c91d06e93cd0bb3d4a808bcf32375ca1904609835c3031799e3ecae/watchfiles-1.1.1-cp314-cp314-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:04e78dd0b6352db95507fd8cb46f39d185cf8c74e4cf1e4fbad1d3df96faf510", size = 474836, upload-time = "2025-10-14T15:05:33.209Z" },
    { url = "https://files.pythonhosted.org/packages/b4/36/ded8aebea91919485b7bbabbd14f5f359326cb5ec218cd67074d1e426d74/watchfiles-1.1.1-cp314-cp314-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:5c85794a4cfa094714fb9c08d4a218375b2b95b8ed1666e8677c349906246c05", size = 455099, upload-time = "2025-10-14T15:05:34.189Z" },
    { url = "https://files.pythonhosted.org/packages/98/e0/8c9bdba88af756a2fce230dd365fab2baf927ba42cd47521ee7498fd5211/watchfiles-1.1.1-cp314-cp314-musllinux_1_1_aarch64.whl", hash = "sha256:74d5012b7630714b66be7b7b7a78855ef7ad58e8650c73afc4c076a1f480a8d6", size = 630626, upload-time = "2025-10-14T15:05:35.216Z" },
    { url = "https://files.pythonhosted.org/packages/2a/84/a95db05354bf2d19e438520d92a8ca475e578c647f78f53197f5a2f17aaf/watchfiles-1.1.1-cp314-cp314-musllinux_1_1_x86_64.whl", hash = "sha256:8fbe85cb3201c7d380d3d0b90e63d520f15d6afe217165d7f98c9c649654db81", size = 622519, upload-time = "2025-10-14T15:05:36.259Z" },
    { url = "https://files.pythonhosted.org/packages/1d/ce/d8acdc8de545de995c339be67711e474c77d643555a9bb74a9334252bd55/watchfiles-1.1.1-cp314-cp314-win32.whl", hash = "sha256:3fa0b59c92278b5a7800d3ee7733da9d096d4aabcfabb9a928918bd276ef9b9b", size = 272078, upload-time = "2025-10-14T15:05:37.63Z" },
    { url = "https://files.pythonhosted.org/packages/c4/c9/a74487f72d0451524be827e8edec251da0cc1fcf111646a511ae752e1a3d/watchfiles-1.1.1-cp314-cp314-win_amd64.whl", hash = "sha256:c2047d0b6cea13b3316bdbafbfa0c4228ae593d995030fda39089d36e64fc03a", size = 287664, upload-time = "2025-10-14T15:05:38.95Z" },
    { url = "https://files.pythonhosted.org/packages/df/b8/8ac000702cdd496cdce998c6f4ee0ca1f15977bba51bdf07d872ebdfc34c/watchfiles-1.1.1-cp314-cp314-win_arm64.whl", hash = "sha256:842178b126593addc05acf6fce960d28bc5fae7afbaa2c6c1b3a7b9460e5be02", size = 277154, upload-time = "2025-10-14T15:05:39.954Z" },
    { url = "https://files.pythonhosted.org/packages/47/a8/e3af2184707c29f0f14b1963c0aace6529f9d1b8582d5b99f31bbf42f59e/watchfiles-1.1.1-cp314-cp314t-macosx_10_12_x86_64.whl", hash = "sha256:88863fbbc1a7312972f1c511f202eb30866370ebb8493aef2812b9ff28156a21", size = 403820, upload-time = "2025-10-14T15:05:40.932Z" },
    { url = "https://files.pythonhosted.org/packages/c0/ec/e47e307c2f4bd75f9f9e8afbe3876679b18e1bcec449beca132a1c5ffb2d/watchfiles-1.1.1-cp314-cp314t-macosx_11_0_arm64.whl", hash = "sha256:55c7475190662e202c08c6c0f4d9e345a29367438cf8e8037f3155e10a88d5a5", size = 390510, upload-time = "2025-10-14T15:05:41.945Z" },
    { url = "https://files.pythonhosted.org/packages/d5/a0/ad235642118090f66e7b2f18fd5c42082418404a79205cdfca50b6309c13/watchfiles-1.1.1-cp314-cp314t-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:3f53fa183d53a1d7a8852277c92b967ae99c2d4dcee2bfacff8868e6e30b15f7", size = 448408, upload-time = "2025-10-14T15:05:43.385Z" },
    { url = "https://files.pythonhosted.org/packages/df/85/97fa10fd5ff3332ae17e7e40e20784e419e28521549780869f1413742e9d/watchfiles-1.1.1-cp314-cp314t-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:6aae418a8b323732fa89721d86f39ec8f092fc2af67f4217a2b07fd3e93c6101", size = 458968, upload-time = "2025-10-14T15:05:44.404Z" },
    { url = "https://files.pythonhosted.org/packages/47/c2/9059c2e8966ea5ce678166617a7f75ecba6164375f3b288e50a40dc6d489/watchfiles-1.1.1-cp314-cp314t-manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:f096076119da54a6080e8920cbdaac3dbee667eb91dcc5e5b78840b87415bd44", size = 488096, upload-time = "2025-10-14T15:05:45.398Z" },
    { url = "https://files.pythonhosted.org/packages/94/44/d90a9ec8ac309bc26db808a13e7bfc0e4e78b6fc051078a554e132e80160/watchfiles-1.1.1-cp314-cp314t-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:00485f441d183717038ed2e887a7c868154f216877653121068107b227a2f64c", size = 596040, upload-time = "2025-10-14T15:05:46.502Z" },
    { url = "https://files.pythonhosted.org/packages/95/68/4e3479b20ca305cfc561db3ed207a8a1c745ee32bf24f2026a129d0ddb6e/watchfiles-1.1.1-cp314-cp314t-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:a55f3e9e493158d7bfdb60a1165035f1cf7d320914e7b7ea83fe22c6023b58fc", size = 473847, upload-time = "2025-10-14T15:05:47.484Z" },
    { url = "https://files.pythonhosted.org/packages/4f/55/2af26693fd15165c4ff7857e38330e1b61ab8c37d15dc79118cdba115b7a/watchfiles-1.1.1-cp314-cp314t-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:8c91ed27800188c2ae96d16e3149f199d62f86c7af5f5f4d2c61a3ed8cd3666c", size = 455072, upload-time = "2025-10-14T15:05:48.928Z" },
    { url = "https://files.pythonhosted.org/packages/66/1d/d0d200b10c9311ec25d2273f8aad8c3ef7cc7ea11808022501811208a750/watchfiles-1.1.1-cp314-cp314t-musllinux_1_1_aarch64.whl", hash = "sha256:311ff15a0bae3714ffb603e6ba6dbfba4065ab60865d15a6ec544133bdb21099", size = 629104, upload-time = "2025-10-14T15:05:49.908Z" },
    { url = "https://files.pythonhosted.org/packages/e3/bd/fa9bb053192491b3867ba07d2343d9f2252e00811567d30ae8d0f78136fe/watchfiles-1.1.1-cp314-cp314t-musllinux_1_1_x86_64.whl", hash = "sha256:a916a2932da8f8ab582f242c065f5c81bed3462849ca79ee357dd9551b0e9b01", size = 622112, upload-time = "2025-10-14T15:05:50.941Z" },
    { url = "https://files.pythonhosted.org/packages/ba/4c/a888c91e2e326872fa4705095d64acd8aa2fb9c1f7b9bd0588f33850516c/watchfiles-1.1.1-pp310-pypy310_pp73-macosx_10_12_x86_64.whl", hash = "sha256:17ef139237dfced9da49fb7f2232c86ca9421f666d78c264c7ffca6601d154c3", size = 409611, upload-time = "2025-10-14T15:06:05.809Z" },
    { url = "https://files.pythonhosted.org/packages/1e/c7/5420d1943c8e3ce1a21c0a9330bcf7edafb6aa65d26b21dbb3267c9e8112/watchfiles-1.1.1-pp310-pypy310_pp73-macosx_11_0_arm64.whl", hash = "sha256:672b8adf25b1a0d35c96b5888b7b18699d27d4194bac8beeae75be4b7a3fc9b2", size = 396889, upload-time = "2025-10-14T15:06:07.035Z" },
    { url = "https://files.pythonhosted.org/packages/0c/e5/0072cef3804ce8d3aaddbfe7788aadff6b3d3f98a286fdbee9fd74ca59a7/watchfiles-1.1.1-pp310-pypy310_pp73-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:77a13aea58bc2b90173bc69f2a90de8e282648939a00a602e1dc4ee23e26b66d", size = 451616, upload-time = "2025-10-14T15:06:08.072Z" },
    { url = "https://files.pythonhosted.org/packages/83/4e/b87b71cbdfad81ad7e83358b3e447fedd281b880a03d64a760fe0a11fc2e/watchfiles-1.1.1-pp310-pypy310_pp73-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:0b495de0bb386df6a12b18335a0285dda90260f51bdb505503c02bcd1ce27a8b", size = 458413, upload-time = "2025-10-14T15:06:09.209Z" },
    { url = "https://files.pythonhosted.org/packages/d3/8e/e500f8b0b77be4ff753ac94dc06b33d8f0d839377fee1b78e8c8d8f031bf/watchfiles-1.1.1-pp311-pypy311_pp73-macosx_10_12_x86_64.whl", hash = "sha256:db476ab59b6765134de1d4fe96a1a9c96ddf091683599be0f26147ea1b2e4b88", size = 408250, upload-time = "2025-10-14T15:06:10.264Z" },
    { url = "https://files.pythonhosted.org/packages/bd/95/615e72cd27b85b61eec764a5ca51bd94d40b5adea5ff47567d9ebc4d275a/watchfiles-1.1.1-pp311-pypy311_pp73-macosx_11_0_arm64.whl", hash = "sha256:89eef07eee5e9d1fda06e38822ad167a044153457e6fd997f8a858ab7564a336", size = 396117, upload-time = "2025-10-14T15:06:11.28Z" },
    { url = "https://files.pythonhosted.org/packages/c9/81/e7fe958ce8a7fb5c73cc9fb07f5aeaf755e6aa72498c57d760af760c91f8/watchfiles-1.1.1-pp311-pypy311_pp73-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:ce19e06cbda693e9e7686358af9cd6f5d61312ab8b00488bc36f5aabbaf77e24", size = 450493, upload-time = "2025-10-14T15:06:12.321Z" },
    { url = "https://files.pythonhosted.org/packages/6e/d4/ed38dd3b1767193de971e694aa544356e63353c33a85d948166b5ff58b9e/watchfiles-1.1.1-pp311-pypy311_pp73-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:3e6f39af2eab0118338902798b5aa6664f46ff66bc0280de76fca67a7f262a49", size = 457546, upload-time = "2025-10-14T15:06:13.372Z" },
]

[[package]]
name = "websockets"
version = "15.0.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/21/e6/26d09fab466b7ca9c7737474c52be4f76a40301b08362eb2dbc19dcc16c1/websockets-15.0.1.tar.gz", hash = "sha256:82544de02076bafba038ce055ee6412d68da13ab47f0c60cab827346de828dee", size = 177016, upload-time = "2025-03-05T20:03:41.606Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/1e/da/6462a9f510c0c49837bbc9345aca92d767a56c1fb2939e1579df1e1cdcf7/websockets-15.0.1-cp310-cp310-macosx_10_9_universal2.whl", hash = "sha256:d63efaa0cd96cf0c5fe4d581521d9fa87744540d4bc999ae6e08595a1014b45b", size = 175423, upload-time = "2025-03-05T20:01:35.363Z" },
    { url = "https://files.pythonhosted.org/packages/1c/9f/9d11c1a4eb046a9e106483b9ff69bce7ac880443f00e5ce64261b47b07e7/websockets-15.0.1-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:ac60e3b188ec7574cb761b08d50fcedf9d77f1530352db4eef1707fe9dee7205", size = 173080, upload-time = "2025-03-05T20:01:37.304Z" },
    { url = "https://files.pythonhosted.org/packages/d5/4f/b462242432d93ea45f297b6179c7333dd0402b855a912a04e7fc61c0d71f/websockets-15.0.1-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:5756779642579d902eed757b21b0164cd6fe338506a8083eb58af5c372e39d9a", size = 173329, upload-time = "2025-03-05T20:01:39.668Z" },
    { url = "https://files.pythonhosted.org/packages/6e/0c/6afa1f4644d7ed50284ac59cc70ef8abd44ccf7d45850d989ea7310538d0/websockets-15.0.1-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:0fdfe3e2a29e4db3659dbd5bbf04560cea53dd9610273917799f1cde46aa725e", size = 182312, upload-time = "2025-03-05T20:01:41.815Z" },
    { url = "https://files.pythonhosted.org/packages/dd/d4/ffc8bd1350b229ca7a4db2a3e1c482cf87cea1baccd0ef3e72bc720caeec/websockets-15.0.1-cp310-cp310-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:4c2529b320eb9e35af0fa3016c187dffb84a3ecc572bcee7c3ce302bfeba52bf", size = 181319, upload-time = "2025-03-05T20:01:43.967Z" },
    { url = "https://files.pythonhosted.org/packages/97/3a/5323a6bb94917af13bbb34009fac01e55c51dfde354f63692bf2533ffbc2/websockets-15.0.1-cp310-cp310-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:ac1e5c9054fe23226fb11e05a6e630837f074174c4c2f0fe442996112a6de4fb", size = 181631, upload-time = "2025-03-05T20:01:46.104Z" },
    { url = "https://files.pythonhosted.org/packages/a6/cc/1aeb0f7cee59ef065724041bb7ed667b6ab1eeffe5141696cccec2687b66/websockets-15.0.1-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:5df592cd503496351d6dc14f7cdad49f268d8e618f80dce0cd5a36b93c3fc08d", size = 182016, upload-time = "2025-03-05T20:01:47.603Z" },
    { url = "https://files.pythonhosted.org/packages/79/f9/c86f8f7af208e4161a7f7e02774e9d0a81c632ae76db2ff22549e1718a51/websockets-15.0.1-cp310-cp310-musllinux_1_2_i686.whl", hash = "sha256:0a34631031a8f05657e8e90903e656959234f3a04552259458aac0b0f9ae6fd9", size = 181426, upload-time = "2025-03-05T20:01:48.949Z" },
    { url = "https://files.pythonhosted.org/packages/c7/b9/828b0bc6753db905b91df6ae477c0b14a141090df64fb17f8a9d7e3516cf/websockets-15.0.1-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:3d00075aa65772e7ce9e990cab3ff1de702aa09be3940d1dc88d5abf1ab8a09c", size = 181360, upload-time = "2025-03-05T20:01:50.938Z" },
    { url = "https://files.pythonhosted.org/packages/89/fb/250f5533ec468ba6327055b7d98b9df056fb1ce623b8b6aaafb30b55d02e/websockets-15.0.1-cp310-cp310-win32.whl", hash = "sha256:1234d4ef35db82f5446dca8e35a7da7964d02c127b095e172e54397fb6a6c256", size = 176388, upload-time = "2025-03-05T20:01:52.213Z" },
    { url = "https://files.pythonhosted.org/packages/1c/46/aca7082012768bb98e5608f01658ff3ac8437e563eca41cf068bd5849a5e/websockets-15.0.1-cp310-cp310-win_amd64.whl", hash = "sha256:39c1fec2c11dc8d89bba6b2bf1556af381611a173ac2b511cf7231622058af41", size = 176830, upload-time = "2025-03-05T20:01:53.922Z" },
    { url = "https://files.pythonhosted.org/packages/9f/32/18fcd5919c293a398db67443acd33fde142f283853076049824fc58e6f75/websockets-15.0.1-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:823c248b690b2fd9303ba00c4f66cd5e2d8c3ba4aa968b2779be9532a4dad431", size = 175423, upload-time = "2025-03-05T20:01:56.276Z" },
    { url = "https://files.pythonhosted.org/packages/76/70/ba1ad96b07869275ef42e2ce21f07a5b0148936688c2baf7e4a1f60d5058/websockets-15.0.1-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:678999709e68425ae2593acf2e3ebcbcf2e69885a5ee78f9eb80e6e371f1bf57", size = 173082, upload-time = "2025-03-05T20:01:57.563Z" },
    { url = "https://files.pythonhosted.org/packages/86/f2/10b55821dd40eb696ce4704a87d57774696f9451108cff0d2824c97e0f97/websockets-15.0.1-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:d50fd1ee42388dcfb2b3676132c78116490976f1300da28eb629272d5d93e905", size = 173330, upload-time = "2025-03-05T20:01:59.063Z" },
    { url = "https://files.pythonhosted.org/packages/a5/90/1c37ae8b8a113d3daf1065222b6af61cc44102da95388ac0018fcb7d93d9/websockets-15.0.1-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:d99e5546bf73dbad5bf3547174cd6cb8ba7273062a23808ffea025ecb1cf8562", size = 182878, upload-time = "2025-03-05T20:02:00.305Z" },
    { url = "https://files.pythonhosted.org/packages/8e/8d/96e8e288b2a41dffafb78e8904ea7367ee4f891dafc2ab8d87e2124cb3d3/websockets-15.0.1-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:66dd88c918e3287efc22409d426c8f729688d89a0c587c88971a0faa2c2f3792", size = 181883, upload-time = "2025-03-05T20:02:03.148Z" },
    { url = "https://files.pythonhosted.org/packages/93/1f/5d6dbf551766308f6f50f8baf8e9860be6182911e8106da7a7f73785f4c4/websockets-15.0.1-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:8dd8327c795b3e3f219760fa603dcae1dcc148172290a8ab15158cf85a953413", size = 182252, upload-time = "2025-03-05T20:02:05.29Z" },
    { url = "https://files.pythonhosted.org/packages/d4/78/2d4fed9123e6620cbf1706c0de8a1632e1a28e7774d94346d7de1bba2ca3/websockets-15.0.1-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:8fdc51055e6ff4adeb88d58a11042ec9a5eae317a0a53d12c062c8a8865909e8", size = 182521, upload-time = "2025-03-05T20:02:07.458Z" },
    { url = "https://files.pythonhosted.org/packages/e7/3b/66d4c1b444dd1a9823c4a81f50231b921bab54eee2f69e70319b4e21f1ca/websockets-15.0.1-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:693f0192126df6c2327cce3baa7c06f2a117575e32ab2308f7f8216c29d9e2e3", size = 181958, upload-time = "2025-03-05T20:02:09.842Z" },
    { url = "https://files.pythonhosted.org/packages/08/ff/e9eed2ee5fed6f76fdd6032ca5cd38c57ca9661430bb3d5fb2872dc8703c/websockets-15.0.1-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:54479983bd5fb469c38f2f5c7e3a24f9a4e70594cd68cd1fa6b9340dadaff7cf", size = 181918, upload-time = "2025-03-05T20:02:11.968Z" },
    { url = "https://files.pythonhosted.org/packages/d8/75/994634a49b7e12532be6a42103597b71098fd25900f7437d6055ed39930a/websockets-15.0.1-cp311-cp311-win32.whl", hash = "sha256:16b6c1b3e57799b9d38427dda63edcbe4926352c47cf88588c0be4ace18dac85", size = 176388, upload-time = "2025-03-05T20:02:13.32Z" },
    { url = "https://files.pythonhosted.org/packages/98/93/e36c73f78400a65f5e236cd376713c34182e6663f6889cd45a4a04d8f203/websockets-15.0.1-cp311-cp311-win_amd64.whl", hash = "sha256:27ccee0071a0e75d22cb35849b1db43f2ecd3e161041ac1ee9d2352ddf72f065", size = 176828, upload-time = "2025-03-05T20:02:14.585Z" },
    { url = "https://files.pythonhosted.org/packages/51/6b/4545a0d843594f5d0771e86463606a3988b5a09ca5123136f8a76580dd63/websockets-15.0.1-cp312-cp312-macosx_10_13_universal2.whl", hash = "sha256:3e90baa811a5d73f3ca0bcbf32064d663ed81318ab225ee4f427ad4e26e5aff3", size = 175437, upload-time = "2025-03-05T20:02:16.706Z" },
    { url = "https://files.pythonhosted.org/packages/f4/71/809a0f5f6a06522af902e0f2ea2757f71ead94610010cf570ab5c98e99ed/websockets-15.0.1-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:592f1a9fe869c778694f0aa806ba0374e97648ab57936f092fd9d87f8bc03665", size = 173096, upload-time = "2025-03-05T20:02:18.832Z" },
    { url = "https://files.pythonhosted.org/packages/3d/69/1a681dd6f02180916f116894181eab8b2e25b31e484c5d0eae637ec01f7c/websockets-15.0.1-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:0701bc3cfcb9164d04a14b149fd74be7347a530ad3bbf15ab2c678a2cd3dd9a2", size = 173332, upload-time = "2025-03-05T20:02:20.187Z" },
    { url = "https://files.pythonhosted.org/packages/a6/02/0073b3952f5bce97eafbb35757f8d0d54812b6174ed8dd952aa08429bcc3/websockets-15.0.1-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:e8b56bdcdb4505c8078cb6c7157d9811a85790f2f2b3632c7d1462ab5783d215", size = 183152, upload-time = "2025-03-05T20:02:22.286Z" },
    { url = "https://files.pythonhosted.org/packages/74/45/c205c8480eafd114b428284840da0b1be9ffd0e4f87338dc95dc6ff961a1/websockets-15.0.1-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:0af68c55afbd5f07986df82831c7bff04846928ea8d1fd7f30052638788bc9b5", size = 182096, upload-time = "2025-03-05T20:02:24.368Z" },
    { url = "https://files.pythonhosted.org/packages/14/8f/aa61f528fba38578ec553c145857a181384c72b98156f858ca5c8e82d9d3/websockets-15.0.1-cp312-cp312-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:64dee438fed052b52e4f98f76c5790513235efaa1ef7f3f2192c392cd7c91b65", size = 182523, upload-time = "2025-03-05T20:02:25.669Z" },
    { url = "https://files.pythonhosted.org/packages/ec/6d/0267396610add5bc0d0d3e77f546d4cd287200804fe02323797de77dbce9/websockets-15.0.1-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:d5f6b181bb38171a8ad1d6aa58a67a6aa9d4b38d0f8c5f496b9e42561dfc62fe", size = 182790, upload-time = "2025-03-05T20:02:26.99Z" },
    { url = "https://files.pythonhosted.org/packages/02/05/c68c5adbf679cf610ae2f74a9b871ae84564462955d991178f95a1ddb7dd/websockets-15.0.1-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:5d54b09eba2bada6011aea5375542a157637b91029687eb4fdb2dab11059c1b4", size = 182165, upload-time = "2025-03-05T20:02:30.291Z" },
    { url = "https://files.pythonhosted.org/packages/29/93/bb672df7b2f5faac89761cb5fa34f5cec45a4026c383a4b5761c6cea5c16/websockets-15.0.1-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:3be571a8b5afed347da347bfcf27ba12b069d9d7f42cb8c7028b5e98bbb12597", size = 182160, upload-time = "2025-03-05T20:02:31.634Z" },
    { url = "https://files.pythonhosted.org/packages/ff/83/de1f7709376dc3ca9b7eeb4b9a07b4526b14876b6d372a4dc62312bebee0/websockets-15.0.1-cp312-cp312-win32.whl", hash = "sha256:c338ffa0520bdb12fbc527265235639fb76e7bc7faafbb93f6ba80d9c06578a9", size = 176395, upload-time = "2025-03-05T20:02:33.017Z" },
    { url = "https://files.pythonhosted.org/packages/7d/71/abf2ebc3bbfa40f391ce1428c7168fb20582d0ff57019b69ea20fa698043/websockets-15.0.1-cp312-cp312-win_amd64.whl", hash = "sha256:fcd5cf9e305d7b8338754470cf69cf81f420459dbae8a3b40cee57417f4614a7", size = 176841, upload-time = "2025-03-05T20:02:34.498Z" },
    { url = "https://files.pythonhosted.org/packages/cb/9f/51f0cf64471a9d2b4d0fc6c534f323b664e7095640c34562f5182e5a7195/websockets-15.0.1-cp313-cp313-macosx_10_13_universal2.whl", hash = "sha256:ee443ef070bb3b6ed74514f5efaa37a252af57c90eb33b956d35c8e9c10a1931", size = 175440, upload-time = "2025-03-05T20:02:36.695Z" },
    { url = "https://files.pythonhosted.org/packages/8a/05/aa116ec9943c718905997412c5989f7ed671bc0188ee2ba89520e8765d7b/websockets-15.0.1-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:5a939de6b7b4e18ca683218320fc67ea886038265fd1ed30173f5ce3f8e85675", size = 173098, upload-time = "2025-03-05T20:02:37.985Z" },
    { url = "https://files.pythonhosted.org/packages/ff/0b/33cef55ff24f2d92924923c99926dcce78e7bd922d649467f0eda8368923/websockets-15.0.1-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:746ee8dba912cd6fc889a8147168991d50ed70447bf18bcda7039f7d2e3d9151", size = 173329, upload-time = "2025-03-05T20:02:39.298Z" },
    { url = "https://files.pythonhosted.org/packages/31/1d/063b25dcc01faa8fada1469bdf769de3768b7044eac9d41f734fd7b6ad6d/websockets-15.0.1-cp313-cp313-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:595b6c3969023ecf9041b2936ac3827e4623bfa3ccf007575f04c5a6aa318c22", size = 183111, upload-time = "2025-03-05T20:02:40.595Z" },
    { url = "https://files.pythonhosted.org/packages/93/53/9a87ee494a51bf63e4ec9241c1ccc4f7c2f45fff85d5bde2ff74fcb68b9e/websockets-15.0.1-cp313-cp313-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:3c714d2fc58b5ca3e285461a4cc0c9a66bd0e24c5da9911e30158286c9b5be7f", size = 182054, upload-time = "2025-03-05T20:02:41.926Z" },
    { url = "https://files.pythonhosted.org/packages/ff/b2/83a6ddf56cdcbad4e3d841fcc55d6ba7d19aeb89c50f24dd7e859ec0805f/websockets-15.0.1-cp313-cp313-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:0f3c1e2ab208db911594ae5b4f79addeb3501604a165019dd221c0bdcabe4db8", size = 182496, upload-time = "2025-03-05T20:02:43.304Z" },
    { url = "https://files.pythonhosted.org/packages/98/41/e7038944ed0abf34c45aa4635ba28136f06052e08fc2168520bb8b25149f/websockets-15.0.1-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:229cf1d3ca6c1804400b0a9790dc66528e08a6a1feec0d5040e8b9eb14422375", size = 182829, upload-time = "2025-03-05T20:02:48.812Z" },
    { url = "https://files.pythonhosted.org/packages/e0/17/de15b6158680c7623c6ef0db361da965ab25d813ae54fcfeae2e5b9ef910/websockets-15.0.1-cp313-cp313-musllinux_1_2_i686.whl", hash = "sha256:756c56e867a90fb00177d530dca4b097dd753cde348448a1012ed6c5131f8b7d", size = 182217, upload-time = "2025-03-05T20:02:50.14Z" },
    { url = "https://files.pythonhosted.org/packages/33/2b/1f168cb6041853eef0362fb9554c3824367c5560cbdaad89ac40f8c2edfc/websockets-15.0.1-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:558d023b3df0bffe50a04e710bc87742de35060580a293c2a984299ed83bc4e4", size = 182195, upload-time = "2025-03-05T20:02:51.561Z" },
    { url = "https://files.pythonhosted.org/packages/86/eb/20b6cdf273913d0ad05a6a14aed4b9a85591c18a987a3d47f20fa13dcc47/websockets-15.0.1-cp313-cp313-win32.whl", hash = "sha256:ba9e56e8ceeeedb2e080147ba85ffcd5cd0711b89576b83784d8605a7df455fa", size = 176393, upload-time = "2025-03-05T20:02:53.814Z" },
    { url = "https://files.pythonhosted.org/packages/1b/6c/c65773d6cab416a64d191d6ee8a8b1c68a09970ea6909d16965d26bfed1e/websockets-15.0.1-cp313-cp313-win_amd64.whl", hash = "sha256:e09473f095a819042ecb2ab9465aee615bd9c2028e4ef7d933600a8401c79561", size = 176837, upload-time = "2025-03-05T20:02:55.237Z" },
    { url = "https://files.pythonhosted.org/packages/02/9e/d40f779fa16f74d3468357197af8d6ad07e7c5a27ea1ca74ceb38986f77a/websockets-15.0.1-pp310-pypy310_pp73-macosx_10_15_x86_64.whl", hash = "sha256:0c9e74d766f2818bb95f84c25be4dea09841ac0f734d1966f415e4edfc4ef1c3", size = 173109, upload-time = "2025-03-05T20:03:17.769Z" },
    { url = "https://files.pythonhosted.org/packages/bc/cd/5b887b8585a593073fd92f7c23ecd3985cd2c3175025a91b0d69b0551372/websockets-15.0.1-pp310-pypy310_pp73-macosx_11_0_arm64.whl", hash = "sha256:1009ee0c7739c08a0cd59de430d6de452a55e42d6b522de7aa15e6f67db0b8e1", size = 173343, upload-time = "2025-03-05T20:03:19.094Z" },
    { url = "https://files.pythonhosted.org/packages/fe/ae/d34f7556890341e900a95acf4886833646306269f899d58ad62f588bf410/websockets-15.0.1-pp310-pypy310_pp73-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:76d1f20b1c7a2fa82367e04982e708723ba0e7b8d43aa643d3dcd404d74f1475", size = 174599, upload-time = "2025-03-05T20:03:21.1Z" },
    { url = "https://files.pythonhosted.org/packages/71/e6/5fd43993a87db364ec60fc1d608273a1a465c0caba69176dd160e197ce42/websockets-15.0.1-pp310-pypy310_pp73-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:f29d80eb9a9263b8d109135351caf568cc3f80b9928bccde535c235de55c22d9", size = 174207, upload-time = "2025-03-05T20:03:23.221Z" },
    { url = "https://files.pythonhosted.org/packages/2b/fb/c492d6daa5ec067c2988ac80c61359ace5c4c674c532985ac5a123436cec/websockets-15.0.1-pp310-pypy310_pp73-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:b359ed09954d7c18bbc1680f380c7301f92c60bf924171629c5db97febb12f04", size = 174155, upload-time = "2025-03-05T20:03:25.321Z" },
    { url = "https://files.pythonhosted.org/packages/68/a1/dcb68430b1d00b698ae7a7e0194433bce4f07ded185f0ee5fb21e2a2e91e/websockets-15.0.1-pp310-pypy310_pp73-win_amd64.whl", hash = "sha256:cad21560da69f4ce7658ca2cb83138fb4cf695a2ba3e475e0559e05991aa8122", size = 176884, upload-time = "2025-03-05T20:03:27.934Z" },
    { url = "https://files.pythonhosted.org/packages/fa/a8/5b41e0da817d64113292ab1f8247140aac61cbf6cfd085d6a0fa77f4984f/websockets-15.0.1-py3-none-any.whl", hash = "sha256:f7a866fbc1e97b5c617ee4116daaa09b722101d4a3c170c787450ba409f9736f", size = 169743, upload-time = "2025-03-05T20:03:39.41Z" },
]

[[package]]
name = "zipp"
version = "3.23.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/e3/02/0f2892c661036d50ede074e376733dca2ae7c6eb617489437771209d4180/zipp-3.23.0.tar.gz", hash = "sha256:a07157588a12518c9d4034df3fbbee09c814741a33ff63c05fa29d26a2404166", size = 25547, upload-time = "2025-06-08T17:06:39.4Z" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/2e/54/647ade08bf0db230bfea292f893923872fd20be6ac6f53b2b936ba839d75/zipp-3.23.0-py3-none-any.whl", hash = "sha256:071652d6115ed432f5ce1d34c336c0adfd6a884660d1e9712a256d3d3bd4b14e", size = 10276, upload-time = "2025-06-08T17:06:38.034Z" },
]
```

---

## File: `.github/core/user_agent_mixin.py`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/.github/core/user_agent_mixin.py`

```python
USER_AGENT = "ALPACA-MCP-SERVER"

class UserAgentMixin:
    def _get_default_headers(self) -> dict:
        headers = self._get_auth_headers()
        headers["User-Agent"] = USER_AGENT
        return headers
```

---

## File: `.github/workflows/ci.yml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/.github/workflows/ci.yml`

```yaml
name: CI
permissions:
  contents: read

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # ── Job 1: Core tests (no secrets, no network) ────────────────────────
  # Runs integrity checks and server construction tests on every PR.
  test-core:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv pip install --system -e ".[dev]"

      - name: Run core tests
        run: pytest tests/test_integrity.py tests/test_server_construction.py

  # ── Job 2: Integration tests (paper API, secrets required) ────────────
  # Runs only on pushes to main and PRs from the same repo (not forks).
  # Fork PRs cannot access secrets, so this job is skipped for them.
  #
  # Required GitHub Secrets (Settings > Secrets and variables > Actions):
  #   ALPACA_API_KEY    — paper trading account API key
  #   ALPACA_SECRET_KEY — paper trading account secret key
  test-integration:
    runs-on: ubuntu-latest
    if: >-
      github.event_name == 'push' ||
      github.event.pull_request.head.repo.full_name == github.repository
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv pip install --system -e ".[dev]"

      - name: Run integration tests
        env:
          ALPACA_API_KEY: ${{ secrets.ALPACA_API_KEY }}
          ALPACA_SECRET_KEY: ${{ secrets.ALPACA_SECRET_KEY }}
          ALPACA_PAPER_TRADE: "true"
        run: pytest tests/ -m integration
```

---

## File: `.github/workflows/stale.yaml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/.github/workflows/stale.yaml`

```yaml
name: 'Close stale issues and PRs'
on:
  schedule:
    - cron: '30 1 * * *'


jobs:
  stale:
    permissions:
      pull-requests: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@v9
        with:
          stale-issue-message: 'This issue is stale because it has been open 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.'
          stale-pr-message: 'This PR is stale because it has been open 14 days with no activity. Remove stale label or comment or this will be closed in 5 days.'
          close-issue-message: 'This issue was closed because it has been stalled for 5 days with no activity.'
          close-pr-message: 'This PR was closed because it has been stalled for 5 days with no activity.'
          days-before-issue-stale: -1
          days-before-pr-stale: 14
          days-before-issue-close: -1
          days-before-pr-close: 5 
```

---

## File: `.well-known/mcp/manifest.json`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/.well-known/mcp/manifest.json`

```json
{
  "_comment": "GitHub MCP Registry Manifest",
  "_location": "/.well-known/mcp/manifest.json",
  "version": "2.0.0",
  "schema_version": "0.2.0",
  "manifest_version": "0.3",
  "name": "alpaca-mcp-server",
  "display_name": "Alpaca MCP Server",
  "description": "Alpaca Trading API integration for Model Context Protocol. V2 generates 60+ tools from Alpaca's OpenAPI specs using FastMCP, with toolset filtering and hand-crafted order overrides.",
  "author": "Alpaca",
  "license": "MIT",
  "homepage": "https://alpaca.markets/",
  "repository": "https://github.com/alpacahq/alpaca-mcp-server",
  "documentation": "https://github.com/alpacahq/alpaca-mcp-server#readme",
  "categories": ["finance", "trading", "data", "api"],
  "tags": ["alpaca", "stocks", "options", "crypto", "portfolio", "market-data"],
  "privacy_policies": ["https://s3.amazonaws.com/files.alpaca.markets/disclosures/PrivacyPolicy.pdf"],

  "installation": {
    "uvx": "alpaca-mcp-server",
    "pypi": "alpaca-mcp-server",
    "github": "git+https://github.com/alpacahq/alpaca-mcp-server.git"
  },

  "configuration": {
    "required_env_vars": [
      {
        "name": "ALPACA_API_KEY",
        "description": "Alpaca API key for trading account access",
        "sensitive": true
      },
      {
        "name": "ALPACA_SECRET_KEY",
        "description": "Alpaca secret key for trading account access",
        "sensitive": true
      }
    ],
    "optional_env_vars": [
      {
        "name": "ALPACA_TOOLSETS",
        "description": "Comma-separated list of toolsets to enable (e.g. account,trading,stock-data). All enabled by default.",
        "default": ""
      }
    ]
  },

  "toolsets": {
    "account": ["get_account_info", "get_account_config", "update_account_config", "get_portfolio_history", "get_account_activities", "get_account_activities_by_type"],
    "trading": ["get_orders", "get_order_by_id", "get_order_by_client_id", "replace_order_by_id", "cancel_order_by_id", "cancel_all_orders", "get_all_positions", "get_open_position", "close_position", "close_all_positions", "exercise_options_position", "do_not_exercise_options_position", "place_stock_order", "place_crypto_order", "place_option_order"],
    "watchlists": ["get_watchlists", "create_watchlist", "get_watchlist_by_id", "update_watchlist_by_id", "delete_watchlist_by_id", "add_asset_to_watchlist_by_id", "remove_asset_from_watchlist_by_id"],
    "assets": ["get_all_assets", "get_asset", "get_option_contracts", "get_option_contract", "get_calendar", "get_clock", "get_corporate_action_announcements", "get_corporate_action_announcement"],
    "stock-data": ["get_stock_bars", "get_stock_quotes", "get_stock_trades", "get_stock_latest_bar", "get_stock_latest_quote", "get_stock_latest_trade", "get_stock_snapshot", "get_most_active_stocks", "get_market_movers"],
    "crypto-data": ["get_crypto_bars", "get_crypto_quotes", "get_crypto_trades", "get_crypto_latest_bar", "get_crypto_latest_quote", "get_crypto_latest_trade", "get_crypto_snapshot", "get_crypto_latest_orderbook"],
    "options-data": ["get_option_bars", "get_option_trades", "get_option_latest_trade", "get_option_latest_quote", "get_option_snapshot", "get_option_chain", "get_option_exchange_codes"],
    "corporate-actions": ["get_corporate_actions"]
  },

  "capabilities": {
    "real_time_data": true,
    "historical_data": true,
    "order_management": true,
    "portfolio_management": true,
    "options_trading": true,
    "crypto_trading": true,
    "market_data": true,
    "paper_trading": true,
    "live_trading": true,
    "watchlist_management": true,
    "corporate_actions": true,
    "market_calendar": true,
    "toolset_filtering": true
  },

  "requirements": {
    "python": ">=3.10",
    "alpaca_account": "Required - Free paper trading or paid live account"
  }
}
```

---

## File: `scripts/sync-specs.sh`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/scripts/sync-specs.sh`

```bash
#!/bin/bash
set -e
SPECS_DIR="$(dirname "$0")/../src/alpaca_mcp_server/specs"
curl -sL https://docs.alpaca.markets/openapi/trading-api.json -o "$SPECS_DIR/trading-api.json"
curl -sL https://docs.alpaca.markets/openapi/market-data-api.json -o "$SPECS_DIR/market-data-api.json"
echo "Specs updated. Run 'git diff' to see changes."
```

---

## File: `src/alpaca_mcp_server/__init__.py`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/src/alpaca_mcp_server/__init__.py`

```python
"""
Alpaca MCP Server - Trading API Integration for Model Context Protocol

This package provides a comprehensive MCP server implementation for Alpaca
Trading API, enabling natural language trading operations through AI assistants.

Key Features:
- Stock, ETF, options, and crypto trading
- Portfolio management and account information
- Real-time market data and historical data
- Watchlist management
- Corporate actions and market calendar
"""

__version__ = "2.0.0"
__author__ = "Alpaca"
__license__ = "MIT"
__description__ = "Alpaca Trading API integration for Model Context Protocol (MCP)"

__all__ = ["__version__"]
```

---

## File: `src/alpaca_mcp_server/cli.py`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/src/alpaca_mcp_server/cli.py`

```python
"""
CLI entry point for the Alpaca MCP Server.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__


@click.command()
@click.version_option(version=__version__, prog_name="alpaca-mcp-server")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "streamable-http", "sse"]),
    default="stdio",
    help="Transport protocol (default: stdio)",
)
@click.option("--host", default="127.0.0.1", help="Host to bind (HTTP transport only)")
@click.option("--port", type=int, default=8000, help="Port to bind (HTTP transport only)")
@click.option(
    "--env-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Load environment variables from this file before starting",
)
def main(transport: str, host: str, port: int, env_file: Optional[Path]):
    """Alpaca MCP Server — Trading API integration for Model Context Protocol."""
    if env_file is not None:
        from dotenv import load_dotenv

        load_dotenv(env_file, override=False)

    if not os.environ.get("ALPACA_API_KEY") or not os.environ.get("ALPACA_SECRET_KEY"):
        click.echo(
            "Error: ALPACA_API_KEY and ALPACA_SECRET_KEY must be set.\n"
            "Set them in your MCP client config's env block or pass --env-file.",
            err=True,
        )
        sys.exit(1)

    from .server import build_server

    server = build_server()

    if transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport=transport, host=host, port=port)
```

---

## File: `src/alpaca_mcp_server/server.py`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/src/alpaca_mcp_server/server.py`

```python
"""
Alpaca MCP Server v2 — FastMCP + OpenAPI

Builds MCP tools from Alpaca's OpenAPI specs at process init time.
No hand-crafted tool functions except for overrides (e.g., order placement).
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.providers.openapi.routing import MCPType

from .names import TOOL_DESCRIPTIONS, TOOL_NAMES
from .toolsets import OVERRIDE_OPERATION_IDS, TOOLSETS, get_active_operations

SPECS_DIR = Path(__file__).parent / "specs"

TRADING_API_BASE_URLS = {
    "paper": "https://paper-api.alpaca.markets",
    "live": "https://api.alpaca.markets",
}
MARKET_DATA_BASE_URL = "https://data.alpaca.markets"


def _load_spec(name: str) -> dict[str, Any]:
    path = SPECS_DIR / f"{name}.json"
    return json.loads(path.read_text())


def _make_filter(allowed_ops: set[str]):
    """Create a route_map_fn that includes only allowlisted operationIds."""
    def filter_fn(route, default_type):
        if route.operation_id in allowed_ops and route.operation_id not in OVERRIDE_OPERATION_IDS:
            return MCPType.TOOL
        return MCPType.EXCLUDE
    return filter_fn


def _make_customizer(descriptions: dict[str, str]):
    """Create an mcp_component_fn that overrides descriptions where provided."""
    def customizer(route, component):
        if route.operation_id in descriptions:
            component.description = descriptions[route.operation_id]
    return customizer


def _build_auth_headers() -> dict[str, str]:
    key = os.environ.get("ALPACA_API_KEY", "")
    secret = os.environ.get("ALPACA_SECRET_KEY", "")
    return {
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": secret,
    }


def _get_trading_base_url() -> str:
    paper = os.environ.get("ALPACA_PAPER_TRADE", "true").lower() in ("true", "1", "yes")
    return TRADING_API_BASE_URLS["paper" if paper else "live"]


def _parse_toolsets() -> set[str] | None:
    raw = os.environ.get("ALPACA_TOOLSETS", "").strip()
    if not raw:
        return None
    return {t.strip() for t in raw.split(",") if t.strip()}


def build_server() -> FastMCP:
    """Construct the Alpaca MCP server from OpenAPI specs."""
    active_toolsets = _parse_toolsets()
    spec_ops = get_active_operations(active_toolsets)

    auth_headers = _build_auth_headers()
    trading_base = _get_trading_base_url()
    data_base = os.environ.get("DATA_API_URL", MARKET_DATA_BASE_URL).rstrip("/")

    clients: list[httpx.AsyncClient] = []

    trading_client: httpx.AsyncClient | None = None
    if "trading" in spec_ops:
        trading_client = httpx.AsyncClient(
            base_url=trading_base,
            headers=auth_headers,
            timeout=30.0,
        )
        clients.append(trading_client)

    data_client: httpx.AsyncClient | None = None
    if "market-data" in spec_ops:
        data_client = httpx.AsyncClient(
            base_url=data_base,
            headers=auth_headers,
            timeout=30.0,
        )
        clients.append(data_client)

    @asynccontextmanager
    async def lifespan(_server: FastMCP) -> AsyncIterator[dict]:
        try:
            yield {}
        finally:
            for c in clients:
                await c.aclose()

    main = FastMCP("Alpaca MCP Server", lifespan=lifespan)

    if trading_client is not None:
        allowed = spec_ops["trading"]
        spec = _load_spec("trading-api")
        sub = FastMCP.from_openapi(
            spec,
            client=trading_client,
            name="Alpaca Trading",
            mcp_names=TOOL_NAMES,
            route_map_fn=_make_filter(allowed),
            mcp_component_fn=_make_customizer(TOOL_DESCRIPTIONS),
            validate_output=False,
        )
        main.mount(sub)

    if data_client is not None:
        allowed = spec_ops["market-data"]
        spec = _load_spec("market-data-api")
        sub = FastMCP.from_openapi(
            spec,
            client=data_client,
            name="Alpaca Market Data",
            mcp_names=TOOL_NAMES,
            route_map_fn=_make_filter(allowed),
            mcp_component_fn=_make_customizer(TOOL_DESCRIPTIONS),
            validate_output=False,
        )
        main.mount(sub)

    active_ts = active_toolsets if active_toolsets is not None else set(TOOLSETS.keys())

    if trading_client is not None and "trading" in active_ts:
        _register_trading_overrides(main, trading_client)

    if data_client is not None and active_ts & {"stock-data", "crypto-data"}:
        _register_market_data_overrides(main, data_client)

    return main


def _register_trading_overrides(server: FastMCP, trading_client: httpx.AsyncClient) -> None:
    """Register hand-crafted override tools for complex trading endpoints."""
    from .overrides import register_order_tools
    register_order_tools(server, trading_client)


def _register_market_data_overrides(server: FastMCP, data_client: httpx.AsyncClient) -> None:
    """Register hand-crafted override tools for historical market data."""
    from .market_data_overrides import register_market_data_tools
    register_market_data_tools(server, data_client)
```

---

## File: `src/alpaca_mcp_server/names.py`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/src/alpaca_mcp_server/names.py`

```python
"""
Tool name and description overrides for the Alpaca MCP Server.

Maps OpenAPI operationIds to user-friendly MCP tool names and curated
descriptions ported from the v1 server. These keep the v1 tool naming
convention while using FastMCP's from_openapi() under the hood.

Each key is the operationId from the OpenAPI spec. Values contain:
  - name:        the MCP tool name exposed to clients
  - description: curated description shown to LLMs
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolOverride:
    name: str
    description: str


TOOLS: dict[str, ToolOverride] = {
    # --- Account ---
    "getAccount": ToolOverride(
        name="get_account_info",
        description=(
            "Retrieves and formats the current account information "
            "including balances and status."
        ),
    ),
    "getAccountConfig": ToolOverride(
        name="get_account_config",
        description=(
            "Retrieves the current account configuration settings, including "
            "trading restrictions, margin settings, PDT checks, and options trading level."
        ),
    ),
    "patchAccountConfig": ToolOverride(
        name="update_account_config",
        description=(
            "Updates one or more account configuration settings. Only the fields you "
            "provide will be changed; all others retain their current values."
        ),
    ),
    "getAccountPortfolioHistory": ToolOverride(
        name="get_portfolio_history",
        description=(
            "Retrieves account portfolio history (equity and P/L) over a requested time window."
        ),
    ),
    "getAccountActivities": ToolOverride(
        name="get_account_activities",
        description=(
            "Returns a list of account activities such as fills, dividends, and transfers."
        ),
    ),
    "getAccountActivitiesByActivityType": ToolOverride(
        name="get_account_activities_by_type",
        description=(
            "Returns account activity entries for a specific type of activity."
        ),
    ),

    # --- Trading: Orders ---
    "getAllOrders": ToolOverride(
        name="get_orders",
        description="Retrieves and formats orders with the specified filters.",
    ),
    "getOrderByOrderID": ToolOverride(
        name="get_order_by_id",
        description="Retrieves a single order by its ID.",
    ),
    "getOrderByClientOrderId": ToolOverride(
        name="get_order_by_client_id",
        description=(
            "Retrieves a single order specified by the client order ID. "
            "Note: if the order was replaced, this returns the original order "
            "(status \"replaced\") with a replaced_by field pointing to the new order ID."
        ),
    ),
    "patchOrderByOrderId": ToolOverride(
        name="replace_order_by_id",
        description=(
            "Replaces an existing open order with updated parameters. "
            "At least one optional field must be provided."
        ),
    ),
    "deleteOrderByOrderID": ToolOverride(
        name="cancel_order_by_id",
        description="Cancel a specific order by its ID.",
    ),
    "deleteAllOrders": ToolOverride(
        name="cancel_all_orders",
        description="Cancel all open orders.",
    ),

    # --- Trading: Positions ---
    "getAllOpenPositions": ToolOverride(
        name="get_all_positions",
        description="Retrieves all current positions in the portfolio as JSON.",
    ),
    "getOpenPosition": ToolOverride(
        name="get_open_position",
        description="Retrieves and formats details for a specific open position.",
    ),
    "deleteOpenPosition": ToolOverride(
        name="close_position",
        description=(
            "Closes a specific position for a single symbol by placing a sell order. "
            "If the market is closed, the sell order will remain queued and execute "
            "at the next market open."
        ),
    ),
    "deleteAllOpenPositions": ToolOverride(
        name="close_all_positions",
        description=(
            "Closes all open positions by placing sell orders for each. "
            "If the market is closed, the sell orders will remain queued and execute "
            "at the next market open."
        ),
    ),
    "optionExercise": ToolOverride(
        name="exercise_options_position",
        description="Exercises a held option contract, converting it into the underlying asset.",
    ),
    "optionDoNotExercise": ToolOverride(
        name="do_not_exercise_options_position",
        description="Submits a do-not-exercise instruction for a held option contract.",
    ),

    # --- Watchlists ---
    "getWatchlists": ToolOverride(
        name="get_watchlists",
        description="Get all watchlists for the account.",
    ),
    "postWatchlist": ToolOverride(
        name="create_watchlist",
        description="Creates a new watchlist with specified symbols.",
    ),
    "getWatchlistById": ToolOverride(
        name="get_watchlist_by_id",
        description="Get a specific watchlist by its ID.",
    ),
    "updateWatchlistById": ToolOverride(
        name="update_watchlist_by_id",
        description=(
            "Update an existing watchlist. IMPORTANT: this replaces the entire watchlist. "
            "You must include the symbols parameter with the full list of desired symbols, "
            "otherwise all assets will be removed."
        ),
    ),
    "deleteWatchlistById": ToolOverride(
        name="delete_watchlist_by_id",
        description="Delete a specific watchlist by its ID.",
    ),
    "addAssetToWatchlist": ToolOverride(
        name="add_asset_to_watchlist_by_id",
        description="Add an asset by symbol to a specific watchlist.",
    ),
    "removeAssetFromWatchlist": ToolOverride(
        name="remove_asset_from_watchlist_by_id",
        description="Remove an asset by symbol from a specific watchlist.",
    ),

    # --- Assets & Market Info ---
    "get-v2-assets": ToolOverride(
        name="get_all_assets",
        description=(
            "Get all available assets with optional filtering. "
            "WARNING: The unfiltered response is very large (thousands of assets). "
            "Always narrow results with the status, asset_class, or exchange parameters. "
            "To look up a single asset, use get_asset instead."
        ),
    ),
    "get-v2-assets-symbol_or_asset_id": ToolOverride(
        name="get_asset",
        description="Retrieves and formats detailed information about a specific asset.",
    ),
    "get-options-contracts": ToolOverride(
        name="get_option_contracts",
        description="Retrieves option contracts for underlying symbol(s).",
    ),
    "get-option-contract-symbol_or_id": ToolOverride(
        name="get_option_contract",
        description="Retrieves a single option contract by symbol or contract ID.",
    ),
    "LegacyCalendar": ToolOverride(
        name="get_calendar",
        description=(
            "Retrieves and formats market calendar for specified date range. "
            "WARNING: Always provide start and end dates (YYYY-MM-DD). "
            "Without date bounds the response contains the entire multi-year "
            "calendar and will be extremely large."
        ),
    ),
    "LegacyClock": ToolOverride(
        name="get_clock",
        description="Retrieves and formats current market status and next open/close times.",
    ),
    "get-v2-corporate_actions-announcements": ToolOverride(
        name="get_corporate_action_announcements",
        description=(
            "Retrieves corporate action announcements (dividends, mergers, splits, spinoffs). "
            "Use a narrow date range and filter by symbol when possible — "
            "broad queries can return very large responses."
        ),
    ),
    "get-v2-corporate_actions-announcements-id": ToolOverride(
        name="get_corporate_action_announcement",
        description="Retrieves a single corporate action announcement by ID.",
    ),

    # --- Stock Data ---
    "StockBars": ToolOverride(
        name="get_stock_bars",
        description=(
            "Retrieves and formats historical price bars for stocks "
            "with configurable timeframe and time range."
        ),
    ),
    "StockQuotes": ToolOverride(
        name="get_stock_quotes",
        description="Retrieves and formats historical quote data (level 1 bid/ask) for stocks.",
    ),
    "StockTrades": ToolOverride(
        name="get_stock_trades",
        description="Retrieves and formats historical trades for stocks.",
    ),
    "StockLatestBars": ToolOverride(
        name="get_stock_latest_bar",
        description="Get the latest minute bar for one or more stocks.",
    ),
    "StockLatestQuotes": ToolOverride(
        name="get_stock_latest_quote",
        description="Retrieves and formats the latest quote for one or more stocks.",
    ),
    "StockLatestTrades": ToolOverride(
        name="get_stock_latest_trade",
        description="Get the latest trade for one or more stocks.",
    ),
    "StockSnapshots": ToolOverride(
        name="get_stock_snapshot",
        description=(
            "Retrieves comprehensive snapshots of stock symbols including latest trade, "
            "quote, minute bar, daily bar, and previous daily bar."
        ),
    ),
    "MostActives": ToolOverride(
        name="get_most_active_stocks",
        description="Screens the market for most active stocks by volume or trade count.",
    ),
    "Movers": ToolOverride(
        name="get_market_movers",
        description="Returns the top market movers (gainers and losers) based on real-time SIP data.",
    ),

    # --- Crypto Data ---
    "CryptoBars": ToolOverride(
        name="get_crypto_bars",
        description=(
            "Retrieves and formats historical price bars for cryptocurrencies "
            "with configurable timeframe and time range."
        ),
    ),
    "CryptoQuotes": ToolOverride(
        name="get_crypto_quotes",
        description="Returns historical quote data for one or more crypto symbols.",
    ),
    "CryptoTrades": ToolOverride(
        name="get_crypto_trades",
        description="Returns historical trade data for one or more crypto symbols.",
    ),
    "CryptoLatestBars": ToolOverride(
        name="get_crypto_latest_bar",
        description=(
            "Returns the latest minute bar for one or more crypto symbols. "
            "The loc parameter is required — always set loc to \"us\"."
        ),
    ),
    "CryptoLatestQuotes": ToolOverride(
        name="get_crypto_latest_quote",
        description=(
            "Returns the latest quote for one or more crypto symbols. "
            "The loc parameter is required — always set loc to \"us\"."
        ),
    ),
    "CryptoLatestTrades": ToolOverride(
        name="get_crypto_latest_trade",
        description=(
            "Returns the latest trade for one or more crypto symbols. "
            "The loc parameter is required — always set loc to \"us\"."
        ),
    ),
    "CryptoSnapshots": ToolOverride(
        name="get_crypto_snapshot",
        description=(
            "Returns a snapshot for one or more crypto symbols including latest trade, "
            "quote, minute bar, daily bar, and previous daily bar. "
            "The loc parameter is required — always set loc to \"us\"."
        ),
    ),
    "CryptoLatestOrderbooks": ToolOverride(
        name="get_crypto_latest_orderbook",
        description=(
            "Returns the latest orderbook for one or more crypto symbols. "
            "The loc parameter is required — always set loc to \"us\". "
            "Note: the response includes the full order book depth and can be large."
        ),
    ),

    # --- Options Data ---
    "optionBars": ToolOverride(
        name="get_option_bars",
        description="Retrieves historical bar (OHLCV) data for one or more option contracts.",
    ),
    "OptionTrades": ToolOverride(
        name="get_option_trades",
        description="Retrieves historical trade data for one or more option contracts.",
    ),
    "OptionLatestTrades": ToolOverride(
        name="get_option_latest_trade",
        description="Retrieves the latest trade for one or more option contracts.",
    ),
    "OptionLatestQuotes": ToolOverride(
        name="get_option_latest_quote",
        description=(
            "Retrieves and formats the latest quote for one or more option contracts "
            "including bid/ask prices, sizes, and exchange information."
        ),
    ),
    "OptionSnapshots": ToolOverride(
        name="get_option_snapshot",
        description=(
            "Retrieves comprehensive snapshots of option contracts including latest trade, "
            "quote, implied volatility, and Greeks."
        ),
    ),
    "OptionChain": ToolOverride(
        name="get_option_chain",
        description=(
            "Retrieves option chain data for an underlying symbol, including latest trade, "
            "quote, implied volatility, and greeks for each contract. "
            "The response can be very large. Use the type (call/put), "
            "strike_price_gte/lte, expiration_date, and limit parameters "
            "to narrow results."
        ),
    ),
    "OptionMetaExchanges": ToolOverride(
        name="get_option_exchange_codes",
        description=(
            "Retrieves the mapping of exchange codes to exchange names for option market data. "
            "Useful for interpreting exchange fields returned by other option data tools."
        ),
    ),

    # --- Corporate Actions (Market Data) ---
    "CorporateActions": ToolOverride(
        name="get_corporate_actions",
        description="Retrieves and formats corporate action announcements.",
    ),
}

# Derived lookups used by server.py
TOOL_NAMES: dict[str, str] = {op_id: t.name for op_id, t in TOOLS.items()}
TOOL_DESCRIPTIONS: dict[str, str] = {op_id: t.description for op_id, t in TOOLS.items()}
```

---

## File: `src/alpaca_mcp_server/toolsets.py`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/src/alpaca_mcp_server/toolsets.py`

```python
"""
Toolset definitions for the Alpaca MCP Server.

Each toolset maps to a set of operationIds from the OpenAPI specs. Only endpoints
listed here are exposed as MCP tools. New endpoints are excluded by default —
add their operationId to the appropriate toolset to include them.
"""

TOOLSETS: dict[str, dict] = {
    "account": {
        "spec": "trading",
        "operations": {
            "getAccount",
            "getAccountConfig",
            "patchAccountConfig",
            "getAccountPortfolioHistory",
            "getAccountActivities",
            "getAccountActivitiesByActivityType",
        },
    },
    "trading": {
        "spec": "trading",
        "operations": {
            "getAllOrders",
            "getOrderByOrderID",
            "getOrderByClientOrderId",
            "patchOrderByOrderId",
            "deleteOrderByOrderID",
            "deleteAllOrders",
            # postOrder is excluded — replaced by overrides
            # (place_stock_order, place_crypto_order, place_option_order)
            "getAllOpenPositions",
            "getOpenPosition",
            "deleteOpenPosition",
            "deleteAllOpenPositions",
            "optionExercise",
            "optionDoNotExercise",
        },
    },
    "watchlists": {
        "spec": "trading",
        "operations": {
            "getWatchlists",
            "postWatchlist",
            "getWatchlistById",
            "updateWatchlistById",
            "deleteWatchlistById",
            "addAssetToWatchlist",
            "removeAssetFromWatchlist",
        },
    },
    "assets": {
        "spec": "trading",
        "operations": {
            "get-v2-assets",
            "get-v2-assets-symbol_or_asset_id",
            "get-options-contracts",
            "get-option-contract-symbol_or_id",
            "LegacyCalendar",
            "LegacyClock",
            "get-v2-corporate_actions-announcements",
            "get-v2-corporate_actions-announcements-id",
        },
    },
    "stock-data": {
        "spec": "market-data",
        "operations": {
            "StockBars",
            "StockQuotes",
            "StockTrades",
            "StockLatestBars",
            "StockLatestQuotes",
            "StockLatestTrades",
            "StockSnapshots",
            "MostActives",
            "Movers",
        },
    },
    "crypto-data": {
        "spec": "market-data",
        "operations": {
            "CryptoBars",
            "CryptoQuotes",
            "CryptoTrades",
            "CryptoLatestBars",
            "CryptoLatestQuotes",
            "CryptoLatestTrades",
            "CryptoSnapshots",
            "CryptoLatestOrderbooks",
        },
    },
    "options-data": {
        "spec": "market-data",
        "operations": {
            "optionBars",
            "OptionTrades",
            "OptionLatestTrades",
            "OptionLatestQuotes",
            "OptionSnapshots",
            "OptionChain",
            "OptionMetaExchanges",
        },
    },
    "corporate-actions": {
        "spec": "market-data",
        "operations": {
            "CorporateActions",
        },
    },
}

OVERRIDE_OPERATION_IDS = {
    "postOrder",
    "StockBars",
    "StockQuotes",
    "StockTrades",
    "CryptoBars",
    "CryptoQuotes",
    "CryptoTrades",
}


def get_active_operations(active_toolsets: set[str] | None = None) -> dict[str, set[str]]:
    """Return allowed operationIds grouped by spec name.

    Args:
        active_toolsets: Set of toolset names to enable. None means all.

    Returns:
        Dict mapping spec name ("trading" / "market-data") to sets of operationIds.
    """
    spec_ops: dict[str, set[str]] = {}
    for ts_name, ts_config in TOOLSETS.items():
        if active_toolsets is not None and ts_name not in active_toolsets:
            continue
        spec = ts_config["spec"]
        spec_ops.setdefault(spec, set()).update(ts_config["operations"])
    return spec_ops
```

---

## File: `src/alpaca_mcp_server/overrides.py`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/src/alpaca_mcp_server/overrides.py`

```python
"""
Hand-crafted tool overrides for endpoints too complex for auto-generation.

POST /v2/orders has 17+ parameters covering stocks, crypto, options, bracket
orders, trailing stops, and multi-leg orders. We split it into three focused
tools with curated parameters per asset class.
"""

from __future__ import annotations

from typing import Optional

import httpx
from fastmcp import FastMCP


def _error(message: str, **extra: object) -> dict:
    """Build a standardised error dict returned to the LLM."""
    err: dict = {"message": message}
    err.update(extra)
    return {"error": err}


async def _post_order(client: httpx.AsyncClient, body: dict) -> dict:
    """Submit an order and return the response, surfacing API error details.

    Catches read-timeouts explicitly because the request may have reached
    Alpaca even though we never received the response.  A generic retry
    would risk placing a duplicate order.
    """
    try:
        resp = await client.post("/v2/orders", json=body)
    except httpx.ReadTimeout:
        return _error(
            "Request was sent but timed out waiting for a response. "
            "The order MAY have been placed. Check open orders before "
            "retrying. If you set client_order_id, you can safely retry "
            "with the same value — the API will reject the duplicate.",
            timeout=True,
        )

    if resp.is_error:
        try:
            detail = resp.json()
        except Exception:
            detail = {"raw": resp.text}
        return _error(
            "API rejected the order",
            http_status=resp.status_code,
            detail=detail,
        )
    return resp.json()


def register_order_tools(
    server: FastMCP,
    client: httpx.AsyncClient,
) -> None:
    """Register the three order placement tools on the given server."""

    @server.tool(
        annotations={
            "title": "Place Stock Order",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        }
    )
    async def place_stock_order(
        symbol: str,
        side: str,
        qty: Optional[str] = None,
        notional: Optional[str] = None,
        type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[str] = None,
        stop_price: Optional[str] = None,
        trail_price: Optional[str] = None,
        trail_percent: Optional[str] = None,
        extended_hours: bool = False,
        client_order_id: Optional[str] = None,
        order_class: Optional[str] = None,
        take_profit_limit_price: Optional[str] = None,
        stop_loss_stop_price: Optional[str] = None,
        stop_loss_limit_price: Optional[str] = None,
    ) -> dict:
        """Place a stock or ETF order.

        Args:
            symbol: Stock ticker (e.g., "AAPL", "SPY").
            side: "buy" or "sell".
            qty: Number of shares. Mutually exclusive with notional.
            notional: Dollar amount to trade. Mutually exclusive with qty.
                      Only valid for market orders with time_in_force="day".
            type: Order type — "market", "limit", "stop", "stop_limit",
                  "trailing_stop".
            time_in_force: "day", "gtc", "opg", "cls", "ioc", or "fok".
            limit_price: Required for limit and stop_limit orders.
            stop_price: Required for stop and stop_limit orders.
            trail_price: Dollar trail amount for trailing_stop orders.
            trail_percent: Percent trail for trailing_stop orders.
            extended_hours: Allow execution in extended hours. Only works
                            with type="limit" and time_in_force="day".
            client_order_id: Unique idempotency key. If the request times out,
                             you can safely retry with the same value — the API
                             will reject duplicates. Recommended for every order.
            order_class: "simple", "bracket", "oco", or "oto". Automatically
                         set to "bracket" when take_profit or stop_loss params
                         are provided.
            take_profit_limit_price: Limit price for bracket take-profit leg.
            stop_loss_stop_price: Stop price for bracket stop-loss leg.
            stop_loss_limit_price: Limit price for bracket stop-loss leg.
        """
        if stop_loss_limit_price is not None and stop_loss_stop_price is None:
            return _error(
                "stop_loss_limit_price requires stop_loss_stop_price"
            )

        has_bracket_params = (
            take_profit_limit_price is not None
            or stop_loss_stop_price is not None
        )
        if has_bracket_params and order_class is None:
            order_class = "bracket"

        body: dict = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "time_in_force": time_in_force,
        }
        if qty is not None:
            body["qty"] = qty
        if notional is not None:
            body["notional"] = notional
        if limit_price is not None:
            body["limit_price"] = limit_price
        if stop_price is not None:
            body["stop_price"] = stop_price
        if trail_price is not None:
            body["trail_price"] = trail_price
        if trail_percent is not None:
            body["trail_percent"] = trail_percent
        if extended_hours:
            body["extended_hours"] = True
        if client_order_id is not None:
            body["client_order_id"] = client_order_id
        if order_class is not None:
            body["order_class"] = order_class
        if take_profit_limit_price is not None:
            body["take_profit"] = {"limit_price": take_profit_limit_price}
        if stop_loss_stop_price is not None:
            sl: dict = {"stop_price": stop_loss_stop_price}
            if stop_loss_limit_price is not None:
                sl["limit_price"] = stop_loss_limit_price
            body["stop_loss"] = sl

        return await _post_order(client, body)

    @server.tool(
        annotations={
            "title": "Place Crypto Order",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        }
    )
    async def place_crypto_order(
        symbol: str,
        side: str,
        qty: Optional[str] = None,
        notional: Optional[str] = None,
        type: str = "market",
        time_in_force: str = "gtc",
        limit_price: Optional[str] = None,
        stop_price: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> dict:
        """Place a cryptocurrency order.

        Args:
            symbol: Crypto pair (e.g., "BTC/USD", "ETH/USD").
            side: "buy" or "sell".
            qty: Number of coins/tokens. Mutually exclusive with notional.
            notional: Dollar amount to trade. Mutually exclusive with qty.
                      Only valid for market orders.
            type: "market", "limit", or "stop_limit".
            time_in_force: "gtc" (default) or "ioc". Crypto does not
                           support "day" or "fok".
            limit_price: Required for limit and stop_limit orders.
            stop_price: Required for stop_limit orders.
            client_order_id: Unique idempotency key. If the request times out,
                             you can safely retry with the same value — the API
                             will reject duplicates. Recommended for every order.
        """
        body: dict = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "time_in_force": time_in_force,
        }
        if qty is not None:
            body["qty"] = qty
        if notional is not None:
            body["notional"] = notional
        if limit_price is not None:
            body["limit_price"] = limit_price
        if stop_price is not None:
            body["stop_price"] = stop_price
        if client_order_id is not None:
            body["client_order_id"] = client_order_id

        return await _post_order(client, body)

    @server.tool(
        annotations={
            "title": "Place Option Order",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        }
    )
    async def place_option_order(
        qty: str,
        type: str = "market",
        time_in_force: str = "day",
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        position_intent: Optional[str] = None,
        limit_price: Optional[str] = None,
        client_order_id: Optional[str] = None,
        order_class: Optional[str] = None,
        legs: Optional[list[dict]] = None,
    ) -> dict:
        """Place an options order (single-leg or multi-leg).

        For single-leg orders, provide symbol, side, and qty.
        For multi-leg orders, provide qty, legs, and optionally
        order_class="mleg" (auto-inferred). Symbol and side on the
        parent are not needed for multi-leg.

        Args:
            qty: Number of contracts. Required for both single-leg and
                 multi-leg orders. For multi-leg, this is the strategy
                 multiplier — each leg's ratio_qty is scaled by this
                 value (e.g., qty="10" with ratio_qty="2" = 20
                 contracts for that leg).
            type: "market" or "limit".
            time_in_force: "day" only. Options do not support other
                           values.
            symbol: OCC option symbol (e.g., "AAPL250321C00150000").
                    Required for single-leg.
            side: "buy" or "sell". Required for single-leg.
            position_intent: "buy_to_open", "buy_to_close", "sell_to_open",
                             or "sell_to_close". Clarifies whether the trade
                             opens or closes a position. Optional but
                             recommended.
            limit_price: Required for limit orders. For multi-leg, this is
                         the net debit/credit (positive = debit/cost,
                         negative = credit/proceeds).
            client_order_id: Unique idempotency key. If the request times out,
                             you can safely retry with the same value — the API
                             will reject duplicates. Recommended for every order.
            order_class: Set to "mleg" for multi-leg orders. Automatically
                         inferred when legs are provided.
            legs: List of leg dicts for multi-leg orders (max 4). Each leg
                  requires "symbol" and "ratio_qty" (string). Optional
                  per-leg fields: "side" ("buy" or "sell") and
                  "position_intent".
        """
        is_multi_leg = legs is not None or order_class == "mleg"

        if is_multi_leg and legs is None:
            return _error(
                "Multi-leg orders require the legs parameter"
            )

        if not is_multi_leg and (symbol is None or side is None):
            return _error(
                "Single-leg orders require symbol and side"
            )

        if legs is not None and order_class is None:
            order_class = "mleg"

        body: dict = {
            "qty": qty,
            "type": type,
            "time_in_force": time_in_force,
        }
        if symbol is not None:
            body["symbol"] = symbol
        if side is not None:
            body["side"] = side
        if position_intent is not None:
            body["position_intent"] = position_intent
        if limit_price is not None:
            body["limit_price"] = limit_price
        if client_order_id is not None:
            body["client_order_id"] = client_order_id
        if order_class is not None:
            body["order_class"] = order_class
        if legs is not None:
            body["legs"] = legs

        return await _post_order(client, body)
```

---

## File: `src/alpaca_mcp_server/market_data_overrides.py`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/src/alpaca_mcp_server/market_data_overrides.py`

```python
"""
Hand-crafted overrides for historical market data endpoints.

The raw OpenAPI endpoints require absolute ISO-8601 timestamps for time ranges.
These overrides add relative-time convenience parameters (days, hours, minutes)
that auto-compute the start timestamp — LLMs are unreliable at computing ISO
timestamps from expressions like "last 5 days", so this removes that failure mode.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastmcp import FastMCP

_TIMEFRAME_ALIASES: dict[str, str] = {
    "1min": "1Min", "5min": "5Min", "15min": "15Min", "30min": "30Min",
    "1hour": "1Hour", "4hour": "4Hour",
    "1day": "1Day", "1week": "1Week", "1month": "1Month",
}

_TIMEFRAME_PATTERN = re.compile(r"^(\d+)(min|hour|day|week|month)$")


def _relative_start(days: int = 0, hours: int = 0, minutes: int = 0) -> str | None:
    """ISO-8601 timestamp computed as now(UTC) minus the given offset.

    Returns None when offset is zero so the API can apply its own default.
    """
    if days == 0 and hours == 0 and minutes == 0:
        return None
    start = datetime.now(timezone.utc) - timedelta(days=days, hours=hours, minutes=minutes)
    return start.strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_timeframe(tf: str) -> str:
    """Map case variants (e.g. '2hour') to API-expected format ('2Hour')."""
    lower = tf.lower().strip()
    alias = _TIMEFRAME_ALIASES.get(lower)
    if alias:
        return alias
    m = _TIMEFRAME_PATTERN.match(lower)
    if m:
        return m.group(1) + m.group(2).capitalize()
    return tf


def _error(message: str, **extra: object) -> dict:
    err: dict = {"message": message}
    err.update(extra)
    return {"error": err}


async def _get(client: httpx.AsyncClient, path: str, params: dict) -> dict:
    """GET request with error handling matching the order override pattern."""
    params = {k: v for k, v in params.items() if v is not None}
    try:
        resp = await client.get(path, params=params)
    except httpx.ReadTimeout:
        return _error(
            "Request timed out. Try narrowing the time range or reducing the limit.",
            timeout=True,
        )
    except httpx.HTTPError as exc:
        return _error(f"HTTP transport error: {exc}")

    if resp.is_error:
        try:
            detail = resp.json()
        except Exception:
            detail = {"raw": resp.text}
        return _error(
            "Market data API error",
            http_status=resp.status_code,
            detail=detail,
        )
    try:
        return resp.json()
    except Exception:
        return {"raw_response": resp.text}


def register_market_data_tools(
    server: FastMCP,
    client: httpx.AsyncClient,
) -> None:
    """Register the six historical market data tools on the given server."""

    # ── Stock Historical Data ──────────────────────────────────────────────

    @server.tool(
        annotations={
            "title": "Get Stock Bars",
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    async def get_stock_bars(
        symbols: str,
        timeframe: str = "1Day",
        start: Optional[str] = None,
        end: Optional[str] = None,
        days: int = 5,
        hours: int = 0,
        minutes: int = 0,
        limit: int = 1000,
        adjustment: str = "raw",
        feed: Optional[str] = None,
        currency: Optional[str] = None,
        sort: str = "asc",
        asof: Optional[str] = None,
    ) -> dict:
        """Retrieve historical price bars (OHLCV) for one or more stocks.

        When start is omitted, it is automatically computed as
        now minus the days/hours/minutes lookback.

        Args:
            symbols: Comma-separated tickers (e.g. "AAPL" or "AAPL,MSFT,GOOG").
            timeframe: Bar aggregation period — "1Min", "5Min", "15Min",
                       "30Min", "1Hour", "1Day", "1Week", or "1Month".
            start: Inclusive start time (RFC 3339). Omit to use relative lookback.
            end: Inclusive end time (RFC 3339). Omit for current time.
            days: Days to look back when start is omitted (default 5).
            hours: Additional hours in the lookback (default 0).
            minutes: Additional minutes in the lookback (default 0).
            limit: Max total data points returned across all symbols,
                   1–10000 (default 1000).
            adjustment: Price adjustment — "raw", "split", "dividend",
                        "spin-off", or "all". Comma-separated combos allowed
                        (e.g. "split,dividend"). Default "raw".
            feed: Data feed — "sip" (all US exchanges, default, paid),
                  "iex" (IEX only, free tier), "otc", or "boats".
            currency: Price currency (ISO 4217, e.g. "USD"). Default USD.
            sort: Timestamp sort order — "asc" (default) or "desc".
            asof: As-of date (YYYY-MM-DD) for point-in-time symbol mapping.
                  Useful for backtesting with historical ticker changes.
        """
        if start is None:
            start = _relative_start(days=days, hours=hours, minutes=minutes)
        return await _get(client, "/v2/stocks/bars", {
            "symbols": symbols,
            "timeframe": _normalize_timeframe(timeframe),
            "start": start,
            "end": end,
            "limit": limit,
            "adjustment": adjustment,
            "feed": feed,
            "currency": currency,
            "sort": sort,
            "asof": asof,
        })

    @server.tool(
        annotations={
            "title": "Get Stock Quotes",
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    async def get_stock_quotes(
        symbols: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        days: int = 0,
        hours: int = 0,
        minutes: int = 20,
        limit: int = 1000,
        feed: Optional[str] = None,
        currency: Optional[str] = None,
        sort: str = "asc",
        asof: Optional[str] = None,
    ) -> dict:
        """Retrieve historical bid/ask quotes (level 1) for one or more stocks.

        When start is omitted, it is automatically computed as
        now minus the days/hours/minutes lookback.

        Args:
            symbols: Comma-separated tickers (e.g. "AAPL" or "AAPL,MSFT").
            start: Inclusive start time (RFC 3339). Omit to use relative lookback.
            end: Inclusive end time (RFC 3339). Omit for current time.
            days: Days to look back when start is omitted (default 0).
            hours: Additional hours in the lookback (default 0).
            minutes: Additional minutes in the lookback (default 20).
            limit: Max total data points returned across all symbols,
                   1–10000 (default 1000).
            feed: Data feed — "sip" (all US exchanges, default, paid),
                  "iex" (free tier), "otc", or "boats".
                  Paper/free accounts must set feed="iex" to avoid 403 errors.
            currency: Price currency (ISO 4217). Default USD.
            sort: Timestamp sort order — "asc" (default) or "desc".
            asof: As-of date (YYYY-MM-DD) for point-in-time symbol mapping.
        """
        if start is None:
            start = _relative_start(days=days, hours=hours, minutes=minutes)
        return await _get(client, "/v2/stocks/quotes", {
            "symbols": symbols,
            "start": start,
            "end": end,
            "limit": limit,
            "feed": feed,
            "currency": currency,
            "sort": sort,
            "asof": asof,
        })

    @server.tool(
        annotations={
            "title": "Get Stock Trades",
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    async def get_stock_trades(
        symbols: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        days: int = 0,
        hours: int = 0,
        minutes: int = 20,
        limit: int = 1000,
        feed: Optional[str] = None,
        currency: Optional[str] = None,
        sort: str = "asc",
        asof: Optional[str] = None,
    ) -> dict:
        """Retrieve historical trade data for one or more stocks.

        When start is omitted, it is automatically computed as
        now minus the days/hours/minutes lookback.

        Args:
            symbols: Comma-separated tickers (e.g. "AAPL" or "AAPL,MSFT").
            start: Inclusive start time (RFC 3339). Omit to use relative lookback.
            end: Inclusive end time (RFC 3339). Omit for current time.
            days: Days to look back when start is omitted (default 0).
            hours: Additional hours in the lookback (default 0).
            minutes: Additional minutes in the lookback (default 20).
            limit: Max total data points returned across all symbols,
                   1–10000 (default 1000).
            feed: Data feed — "sip" (all US exchanges, default, paid),
                  "iex" (free tier), "otc", or "boats".
                  Paper/free accounts must set feed="iex" to avoid 403 errors.
            currency: Price currency (ISO 4217). Default USD.
            sort: Timestamp sort order — "asc" (default) or "desc".
            asof: As-of date (YYYY-MM-DD) for point-in-time symbol mapping.
        """
        if start is None:
            start = _relative_start(days=days, hours=hours, minutes=minutes)
        return await _get(client, "/v2/stocks/trades", {
            "symbols": symbols,
            "start": start,
            "end": end,
            "limit": limit,
            "feed": feed,
            "currency": currency,
            "sort": sort,
            "asof": asof,
        })

    # ── Crypto Historical Data ─────────────────────────────────────────────

    @server.tool(
        annotations={
            "title": "Get Crypto Bars",
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    async def get_crypto_bars(
        symbols: str,
        timeframe: str = "1Hour",
        start: Optional[str] = None,
        end: Optional[str] = None,
        days: int = 1,
        hours: int = 0,
        minutes: int = 0,
        limit: int = 1000,
        sort: str = "asc",
    ) -> dict:
        """Retrieve historical price bars (OHLCV) for one or more cryptocurrencies.

        When start is omitted, it is automatically computed as
        now minus the days/hours/minutes lookback.

        Args:
            symbols: Comma-separated crypto pairs (e.g. "BTC/USD" or
                     "BTC/USD,ETH/USD").
            timeframe: Bar aggregation period — "1Min", "5Min", "15Min",
                       "30Min", "1Hour", "1Day", "1Week", or "1Month".
            start: Inclusive start time (RFC 3339). Omit to use relative lookback.
            end: Inclusive end time (RFC 3339). Omit for current time.
            days: Days to look back when start is omitted (default 1).
            hours: Additional hours in the lookback (default 0).
            minutes: Additional minutes in the lookback (default 0).
            limit: Max total data points returned across all symbols,
                   1–10000 (default 1000).
            sort: Timestamp sort order — "asc" (default) or "desc".
        """
        if start is None:
            start = _relative_start(days=days, hours=hours, minutes=minutes)
        return await _get(client, "/v1beta3/crypto/us/bars", {
            "symbols": symbols,
            "timeframe": _normalize_timeframe(timeframe),
            "start": start,
            "end": end,
            "limit": limit,
            "sort": sort,
        })

    @server.tool(
        annotations={
            "title": "Get Crypto Quotes",
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    async def get_crypto_quotes(
        symbols: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        days: int = 0,
        hours: int = 0,
        minutes: int = 15,
        limit: int = 1000,
        sort: str = "asc",
    ) -> dict:
        """Retrieve historical bid/ask quotes for one or more cryptocurrencies.

        When start is omitted, it is automatically computed as
        now minus the days/hours/minutes lookback.

        Args:
            symbols: Comma-separated crypto pairs (e.g. "BTC/USD" or
                     "BTC/USD,ETH/USD").
            start: Inclusive start time (RFC 3339). Omit to use relative lookback.
            end: Inclusive end time (RFC 3339). Omit for current time.
            days: Days to look back when start is omitted (default 0).
            hours: Additional hours in the lookback (default 0).
            minutes: Additional minutes in the lookback (default 15).
            limit: Max total data points returned across all symbols,
                   1–10000 (default 1000).
            sort: Timestamp sort order — "asc" (default) or "desc".
        """
        if start is None:
            start = _relative_start(days=days, hours=hours, minutes=minutes)
        return await _get(client, "/v1beta3/crypto/us/quotes", {
            "symbols": symbols,
            "start": start,
            "end": end,
            "limit": limit,
            "sort": sort,
        })

    @server.tool(
        annotations={
            "title": "Get Crypto Trades",
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    async def get_crypto_trades(
        symbols: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        days: int = 0,
        hours: int = 0,
        minutes: int = 15,
        limit: int = 1000,
        sort: str = "asc",
    ) -> dict:
        """Retrieve historical trade data for one or more cryptocurrencies.

        When start is omitted, it is automatically computed as
        now minus the days/hours/minutes lookback.

        Args:
            symbols: Comma-separated crypto pairs (e.g. "BTC/USD" or
                     "BTC/USD,ETH/USD").
            start: Inclusive start time (RFC 3339). Omit to use relative lookback.
            end: Inclusive end time (RFC 3339). Omit for current time.
            days: Days to look back when start is omitted (default 0).
            hours: Additional hours in the lookback (default 0).
            minutes: Additional minutes in the lookback (default 15).
            limit: Max total data points returned across all symbols,
                   1–10000 (default 1000).
            sort: Timestamp sort order — "asc" (default) or "desc".
        """
        if start is None:
            start = _relative_start(days=days, hours=hours, minutes=minutes)
        return await _get(client, "/v1beta3/crypto/us/trades", {
            "symbols": symbols,
            "start": start,
            "end": end,
            "limit": limit,
            "sort": sort,
        })
```

---

## File: `src/alpaca_mcp_server/specs/trading-api.json`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/src/alpaca_mcp_server/specs/trading-api.json`

```json
{"openapi":"3.0.0","info":{"title":"Trading API","description":"Alpaca's Trading API is a modern platform for algorithmic trading.","version":"2.0.1","contact":{"name":"Alpaca Support","email":"support@alpaca.markets","url":"https://alpaca.markets/support"},"termsOfService":"https://s3.amazonaws.com/files.alpaca.markets/disclosures/library/TermsAndConditions.pdf"},"servers":[{"url":"https://paper-api.alpaca.markets","description":"Paper"},{"url":"https://api.alpaca.markets","description":"Live"}],"tags":[{"name":"Accounts"},{"name":"Assets"},{"name":"Corporate Actions"},{"name":"Orders"},{"name":"Positions"},{"name":"Portfolio History"},{"name":"Watchlists"},{"name":"Account Configurations"},{"name":"Account Activities"},{"name":"Calendar"},{"name":"Clock"},{"name":"Crypto Funding"},{"name":"Crypto Perpetuals Funding (Beta)"},{"name":"Crypto Perpetuals Account Vitals (Beta)"},{"name":"Crypto Perpetuals Leverage (Beta)"}],"paths":{"/v2/account":{"get":{"summary":"Get Account","tags":["Accounts"],"responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Account"},"example":{"id":"1d9eed04-be39-4e01-9b84-a48ac5bbafcf","admin_configurations":{},"user_configurations":null,"account_number":"PALPACA_123","status":"ACTIVE","crypto_status":"ACTIVE","currency":"USD","buying_power":"245432.61","regt_buying_power":"245432.61","daytrading_buying_power":"0","options_buying_power":"122716.305","effective_buying_power":"245432.61","non_marginable_buying_power":"122086.5","bod_dtbp":0,"cash":"122086.5","accrued_fees":"0","pending_transfer_in":"0","portfolio_value":"123346.11","pattern_day_trader":true,"trading_blocked":false,"transfers_blocked":false,"account_blocked":false,"created_at":"2023-01-01T18:20:20.272275Z","trade_suspended_by_user":false,"multiplier":"2","shorting_enabled":true,"equity":"123346.11","last_equity":"122011.09751111286868","long_market_value":"1259.61","short_market_value":"0","position_market_value":"1259.61","initial_margin":"629.8","maintenance_margin":"377.88","last_maintenance_margin":"480.73","sma":"123369.74","daytrade_count":0,"balance_asof":"2023-09-27","crypto_tier":1,"options_trading_level":2,"intraday_adjustments":"0","pending_reg_taf_fees":"0"}}}}},"operationId":"getAccount","parameters":[],"description":"Returns your account details."}},"/v2/orders":{"post":{"tags":["Orders"],"summary":"Create an Order","operationId":"postOrder","description":"Places a new order for the given account. An order request may be rejected if the account is not authorized for trading, or if the tradable balance is insufficient to fill the order.","requestBody":{"required":true,"content":{"application/json":{"schema":{"type":"object","properties":{"symbol":{"type":"string","x-stoplight":{"id":"ss5ik56n2ju1s"},"description":"symbol, asset ID, or currency pair to identify the asset to trade, required for all order classes except for `mleg`."},"qty":{"type":"string","x-stoplight":{"id":"o73n1g4sdbylf"},"description":"number of shares to trade. Can be fractionable for only market and day order types. Required for `mleg` order class, represents the number of units to trade of this strategy."},"notional":{"type":"string","x-stoplight":{"id":"0pqrvqmmsladt"},"description":"dollar amount to trade. Cannot work with `qty`. Can only work for market order types and day for time in force."},"side":{"$ref":"#/components/schemas/OrderSide"},"type":{"$ref":"#/components/schemas/OrderType"},"time_in_force":{"$ref":"#/components/schemas/TimeInForce"},"limit_price":{"type":"string","x-stoplight":{"id":"0pz01a130upwd"},"description":"Required if type is `limit` or `stop_limit`.\nIn case of `mleg`, the limit_price parameter is expressed with the following notation:\n- A positive value indicates a debit, representing a cost or payment to be made.\n- A negative value signifies a credit, reflecting an amount to be received."},"stop_price":{"type":"string","x-stoplight":{"id":"ctaacyol2uvib"},"description":"required if type is `stop` or `stop_limit`"},"trail_price":{"type":"string","x-stoplight":{"id":"eje00dcpg2s0c"},"description":"this or `trail_percent` is required if type is `trailing_stop`"},"trail_percent":{"type":"string","x-stoplight":{"id":"l72my4e1qz36r"},"description":"this or `trail_price` is required if type is `trailing_stop`"},"extended_hours":{"type":"boolean","x-stoplight":{"id":"gqhf6gxwkrzr8"},"description":"(default) false. If true, order will be eligible to execute in premarket/afterhours. Only works with type limit and time_in_force day."},"client_order_id":{"type":"string","x-stoplight":{"id":"duyztdwi66wfk"},"description":"A unique identifier for the order. Automatically generated if not sent. (<= 128 characters)","maxLength":128},"order_class":{"$ref":"#/components/schemas/OrderClass"},"legs":{"type":"array","description":"list of order legs (<= 4)","items":{"$ref":"#/components/schemas/MLegOrderLeg"},"maxLength":4},"take_profit":{"type":"object","description":"Takes in a string/number value for limit_price","properties":{"limit_price":{"type":"string","format":"decimal","example":"3.14"}}},"stop_loss":{"description":"Takes in string/number values for stop_price and limit_price","type":"object","properties":{"stop_price":{"type":"string","format":"decimal","example":"3.14"},"limit_price":{"type":"string","format":"decimal","example":"3.14"}}},"position_intent":{"$ref":"#/components/schemas/PositionIntent"},"advanced_instructions":{"$ref":"#/components/schemas/AdvancedInstructions"}},"required":["type","time_in_force"]},"examples":{"Equity":{"summary":"Buy an equity stock","value":{"symbol":"AAPL","qty":"2","side":"buy","type":"limit","limit_price":"150","time_in_force":"gtc"}},"Options":{"summary":"Buy an option contract","value":{"symbol":"AAPL250620C00100000","qty":"2","side":"buy","type":"limit","limit_price":"10","time_in_force":"day"}},"MultilegOptions":{"summary":"Option Call spread","value":{"order_class":"mleg","type":"limit","limit_price":"10","qty":"3","time_in_force":"day","legs":[{"side":"buy","position_intent":"buy_to_open","symbol":"AAPL241213C00250000","ratio_qty":"3"},{"side":"sell","position_intent":"sell_to_open","symbol":"AAPL241213C00260000","ratio_qty":"1"}]}},"Crypto":{"summary":"Buy a crypto coin","value":{"symbol":"ETH/USD","qty":"0.02","side":"buy","type":"limit","limit_price":"2100","time_in_force":"gtc"}}}}},"description":""},"parameters":[],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Order"},"examples":{"Equity":{"$ref":"#/components/examples/EquityOrderResponse"},"Options":{"$ref":"#/components/examples/OptionOrderResponse"},"Crypto":{"$ref":"#/components/examples/CryptoOrderResponse"},"MultilegOptions":{"$ref":"#/components/examples/MultilegOptionsOrderResponse"}}}}},"403":{"description":"Forbidden\n\nBuying power or shares is not sufficient."},"422":{"description":"Unprocessable\n\nInput parameters are not recognized."}}},"get":{"tags":["Orders"],"summary":"Get All Orders","parameters":[{"schema":{"type":"string","enum":["open","closed","all"],"example":"open"},"in":"query","name":"status","description":"Order status to be queried. open, closed or all. Defaults to open."},{"schema":{"type":"integer"},"in":"query","name":"limit","description":"The maximum number of orders in response. Defaults to 50 and max is 500."},{"schema":{"type":"string"},"in":"query","name":"after","description":"The response will include only ones submitted after this timestamp (exclusive.)"},{"schema":{"type":"string"},"in":"query","name":"until","description":"The response will include only ones submitted until this timestamp (exclusive.)"},{"schema":{"type":"string","enum":["asc","desc"]},"in":"query","name":"direction","description":"The chronological order of response based on the submission time. asc or desc. Defaults to desc."},{"schema":{"type":"boolean"},"in":"query","name":"nested","description":"If true, the result will roll up multi-leg orders under the legs field of primary order."},{"schema":{"type":"string"},"in":"query","name":"symbols","description":"A comma-separated list of symbols to filter by (ex. “AAPL,TSLA,MSFT”). A currency pair is required for crypto orders (ex. “BTCUSD,BCHUSD,LTCUSD,ETCUSD”)."},{"schema":{"type":"string"},"in":"query","name":"side","description":"Filters down to orders that have a matching side field set."},{"name":"asset_class","in":"query","description":"A comma-separated list of asset classes, the response will include only orders in the specified asset classes. By specifying `us_option` as the class, you can query option orders by underlying symbol using the symbols parameter.","schema":{"type":"array","items":{"type":"string","enum":["us_equity","us_option","crypto","all"]}}},{"schema":{"type":"string"},"in":"query","name":"before_order_id","description":"Return orders submitted before the order with this ID (exclusive).\nMutually exclusive with `after_order_id`. Do not combine with `after`/`until`.\n"},{"schema":{"type":"string"},"in":"query","name":"after_order_id","description":"Return orders submitted after the order with this ID (exclusive).\nMutually exclusive with `before_order_id`. Do not combine with `after`/`until`.\n"}],"responses":{"200":{"description":"Successful response\n\nAn array of Order objects","content":{"application/json":{"schema":{"type":"array","items":{"$ref":"#/components/schemas/Order"}},"examples":{"Equity":{"$ref":"#/components/examples/EquityOrderResponse"},"Options":{"$ref":"#/components/examples/OptionOrderResponse"},"Crypto":{"$ref":"#/components/examples/CryptoOrderResponse"},"MultilegOptions":{"$ref":"#/components/examples/MultilegOptionsOrderResponse"}}}}}},"operationId":"getAllOrders","description":"Retrieves a list of orders for the account, filtered by the supplied query parameters.","x-internal":false},"delete":{"tags":["Orders"],"summary":"Delete All Orders","parameters":[],"responses":{"207":{"description":"Multi-Status with body.\n\nan array of objects that include the order id and http status code for each status request.","content":{"application/json":{"schema":{"type":"array","items":{"$ref":"#/components/schemas/CanceledOrderResponse"}}}}},"500":{"description":"Failed to cancel order."}},"operationId":"deleteAllOrders","description":"Attempts to cancel all open orders. A response will be provided for each order that is attempted to be cancelled. If an order is no longer cancelable, the server will respond with status 500 and reject the request."}},"/v2/orders:by_client_order_id":{"get":{"tags":["Orders"],"summary":"Get Order by Client Order ID","description":"Retrieves a single order specified by the client order ID.","operationId":"getOrderByClientOrderId","parameters":[{"name":"client_order_id","in":"query","required":true,"description":"The client-assigned order ID.","schema":{"type":"string"}}],"responses":{"200":{"description":"Successfully retrieved the order matching the client_order_id.","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Order"}}}}}}},"/v2/orders/{order_id}":{"get":{"tags":["Orders"],"summary":"Get Order by ID","parameters":[{"schema":{"type":"boolean"},"in":"query","name":"nested","description":"If true, the result will roll up multi-leg orders under the legs field of primary order."}],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Order"},"examples":{"Equity":{"$ref":"#/components/examples/EquityOrderResponse"},"Options":{"$ref":"#/components/examples/OptionOrderResponse"},"Crypto":{"$ref":"#/components/examples/CryptoOrderResponse"},"MultilegOptions":{"$ref":"#/components/examples/MultilegOptionsOrderResponse"}}}}}},"operationId":"getOrderByOrderID","description":"Retrieves a single order for the given order_id."},"patch":{"tags":["Orders"],"summary":"Replace Order by ID","description":"Replaces a single order with updated parameters. Each parameter overrides the corresponding attribute of the existing order. The other attributes remain the same as the existing order.\n\nA success return code from a replaced order does NOT guarantee the existing open order has been replaced. If the existing open order is filled before the replacing (new) order reaches the execution venue, the replacing (new) order is rejected, and these events are sent in the trade_updates stream channel.\n\nWhile an order is being replaced, buying power is reduced by the larger of the two orders that have been placed (the old order being replaced, and the newly placed order to replace it). If you are replacing a buy entry order with a higher limit price than the original order, the buying power is calculated based on the newly placed order. If you are replacing it with a lower limit price, the buying power is calculated based on the old order.\n\nNote: Order cannot be replaced when the status is `accepted`, `pending_new`, `pending_cancel` or `pending_replace`.\n","requestBody":{"required":true,"content":{"application/json":{"schema":{"$ref":"#/components/schemas/PatchOrderRequest"}}}},"responses":{"200":{"description":"Successful response\n\nThe new Order object with the new order ID.","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Order"}}}}},"operationId":"patchOrderByOrderId"},"delete":{"tags":["Orders"],"summary":"Delete Order by ID","parameters":[],"responses":{"204":{"description":"No Content"},"422":{"description":"The order status is not cancelable."}},"operationId":"deleteOrderByOrderID","description":"Attempts to cancel an Open Order. If the order is no longer cancelable, the request will be rejected with status 422; otherwise accepted with return status 204."},"parameters":[{"schema":{"type":"string","format":"uuid"},"name":"order_id","in":"path","required":true,"description":"order id"}]},"/v2/positions":{"get":{"tags":["Positions"],"summary":"All Open Positions","parameters":[],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"type":"array","items":{"$ref":"#/components/schemas/Position"}}}}}},"operationId":"getAllOpenPositions","description":"The positions API provides information about an account’s current open positions. The response will include information such as cost basis, shares traded, and market value, which will be updated live as price information is updated. Once a position is closed, it will no longer be queryable through this API\n\nRetrieves a list of the account’s open positions"},"delete":{"tags":["Positions"],"summary":"Close All Positions","parameters":[{"schema":{"type":"boolean"},"in":"query","name":"cancel_orders","description":"If true is specified, cancel all open orders before liquidating all positions."}],"responses":{"207":{"description":"Multi-Status with body.\n\nan array of PositionClosed responses","content":{"application/json":{"schema":{"type":"array","items":{"$ref":"#/components/schemas/PositionClosedReponse"}}}}},"500":{"description":"Failed to liquidate"}},"operationId":"deleteAllOpenPositions","description":"Closes (liquidates) all of the account’s open long and short positions. A response will be provided for each order that is attempted to be cancelled. If an order is no longer cancelable, the server will respond with status 500 and reject the request."}},"/v2/positions/{symbol_or_asset_id}":{"get":{"tags":["Positions"],"summary":"Get an Open Position","description":"Retrieves the account’s open position for the given symbol or assetId.","parameters":[],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Position"}}}}},"operationId":"getOpenPosition"},"delete":{"tags":["Positions"],"summary":"Close a Position","parameters":[{"schema":{"type":"number"},"in":"query","name":"qty","description":"the number of shares to liquidate. Can accept up to 9 decimal points. Cannot work with percentage"},{"schema":{"type":"number"},"in":"query","name":"percentage","description":"percentage of position to liquidate. Must be between 0 and 100. Would only sell fractional if position is originally fractional. Can accept up to 9 decimal points. Cannot work with qty"}],"responses":{"200":{"description":"Successful response\n\nReturns the order created to close out this position","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Order"}}}}},"description":"Closes (liquidates) the account’s open position for the given symbol. Works for both long and short positions.","operationId":"deleteOpenPosition"},"parameters":[{"schema":{"type":"string"},"name":"symbol_or_asset_id","in":"path","required":true,"description":"symbol or assetId"}]},"/v2/positions/{symbol_or_contract_id}/exercise":{"post":{"tags":["Positions"],"summary":"Exercise an Options Position","description":"This endpoint enables users to exercise a held option contract, converting it into the underlying asset based on the specified terms.\nAll available held shares of this option contract will be exercised.\nBy default, Alpaca will automatically exercise in-the-money (ITM) contracts at expiry.\nExercise requests will be processed immediately once received. Exercise requests submitted between market close and midnight will be rejected to avoid any confusion about when the exercise will settle.\nTo cancel an exercise request or to submit a Do-not-exercise (DNE) instruction, you can use the do-not-exercise endpoint or contact our support team.","operationId":"optionExercise","parameters":[{"schema":{"type":"string","format":"uuid"},"name":"symbol_or_contract_id","in":"path","required":true,"description":"Option contract symbol or ID."}],"requestBody":{"description":"Empty request body","content":{}},"responses":{"200":{"description":"Successful Response\n\nExercise instruction successfully submitted."},"403":{"description":"Forbidden\n\nAvailable position quantity is not sufficient.","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Error"},"examples":{"No Available Position":{"value":{"code":40310000,"message":"no available position for the specified contract"}},"Short Position":{"value":{"code":40310001,"message":"cannot exercise short position"}}}}}},"422":{"description":"Invalid Parameters.\n\nOne or more parameters provided are invalid.","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Error"},"examples":{"Invalid Symbol":{"value":{"code":42210000,"message":"invalid symbol"}}}}}}}}},"/v2/positions/{symbol_or_contract_id}/do-not-exercise":{"post":{"tags":["Positions"],"summary":"Do Not Exercise an Options Position","description":"This endpoint enables users to submit a do-not-exercise (DNE) instruction for a held option contract, preventing automatic exercise at expiry.\nBy default, Alpaca will automatically exercise in-the-money (ITM) contracts at expiry. This endpoint allows users to override that behavior.\nTo override this behavior and submit an exercise instruction, please contact our support team.","operationId":"optionDoNotExercise","parameters":[{"schema":{"type":"string","format":"uuid"},"name":"symbol_or_contract_id","in":"path","required":true,"description":"Option contract symbol or ID."}],"requestBody":{"description":"Empty request body","content":{}},"responses":{"200":{"description":"Successful Response\n\nDo-not-exercise instruction successfully submitted."},"403":{"description":"Forbidden\n\nAvailable position quantity is not sufficient or no position found.","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Error"},"examples":{"No Available Position":{"value":{"code":40310000,"message":"no available position for the specified contract"}},"Short Position":{"value":{"code":40310001,"message":"cannot submit DNE for short position"}}}}}},"422":{"description":"Invalid Parameters.\n\nOne or more parameters provided are invalid.","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Error"},"examples":{"Invalid Symbol":{"value":{"code":42210000,"message":"invalid symbol"}}}}}}}}},"/v2/account/portfolio/history":{"get":{"tags":["Portfolio History"],"summary":"Get Account Portfolio History","parameters":[{"schema":{"type":"string"},"in":"query","name":"period","description":"The duration of the data in `number` + `unit` format, such as 1D, where `unit` can be D for day, W for week, M for month and A for year. Defaults to 1M.\n\nOnly two of `start`, `end` and `period` can be specified at the same time.\n\nFor intraday timeframes (\\<1D) only 30 days or less can be queried, for 1D resolutions there is no such limit, data is available since the\ncreation of the account.\n"},{"schema":{"type":"string"},"in":"query","name":"timeframe","description":"The resolution of time window. 1Min, 5Min, 15Min, 1H, or 1D. If omitted, 1Min for less than 7 days period,\n15Min for less than 30 days, or otherwise 1D.\n\nFor queries with longer than 30 days of `period`, the system only accepts 1D as `timeframe`.\n"},{"schema":{"type":"string","enum":["market_hours","extended_hours","continuous"],"default":"market_hours"},"in":"query","name":"intraday_reporting","description":"For intraday resolutions (<1D) this specifies which timestamps to return data points for:\n\nAllowed values are:\n- **market_hours**\n\n  Only timestamps for the core equity trading hours are returned (usually 9:30am to 4:00pm, trading days only)\n\n- **extended_hours**\n\n  Returns timestamps for the whole session including extended hours (usually 4:00am to 8:00pm, trading days only)\n\n- **continuous**\n\n  Returns price data points 24/7 (for off-session times too). To calculate the equity values we are using the following prices:\n\n  Between 4:00am and 10:00pm on trading days the valuation will be calculated based on the last trade (extended hours and normal hours respectively).\n\n  After 10:00pm, until the next session open the equities will be valued at their official closing price on the primary exchange.\n"},{"schema":{"type":"string","format":"date-time","example":"2021-03-16T18:38:01Z"},"in":"query","name":"start","description":"The timestamp the data is returned starting from in RFC3339 format (including timezone specification). Defaults to `end` minus `period`\n\nIf provided, the `start` value is always normalized to the `America/New_York` timezone and adjusted to the nearest `timeframe` interval, e.g. seconds are always truncated and the time is rounded backwards to the nearest interval of `1Min`, `5Min`, `15Min`, or `1H`.\n\nIf `timeframe=1D` and `start` is not a valid trading date, find the next available trading date. For example, if `start` occurs on Saturday or Sunday after converting to the America/New_York timezone, `start` is adjusted to the first weekday that is not a market holiday (e.g. Monday).\n\nIf `timeframe` is less than `1D` and `intraday_reporting` is not `continuous`, `start` always reflects the beginning of a market session. If `start` is between midnight and the end (inclusive) of an active trading day, `start` is set to the beginning of the session on the specified day. Otherwise, if `start` occurs outside of the market session, the next available market date is used.\n\nFor example, when `intraday_reporting=market_hours` and `start=2023-10-19T23:59:59-04:00`, the provided `start` date occurs outside of the regular market session. The effective `start` timestamp is adjusted to the beginning of the next session: `2023-10-20T09:30:00-04:00`\n\n`start` may be be combined with one of `end` or `period`.\n\nProviding all of `start`, `end`, and `period` is invalid.\n"},{"schema":{"type":"string","enum":["no_reset","per_day"],"default":"per_day"},"in":"query","name":"pnl_reset","description":"`pnl_reset` defines how we are calculating the baseline values for Profit And Loss (pnl) for queries with `timeframe` less than 1D (intraday queries).\n\nThe default behavior for intraday queries is that we reset the pnl value to the previous day's closing equity for each **trading** day.\n\nIn case of crypto (given its continuous nature), this might not be desired: specifying \"no_reset\" disables this behavior and all pnl values\nreturned will be relative to the closing equity of the previous trading day.\n\nFor 1D resolution all PnL values are calculated relative to the `base_value`, we are not resetting the base value.\n"},{"schema":{"type":"string","format":"date-time","example":"2021-03-16T18:38:01Z"},"in":"query","name":"end","description":"The timestamp the data is returned up to in RFC3339 format (including timezone specification). Defaults to the current time.\n\nIf provided, the `end` value is always normalized to the `America/New_York` timezone and adjusted to the nearest `timeframe` interval, e.g. seconds are always truncated and the time is rounded backwards to the nearest interval of `1Min`, `5Min`, `15Min`, or `1H`.\n\nWhen `intraday_reporting` is either `market_hours` or `extended_hours`, the `end` value is adjusted to not occur after session close on the specified day. For example if the `intraday_reporting` is `extended_hours`, and the timestamp specified is `2023-10-19T21:33:00-04:00`, `end` is adjusted to `2023-10-19T20:00:00-04:00`.\n\n`end` may be combined with `start` or `period`.\n\nProviding all of `start`, `end`, and `period` is invalid.\n"},{"schema":{"type":"string"},"in":"query","name":"extended_hours","description":"**deprecated**: Users are strongly advised to **rely on the `intraday_reporting` query parameter** for better control\nof the reporting range.\n\nIf true, include extended hours in the result. This is effective only for timeframe less than 1D.\n"},{"schema":{"type":"string"},"in":"query","name":"cashflow_types","description":"The cashflow activities to include in the report. One of 'ALL', 'NONE', or a comma-separated list of activity types."}],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/PortfolioHistory"}}}}},"operationId":"getAccountPortfolioHistory","description":"Returns timeseries data about equity and profit/loss (P/L) of the account in requested timespan."}},"/v2/watchlists":{"get":{"tags":["Watchlists"],"summary":"Get All Watchlists","parameters":[],"responses":{"200":{"description":"Successful response","content":{"application/json":{"examples":{"example-1":{"value":[{"id":"3174d6df-7726-44b4-a5bd-7fda5ae6e009","account_id":"abe25343-a7ba-4255-bdeb-f7e013e9ee5d","created_at":"2022-01-31T21:49:05.14628Z","updated_at":"2022-01-31T21:49:05.14628Z","name":"Primary Watchlist"}]}},"schema":{"type":"array","items":{"$ref":"#/components/schemas/WatchlistWithoutAsset"}}}}}},"operationId":"getWatchlists","description":"Returns the list of watchlists registered under the account."},"post":{"tags":["Watchlists"],"summary":"Create Watchlist","description":"Create a new watchlist with initial set of assets.","requestBody":{"required":true,"content":{"application/json":{"schema":{"$ref":"#/components/schemas/UpdateWatchlistRequest"}}}},"parameters":[],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Watchlist"}}}}},"operationId":"postWatchlist"}},"/v2/watchlists/{watchlist_id}":{"get":{"tags":["Watchlists"],"summary":"Get Watchlist by ID","parameters":[],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Watchlist"}}}}},"operationId":"getWatchlistById","description":"Returns a watchlist identified by the ID."},"put":{"tags":["Watchlists"],"summary":"Update Watchlist By Id","requestBody":{"content":{"application/json":{"schema":{"$ref":"#/components/schemas/UpdateWatchlistRequest"}}}},"parameters":[],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Watchlist"}}}}},"operationId":"updateWatchlistById","description":"Update the name and/or content of watchlist"},"post":{"tags":["Watchlists"],"summary":"Add Asset to Watchlist","requestBody":{"content":{"application/json":{"schema":{"type":"object","properties":{"symbol":{"type":"string","x-stoplight":{"id":"wb0v0f7q0ms5e"},"description":"the symbol name to add to the watchlist"}}}}}},"parameters":[],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Watchlist"}}}}},"operationId":"addAssetToWatchlist","description":"Append an asset for the symbol to the end of watchlist asset list"},"delete":{"tags":["Watchlists"],"summary":"Delete Watchlist By Id","parameters":[],"responses":{"204":{"description":"No Content"},"404":{"description":"Watchlist not found"}},"operationId":"deleteWatchlistById","description":"Delete a watchlist. This is a permanent deletion."},"parameters":[{"schema":{"type":"string","format":"uuid"},"name":"watchlist_id","in":"path","required":true,"description":"watchlist id"}]},"/v2/watchlists:by_name":{"get":{"tags":["Watchlists"],"summary":"Get Watchlist by Name","parameters":[{"schema":{"type":"string"},"in":"query","name":"name","required":true,"description":"name of the watchlist"}],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Watchlist"}}}}},"operationId":"getWatchlistByName","description":"You can also call GET, PUT, POST and DELETE with watchlist name with another endpoint /v2/watchlists:by_name and query parameter name=<watchlist_name>, instead of /v2/watchlists/{watchlist_id} endpoints\n\nReturns a watchlist by name"},"put":{"tags":["Watchlists"],"summary":"Update Watchlist By Name","requestBody":{"content":{"application/json":{"schema":{"$ref":"#/components/schemas/UpdateWatchlistRequest"}}}},"parameters":[{"schema":{"type":"string"},"in":"query","name":"name","required":true,"description":"name of the watchlist"}],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Watchlist"}}}}},"operationId":"updateWatchlistByName","description":"Update the name and/or content of watchlist"},"post":{"tags":["Watchlists"],"summary":"Add Asset to Watchlist By Name","requestBody":{"content":{"application/json":{"schema":{"type":"object","properties":{"symbol":{"type":"string","x-stoplight":{"id":"w4vw4ifmq7o9e"},"description":"the symbol name to add to the watchlist"}}}}}},"parameters":[{"schema":{"type":"string"},"in":"query","name":"name","required":true,"description":"name of the watchlist"}],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Watchlist"}}}}},"operationId":"addAssetToWatchlistByName","description":"Append an asset for the symbol to the end of watchlist asset list"},"delete":{"tags":["Watchlists"],"summary":"Delete Watchlist By Name","parameters":[{"schema":{"type":"string"},"in":"query","name":"name","required":true,"description":"name of the watchlist"}],"responses":{"204":{"description":"No Content"}},"operationId":"deleteWatchlistByName","description":"Delete a watchlist. This is a permanent deletion."},"parameters":[]},"/v2/watchlists/{watchlist_id}/{symbol}":{"delete":{"tags":["Watchlists"],"summary":"Delete Symbol from Watchlist","parameters":[],"responses":{"200":{"content":{"application/json":{"schema":{"$ref":"#/components/schemas/Watchlist"}}},"description":"Returns the updated watchlist"}},"operationId":"removeAssetFromWatchlist","description":"Delete one entry for an asset by symbol name"},"parameters":[{"schema":{"type":"string","format":"uuid"},"name":"watchlist_id","in":"path","required":true,"description":"Watchlist ID"},{"schema":{"type":"string"},"name":"symbol","in":"path","required":true,"description":"symbol name to remove from the watchlist content"}]},"/v2/account/configurations":{"get":{"tags":["Account Configurations"],"summary":"Get Account Configurations","parameters":[],"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/AccountConfigurations"}}}}},"operationId":"getAccountConfig","description":"gets the current account configuration values"},"patch":{"tags":["Account Configurations"],"summary":"Account Configurations","parameters":[],"requestBody":{"content":{"application/json":{"schema":{"$ref":"#/components/schemas/AccountConfigurations"}}}},"responses":{"200":{"description":"Successful response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/AccountConfigurations"}}}}},"operationId":"patchAccountConfig","description":"Updates and returns the current account configuration values"}},"/v2/account/activities":{"get":{"summary":"Retrieve Account Activities","tags":["Account Activities"],"responses":{"200":{"description":"returns an array of Account activities","content":{"application/json":{"schema":{"type":"array","items":{"anyOf":[{"$ref":"#/components/schemas/TradingActivities"},{"$ref":"#/components/schemas/NonTradeActivities"}],"description":"Will be a mix of TradingActivity or NonTradeActivity objects based on what is passed in the activity_types parameter"}}}}}},"operationId":"getAccountActivities","description":"Returns a list of activities\n\nNotes:\n* Pagination is handled using the `page_token` and `page_size` parameters.\n* `page_token` represents the ID of the last item on your current page of results.\n   For example, if the ID of the last activity in your first response is `20220203000000000::045b3b8d-c566-4bef-b741-2bf598dd6ae7`, you would pass that value as `page_token` to retrieve the next page of results.","parameters":[{"name":"activity_types","in":"query","schema":{"type":"array","items":{"$ref":"#/components/schemas/ActivityType"}},"style":"form","explode":false,"description":"A comma-separated list of activity types used to filter the results."},{"name":"category","in":"query","schema":{"type":"string","enum":["trade_activity","non_trade_activity"]},"description":"The activity category. Cannot be used with \"activity_types\" parameter."},{"name":"date","in":"query","schema":{"type":"string","format":"date-time"},"description":"Filter activities by the activity date. Both formats YYYY-MM-DD and YYYY-MM-DDTHH:MM:SSZ are supported."},{"name":"until","in":"query","schema":{"type":"string","format":"date-time"},"description":"Get activities created before this date. Both formats YYYY-MM-DD and YYYY-MM-DDTHH:MM:SSZ are supported."},{"name":"after","in":"query","schema":{"type":"string","format":"date-time"},"description":"Get activities created after this date. Both formats YYYY-MM-DD and YYYY-MM-DDTHH:MM:SSZ are supported."},{"name":"direction","in":"query","schema":{"type":"string","enum":["asc","desc"],"default":"desc","example":"desc"},"description":"The chronological order of response based on the activity datetime."},{"name":"page_size","in":"query","schema":{"type":"integer","minimum":1,"maximum":100,"default":100},"description":"The maximum number of entries to return in the response."},{"name":"page_token","in":"query","schema":{"type":"string"},"description":"Token used for pagination. Provide the ID of the last activity from the last page to retrieve the next set of results."}]}},"/v2/account/activities/{activity_type}":{"parameters":[{"schema":{"type":"string"},"name":"activity_type","in":"path","description":"The activity type you want to view entries for. A list of valid activity types can be found at the bottom of this page.","required":true}],"get":{"summary":"Retrieve Account Activities of Specific Type","tags":["Account Activities"],"responses":{"200":{"description":"returns an array of Account activities","content":{"application/json":{"schema":{"type":"array","items":{"oneOf":[{"$ref":"#/components/schemas/TradingActivities"},{"$ref":"#/components/schemas/NonTradeActivities"}],"description":"Will be one of a TradingActivity or NonTradeActivity based on activity_type used in path"}}}}}},"operationId":"getAccountActivitiesByActivityType","description":"Returns account activity entries for a specific type of activity.","parameters":[{"name":"date","in":"query","schema":{"type":"string","format":"date-time"},"description":"Filter activities by the activity date. Both formats YYYY-MM-DD and YYYY-MM-DDTHH:MM:SSZ are supported."},{"name":"until","in":"query","schema":{"type":"string","format":"date-time"},"description":"Get activities created before this date. Both formats YYYY-MM-DD and YYYY-MM-DDTHH:MM:SSZ are supported."},{"name":"after","in":"query","schema":{"type":"string","format":"date-time"},"description":"Get activities created after this date. Both formats YYYY-MM-DD and YYYY-MM-DDTHH:MM:SSZ are supported."},{"name":"direction","in":"query","schema":{"type":"string","enum":["asc","desc"],"default":"desc","example":"desc"},"description":"The chronological order of response based on the activity datetime."},{"name":"page_size","in":"query","schema":{"type":"integer","minimum":1,"maximum":100,"default":100},"description":"The maximum number of entries to return in the response."},{"name":"page_token","in":"query","schema":{"type":"string"},"description":"Token used for pagination. Provide the ID of the last activity from the last page to retrieve the next set of results."}]}},"/v2/calendar":{"get":{"summary":"Get US Market Calendar","tags":["Calendar"],"parameters":[{"$ref":"#/components/parameters/legacy_start"},{"$ref":"#/components/parameters/legacy_end"},{"$ref":"#/components/parameters/legacy_date_type"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/legacy_public_calendar_resp"}}}},"400":{"$ref":"#/components/responses/400"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"LegacyCalendar","description":"The calendar API serves the full list of market days from 1970 to 2029. It can also be queried by specifying a start and/or end time to narrow down the results. In addition to the dates, the response also contains the specific open and close times for the market days, taking into account early closures.\n"}},"/v2/clock":{"get":{"summary":"Get US Market Clock","tags":["Calendar"],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/legacy_clock"}}}},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"LegacyClock","description":"The clock API serves the current market timestamp, whether or not the market is currently open, as well as the times of the next market open and close.\n"}},"/v3/calendar/{market}":{"get":{"summary":"Get Market Calendar","tags":["Calendar"],"parameters":[{"$ref":"#/components/parameters/market"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/timezone"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/public_calendar_resp"}}}},"400":{"$ref":"#/components/responses/400"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"Calendar","description":"This endpoint returns the market calendar."}},"/v3/clock":{"get":{"summary":"Get Market Clock","tags":["Calendar"],"parameters":[{"$ref":"#/components/parameters/markets"},{"$ref":"#/components/parameters/time"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/clock_resp"}}}},"400":{"$ref":"#/components/responses/400"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"Clock","description":"This API serves information about multiple markets: the current time, if it's a market day, the current phase of the market, etc.\n"}},"/v2/assets":{"get":{"summary":"Get Assets","tags":["Assets"],"responses":{"200":{"description":"An array of asset objects","content":{"application/json":{"schema":{"type":"array","items":{"$ref":"#/components/schemas/Assets"}}}}}},"operationId":"get-v2-assets","description":"The assets API serves as the master list of assets available for trade and data consumption from Alpaca. Assets are sorted by asset class, exchange and symbol.","parameters":[{"schema":{"type":"string"},"in":"query","name":"status","description":"e.g. “active”. By default, all statuses are included."},{"schema":{"type":"string"},"in":"query","name":"asset_class","description":"Defaults to us_equity."},{"schema":{"type":"string"},"in":"query","name":"exchange","description":"Optional AMEX, ARCA, BATS, NYSE, NASDAQ, NYSEARCA or OTC"},{"schema":{"type":"array","items":{"type":"string","enum":["ptp_no_exception","ptp_with_exception","ipo","has_options","options_late_close","fractional_eh_enabled","overnight_tradable","overnight_halted"]},"example":["ptp_no_exception","ipo"],"default":[]},"in":"query","name":"attributes","description":"Comma separated values to query for more than one attribute. Assets which have any of the given attributes will be included.\n\nSupported values:\n- `ptp_no_exception`: Asset is a Publicly Traded Partnership (PTP) without a qualified notice; non-U.S. customers may incur 10% withholding on gross proceeds as per IRS guidance, and are blocked from being purchased by default.\n- `ptp_with_exception`: Users can open positions in these PTPs without general restrictions.\n- `ipo`: Accepting limit orders only before the stock begins trading on the secondary market.\n- `has_options`: The underlying equity has listed options available on the platform. Note: if the equity had inactive/expired contracts in the past, this will still show up.\n- `options_late_close`: Indicates the underlying asset's options contracts close at 4:15pm ET instead of the standard 4:00pm ET.\n- `fractional_eh_enabled`: Indicates the asset accepts fractional orders during extended hours sessions (pre-market, post-market, and overnight if enabled).\n- `overnight_tradable`: Asset is eligible for overnight (24x5) trading in supported venues on the platform.\n- `overnight_halted`: Asset is not eligible for overnight trading but is currently halted/blocked for overnight sessions due to risk, corporate action, compliance, or venue constraints.","explode":false}]}},"/v2/assets/{symbol_or_asset_id}":{"parameters":[{"schema":{"type":"string"},"name":"symbol_or_asset_id","in":"path","required":true,"description":"symbol or assetId. CUSIP is also accepted for US equities."}],"get":{"summary":"Get an Asset by ID or Symbol","tags":["Assets"],"responses":{"200":{"description":"An Asset object","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Assets"}}}},"404":{"description":"Not Found"}},"operationId":"get-v2-assets-symbol_or_asset_id","description":"Get the asset model for a given symbol or asset_id. The symbol or asset_id should be passed in as a path parameter.\n\n**Note**: For crypto, the symbol has to follow old symbology, e.g. BTCUSD.\n\n**Note**: For coin pairs, the symbol should be separated by a slash (/), e.g. BTC/USDT. Since the slash is a special character in HTTP, use the URL encoded version instead, e.g. /v2/assets/BTC%2FUSDT"}},"/v2/options/contracts":{"get":{"summary":"Get Option Contracts","description":"This endpoint allows you to retrieve a list of option contracts based on various filtering criteria.\nBy default only active contracts that expire before the upcoming weekend are returned.\n","tags":["Assets"],"operationId":"get-options-contracts","parameters":[{"name":"underlying_symbols","in":"query","description":"Filter contracts by one or more underlying symbols.","schema":{"type":"string"},"example":"AAPL,SPY"},{"name":"show_deliverables","in":"query","description":"Include deliverables array in the response.","schema":{"type":"boolean"},"example":true},{"name":"status","in":"query","description":"Filter contracts by status (active/inactive). By default only active contracts are returned.","schema":{"type":"string","enum":["active","inactive"]},"example":"active"},{"name":"expiration_date","in":"query","description":"Filter contracts by the exact expiration date (format: YYYY-MM-DD).","schema":{"type":"string","format":"date"},"example":"2025-06-20"},{"name":"expiration_date_gte","in":"query","description":"Filter contracts with expiration date greater than or equal to the specified date.","schema":{"type":"string","format":"date"},"example":"2025-06-20"},{"name":"expiration_date_lte","in":"query","description":"Filter contracts with expiration date less than or equal to the specified date. By default this is set to the next weekend.","schema":{"type":"string","format":"date"},"example":"2025-06-20"},{"name":"root_symbol","in":"query","description":"Filter contracts by the root symbol.","schema":{"type":"string"},"example":"AAPL"},{"name":"type","in":"query","description":"Filter contracts by the type (call/put).","schema":{"type":"string","enum":["call","put"]},"example":"call"},{"name":"style","in":"query","description":"Filter contracts by the style (american/european).","schema":{"type":"string","enum":["american","european"]},"example":"american"},{"name":"strike_price_gte","in":"query","description":"Filter contracts with strike price greater than or equal to the specified value.","schema":{"type":"number"},"example":50},{"name":"strike_price_lte","in":"query","description":"Filter contracts with strike price less than or equal to the specified value.","schema":{"type":"number"},"example":100},{"$ref":"#/components/parameters/PageToken"},{"name":"limit","in":"query","description":"The number of contracts to limit per page (default=100, max=10000).","schema":{"type":"integer"},"example":100},{"name":"ppind","in":"query","schema":{"type":"boolean"},"example":"true","description":"The ppind(Penny Program Indicator) field indicates whether an option contract is eligible for penny price increments,\nwith `true` meaning it is part of the Penny Program and `false` meaning it is not."}],"responses":{"200":{"description":"Successful Response.","content":{"application/json":{"schema":{"type":"object","properties":{"option_contracts":{"type":"array","items":{"$ref":"#/components/schemas/OptionContract"}},"next_page_token":{"$ref":"#/components/schemas/NextPageToken"}},"required":["option_contracts"]}}}}}}},"/v2/options/contracts/{symbol_or_id}":{"parameters":[{"schema":{"type":"string"},"name":"symbol_or_id","in":"path","required":true,"description":"symbol or contract ID"}],"get":{"summary":"Get an option contract by ID or Symbol","description":"Get an option contract by symbol or contract ID. The symbol or id should be passed in as a path parameter.","tags":["Assets"],"operationId":"get-option-contract-symbol_or_id","responses":{"200":{"description":"An option contract","content":{"application/json":{"schema":{"$ref":"#/components/schemas/OptionContract"}}}},"404":{"description":"Not Found","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Error"},"examples":{"Contract Not Found":{"value":{"code":40410000,"message":"option contract TSLA231110C00021000 not found"}}}}}}}}},"/v2/assets/fixed_income/us_treasuries":{"get":{"summary":"Get US treasuries","tags":["Assets"],"parameters":[{"name":"subtype","in":"query","schema":{"$ref":"#/components/schemas/treasury_subtype"}},{"name":"bond_status","in":"query","schema":{"$ref":"#/components/schemas/bond_status"}},{"name":"cusips","description":"A comma-separated list of CUSIPs with a limit of 1000.","in":"query","schema":{"type":"string"},"example":"912810UG1,912797PM3"},{"name":"isins","description":"A comma-separated list of ISINs with a limit of 1000.","in":"query","schema":{"type":"string"},"example":"US912810UG12,US912797PM34"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/us_treasuries_resp"}}}},"400":{"$ref":"#/components/responses/400"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"UsTreasuries","description":"Serves the list of US treasuries available at Alpaca. The response is sorted by ISIN."}},"/v2/assets/fixed_income/us_corporates":{"get":{"summary":"Get US corporates","tags":["Assets"],"parameters":[{"name":"bond_status","in":"query","schema":{"$ref":"#/components/schemas/bond_status"}},{"name":"isins","description":"A comma-separated list of ISINs with a limit of 1000.","in":"query","schema":{"type":"string"},"example":"US912810UG12,US912797PM34"},{"name":"cusips","description":"A comma-separated list of CUSIPs with a limit of 1000.","in":"query","schema":{"type":"string"},"example":"912810UG1,912797PM3"},{"name":"tickers","description":"A comma-separated list of tickers with a limit of 1000.","in":"query","schema":{"type":"string"},"example":"BAC,MSFT"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/us_corporates_resp"}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"UsCorporates","description":"Serves the list of US corporates available at Alpaca. The response is sorted by ISIN."}},"/v2/corporate_actions/announcements/{id}":{"parameters":[{"schema":{"type":"string"},"name":"id","in":"path","required":true,"description":"The corporate announcement’s id"}],"get":{"summary":"Retrieve a Specific Announcement","deprecated":true,"tags":["Corporate Actions"],"responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","x-examples":{"Example 1":{"id":"be3c368a-4c7c-4384-808e-f02c9f5a8afe","corporate_actions_id":"F58684224_XY37","ca_type":"Dividend","ca_sub_type":"DIV","initiating_symbol":"MLLAX","initiating_original_cusip":5.5275e+105,"target_symbol":"MLLAX","target_original_cusip":5.5275e+105,"declaration_date":"2021-01-05","expiration_date":"2021-01-12","record_date":"2021-01-13","payable_date":"2021-01-14","cash":"0.018","old_rate":"1","new_rate":"1"}},"properties":{"id":{"type":"string"},"corporate_actions_id":{"type":"string"},"ca_type":{"type":"string","description":"A comma-delimited list of Dividend, Merger, Spinoff, or Split."},"ca_sub_type":{"type":"string"},"initiating_symbol":{"type":"string"},"initiating_original_cusip":{"type":"string"},"target_symbol":{"type":"string"},"target_original_cusip":{"type":"string"},"declaration_date":{"type":"string"},"expiration_date":{"type":"string"},"record_date":{"type":"string"},"payable_date":{"type":"string"},"cash":{"type":"string"},"old_rate":{"type":"string"},"new_rate":{"type":"string"}}}}}}},"operationId":"get-v2-corporate_actions-announcements-id","description":"This endpoint is deprecated, please use [the new corporate actions endpoint](https://docs.alpaca.markets/reference/corporateactions-1) instead."}},"/v2/corporate_actions/announcements":{"get":{"summary":"Retrieve Announcements","deprecated":true,"tags":["Corporate Actions"],"responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"array","items":{"type":"object","properties":{"id":{"type":"string"},"corporate_actions_id":{"type":"string"},"ca_type":{"type":"string"},"ca_sub_type":{"type":"string"},"initiating_symbol":{"type":"string"},"initiating_original_cusip":{"type":"string"},"target_symbol":{"type":"string"},"target_original_cusip":{"type":"string"},"declaration_date":{"type":"string"},"expiration_date":{"type":"string"},"record_date":{"type":"string"},"payable_date":{"type":"string"},"cash":{"type":"string"},"old_rate":{"type":"string"},"new_rate":{"type":"string"},"corporate_action_id":{"type":"string"},"ex_date":{"type":"string"}}},"x-examples":{"Example 1":[{"id":"be3c368a-4c7c-4384-808e-f02c9f5a8afe","corporate_actions_id":"F58684224_XY37","ca_type":"Dividend","ca_sub_type":"DIV","initiating_symbol":"MLLAX","initiating_original_cusip":5.5275e+105,"target_symbol":"MLLAX","target_original_cusip":5.5275e+105,"declaration_date":"2021-01-05","expiration_date":"2021-01-12","record_date":"2021-01-13","payable_date":"2021-01-14","cash":"0.018","old_rate":"1","new_rate":"1"},{"corporate_action_id":"48251W104_AD21","ca_type":"Dividend","ca_sub_type":"cash","initiating_symbol":"KKR","initiating_original_cusip":"G52830109","target_symbol":"KKR","target_original_cusip":"G52830109","declaration_date":"2021-11-01","ex_date":"2021-11-12","record_date":"2021-11-15","payable_date":"2021-11-30","cash":"0.145","old_rate":"1","new_rate":"1"}]}}}}}},"operationId":"get-v2-corporate_actions-announcements","description":"This endpoint is deprecated, please use [the new corporate actions endpoint](https://docs.alpaca.markets/reference/corporateactions-1) instead.","parameters":[{"schema":{"type":"string"},"in":"query","name":"ca_types","description":"A comma-delimited list of Dividend, Merger, Spinoff, or Split.","required":true},{"schema":{"type":"string"},"in":"query","name":"since","description":"The start (inclusive) of the date range when searching corporate action announcements. This should follow the YYYY-MM-DD format. The date range is limited to 90 days.","required":true},{"schema":{"type":"string"},"in":"query","name":"until","description":"The end (inclusive) of the date range when searching corporate action announcements. This should follow the YYYY-MM-DD format. The date range is limited to 90 days.","required":true},{"schema":{"type":"string"},"in":"query","name":"symbol","description":"The symbol of the company initiating the announcement."},{"schema":{"type":"string"},"in":"query","name":"cusip","description":"The CUSIP of the company initiating the announcement."},{"schema":{"type":"string"},"in":"query","name":"date_type","description":"declaration_date, ex_date, record_date, or payable_date"}]}},"/v2/wallets":{"parameters":[{"name":"asset","in":"query","description":"Filter by crypto asset symbol, e.g. BTC, ETH, USDT. If specified and no wallet exists, one will be created.","schema":{"type":"string"}},{"name":"network","in":"query","description":"Optional network identifier. Use to request wallets for a specific network when asset is a multi-chain crypto asset. If not specified, the default network (ethereum) will be used.","schema":{"type":"string","enum":["ethereum","solana"]}}],"get":{"tags":["Crypto Funding"],"summary":"Retrieve Crypto Funding Wallets","description":"Lists wallets for the account given in the path parameter. If an asset is specified and no wallet for the account and asset pair exists one will be created. If no asset is specified only existing wallets will be listed for the account. An account may have at most one wallet per asset.","operationId":"listCryptoFundingWallets","responses":{"200":{"description":"A single wallet object if an asset is specified or an array of wallet objects if no asset is specified","content":{"application/json":{"schema":{"$ref":"#/components/schemas/CryptoWallet"}}}}}}},"/v2/wallets/transfers":{"get":{"tags":["Crypto Funding"],"summary":"Retrieve Crypto Funding Transfers","description":"Returns an array of all transfers associated with the given account across all wallets.","operationId":"listCryptoFundingTransfers","responses":{"200":{"description":"An array of transfer objects","content":{"application/json":{"schema":{"$ref":"#/components/schemas/CryptoTransfer"}}}}}},"post":{"tags":["Crypto Funding"],"summary":"Request a New Withdrawal","operationId":"createCryptoTransferForAccount","description":"Creates a withdrawal request. Note that outgoing withdrawals must be sent to a whitelisted address and you must whitelist addresses at least 24 hours in advance. If you attempt to withdraw funds to a non-whitelisted address then the transfer will be rejected.","requestBody":{"required":true,"content":{"application/json":{"schema":{"$ref":"#/components/schemas/CreateCryptoTransferRequest"}}}},"responses":{"200":{"description":"Successfully requested a transfer.","content":{"application/json":{"schema":{"$ref":"#/components/schemas/CryptoTransfer"}}}}}}},"/v2/wallets/transfers/{transfer_id}":{"parameters":[{"schema":{"type":"string"},"name":"transfer_id","in":"path","required":true,"description":"The crypto transfer to retrieve"}],"get":{"tags":["Crypto Funding"],"summary":"Retrieve a Crypto Funding Transfer","description":"Returns a specific wallet transfer by passing into the query the transfer_id.","operationId":"getCryptoFundingTransfer","responses":{"200":{"description":"A single crypto transfer object","content":{"application/json":{"schema":{"$ref":"#/components/schemas/CryptoTransfer"}}}}}}},"/v2/wallets/whitelists":{"get":{"tags":["Crypto Funding"],"summary":"An array of whitelisted addresses","operationId":"listWhitelistedAddress","responses":{"200":{"description":"An array of whitelisted objects","content":{"application/json":{"schema":{"$ref":"#/components/schemas/WhitelistedAddress"}}}}}},"post":{"tags":["Crypto Funding"],"summary":"Request a new whitelisted address","operationId":"createWhitelistedAddress","requestBody":{"required":true,"content":{"application/json":{"schema":{"type":"object","properties":{"address":{"type":"string","description":"The address to be whitelisted"},"asset":{"type":"string","description":"Symbol of underlying asset for the whitelisted address"}}}}}},"responses":{"200":{"description":"Successfully requested a whitelisted address","content":{"application/json":{"schema":{"$ref":"#/components/schemas/WhitelistedAddress"}}}}}}},"/v2/wallets/whitelists/{whitelisted_address_id}":{"parameters":[{"schema":{"type":"string"},"name":"whitelisted_address_id","in":"path","required":true,"description":"The whitelisted address to delete"}],"delete":{"tags":["Crypto Funding"],"summary":"Delete a whitelisted address","operationId":"deleteWhitelistedAddress","responses":{"200":{"description":"Successfully deleted a whitelisted address"}}}},"/v2/wallets/fees/estimate":{"get":{"tags":["Crypto Funding"],"summary":"Returns the estimated gas fee for a proposed transaction.","operationId":"getCryptoTransferEstimate","parameters":[{"name":"asset","in":"query","description":"The asset for the proposed transaction","schema":{"type":"string"}},{"name":"from_address","in":"query","description":"The originating address of the proposed transaction","schema":{"type":"string"}},{"name":"to_address","in":"query","description":"The destination address of the proposed transaction","schema":{"type":"string"}},{"name":"amount","in":"query","description":"The amount, denoted in the specified asset, of the proposed transaction","schema":{"type":"string"}}],"responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","properties":{"fee":{"type":"string"}}}}}}}}},"/v2/perpetuals/wallets":{"parameters":[{"name":"asset","in":"query","schema":{"type":"string"}}],"get":{"tags":["Crypto Perpetuals Funding (Beta)"],"summary":"Retrieve Crypto Funding Wallets","description":"Lists wallets for the account given in the path parameter. If an asset is specified and no wallet for the account and asset pair exists one will be created. If no asset is specified only existing wallets will be listed for the account. An account may have at most one wallet per asset","operationId":"listCryptoPerpFundingWallets","responses":{"200":{"description":"A single wallet object if an asset is specified or an array of wallet objects if no asset is specified","content":{"application/json":{"schema":{"$ref":"#/components/schemas/CryptoWallet"}}}}}}},"/v2/perpetuals/wallets/transfers":{"get":{"tags":["Crypto Perpetuals Funding (Beta)"],"summary":"Retrieve Crypto Funding Transfers","description":"Returns an array of all transfers associated with the given account across all wallets","operationId":"listCryptoPerpFundingTransfers","responses":{"200":{"description":"An array of transfer objects","content":{"application/json":{"schema":{"$ref":"#/components/schemas/CryptoTransfer"}}}}}},"post":{"tags":["Crypto Perpetuals Funding (Beta)"],"summary":"Request a New Withdrawal","operationId":"createCryptoPerpTransferForAccount","description":"Creates a withdrawal request. Note that outgoing withdrawals must be sent to a whitelisted address and you must whitelist addresses at least 24 hours in advance. If you attempt to withdraw funds to a non-whitelisted address then the transfer will be rejected","requestBody":{"required":true,"content":{"application/json":{"schema":{"$ref":"#/components/schemas/CreateCryptoTransferRequest"}}}},"responses":{"200":{"description":"Successfully requested a transfer.","content":{"application/json":{"schema":{"$ref":"#/components/schemas/CryptoTransfer"}}}}}}},"/v2/perpetuals/wallets/transfers/{transfer_id}":{"parameters":[{"schema":{"type":"string"},"name":"transfer_id","in":"path","required":true,"description":"The crypto transfer to retrieve"}],"get":{"tags":["Crypto Perpetuals Funding (Beta)"],"summary":"Retrieve a Crypto Funding Transfer","description":"Returns a specific wallet transfer by passing into the query the transfer_id","operationId":"getCryptoPerpFundingTransfer","responses":{"200":{"description":"A single crypto transfer object","content":{"application/json":{"schema":{"$ref":"#/components/schemas/CryptoTransfer"}}}}}}},"/v2/perpetuals/wallets/whitelists":{"get":{"tags":["Crypto Perpetuals Funding (Beta)"],"summary":"An array of whitelisted addresses","operationId":"listWhitelistedPerpAddress","responses":{"200":{"description":"An array of whitelisted objects","content":{"application/json":{"schema":{"$ref":"#/components/schemas/WhitelistedAddress"}}}}}},"post":{"tags":["Crypto Perpetuals Funding (Beta)"],"summary":"Request a new whitelisted address","operationId":"createWhitelistedPerpAddress","requestBody":{"required":true,"content":{"application/json":{"schema":{"type":"object","properties":{"address":{"type":"string","description":"The address to be whitelisted"},"asset":{"type":"string","description":"Symbol of underlying asset for the whitelisted address"}}}}}},"responses":{"200":{"description":"Successfully requested a whitelisted address","content":{"application/json":{"schema":{"$ref":"#/components/schemas/WhitelistedAddress"}}}}}}},"/v2/perpetuals/wallets/whitelists/{whitelisted_address_id}":{"parameters":[{"schema":{"type":"string"},"name":"whitelisted_address_id","in":"path","required":true,"description":"The whitelisted address to delete"}],"delete":{"tags":["Crypto Perpetuals Funding (Beta)"],"summary":"Delete a whitelisted address","operationId":"deleteWhitelistedPerpAddress","responses":{"200":{"description":"Successfully deleted a whitelisted address"}}}},"/v2/perpetuals/wallets/fees/estimate":{"get":{"tags":["Crypto Perpetuals Funding (Beta)"],"summary":"Returns the estimated gas fee for a proposed transaction","operationId":"getCryptoPerpTransferEstimate","parameters":[{"name":"asset","in":"query","description":"The asset for the proposed transaction","schema":{"type":"string"}},{"name":"from_address","in":"query","description":"The originating address of the proposed transaction","schema":{"type":"string"}},{"name":"to_address","in":"query","description":"The destination address of the proposed transaction","schema":{"type":"string"}},{"name":"amount","in":"query","description":"The amount, denoted in the specified asset, of the proposed transaction","schema":{"type":"string"}}],"responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","properties":{"fee":{"type":"string"}}}}}}}}},"/v2/perpetuals/leverage":{"get":{"tags":["Crypto Perpetuals Leverage (Beta)"],"summary":"Get Account Leverage for an Asset","description":"Retrieves the current leverage setting for the crypto perpetuals account, specific to a given underlying asset. To use this endpoint, provide the 'symbol' of the asset as a query parameter. The system will return the asset's symbol and the integer value representing the current leverage applied to it within the account","operationId":"getCryptoPerpAccountLeverage","parameters":[{"name":"symbol","in":"query","description":"Symbol of underlying asset","schema":{"type":"string"}}],"responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","properties":{"symbol":{"type":"string","description":"Symbol of underlying asset"},"leverage":{"type":"integer"}}}}}}}},"post":{"tags":["Crypto Perpetuals Leverage (Beta)"],"summary":"Set Account Leverage for an Asset","description":"Updates the leverage for the crypto perpetuals account for a specific underlying asset. Provide the 'symbol' of the asset and the desired 'leverage' (as an integer) using query parameters. The system will return the asset's symbol and the newly set leverage value upon successful update","operationId":"setCryptoPerpAccountLeverage","parameters":[{"name":"symbol","in":"query","description":"Symbol of underlying asset","schema":{"type":"string"}},{"name":"leverage","in":"query","description":"Leverage for the underlying asset","schema":{"type":"integer"}}],"responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","properties":{"symbol":{"type":"string","description":"Symbol of underlying asset"},"leverage":{"type":"integer"}}}}}}}}},"/v2/perpetuals/account_vitals":{"get":{"tags":["Crypto Perpetuals Account Vitals (Beta)"],"summary":"Retrieve Account Vitals","description":"Fetches key financial metrics for the crypto perpetuals account, providing a snapshot of its current status by detailing the relationship between the user's positions and their collateral. The response includes maintenance margin (USDT), collateral balance (USDT), total collateral (USDT), and profit/loss (USDT)","operationId":"getCryptoPerpAccountVitals","responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","properties":{"maintenance_margin":{"type":"number","description":"MaintenanceMargin (USDT) is the sum of each position's individual maintenance margin"},"collateral_balance":{"type":"integer","description":"CollateralBalance (USDT) is the sum of the unrealized PnL on each position plus TotalCollateral"},"total_collateral":{"type":"integer","description":"TotalCollateral (USDT) across all collateral assets"},"profit_loss":{"type":"integer","description":"ProfitAndLoss (USDT) is the net of realized and unrealized PnL across all positions"}}}}}}}}}},"components":{"securitySchemes":{"API_Key":{"name":"APCA-API-KEY-ID","type":"apiKey","in":"header","description":""},"API_Secret":{"name":"APCA-API-SECRET-KEY","type":"apiKey","in":"header","description":""}},"parameters":{"PageToken":{"name":"page_token","in":"query","required":false,"description":"Used for pagination, this token retrieves the next page of results. It is obtained from the response of the preceding page when additional pages are available.","schema":{"type":"string","example":"MA=="}},"legacy_start":{"name":"start","in":"query","schema":{"type":"string","format":"date-time","x-go-type":"legacyTime"},"description":"The first date to retrieve data for (inclusive)."},"legacy_end":{"name":"end","in":"query","schema":{"type":"string","format":"date-time","x-go-type":"legacyTime"},"description":"The last date to retrieve data for (inclusive)."},"legacy_date_type":{"name":"date_type","in":"query","schema":{"type":"string","enum":["TRADING","SETTLEMENT"]},"description":"Indicates what start and end mean. Default: TRADING. If TRADING is specified, returns a calendar whose trading date matches start, end. If SETTLEMENT is specified, returns the calendar whose settlement date matches start and end.\n"},"market":{"name":"market","in":"path","required":true,"schema":{"$ref":"#/components/schemas/market"}},"start":{"name":"start","in":"query","required":false,"schema":{"type":"string","format":"date"},"description":"The first date to retrieve data for (inclusive). Default: today.\n","example":"2025-01-01"},"end":{"name":"end","in":"query","required":false,"schema":{"type":"string","format":"date"},"description":"The last date to retrieve data for (inclusive). Default: one week from the start date.\n","example":"2030-01-01"},"timezone":{"name":"timezone","in":"query","required":false,"schema":{"type":"string","enum":["UTC"]},"description":"Timezone of the times. Default: the timezone of the market.\n"},"markets":{"name":"markets","description":"Comma-separated list of markets. Available market codes:\n- BMO\n- BNYM\n- BOATS\n- CEUX\n- CHIX\n- HKEX\n- IEX\n- IEXG\n- LSE\n- NASDAQ\n- NYSE\n- OCEA\n- OPRA\n- OTC\n- OTCM\n- SIFMA\n- TADAWUL\n- XETR\n- XETRA\n- XHKG\n- XLON\n- XNAS\n- XNYS\n- XSAU\n","in":"query","schema":{"type":"string"},"example":"NYSE,LSE"},"time":{"name":"time","description":"Instead of the current time, use this time for the clock.","in":"query","required":false,"schema":{"type":"string","format":"date-time"}}},"schemas":{"Account":{"title":"Account","type":"object","description":"The account API serves important information related to an account, including account status, funds available for trade, funds available for withdrawal, and various flags relevant to an account’s ability to trade. An account maybe be blocked for just for trades (trades_blocked flag) or for both trades and transfers (account_blocked flag) if Alpaca identifies the account to engaging in any suspicious activity. Also, in accordance with FINRA’s pattern day trading rule, an account may be flagged for pattern day trading (pattern_day_trader flag), which would inhibit an account from placing any further day-trades. Please note that cryptocurrencies are not eligible assets to be used as collateral for margin accounts and will require the asset be traded using cash only.\n","x-examples":{"example-1":{"account_blocked":false,"account_number":"010203ABCD","buying_power":"262113.632","cash":"-23140.2","created_at":"2019-06-12T22:47:07.99658Z","currency":"USD","daytrade_count":0,"balance_asof":"2023-09-27","daytrading_buying_power":"262113.632","equity":"103820.56","id":"e6fe16f3-64a4-4921-8928-cadf02f92f98","initial_margin":"63480.38","last_equity":"103529.24","last_maintenance_margin":"38000.832","long_market_value":"126960.76","maintenance_margin":"38088.228","multiplier":"4","pattern_day_trader":false,"portfolio_value":"103820.56","regt_buying_power":"80680.36","options_buying_power":"40340.18","short_market_value":"0","shorting_enabled":true,"sma":"0","status":"ACTIVE","trade_suspended_by_user":false,"trading_blocked":false,"transfers_blocked":false,"options_approved_level":2,"options_trading_level":1,"intraday_adjustments":"0","pending_reg_taf_fees":"0"}},"properties":{"id":{"type":"string","description":"Account Id.\n","format":"uuid"},"account_number":{"type":"string","description":"Account number."},"status":{"$ref":"#/components/schemas/AccountStatus"},"currency":{"type":"string","description":"USD\n","example":"USD"},"cash":{"description":"Cash Balance\n","type":"string"},"portfolio_value":{"description":"Total value of cash + holding positions (This field is deprecated. It is equivalent to the equity field.)","type":"string"},"non_marginable_buying_power":{"description":"Current available non-margin dollar buying power","type":"string","x-stoplight":{"id":"z0ydzt6yqegll"}},"accrued_fees":{"description":"The fees collected.","type":"string","x-stoplight":{"id":"b1gospbwoz961"}},"pending_transfer_in":{"description":"Cash pending transfer in.","type":"string","x-stoplight":{"id":"83ckvzqu3jewp"}},"pending_transfer_out":{"description":"Cash pending transfer out.","type":"string","x-stoplight":{"id":"gkxijaueofvdg"}},"pattern_day_trader":{"type":"boolean","description":"Whether or not the account has been flagged as a pattern day trader"},"trade_suspended_by_user":{"type":"boolean","description":"User setting. If true, the account is not allowed to place orders."},"trading_blocked":{"type":"boolean","description":"If true, the account is not allowed to place orders.\n"},"transfers_blocked":{"type":"boolean","description":"If true, the account is not allowed to request money transfers."},"account_blocked":{"type":"boolean","description":"If true, the account activity by user is prohibited."},"created_at":{"type":"string","description":"Timestamp this account was created at\n","format":"date-time"},"shorting_enabled":{"type":"boolean","description":"Flag to denote whether or not the account is permitted to short"},"long_market_value":{"description":"Real-time MtM value of all long positions held in the account\n","type":"string"},"short_market_value":{"description":"Real-time MtM value of all short positions held in the account","type":"string"},"equity":{"description":"Cash + long_market_value + short_market_value","type":"string"},"last_equity":{"description":"Equity as of previous trading day at 16:00:00 ET","type":"string"},"multiplier":{"description":"Buying power multiplier that represents account margin classification; valid values 1 (standard limited margin account with 1x buying power), 2 (reg T margin account with 2x intraday and overnight buying power; this is the default for all non-PDT accounts with $2,000 or more equity), 4 (PDT account with 4x intraday buying power and 2x reg T overnight buying power)","type":"string"},"buying_power":{"description":"Current available $ buying power; If multiplier = 4, this is your daytrade buying power which is calculated as (last_equity - (last) maintenance_margin) * 4; If multiplier = 2, buying_power = max(equity – initial_margin,0) * 2; If multiplier = 1, buying_power = cash","type":"string"},"initial_margin":{"description":"Reg T initial margin requirement (continuously updated value)","type":"string"},"maintenance_margin":{"description":"Maintenance margin requirement (continuously updated value)","type":"string"},"sma":{"type":"string","description":"Value of special memorandum account (will be used at a later date to provide additional buying_power)"},"daytrade_count":{"type":"integer","description":"The current number of daytrades that have been made in the last 5 trading days (inclusive of today)"},"balance_asof":{"type":"string","example":"2021-04-01","description":"The date of the snapshot for `last_*` fields"},"last_maintenance_margin":{"description":"Your maintenance margin requirement on the previous trading day","type":"string"},"daytrading_buying_power":{"description":"Your buying power for day trades (continuously updated value)","type":"string"},"regt_buying_power":{"description":"Your buying power under Regulation T (your excess equity - equity minus margin value - times your margin multiplier)\n","type":"string"},"options_buying_power":{"description":"Your buying power for options trading\n","type":"string"},"options_approved_level":{"type":"integer","example":3,"description":"The options trading level that was approved for this account.\n0=disabled, 1=Covered Call/Cash-Secured Put, 2=Long Call/Put, 3=Spreads/Straddles.\n","enum":[0,1,2,3]},"options_trading_level":{"type":"integer","example":3,"description":"The effective options trading level of the account.\nThis is the minimum between account options_approved_level and account configurations max_options_trading_level.\n0=disabled, 1=Covered Call/Cash-Secured Put, 2=Long Call/Put, 3=Spreads/Straddles.\n","enum":[0,1,2,3]},"intraday_adjustments":{"type":"string","example":"0","description":"The intraday adjustment by non_trade_activities such as fund deposit/withdraw.\n"},"pending_reg_taf_fees":{"type":"string","description":"Pending regulatory fees for the account.\n"}},"required":["id","status"]},"AccountStatus":{"type":"string","title":"AccountStatus","enum":["ONBOARDING","SUBMISSION_FAILED","SUBMITTED","ACCOUNT_UPDATED","APPROVAL_PENDING","ACTIVE","REJECTED"],"description":"An enum representing the various possible account status values.\n\nMost likely, the account status is ACTIVE unless there is any problem. The account status may get in ACCOUNT_UPDATED when personal information is being updated from the dashboard, in which case you may not be allowed trading for a short period of time until the change is approved.\n\n- ONBOARDING\n  The account is onboarding.\n- SUBMISSION_FAILED\n  The account application submission failed for some reason.\n- SUBMITTED\n  The account application has been submitted for review.\n- ACCOUNT_UPDATED\n  The account information is being updated.\n- APPROVAL_PENDING\n  The final account approval is pending.\n- ACTIVE\n  The account is active for trading.\n- REJECTED\n  The account application has been rejected.","x-examples":{"example-1":"ACTIVE"},"example":"ACTIVE"},"AccountConfigurations":{"title":"AccountConfigurations","type":"object","x-examples":{"example-1":{"dtbp_check":"entry","trade_confirm_email":"all","suspend_trade":false,"no_shorting":false,"fractional_trading":true,"max_margin_multiplier":"4","pdt_check":"entry","disable_overnight_trading":false}},"description":"The account configuration API provides custom configurations about your trading account settings. These configurations control various allow you to modify settings to suit your trading needs.","properties":{"dtbp_check":{"type":"string","description":"both, entry, or exit. Controls Day Trading Margin Call (DTMC) checks.","enum":["both","entry","exit"]},"trade_confirm_email":{"type":"string","description":"all or none. If none, emails for order fills are not sent."},"suspend_trade":{"type":"boolean","description":"If true, new orders are blocked."},"no_shorting":{"type":"boolean","description":"If true, account becomes long-only mode."},"fractional_trading":{"type":"boolean","description":"If true, account is able to participate in fractional trading"},"max_margin_multiplier":{"type":"string","description":"Can be \"1\", \"2\", or \"4\""},"max_options_trading_level":{"type":"integer","description":"The desired maximum options trading level. 0=disabled, 1=Covered Call/Cash-Secured Put, 2=Long Call/Put, 3=Spreads/Straddles.","enum":[0,1,2,3]},"pdt_check":{"type":"string","example":"entry","description":"`both`, `entry`, or `exit`. If entry orders will be rejected on entering a position if it could result in PDT being set for the account. exit will reject exiting orders if they would result in PDT being set."},"ptp_no_exception_entry":{"type":"boolean","x-stoplight":{"id":"8qvrtnzouzp80"},"description":"If set to true then Alpaca will accept orders for PTP symbols with no exception. Default is false."},"disable_overnight_trading":{"type":"boolean","description":"If true, overnight trading is disabled."}}},"TradingActivities":{"title":"AccountTradingActivities","type":"object","x-examples":{"example-1":{"id":"20220202135509981::2d7be4ff-d1f3-43e9-856a-0f5cf5c5088e","activity_type":"FILL","transaction_time":"2022-02-02T18:55:09.981482Z","type":"fill","price":"174.78","qty":"2","side":"buy","symbol":"AAPL","leaves_qty":"0","order_id":"b5abe576-6a8a-49f3-a353-46b72c1ccae9","cum_qty":"2","order_status":"filled"}},"properties":{"activity_type":{"$ref":"#/components/schemas/ActivityType"},"id":{"type":"string","description":"An id for the activity. Always in “::” format. Can be sent as page_token in requests to facilitate the paging of results."},"cum_qty":{"description":"The cumulative quantity of shares involved in the execution.","type":"string"},"leaves_qty":{"type":"string","description":"For partially_filled orders, the quantity of shares that are left to be filled.\n"},"price":{"type":"string","description":"The per-share price that the trade was executed at."},"qty":{"type":"string","description":"The number of shares involved in the trade execution."},"side":{"type":"string","description":"buy or sell"},"symbol":{"type":"string","description":"The symbol of the security being traded.","example":"AAPL"},"transaction_time":{"type":"string","description":"The time at which the execution occurred.","format":"date-time"},"order_id":{"type":"string","description":"The id for the order that filled.","format":"uuid"},"type":{"type":"string","description":"fill or partial_fill","enum":["fill","partial_fill"],"example":"fill"},"order_status":{"$ref":"#/components/schemas/OrderStatus"}}},"NonTradeActivities":{"title":"AccountNonTradeActivities","type":"object","properties":{"activity_type":{"$ref":"#/components/schemas/ActivityType"},"activity_sub_type":{"$ref":"#/components/schemas/ActivitySubType"},"id":{"type":"string","description":"An ID for the activity, always in “::” format. Can be sent as page_token in requests to facilitate the paging of results."},"date":{"type":"string","description":"The date on which the activity occurred or on which the transaction associated with the activity settled.","format":"date-time"},"net_amount":{"type":"string","description":"The net amount of money (positive or negative) associated with the activity."},"symbol":{"type":"string","description":"The symbol of the security involved with the activity. Not present for all activity types."},"cusip":{"type":"string","description":"The CUSIP of the security involved with the activity. Not present for all activity types."},"qty":{"type":"string","description":"For dividend activities, the number of shares that contributed to the payment. Not present for other activity types.\n"},"per_share_amount":{"type":"string","description":"For dividend activities, the average amount paid per share. Not present for other activity types."},"group_id":{"type":"string","description":"ID used to link activities who share a sibling relationship."},"status":{"type":"string","description":"The activity status.","enum":["executed","correct","canceled"]},"created_at":{"type":"string","format":"date-time","description":"Valid only for non-trading activity types. Null for trading activites."}},"x-examples":{"example-1":{"activity_type":"DIV","activity_sub_type":"SDIV","id":"20190801011955195::5f596936-6f23-4cef-bdf1-3806aae57dbf","date":"2019-08-01","net_amount":"1.02","symbol":"T","qty":"2","per_share_amount":"0.51","status":"executed","created_at":"2021-05-10T14:01:04.650275Z"}}},"ActivityType":{"type":"string","title":"ActivityType","description":"- FILL\n  Order fills (both partial and full fills)\n\n- TRANS\n  Cash transactions (both CSD and CSW)\n\n- MISC\n  Miscellaneous or rarely used activity types (All types except those in TRANS, DIV, or FILL)\n\n- ACATC\n  ACATS IN/OUT (Cash)\n\n- ACATS\n  ACATS IN/OUT (Securities)\n\n- CFEE\n  Crypto fee\n\n- CSD\n  Cash deposit(+)\n\n- CSW\n  Cash withdrawal(-)\n\n- DIV\n  Dividends\n\n- DIVCGL\n  Dividend (capital gain long term)\n\n- DIVCGS\n  Dividend (capital gain short term)\n\n- DIVFEE\n  Dividend fee\n\n- DIVFT\n  Dividend adjusted (Foreign Tax Withheld)\n\n- DIVNRA\n  Dividend adjusted (NRA Withheld)\n\n- DIVROC\n  Dividend return of capital\n\n- DIVTW\n  Dividend adjusted (Tefra Withheld)\n\n- DIVTXEX\n  Dividend (tax exempt)\n\n- FEE\n  Fee denominated in USD\n\n- INT\n  Interest (credit/margin)\n\n- INTNRA\n  Interest adjusted (NRA Withheld)\n\n- INTTW\n  Interest adjusted (Tefra Withheld)\n\n- JNL\n  Journal entry\n\n- JNLC\n  Journal entry (cash)\n\n- JNLS\n  Journal entry (stock)\n\n- MA\n  Merger/Acquisition\n\n- NC\n  Name change\n\n- OPASN\n  Option assignment\n\n- OPCA\n  Option corporate action\n\n- OPCSH\n  Option cash deliverable for non-standard contracts\n\n- OPEXC\n  Option exercise\n\n- OPEXP\n  Option expiration\n\n- OPTRD\n  Option trade\n\n- PTC\n  Pass Thru Charge\n\n- PTR\n  Pass Thru Rebate\n\n- REORG\n  Reorg CA\n\n- SPIN\n  Stock spinoff\n\n- SPLIT\n  Stock split\n\n- FOPT\n  Free of Payment Transfers","enum":["FILL","TRANS","MISC","ACATC","ACATS","CFEE","CSD","CSW","DIV","DIVCGL","DIVCGS","DIVFEE","DIVFT","DIVNRA","DIVROC","DIVTW","DIVTXEX","FEE","INT","INTNRA","INTTW","JNL","JNLC","JNLS","MA","NC","OPASN","OPCA","OPCSH","OPEXC","OPEXP","OPTRD","PTC","PTR","REORG","SPIN","SPLIT","FOPT"],"x-examples":{"example-1":"FILL"}},"ActivitySubType":{"title":"ActivitySubType","type":"string","description":"Represents a more specific classification to the `activity_type`.\nThis field is optional and may not always be populated, depending on the activity type and the available data.\nEach `activity_type` has a set of valid `activity_sub_type` values.\n\nFull mapping of `activity_type` to `activity_sub_type`:\n\n- **DIV**: Dividend activity sub-types:\n  - **CDIV**: Cash Dividend\n  - **SDIV**: Stock Dividend\n  - **SPD**: Substitute Payment In Lieu Of Dividend\n\n- **FEE**: Fee-related activity sub-types:\n  - **REG**: Regulatory Fee\n  - **TAF**: Trading Activity Fee\n  - **LCT**: Local Currency Trading Fee\n  - **ORF**: Options Regulatory Fee\n  - **OCC**: Options Clearing Corporation Fee\n  - **NRC**: Non-Retail Commission Fee\n  - **NRV**: Non-Retail Venue Fee\n  - **COM**: Commission\n  - **CAT**: Consolidated Audit Trail Fee\n\n- **INT**: Interest-related activity sub-types:\n  - **MGN**: Margin Interest\n  - **CDT**: Credit Interest\n  - **SWP**: Sweep Interest\n  - **QII**: Qualified Interest\n\n- **MA**: Merger and Acquisition activity sub-types:\n  - **CMA**: Cash Merger\n  - **SMA**: Stock Merger\n  - **SCMA**: Stock & Cash Merger\n\n- **NC**: Name Change activity sub types\n  - **SNC**: Symbol Name Change\n  - **CNC**: CUSIP Name Change\n  - **SCNC**: Symbol & CUSIP Name Change\n\n- **OPCA**: Option Corporate Action activity sub-types:\n  - **DIV.CDIV**: Cash Dividend\n  - **DIV.SDIV**: Stock Dividend\n  - **MA.CMA**: Cash Merger\n  - **MA.SMA**: Stock Merger\n  - **MA.SCMA**: Stock & Cash Merger\n  - **NC.CNC**: CUSIP Name Change\n  - **NC.SNC**: Symbol Name Change\n  - **NC.SCNC**: Symbol & CUSIP Name Change\n  - **SPIN**: Spin-off\n  - **SPLIT.FSPLIT**: Forward Stock Split\n  - **SPLIT.RSPLIT**: Reverse Stock Split\n  - **SPLIT.USPLIT**: Unit Split\n\n- **REORG**: Reorganization activity sub-types:\n  - **WRM**: Worthless Removal\n\n- **SPLIT**: Stock Split activity sub-types:\n  - **FSPLIT**: Forward Stock Split\n  - **RSPLIT**: Reverse Stock Split\n  - **USPLIT**: Unit Split\n\n- **VOF**: Voluntary Offering activity sub-types:\n  - **VTND**: Tender Offer\n  - **VWRT**: Warrant Exercise\n  - **VRGT**: Rights Offer\n  - **VEXH**: Exchange Offer\n\n- **WH**: Withholding activity sub-types:\n  - **SWH**: State Withholding\n  - **FWH**: Federal Withholding\n  - **SLWH**: Sales Withholding"},"Order":{"description":"The Orders API allows a user to monitor, place and cancel their orders with Alpaca.\n\nEach order has a unique identifier provided by the client. This client-side unique order ID will be automatically generated by the system if not provided by the client, and will be returned as part of the order object along with the rest of the fields described below. Once an order is placed, it can be queried using the client-side order ID to check the status.\n\nUpdates on open orders at Alpaca will also be sent over the streaming interface, which is the recommended method of maintaining order state.","type":"object","title":"Order","properties":{"id":{"type":"string","description":"Order ID"},"client_order_id":{"type":"string","description":"Client unique order ID","maxLength":128},"created_at":{"type":"string","format":"date-time"},"updated_at":{"type":"string","format":"date-time","nullable":true},"submitted_at":{"type":"string","format":"date-time","nullable":true},"filled_at":{"type":"string","format":"date-time","nullable":true},"expired_at":{"type":"string","format":"date-time","nullable":true},"canceled_at":{"type":"string","format":"date-time","nullable":true},"failed_at":{"type":"string","format":"date-time","nullable":true},"replaced_at":{"type":"string","format":"date-time","nullable":true},"replaced_by":{"type":"string","format":"uuid","description":"The order ID that this order was replaced by","nullable":true},"replaces":{"type":"string","format":"uuid","description":"The order ID that this order replaces","nullable":true},"asset_id":{"type":"string","format":"uuid","description":"Asset ID (For options this represents the option contract ID)"},"symbol":{"type":"string","minLength":1,"description":"Asset symbol, required for all order classes except for `mleg`"},"asset_class":{"$ref":"#/components/schemas/AssetClass"},"notional":{"type":"string","minLength":1,"description":"Ordered notional amount. If entered, qty will be null. Can take up to 9 decimal points.","nullable":true},"qty":{"type":"string","minLength":1,"description":"Ordered quantity. If entered, notional will be null. Can take up to 9 decimal points. Required if order class is `mleg`.","nullable":true},"filled_qty":{"type":"string","minLength":1,"description":"Filled quantity"},"filled_avg_price":{"type":"string","description":"Filled average price","nullable":true},"order_class":{"$ref":"#/components/schemas/OrderClass"},"order_type":{"type":"string","deprecated":true,"description":"Deprecated in favour of the field \"type\" "},"type":{"$ref":"#/components/schemas/OrderType"},"side":{"$ref":"#/components/schemas/OrderSide"},"time_in_force":{"$ref":"#/components/schemas/TimeInForce"},"limit_price":{"type":"string","description":"Limit price","nullable":true},"stop_price":{"description":"Stop price","type":"string","nullable":true},"status":{"$ref":"#/components/schemas/OrderStatus"},"extended_hours":{"type":"boolean","description":"If true, eligible for execution outside regular trading hours."},"legs":{"type":"array","description":"When querying non-simple order_class orders in a nested style, an array of Order entities associated with this order. Otherwise, null. Required if order class is `mleg`.","nullable":true,"items":{"$ref":"#/components/schemas/OrderLeg"}},"trail_percent":{"type":"string","description":"The percent value away from the high water mark for trailing stop orders.","nullable":true},"trail_price":{"type":"string","description":"The dollar value away from the high water mark for trailing stop orders.","nullable":true},"hwm":{"type":"string","description":"The highest (lowest) market price seen since the trailing stop order was submitted.","nullable":true},"position_intent":{"$ref":"#/components/schemas/PositionIntent"}},"required":["notional","type","time_in_force"]},"OrderLeg":{"description":"This is copy of Order response schemas as a workaround of displaying issue of nested Order recursively for legs","type":"object","title":"Order","properties":{"id":{"type":"string","description":"Order ID"},"client_order_id":{"type":"string","description":"Client unique order ID","maxLength":128},"created_at":{"type":"string","format":"date-time"},"updated_at":{"type":"string","format":"date-time","nullable":true},"submitted_at":{"type":"string","format":"date-time","nullable":true},"filled_at":{"type":"string","format":"date-time","nullable":true},"expired_at":{"type":"string","format":"date-time","nullable":true},"canceled_at":{"type":"string","format":"date-time","nullable":true},"failed_at":{"type":"string","format":"date-time","nullable":true},"replaced_at":{"type":"string","format":"date-time","nullable":true},"replaced_by":{"type":"string","format":"uuid","description":"The order ID that this order was replaced by","nullable":true},"replaces":{"type":"string","format":"uuid","description":"The order ID that this order replaces","nullable":true},"asset_id":{"type":"string","format":"uuid","description":"Asset ID (For options this represents the option contract ID)"},"symbol":{"type":"string","minLength":1,"description":"Asset symbol"},"asset_class":{"$ref":"#/components/schemas/AssetClass"},"notional":{"type":"string","minLength":1,"description":"Ordered notional amount. If entered, qty will be null. Can take up to 9 decimal points.","nullable":true},"qty":{"type":"string","minLength":1,"description":"Ordered quantity. If entered, notional will be null. Can take up to 9 decimal points.","nullable":true},"filled_qty":{"type":"string","minLength":1,"description":"Filled quantity"},"filled_avg_price":{"type":"string","description":"Filled average price","nullable":true},"order_class":{"$ref":"#/components/schemas/OrderClass"},"order_type":{"type":"string","deprecated":true,"description":"Deprecated in favour of the field \"type\" "},"type":{"$ref":"#/components/schemas/OrderType"},"side":{"$ref":"#/components/schemas/OrderSide"},"time_in_force":{"$ref":"#/components/schemas/TimeInForce"},"limit_price":{"type":"string","description":"Limit price","nullable":true},"stop_price":{"description":"Stop price","type":"string","nullable":true},"status":{"$ref":"#/components/schemas/OrderStatus"},"extended_hours":{"type":"boolean","description":"If true, eligible for execution outside regular trading hours."},"legs":{"type":"array","description":"When querying non-simple order_class orders in a nested style, an array of Order entities associated with this order. Otherwise, null.","nullable":true},"trail_percent":{"type":"string","description":"The percent value away from the high water mark for trailing stop orders.","nullable":true},"trail_price":{"type":"string","description":"The dollar value away from the high water mark for trailing stop orders.","nullable":true},"hwm":{"type":"string","description":"The highest (lowest) market price seen since the trailing stop order was submitted.","nullable":true},"position_intent":{"$ref":"#/components/schemas/PositionIntent"}},"required":["symbol","notional","qty","type","side","time_in_force"]},"MLegOrderLeg":{"description":"Represents an individual leg of a multi-leg options order.","type":"object","title":"MLegOrderLeg","properties":{"side":{"$ref":"#/components/schemas/OrderSide"},"position_intent":{"$ref":"#/components/schemas/PositionIntent"},"symbol":{"type":"string","description":"symbol or asset ID to identify the asset to trade"},"ratio_qty":{"type":"string","description":"proportional quantity of this leg in relation to the overall multi-leg order qty"}},"required":["symbol","ratio_qty"]},"AdvancedInstructions":{"description":"Advanced instructions for Elite Smart Router: https://docs.alpaca.markets/docs/alpaca-elite-smart-router","type":"object","title":"AdvancedInstructions","properties":{"algorithm":{"description":"The advanced routing algorithm to use for the order","type":"string","example":"DMA","enum":["DMA","TWAP","VWAP"]},"destination":{"description":"Target exchange for order execution","type":"string","example":"NYSE","enum":["NYSE","NASDAQ","ARCA"]},"display_qty":{"description":"Maximum shares/contracts displayed on the exchange at any time. Must be in round lot increments","type":"string","format":"decimal","example":"100"},"start_time":{"description":"When the algorithm is to start executing. Must be within current market trading hours","type":"string","format":"date-time","example":"2025-07-21T09:30:00-04:00"},"end_time":{"description":"When the algorithm is to be done executing. Must be within current market trading hours","type":"string","format":"date-time","example":"2025-07-21T15:30:00-04:00"},"max_percentage":{"description":"Maximum percentage of the ticker's period volume this order might participate in. Must be 0 < max_percentage < 1, with up to 3 decimal points precision.","type":"string","format":"decimal","example":"0.314"}},"x-examples":{"example-1":{"algorithm":"DMA","destination":"NYSE","display_qty":100},"example-2":{"algorithm":"TWAP","start_time":"2025-07-21T09:30:00-04:00","end_time":"2025-07-21T15:30:00-04:00","max_percentage":0.314},"example-3":{"algorithm":"VWAP","start_time":"2025-07-21T09:30:00-04:00","end_time":"2025-07-21T15:30:00-04:00","max_percentage":0.314}}},"OrderType":{"type":"string","enum":["market","limit","stop","stop_limit","trailing_stop"],"example":"market","description":"The order types supported by Alpaca vary based on the order's security type. The following provides a comprehensive breakdown of the supported order types for each category:\n - Equity trading: market, limit, stop, stop_limit, trailing_stop.\n - Options trading: market, limit.\n - Multileg Options trading: market, limit.\n - Crypto trading: market, limit, stop_limit.","title":"OrderType"},"OrderSide":{"type":"string","enum":["buy","sell"],"example":"buy","title":"OrderSide","description":"Represents which side this order was on:\n- buy\n- sell\nRequired for all order classes except for mleg."},"OrderClass":{"type":"string","enum":["simple","bracket","oco","oto","mleg",""],"example":"bracket","description":"The order classes supported by Alpaca vary based on the order's security type. The following provides a comprehensive breakdown of the supported order classes for each category:\n  - Equity trading: simple (or \"\"), oco, oto, bracket.\n  - Options trading:\n    - simple (or \"\")\n    - mleg (required for multi-leg complex option strategies)\n  - Crypto trading: simple (or \"\").","title":"OrderClass"},"OrderStatus":{"type":"string","title":"OrderStatus","description":"An order executed through Alpaca can experience several status changes during its lifecycle. The most common statuses are described in detail below:\n\n- new\n  The order has been received by Alpaca, and routed to exchanges for execution. This is the usual initial state of an order.\n\n- partially_filled\n  The order has been partially filled.\n\n- filled\n  The order has been filled, and no further updates will occur for the order.\n\n- done_for_day\n  The order is done executing for the day, and will not receive further updates until the next trading day.\n\n- canceled\n  The order has been canceled, and no further updates will occur for the order. This can be either due to a cancel request by the user, or the order has been canceled by the exchanges due to its time-in-force.\n\n- expired\n  The order has expired, and no further updates will occur for the order.\n\n- replaced\n  The order was replaced by another order, or was updated due to a market event such as corporate action.\n\n- pending_cancel\n  The order is waiting to be canceled.\n\n- pending_replace\n  The order is waiting to be replaced by another order. The order will reject cancel request while in this state.\n\nLess common states are described below. Note that these states only occur on very rare occasions, and most users will likely never see their orders reach these states:\n\n- accepted\n  The order has been received by Alpaca, but hasn’t yet been routed to the execution venue. This could be seen often out side of trading session hours.\n\n- pending_new\n  The order has been received by Alpaca, and routed to the exchanges, but has not yet been accepted for execution. This state only occurs on rare occasions.\n\n- accepted_for_bidding\n  The order has been received by exchanges, and is evaluated for pricing. This state only occurs on rare occasions.\n\n- stopped\n  The order has been stopped, and a trade is guaranteed for the order, usually at a stated price or better, but has not yet occurred. This state only occurs on rare occasions.\n\n- rejected\n  The order has been rejected, and no further updates will occur for the order. This state occurs on rare occasions and may occur based on various conditions decided by the exchanges.\n\n- suspended\n  The order has been suspended, and is not eligible for trading. This state only occurs on rare occasions.\n\n- calculated\n  The order has been completed for the day (either filled or done for day), but remaining settlement calculations are still pending. This state only occurs on rare occasions.\n\n\nAn order may be canceled through the API up until the point it reaches a state of either filled, canceled, or expired.","enum":["new","partially_filled","filled","done_for_day","canceled","expired","replaced","pending_cancel","pending_replace","accepted","pending_new","accepted_for_bidding","stopped","rejected","suspended","calculated"],"example":"new"},"TimeInForce":{"type":"string","title":"TimeInForce","description":"The Time-In-Force values supported by Alpaca vary based on the order's security type. Here is a breakdown of the supported TIFs for each specific security type:\n- Equity trading: day, gtc, opg, cls, ioc, fok.\n- Options trading: day.\n- Crypto trading: gtc, ioc.\n\nBelow are the descriptions of each TIF:\n- day:\n  A day order is eligible for execution only on the day it is live. By default, the order is only valid during Regular Trading Hours (9:30am - 4:00pm ET). If unfilled after the closing auction, it is automatically canceled. If submitted after the close, it is queued and submitted the following trading day. However, if marked as eligible for extended hours, the order can also execute during supported extended hours.\n\n- gtc:\n  The order is good until canceled. Non-marketable GTC limit orders are subject to price adjustments to offset corporate actions affecting the issue. We do not currently support Do Not Reduce (DNR) orders to opt out of such price adjustments.\n\n- opg:\n  Use this TIF with a market/limit order type to submit “market on open” (MOO) and “limit on open” (LOO) orders. This order is eligible to execute only in the market opening auction. Any unfilled orders after the open will be cancelled. OPG orders submitted after 9:28am but before 7:00pm ET will be rejected. OPG orders submitted after 7:00pm will be queued and routed to the following day’s opening auction. On open/on close orders are routed to the primary exchange. Such orders do not necessarily execute exactly at 9:30am / 4:00pm ET but execute per the exchange’s auction rules.\n\n- cls:\n  Use this TIF with a market/limit order type to submit “market on close” (MOC) and “limit on close” (LOC) orders. This order is eligible to execute only in the market closing auction. Any unfilled orders after the close will be cancelled. CLS orders submitted after 3:50pm but before 7:00pm ET will be rejected. CLS orders submitted after 7:00pm will be queued and routed to the following day’s closing auction. Only available with API v2.\n\n- ioc:\n  An Immediate Or Cancel (IOC) order requires all or part of the order to be executed immediately. Any unfilled portion of the order is canceled. Only available with API v2. Most market makers who receive IOC orders will attempt to fill the order on a principal basis only, and cancel any unfilled balance. On occasion, this can result in the entire order being cancelled if the market maker does not have any existing inventory of the security in question.\n\n- fok:\n  A Fill or Kill (FOK) order is only executed if the entire order quantity can be filled, otherwise the order is canceled. Only available with API v2.","enum":["day","gtc","opg","cls","ioc","fok"],"example":"day"},"PositionIntent":{"type":"string","enum":["buy_to_open","buy_to_close","sell_to_open","sell_to_close"],"example":"buy_to_open","title":"PositionIntent","description":"Represents the desired position strategy."},"Assets":{"description":"The assets API serves as the master list of assets available for trade and data consumption from Alpaca. Assets are sorted by asset class, exchange and symbol. Some assets are only available for data consumption via Polygon, and are not tradable with Alpaca. These assets will be marked with the flag tradable=false.\n","type":"object","x-examples":{"example-1":{"id":"b0b6dd9d-8b9b-48a9-ba46-b9d54906e415","class":"us_equity","exchange":"NASDAQ","symbol":"AAPL","name":"Apple Inc. Common Stock","status":"active","tradable":true,"marginable":true,"shortable":true,"easy_to_borrow":true,"fractionable":true}},"title":"Assets","properties":{"id":{"type":"string","format":"uuid","description":"Asset ID"},"class":{"$ref":"#/components/schemas/AssetClass"},"cusip":{"type":"string","nullable":true,"description":"The CUSIP identifier for the asset (US Equities only).\nTo request a specific CUSIP, please reach out to Alpaca support.\n","example":"987654321"},"exchange":{"$ref":"#/components/schemas/Exchange"},"symbol":{"type":"string","description":"The symbol of the asset","example":"AAPL"},"name":{"type":"string","minLength":1,"description":"The official name of the asset"},"status":{"type":"string","description":"active or inactive","example":"active","enum":["active","inactive"]},"tradable":{"type":"boolean","description":"Asset is tradable on Alpaca or not"},"marginable":{"type":"boolean","description":"Asset is marginable or not"},"shortable":{"type":"boolean","description":"Asset is shortable or not"},"easy_to_borrow":{"type":"boolean","description":"Asset is easy-to-borrow or not (filtering for easy_to_borrow = True is the best way to check whether the name is currently available to short at Alpaca)."},"fractionable":{"type":"boolean","description":"Asset is fractionable or not"},"maintenance_margin_requirement":{"type":"number","x-stoplight":{"id":"kujwjd2dcq9bn"},"deprecated":true,"description":"**deprecated**: Please use margin_requirement_long or margin_requirement_short instead. Note that these fields are of type string.\nShows the margin requirement percentage for the asset (equities only).\n"},"margin_requirement_long":{"type":"string","description":"The margin requirement percentage for the asset's long positions (equities only)."},"margin_requirement_short":{"type":"string","description":"The margin requirement percentage for the asset's short positions (equities only)."},"attributes":{"type":"array","x-stoplight":{"id":"40mjg4fj0ykl8"},"description":"Unique characteristics of the asset. Supported values:\n- `ptp_no_exception`: Asset is a Publicly Traded Partnership (PTP) without a qualified notice; non-U.S. customers may incur 10% withholding on gross proceeds as per IRS guidance, and are blocked from being purchased by default.\n- `ptp_with_exception`: Users can open positions in these PTPs without general restrictions.\n- `ipo`: Accepting limit orders only before the stock begins trading on the secondary market.\n- `has_options`: The underlying equity has listed options available on the platform. Note: if the equity had inactive/expired contracts in the past, this will still show up.\n- `options_late_close`: Indicates the underlying asset's options contracts close at 4:15pm ET instead of the standard 4:00pm ET.\n- `fractional_eh_enabled`: Indicates the asset accepts fractional orders during extended hours sessions (pre-market, post-market, and overnight if enabled).\n- `overnight_tradable`: Asset is eligible for overnight (24x5) trading in supported venues on the platform.\n- `overnight_halted`: Asset is not eligible for overnight trading but is currently halted/blocked for overnight sessions due to risk, corporate action, compliance, or venue constraints.","items":{"type":"string","enum":["ptp_no_exception","ptp_with_exception","ipo","has_options","options_late_close","fractional_eh_enabled","overnight_tradable","overnight_halted"]},"example":["ptp_no_exception","ipo"]}},"required":["id","class","exchange","symbol","name","status","tradable","marginable","shortable","easy_to_borrow","fractionable"]},"AssetClass":{"type":"string","title":"AssetClass","enum":["us_equity","us_option","crypto"],"example":"us_equity","description":"This represents the category to which the asset belongs to. It serves to identify the nature of the financial instrument, with options including \"us_equity\" for U.S. equities, \"us_option\" for U.S. options, and \"crypto\" for cryptocurrencies.","x-examples":{"example-1":"us_equity"}},"OptionContract":{"type":"object","properties":{"id":{"type":"string","description":"The unique identifier of the option contract.","example":"98359ef7-5124-49f3-85ea-5cf02df6defa"},"symbol":{"type":"string","description":"The symbol representing the option contract.","example":"AAPL250620C00100000"},"name":{"type":"string","description":"The name of the option contract.","example":"AAPL Jun 20 2025 100 Call"},"status":{"type":"string","description":"The status of the option contract.","enum":["active","inactive"],"example":"active"},"tradable":{"type":"boolean","description":"Indicates whether the option contract is tradable.","example":true},"expiration_date":{"type":"string","format":"date","description":"The expiration date of the option contract.","example":"2025-06-20"},"root_symbol":{"type":"string","description":"The root symbol of the option contract.","example":"AAPL"},"underlying_symbol":{"type":"string","description":"The underlying symbol of the option contract.","example":"AAPL"},"underlying_asset_id":{"type":"string","description":"The unique identifier of the underlying asset.","example":"b0b6dd9d-8b9b-48a9-ba46-b9d54906e415"},"type":{"type":"string","description":"The type of the option contract.","enum":["call","put"],"example":"call"},"style":{"type":"string","description":"The style of the option contract.","enum":["american","european"],"example":"american"},"strike_price":{"type":"string","description":"The strike price of the option contract.","example":"100"},"multiplier":{"type":"string","description":"The multiplier of the option contract is crucial for calculating both the trade premium and the extended strike price. In standard contracts, the multiplier is always set to 100.\nFor instance, if a contract is traded at $1.50 and the multiplier is 100, the total amount debited when buying the contract would be $150.00.\nSimilarly, when exercising a call contract, the total cost will be equal to the strike price times the multiplier.","example":"100"},"size":{"type":"string","description":"Represents the number of underlying shares to be delivered in case the contract is exercised/assigned. For standard contracts, this is always 100.\nThis field should **not** be used as a multiplier, specially for non-standard contracts.","example":"100"},"open_interest":{"type":"string","description":"The open interest of the option contract.","example":"237"},"open_interest_date":{"type":"string","format":"date","description":"The date of the open interest data.","example":"2023-12-11"},"close_price":{"type":"string","description":"The close price of the option contract.","example":"148.38"},"close_price_date":{"type":"string","format":"date","example":"2023-12-11","description":"The date of the close price data."},"deliverables":{"type":"array","description":"Represents the deliverables tied to the option contract. While standard contracts entail a single deliverable, non-standard ones can encompass multiple deliverables, each potentially customized with distinct parameters.\nThis array is included in the list contracts response only if the query parameter show_deliverables=true is provided.\n","items":{"$ref":"#/components/schemas/OptionDeliverable"}}},"required":["id","symbol","name","status","tradable","expiration_date","underlying_symbol","underlying_asset_id","type","style","strike_price","multiplier","size"]},"OptionDeliverable":{"type":"object","properties":{"type":{"type":"string","description":"Type of deliverable, indicating whether it's cash or equity. For standard contracts, it is always \"equity\".\n","enum":["cash","equity"],"example":"equity"},"symbol":{"type":"string","description":"Symbol of the deliverable. For standard contracts, this is equivalent to the underlying symbol of the contract.\n","example":"AAPL"},"asset_id":{"type":"string","description":"Unique identifier of the deliverable asset. For standard contracts, this is equivalent to underlying_asset_id of the contracts.\nThis field is not returned for cash deliverables.\n","example":"b0b6dd9d-8b9b-48a9-ba46-b9d54906e415"},"amount":{"type":"string","description":"The deliverable amount. For cash deliverables, this is the cash amount.\nFor standard contract, this is always 100.\nThis field can be null in case the deliverable settlement is delayed and the amount is yet to be determined.\n","example":"100"},"allocation_percentage":{"type":"string","description":"Cost allocation percentage of the deliverable.\nThis is used to determine the cost basis of the equity shares received from the exercise, specially for non-standard contracts with multiple deliverables.\n","example":"100"},"settlement_type":{"type":"string","description":"Indicates when the deliverable will be settled if the contract is exercised/assigned.\n","enum":["T+0","T+1","T+2","T+3","T+4","T+5"],"example":"T+2"},"settlement_method":{"type":"string","description":"Indicates the settlement method that will be used:\n- **BTOB**: Broker to Broker\n- **CADF**: Cash Difference\n- **CAFX**: Cash Fixed\n- **CCC**: Correspondent Clearing Corp\n","enum":["BTOB","CADF","CAFX","CCC"],"example":"CCC"},"delayed_settlement":{"type":"boolean","description":"If true, the settlement of the deliverable will be delayed.\nFor instance, in the event of a contract with a delayed deliverable being exercised, both the availability of the deliverable and its settlement may be postponed beyond the typical timeframe.\n","example":false}},"required":["type","symbol","amount","allocation_percentage","settlement_type","settlement_method","delayed_settlement"]},"Position":{"description":"The positions API provides information about an account’s current open positions. The response will include information such as cost basis, shares traded, and market value, which will be updated live as price information is updated. Once a position is closed, it will no longer be queryable through this API.","type":"object","x-examples":{"example-1":{"asset_id":"904837e3-3b76-47ec-b432-046db621571b","symbol":"AAPL","exchange":"NASDAQ","asset_class":"us_equity","avg_entry_price":"100.0","qty":"5","qty_available":"4","side":"long","market_value":"600.0","cost_basis":"500.0","unrealized_pl":"100.0","unrealized_plpc":"0.20","unrealized_intraday_pl":"10.0","unrealized_intraday_plpc":"0.0084","current_price":"120.0","lastday_price":"119.0","change_today":"0.0084"},"example-2":{"asset_id":"b0b6dd9d-8b9b-48a9-ba46-b9d54906e415","symbol":"AAPL","exchange":"NASDAQ","asset_class":"us_equity","asset_marginable":false,"qty":"2","qty_available":"2","avg_entry_price":"174.78","side":"long","market_value":"348.58","cost_basis":"349.56","unrealized_pl":"-0.98","unrealized_plpc":"-0.0028035244307129","unrealized_intraday_pl":"-0.98","unrealized_intraday_plpc":"-0.0028035244307129","current_price":"174.29","lastday_price":"174.61","change_today":"-0.0018326556325525"}},"title":"Position","properties":{"asset_id":{"type":"string","description":"Asset ID (For options this represents the option contract ID)","format":"uuid"},"symbol":{"type":"string","description":"Symbol name of the asset","example":"AAPL"},"exchange":{"$ref":"#/components/schemas/ExchangeForPosition"},"asset_class":{"$ref":"#/components/schemas/AssetClass"},"avg_entry_price":{"type":"string","minLength":1,"description":"Average entry price of the position"},"qty":{"type":"string","minLength":1,"description":"The number of shares"},"qty_available":{"type":"string","minLength":1,"description":"Total number of shares available minus open orders / locked for options covered call"},"side":{"type":"string","minLength":1,"description":"“long”"},"market_value":{"type":"string","minLength":1,"description":"Total dollar amount of the position"},"cost_basis":{"type":"string","minLength":1,"description":"Total cost basis in dollar"},"unrealized_pl":{"type":"string","minLength":1,"description":"Unrealized profit/loss in dollars"},"unrealized_plpc":{"type":"string","minLength":1,"description":"Unrealized profit/loss percent (by a factor of 1)"},"unrealized_intraday_pl":{"type":"string","minLength":1,"description":"Unrealized profit/loss in dollars for the day"},"unrealized_intraday_plpc":{"type":"string","minLength":1,"description":"Unrealized profit/loss percent (by a factor of 1)"},"current_price":{"type":"string","minLength":1,"description":"Current asset price per share"},"lastday_price":{"type":"string","minLength":1,"description":"Last day’s asset price per share based on the closing value of the last trading day"},"change_today":{"type":"string","minLength":1,"description":"Percent change from last day price (by a factor of 1)"},"asset_marginable":{"type":"boolean"}},"required":["asset_id","symbol","exchange","asset_class","avg_entry_price","qty","side","market_value","cost_basis","unrealized_pl","unrealized_plpc","unrealized_intraday_pl","unrealized_intraday_plpc","current_price","lastday_price","change_today","asset_marginable"]},"Watchlist":{"description":"The watchlist API provides CRUD operation for the account’s watchlist. An account can have multiple watchlists and each is uniquely identified by id but can also be addressed by user-defined name. Each watchlist is an ordered list of assets.\n","type":"object","x-examples":{"example-1":{"id":"3174d6df-7726-44b4-a5bd-7fda5ae6e009","account_id":"abe25343-a7ba-4255-bdeb-f7e013e9ee5d","created_at":"2022-01-31T21:49:05.14628Z","updated_at":"2022-01-31T21:49:05.14628Z","name":"Primary Watchlist","assets":[{"id":"8ccae427-5dd0-45b3-b5fe-7ba5e422c766","class":"us_equity","exchange":"NASDAQ","symbol":"TSLA","name":"Tesla, Inc. Common Stock","status":"active","tradable":true,"marginable":true,"shortable":true,"easy_to_borrow":true,"fractionable":true}]}},"title":"Watchlist","properties":{"id":{"type":"string","format":"uuid","description":"watchlist id"},"account_id":{"type":"string","format":"uuid","description":"account ID"},"created_at":{"type":"string","format":"date-time"},"updated_at":{"type":"string","format":"date-time"},"name":{"type":"string","minLength":1,"description":"user-defined watchlist name (up to 64 characters)"},"assets":{"type":"array","description":"the content of this watchlist, in the order as registered by the client","items":{"$ref":"#/components/schemas/Assets"}}},"required":["id","account_id","created_at","updated_at","name"]},"WatchlistWithoutAsset":{"description":"The watchlist API provides CRUD operation for the account’s watchlist. An account can have multiple watchlists and each is uniquely identified by id but can also be addressed by user-defined name.\n","type":"object","x-examples":{"example-1":{"id":"3174d6df-7726-44b4-a5bd-7fda5ae6e009","account_id":"abe25343-a7ba-4255-bdeb-f7e013e9ee5d","created_at":"2022-01-31T21:49:05.14628Z","updated_at":"2022-01-31T21:49:05.14628Z","name":"Primary Watchlist"}},"title":"Watchlist","properties":{"id":{"type":"string","format":"uuid","description":"watchlist id"},"account_id":{"type":"string","format":"uuid","description":"account ID"},"created_at":{"type":"string","format":"date-time"},"updated_at":{"type":"string","format":"date-time"},"name":{"type":"string","minLength":1,"description":"user-defined watchlist name (up to 64 characters)"}},"required":["id","account_id","created_at","updated_at","name"]},"Calendar":{"type":"object","x-examples":{"example-1":{"date":"2022-02-01","open":"09:30","close":"16:00","session_open":"0700","session_close":"1900"}},"title":"Calendar","properties":{"date":{"type":"string","minLength":1,"description":"Date string in “%Y-%m-%d” format"},"open":{"type":"string","minLength":1,"description":"The time the market opens at on this date in “%H:%M” format"},"close":{"type":"string","minLength":1,"description":"The time the market closes at on this date in “%H:%M” format"},"settlement_date":{"type":"string","x-stoplight":{"id":"e0st09dxvsjt5"},"description":"Date string in “%Y-%m-%d” format. representing the settlement date for the trade date."}},"required":["date","open","close","settlement_date"]},"Clock":{"title":"Clock","type":"object","properties":{"timestamp":{"type":"string","description":"Current timestamp\n","format":"date-time"},"is_open":{"type":"boolean","description":"Whether or not the market is open\n"},"next_open":{"type":"string","description":"Next Market open timestamp","format":"date-time"},"next_close":{"type":"string","description":"Next market close timestamp","format":"date-time"}},"x-examples":{"example-1":{"timestamp":"2019-08-24T14:15:22Z","is_open":true,"next_open":"2019-08-24T14:15:22Z","next_close":"2019-08-24T14:15:22Z"}}},"PortfolioHistory":{"title":"PortfolioHistory","description":"Timeseries data for equity and profit loss information of the account.","type":"object","properties":{"timestamp":{"type":"array","description":"Time of each data element, left-labeled (the beginning of time window).\n\nThe values returned are in [UNIX epoch format](https://en.wikipedia.org/wiki/Unix_time).\n","items":{"type":"integer"}},"equity":{"type":"array","description":"equity value of the account in dollar amount as of the end of each time window","items":{"type":"number"}},"profit_loss":{"type":"array","description":"profit/loss in dollar from the base value","items":{"type":"number"}},"profit_loss_pct":{"type":"array","description":"profit/loss in percentage from the base value","items":{"type":"number"},"example":[0.001,0.002]},"base_value":{"type":"number","description":"basis in dollar of the profit loss calculation"},"base_value_asof":{"type":"string","format":"date","example":"2023-10-20","description":"If included, then it indicates that the base_value is the account's closing\nequity value at this trading date.\n\nIf not specified, then the baseline calculation is done against the earliest returned data item. This could happen for\naccounts without prior closing balances (e.g. new account) or for queries with 1D timeframes, where the first data point\nis used as a reference point.\n"},"timeframe":{"type":"string","description":"time window size of each data element","example":"15Min"},"cashflow":{"type":"object","description":"accumulated value in dollar amount as of the end of each time window"}},"required":["timestamp","equity","profit_loss","profit_loss_pct","base_value","timeframe"],"x-examples":{"example-intraday-query-15min-1d":{"timestamp":[1697722200,1697723100,1697724000,1697724900,1697725800,1697726700,1697727600,1697728500,1697729400,1697730300,1697731200,1697732100,1697733000,1697733900,1697734800,1697735700,1697736600,1697737500,1697738400,1697739300,1697740200,1697741100,1697742000,1697742900,1697743800,1697744700,1697745600],"equity":[2773.79,2769.04,2768.65,2765.11,2763.03,2763.17,2763.17,2763.47,2763.91,2768.13,2774.98,2757.94,2757.65,2774.54,2775.58,2775.28,2767.9,2762.26,2762.56,2756.99,2756.84,2752.43,2752.13,2748.44,2751.23,2747.54,2748.74],"profit_loss":[-0.37,-5.12,-5.51,-9.05,-11.13,-10.99,-10.99,-10.69,-10.25,-6.03,0.82,-16.22,-16.51,0.38,1.42,1.12,-6.26,-11.9,-11.6,-17.17,-17.32,-21.73,-22.03,-25.72,-22.93,-26.62,-25.42],"profit_loss_pct":[-0.0001,-0.0018,-0.002,-0.0033,-0.004,-0.004,-0.004,-0.0039,-0.0037,-0.0022,0.0003,-0.0058,-0.006,0.0001,0.0005,0.0004,-0.0023,-0.0043,-0.0042,-0.0062,-0.0062,-0.0078,-0.0079,-0.0093,-0.0083,-0.0096,-0.0092],"base_value":2774.16,"base_value_asof":"2023-10-18","timeframe":"15Min"},"example-query-1d-7d":{"timestamp":[1697241600,1697500800,1697587200,1697673600,1697760000],"equity":[2784.79,2794.79,2805.46,2774.16,2748.73],"profit_loss":[0,10.0022,10.6692,-31.2996,-25.4232],"profit_loss_pct":[0,0.0035,0.0074,-0.0038,-0.0129],"base_value":2784.79,"timeframe":"1D"}}},"Exchange":{"title":"Exchange","type":"string","description":"Represents the current exchanges Alpaca supports. List is currently:\n\n- AMEX\n- ARCA\n- BATS\n- NYSE\n- NASDAQ\n- NYSEARCA\n- OTC","enum":["AMEX","ARCA","BATS","NYSE","NASDAQ","NYSEARCA","OTC"],"example":"NYSE"},"ExchangeForPosition":{"title":"Exchange","type":"string","description":"Represents the current exchanges Alpaca supports. List is currently:\n\n- AMEX\n- ARCA\n- BATS\n- NYSE\n- NASDAQ\n- NYSEARCA\n- OTC\n\nCan be empty if not applicable (e.g., for options contracts)","enum":["AMEX","ARCA","BATS","NYSE","NASDAQ","NYSEARCA","OTC",null],"example":"NYSE"},"CanceledOrderResponse":{"title":"CanceledOrderResponse","type":"object","x-examples":{"example-1":{"id":"d56ba3ea-6d04-48ce-8175-817e242ee608","status":200}},"description":"Represents the result of a request to cancel and order","properties":{"id":{"type":"string","format":"uuid","description":"orderId"},"status":{"type":"integer","description":"http response code","example":200}}},"PatchOrderRequest":{"title":"PatchOrderRequest","type":"object","description":"Represents a request to patch an order.","properties":{"qty":{"type":"string","example":"4","description":"number of shares to trade.\n\nYou can only patch full shares for now.\n\nQty of equity fractional/notional orders are not allowed to change."},"time_in_force":{"$ref":"#/components/schemas/TimeInForce"},"limit_price":{"type":"string","example":"3.14","description":"Required if original order's `type` field was `limit` or `stop_limit`.\nIn case of `mleg`, the limit_price parameter is expressed with the following notation:\n- A positive value indicates a debit, representing a cost or payment to be made.\n- A negative value signifies a credit, reflecting an amount to be received."},"stop_price":{"type":"string","example":"3.14","description":"required if original order type is limit or stop_limit"},"trail":{"type":"string","example":"3.14","description":"the new value of the trail_price or trail_percent value (works only for type=“trailing_stop”)"},"client_order_id":{"type":"string","description":"A unique identifier for the new order. Automatically generated if not sent. (<= 128 characters)","maxLength":128},"advanced_instructions":{"$ref":"#/components/schemas/AdvancedInstructions"}}},"PositionClosedReponse":{"title":"PositionClosedReponse","type":"object","description":"Represents the result of asking the api to close a position. ","properties":{"symbol":{"type":"string","description":"Symbol name of the asset"},"status":{"type":"integer","description":"HTTP status code for the attempt to close this position"},"body":{"$ref":"#/components/schemas/Order"}},"required":["symbol","status"],"x-examples":{"example-1":{"symbol":"AAPL","status":200,"body":{"id":"f7f25e89-939a-4587-aaf6-414a6b3c341d","client_order_id":"52f8574c-96d5-49b6-94c1-2570a268434e","created_at":"2022-02-04T16:53:29.53427917Z","updated_at":"2022-02-04T16:53:29.53427917Z","submitted_at":"2022-02-04T16:53:29.533738219Z","filled_at":null,"expired_at":null,"canceled_at":null,"failed_at":null,"replaced_at":null,"replaced_by":null,"replaces":null,"asset_id":"b0b6dd9d-8b9b-48a9-ba46-b9d54906e415","symbol":"AAPL","asset_class":"us_equity","notional":null,"qty":"2","filled_qty":"0","filled_avg_price":null,"order_class":"","order_type":"market","type":"market","side":"sell","time_in_force":"day","limit_price":null,"stop_price":null,"status":"accepted","extended_hours":false,"legs":null,"trail_percent":null,"trail_price":null,"hwm":null}}}},"UpdateWatchlistRequest":{"title":"PostWatchlistRequest","type":"object","description":"Request format used for creating a new watchlist or updating an existing watchlist with a set of assets and name.","properties":{"name":{"type":"string","description":"The watchlist name."},"symbols":{"type":"array","description":"List of asset symbols to include in the watchlist.","items":{"type":"string","nullable":true}}},"required":["name"]},"AddAssetToWatchlistRequest":{"title":"AddAssetToWatchlistRequest","type":"object","description":"Append an asset for the symbol to the end of watchlist asset list","properties":{"symbol":{"type":"string","example":"AAPL","description":"symbol name to append to watchlist"}}},"CryptoWallet":{"type":"object","properties":{"chain":{"type":"string"},"address":{"type":"string"},"created_at":{"type":"string","format":"date-time","description":"Timestamp (RFC3339) of account creation."}}},"CryptoTransfer":{"type":"object","description":"Transfers allow you to transfer assets into your end customer's account (deposits) or out (withdrawal).","properties":{"id":{"type":"string","format":"uuid","description":"The crypto transfer ID"},"tx_hash":{"type":"string","description":"On-chain transaction hash (e.g. 0xabc...xyz)"},"direction":{"$ref":"#/components/schemas/TransferDirection"},"status":{"$ref":"#/components/schemas/CryptoTransferStatus"},"amount":{"type":"string","description":"Amount of transfer denominated in the underlying crypto asset"},"usd_value":{"type":"string","description":"Equivalent USD value at time of transfer"},"network_fee":{"type":"string"},"fees":{"type":"string"},"chain":{"type":"string","description":"Underlying network for given transfer"},"asset":{"type":"string","description":"Symbol of crypto asset for given transfer (e.g. BTC)"},"from_address":{"type":"string","description":"Originating address of the transfer"},"to_address":{"type":"string","description":"Destination address of the transfer"},"created_at":{"type":"string","format":"date-time","description":"Timestamp when transfer was created"}},"x-stoplight":{"id":"f986mttnx5c4n"}},"CryptoTransferStatus":{"type":"string","example":"PROCESSING","enum":["PROCESSING","FAILED","COMPLETE"]},"WhitelistedAddress":{"type":"object","properties":{"id":{"type":"string","description":"Unique ID for whitelisted address"},"chain":{"type":"string","description":"Underlying network this address represents"},"asset":{"type":"string","description":"Symbol of underlying asset for the whitelisted address"},"address":{"type":"string","description":"The whitelisted address"},"status":{"type":"string","description":"Status of whitelisted address which is either ACTIVE or PENDING. Whitelisted addresses will be subjected to a 24 waiting period. After the waiting period is over the status will become ACTIVE.","enum":["APPROVED","PENDING"]},"created_at":{"type":"string","format":"date-time","description":"Timestamp (RFC3339) of account creation."}}},"CreateCryptoTransferRequest":{"title":"CreateCryptoTransferRequest","type":"object","properties":{"amount":{"type":"string","description":"The amount, denoted in the specified asset, to be withdrawn from the user’s wallet"},"address":{"type":"string","description":"The destination wallet address"},"asset":{"type":"string","description":"The crypto asset symbol, e.g. BTC, ETH, USDT."}},"required":["amount","address","asset"]},"TransferDirection":{"type":"string","example":"INCOMING","enum":["INCOMING","OUTGOING"]},"Error":{"title":"Error","type":"object","properties":{"code":{"type":"number"},"message":{"type":"string"}},"required":["code","message"]},"NextPageToken":{"type":"string","description":"Use this token in your next API call to paginate through the dataset and retrieve the next page of results. A null token indicates there are no more data to fetch.\n","nullable":true,"example":"MTAwMA=="},"treasury_subtype":{"type":"string","description":"The subtype of the treasury.","enum":["bond","bill","note","strips","tips","floating"]},"bond_status":{"description":"Status of the bond.","type":"string","enum":["outstanding","matured","pre_issuance"]},"coupon_type":{"description":"The type of the coupon rate","type":"string","enum":["fixed","floating","zero"]},"coupon_frequency":{"description":"How often the coupon is paid","type":"string","enum":["annual","semi_annual","quarterly","monthly","zero"]},"us_treasury":{"description":"A US treasury","type":"object","properties":{"cusip":{"description":"CUSIP is a nine-character alphanumeric code that uniquely identifies the security","type":"string","minLength":12,"maxLength":12,"pattern":"^[A-Z0-9]{9}$"},"isin":{"description":"International Securities Identification Number","type":"string","minLength":12,"maxLength":12,"pattern":"^[A-Z]{2}[A-Z0-9]{9}[0-9]$"},"bond_status":{"$ref":"#/components/schemas/bond_status"},"tradable":{"description":"Whether the treasury is tradable","type":"boolean"},"subtype":{"$ref":"#/components/schemas/treasury_subtype"},"issue_date":{"description":"The date on which the bond was issued","type":"string","format":"date"},"maturity_date":{"description":"The date on which the bond matures","type":"string","format":"date"},"description":{"description":"Description of the treasury","type":"string"},"description_short":{"description":"Short description of the treasury","type":"string"},"close_price":{"description":"The price of the last transaction of a security before the market closes for normal trading, shown as a percentage of par value","type":"number","format":"double"},"close_price_date":{"description":"The date of the close price","type":"string","format":"date"},"close_yield_to_maturity":{"description":"Yield to maturity of the treasury after the last close","type":"number","format":"double"},"close_yield_to_worst":{"description":"Yield to worst of the treasury after the last close","type":"number","format":"double"},"coupon":{"description":"The annual interest rate paid on the bond as a percentage of par value","type":"number","format":"double"},"coupon_type":{"$ref":"#/components/schemas/coupon_type"},"coupon_frequency":{"$ref":"#/components/schemas/coupon_frequency"},"first_coupon_date":{"description":"The date of the first coupon payment","type":"string","format":"date"},"next_coupon_date":{"description":"The date of the next coupon payment","type":"string","format":"date"},"last_coupon_date":{"description":"The date of the last coupon payment","type":"string","format":"date"}},"required":["cusip","isin","bond_status","tradable","subtype","issue_date","maturity_date","description","description_short","coupon","coupon_type","coupon_frequency"]},"us_treasuries_resp":{"type":"object","properties":{"us_treasuries":{"type":"array","items":{"$ref":"#/components/schemas/us_treasury"}}},"required":["us_treasuries"]},"day_count":{"description":"The day count convention used to calculate accrued interest.\n\n- `A/360`: calculates the daily interest using a 360-day year and then multiplies that by the actual number of days in each time period.\n- `A/365`: calculates the daily interest using a 365-day year and then multiplies that by the actual number of days in each time period.\n- `30/360`: calculates the daily interest using a 360-day year and then multiplies that by 30 (standardized month).\n- `30/365`: calculates the daily interest using a 365-day year and then multiplies that by 30 (standardized month).\n- `A/A`: calculates the daily interest using the actual number of days in the year and then multiplies that by the actual number of days in each time period.\n- `30E/360`: number of days equals to the actual number of days (for February). If the start date or the end date of the period is the 31st of a month, that date is set to the 30th. The number of days in a year is 360.\n- `B/252`: calculates the daily interest using a 252-business-day year and then multiplies that by the actual number of days in each time period.\n- `A/364`: calculates the daily interest using a 364-day year and then multiplies that by the actual number of days in each time period.\n","type":"string","enum":["A/360","A/365","30/360","30/365","A/A","30E/360","B/252","A/364"]},"sp_outlook":{"description":"A Standard & Poor's rating outlook indicates S&P's view regarding the potential direction of a long-term credit rating over the intermediate term (2 years for investment grade, 1 year for speculative grade)","type":"string","enum":["positive","negative","developing","stable","not_rated","not_meaningful"]},"call_type":{"description":"The type of call on the bond refers to one of a variety of circumstances under which a callable bond may be called.","type":"string","enum":["ordinary","make_whole","regulatory","special"]},"us_corporate":{"description":"A US corporate","type":"object","properties":{"cusip":{"description":"CUSIP is a nine-character alphanumeric code that uniquely identifies the security","type":"string","minLength":12,"maxLength":12,"pattern":"^[A-Z0-9]{9}$"},"isin":{"description":"International Securities Identification Number","type":"string","minLength":12,"maxLength":12,"pattern":"^[A-Z]{2}[A-Z0-9]{9}[0-9]$"},"bond_status":{"$ref":"#/components/schemas/bond_status"},"tradable":{"description":"Whether the treasury is tradable","type":"boolean"},"marginable":{"description":"Whether the corporate is marginable","type":"boolean"},"reissue_date":{"description":"The date on which the corporate was reissued","type":"string","format":"date"},"reissue_size":{"description":"The total size amount of the corporate reissue in the issuing currency","type":"number"},"reissue_price":{"description":"The price at which the corporate was reissued as a percentage of par value","type":"number","format":"double","x-go-type":"decimal.Decimal","x-go-type-import":{"path":"github.com/alpacahq/alpacadecimal","name":"decimal"}},"issue_date":{"description":"The date on which the bond was issued","type":"string","format":"date"},"maturity_date":{"description":"The date on which the bond matures","type":"string","format":"date"},"country_domicile":{"description":"The country where the corporate is domiciled in the 2-alpha country code format (e.g., US, CA)","type":"string"},"ticker":{"description":"The ticker symbol of the corporate","type":"string"},"seniority":{"description":"The seniority of the corporate bond","type":"string"},"issuer":{"description":"The name of the issuer of the corporate bond","type":"string"},"sector":{"description":"The sector of the corporate bond","type":"string"},"description":{"description":"Description of the corporate bond","type":"string"},"description_short":{"description":"Short description of the corporate bond","type":"string"},"coupon":{"description":"The annual interest rate paid on the bond as a percentage of par value","type":"number","format":"double","x-go-type":"decimal.Decimal","x-go-type-import":{"path":"github.com/alpacahq/alpacadecimal","name":"decimal"}},"coupon_type":{"$ref":"#/components/schemas/coupon_type"},"coupon_frequency":{"$ref":"#/components/schemas/coupon_frequency"},"first_coupon_date":{"description":"The date of the first coupon payment","type":"string","format":"date"},"next_coupon_date":{"description":"The date of the next coupon payment","type":"string","format":"date"},"last_coupon_date":{"description":"The date of the last coupon payment","type":"string","format":"date"},"perpetual":{"description":"A flag representing whether a bond is perpetual","type":"boolean"},"day_count":{"$ref":"#/components/schemas/day_count"},"dated_date":{"description":"The dated date marks the beginning of the period for which interest starts accruing on the bond","type":"string","format":"date"},"issue_size":{"description":"The total size amount of the bond issue in the issuing currency","type":"number"},"issue_price":{"description":"The price at which the bond was originally issued as a percentage of par value","type":"number","format":"double","x-go-type":"decimal.Decimal","x-go-type-import":{"path":"github.com/alpacahq/alpacadecimal","name":"decimal"}},"issue_minimum_denomination":{"description":"The smallest unit of the bond that can be purchased at its initial offering","type":"number"},"par_value":{"description":"The amount that the issuer of the bond will pay back to the bondholder upon maturity","type":"number"},"callable":{"description":"Whether the bond is callable, meaning the issuer has the right, but not the obligation to redeem the bond — in other words, pay out the bondholder — before its maturity date at a set price (the call price)","type":"boolean"},"next_call_date":{"description":"The date of the next possible call on the bond.","type":"string","format":"date"},"next_call_price":{"description":"The price at which a callable bond can be redeemed by the issuer on the next call date, as a percentage of par.","type":"number","format":"double","x-go-type":"decimal.Decimal","x-go-type-import":{"path":"github.com/alpacahq/alpacadecimal","name":"decimal"}},"puttable":{"description":"Whether the bond is puttable, meaning the bondholder has the right, but not the obligation to sell the bond back to the issuer at a set price (the put price) on specified dates before maturity","type":"boolean"},"convertible":{"description":"A flag indicating whether the bond is convertible","type":"boolean"},"reg_s":{"description":"Indicates whether the security falls under Regulation S, a rule that provides an exemption from the registration requirements for securities offerings made outside the United States","type":"boolean"},"sp_rating":{"description":"Standard & Poor's rating for the bond in the standard AAA - D format","type":"string"},"sp_rating_date":{"description":"The date in the timezone of the issuing country of the most recent Standard & Poor's rating for the bond in YYYY-MM-DD format","type":"string","format":"date"},"sp_creditwatch":{"description":"S&P's CreditWatch highlights S&P's opinion regarding the potential direction of a short-term or long-term rating","type":"string"},"sp_creditwatch_date":{"description":"The date of the most recent Standard & Poor's CreditWatch for the bond in YYYY-MM-DD format","type":"string","format":"date"},"sp_outlook":{"$ref":"#/components/schemas/sp_outlook"},"sp_outlook_date":{"description":"The date of the most recent Standard & Poor's outlook for the bond in YYYY-MM-DD format","type":"string","format":"date"},"liquidity_micro_buy":{"description":"Score (from 1-5 if the bond is priced, or null if the bond is not tradable) reflecting the historical depth of executable liquidity to buy with minimum trading sizes less than or equal to $1,000.00","type":"number"},"liquidity_micro_sell":{"description":"Score (from 1-5 or null if the bond is not priced/tradable) reflecting the historical depth of executable liquidity to sell with minimum trading sizes less than or equal to $1,000.00","type":"number"},"liquidity_micro_aggregate":{"description":"Score (from 1-5 or null if the bond is not priced/tradable) reflecting the historical depth of executable liquidity to buy or sell with minimum trading sizes less than or equal to $1,000.00","type":"number"},"liquidity_retail_buy":{"description":"Score (from 1-5 or null if the bond is not priced/tradable) reflecting the historical depth of executable liquidity to buy with minimum trading sizes less than or equal to $10,000.00","type":"number"},"liquidity_retail_sell":{"description":"Score (from 1-5 or null if the bond is not priced/tradable) reflecting the historical depth of executable liquidity to sell with minimum trading sizes less than or equal to 10,000","type":"number"},"liquidity_retail_aggregate":{"description":"Score (from 1-5 or null if the bond is not priced/tradable) reflecting the historical depth of executable liquidity to buy or sell with minimum trading sizes less than or equal to 10,000","type":"number"},"liquidity_institutional_buy":{"description":"Score (from 1-5 or null if the bond is not priced/tradable) reflecting the historical depth of executable liquidity to buy (no minimum trading sizes)","type":"number"},"liquidity_institutional_sell":{"description":"Score (from 1-5 or null if the bond is not priced/tradable) reflecting the historical depth of executable liquidity to sell (no minimum trading sizes)","type":"number"},"liquidity_institutional_aggregate":{"description":"Score (from 1-5 or null if the bond is not priced/tradable) reflecting the historical depth of executable liquidity to buy or sell (no minimum trading sizes)","type":"number"},"close_price":{"description":"The price of the last transaction of a security before the market closes for normal trading, shown as a percentage of par value","type":"number","format":"double","x-go-type":"decimal.Decimal","x-go-type-import":{"path":"github.com/alpacahq/alpacadecimal","name":"decimal"}},"close_price_date":{"description":"The date of the close price","type":"string","format":"date"},"close_yield_to_maturity":{"description":"Yield to maturity of the treasury after the last close","type":"number","format":"double","x-go-type":"decimal.Decimal","x-go-type-import":{"path":"github.com/alpacahq/alpacadecimal","name":"decimal"}},"close_yield_to_worst":{"description":"Yield to worst of the treasury after the last close","type":"number","format":"double","x-go-type":"decimal.Decimal","x-go-type-import":{"path":"github.com/alpacahq/alpacadecimal","name":"decimal"}},"accrued_interest":{"description":"The interest that has accumulated on a bond in dollars per bond between the last interest payment and the present date that has not yet been paid to the bondholder","type":"number","format":"double","x-go-type":"decimal.Decimal","x-go-type-import":{"path":"github.com/alpacahq/alpacadecimal","name":"decimal"}},"call_type":{"$ref":"#/components/schemas/call_type"}},"required":["isin","cusip","bond_status","tradable","marginable","issue_date","country_domicile","ticker","seniority","issuer","sector","description","description_short","coupon","coupon_type","coupon_frequency","perpetual","day_count","dated_date","issue_size","issue_price","issue_minimum_denomination","par_value","callable","puttable","convertible","reg_s"]},"us_corporates_resp":{"type":"object","properties":{"us_corporates":{"type":"array","items":{"$ref":"#/components/schemas/us_corporate"}}},"required":["us_corporates"]},"legacy_calendar_day":{"type":"object","description":"A calendar day.","properties":{"date":{"type":"string","format":"date","description":"Date string in YYYY-MM-DD format.","example":"2025-01-02"},"open":{"type":"string","description":"The time the market opens at on this date in HH:MM format.","example":"09:30"},"close":{"type":"string","description":"The time the market closes at on this date in HH:MM format.","example":"16:00"},"session_open":{"type":"string","description":"The time the session opens at on this date in HHMM format.","example":"0400"},"session_close":{"type":"string","description":"The time the session closes at on this date in HHMM format.","example":"2000"},"settlement_date":{"type":"string","format":"date","description":"Date string in YYYY-MM-DD format. Representing the settlement date for the trade date.","example":"2025-01-03"}},"required":["date","open","close","session_open","session_close","settlement_date"]},"legacy_public_calendar_resp":{"type":"array","items":{"$ref":"#/components/schemas/legacy_calendar_day"}},"legacy_clock":{"title":"Clock","type":"object","properties":{"timestamp":{"type":"string","format":"date-time","description":"Current timestamp."},"is_open":{"type":"boolean","description":"Whether or not the market is open."},"next_open":{"type":"string","description":"Next market open timestamp.","format":"date-time"},"next_close":{"type":"string","description":"Next market close timestamp.","format":"date-time"}},"example":{"timestamp":"2025-06-24T14:15:22-04:00","is_open":true,"next_open":"2025-06-25T09:30:00-04:00","next_close":"2025-06-24T16:00:00-04:00"},"required":["timestamp","is_open","next_open","next_close"]},"market":{"type":"string","description":"The market identifier (MIC, BIC, or acronym).","enum":["BMO","BNYM","BOATS","CEUX","CHIX","HKEX","IEX","IEXG","ISE","LSE","MTA","MTAA","NASDAQ","NYSE","OCEA","OPRA","OTC","OTCM","SIFMA","TADAWUL","XAMS","XBRU","XDUB","XETR","XETRA","XHKG","XLIS","XLON","XNAS","XNYS","XPAR","XSAU"]},"mic":{"type":"string","description":"Market identifier code (ISO 10383).","minLength":4,"maxLength":4,"pattern":"^[A-Z0-9]{4}$","example":"XNYS"},"bic":{"type":"string","description":"Business Identifier Code (BIC/SWIFT).","minLength":11,"maxLength":11,"pattern":"^[A-Z0-9]{11}$","example":"IRVTUS3NXXX"},"market_acronym":{"type":"string","description":"The acronym of the market.","example":"NYSE"},"market_name":{"type":"string","description":"The full name of the market.","example":"New York Stock Exchange"},"market_timezone":{"type":"string","description":"The timezone of the market.","example":"America/New_York"},"public_market":{"type":"object","description":"A market.","properties":{"mic":{"$ref":"#/components/schemas/mic"},"bic":{"$ref":"#/components/schemas/bic"},"acronym":{"$ref":"#/components/schemas/market_acronym"},"name":{"$ref":"#/components/schemas/market_name"},"timezone":{"$ref":"#/components/schemas/market_timezone"}},"required":["acronym","name","timezone"]},"calendar_day":{"type":"object","description":"A calendar day.","properties":{"date":{"type":"string","format":"date","description":"The date of the calendar day.","example":"2025-01-02"},"pre_start":{"type":"string","format":"date-time","description":"The start time of the pre-market session.","example":"2025-01-02T04:00:00-05:00"},"pre_end":{"type":"string","format":"date-time","description":"The end time of the pre-market session.","example":"2025-01-02T09:30:00-05:00"},"lunch_start":{"type":"string","format":"date-time","description":"The start time of the lunch session."},"lunch_end":{"type":"string","format":"date-time","description":"The end time of the lunch session."},"core_start":{"type":"string","format":"date-time","description":"The start time of the core market session.","example":"2025-01-02T09:30:00-05:00"},"core_end":{"type":"string","format":"date-time","description":"The end time of the core market session.","example":"2025-01-02T16:00:00-05:00"},"post_start":{"type":"string","format":"date-time","description":"The start time of the after-hours session.","example":"2025-01-02T16:00:00-05:00"},"post_end":{"type":"string","format":"date-time","description":"The end time of the after-hours session.","example":"2025-01-02T20:00:00-05:00"},"settlement_date":{"type":"string","format":"date","description":"The settlement date.","example":"2025-01-03"}},"required":["date","core_start","core_end"]},"public_calendar_resp":{"type":"object","description":"Calendar response.","properties":{"market":{"$ref":"#/components/schemas/public_market"},"calendar":{"type":"array","description":"The market calendar.","items":{"$ref":"#/components/schemas/calendar_day"}}},"x-go-name":"CalendarResp","required":["market","calendar"]},"phase":{"type":"string","enum":["closed","pre","core","lunch","post"]},"clock":{"type":"object","properties":{"market":{"$ref":"#/components/schemas/public_market"},"timestamp":{"type":"string","format":"date-time","description":"The time on the clock."},"is_market_day":{"type":"boolean","description":"Whether the clock is on a market day."},"next_market_open":{"type":"string","format":"date-time","description":"Next market open timestamp"},"next_market_close":{"type":"string","description":"Next market close timestamp","format":"date-time"},"phase":{"$ref":"#/components/schemas/phase"},"phase_until":{"type":"string","format":"date-time","description":"The end of the current phase."}},"required":["market","timestamp","is_market_day","next_market_open","next_market_close","phase","phase_until"]},"clock_resp":{"type":"object","description":"Clock response.","properties":{"clocks":{"type":"array","items":{"$ref":"#/components/schemas/clock"}}},"x-go-name":"ClockResp","required":["clocks"]}},"headers":{"ratelimit_limit":{"schema":{"type":"integer"},"example":100,"description":"Request limit per minute."},"ratelimit_remaining":{"schema":{"type":"integer"},"example":90,"description":"Request limit per minute remaining."},"ratelimit_reset":{"schema":{"type":"integer"},"example":1674044551,"description":"The UNIX epoch when the remaining quota changes."}},"responses":{"400":{"description":"One of the request parameters is invalid. See the returned message for details.\n","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}}},"401":{"description":"Authentication headers are missing or invalid. Make sure you authenticate your request with a valid API key.\n"},"403":{"description":"The requested resource is forbidden.\n"},"429":{"description":"Too many requests. You hit the rate limit. Use the X-RateLimit-... response headers to make sure you're under the rate limit.\n","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}}},"500":{"description":"Internal server error. We recommend retrying these later. If the issue persists, please contact us on Slack or on the Community Forum.\n"}},"examples":{"EquityOrderResponse":{"value":{"id":"7b08df51-c1ac-453c-99f9-323a5f075f0d","client_order_id":"5680c4bc-9ac1-4a12-a44c-df427ba53032","created_at":"2023-12-12T22:31:24.668464435Z","updated_at":"2023-12-12T22:31:24.668464435Z","submitted_at":"2023-12-12T22:31:24.577215743Z","filled_at":null,"expired_at":null,"canceled_at":null,"failed_at":null,"replaced_at":null,"replaced_by":null,"replaces":null,"asset_id":"b0b6dd9d-8b9b-48a9-ba46-b9d54906e415","symbol":"AAPL","asset_class":"us_equity","notional":null,"qty":"2","filled_qty":"0","filled_avg_price":null,"order_class":"","order_type":"limit","type":"limit","side":"buy","time_in_force":"gtc","limit_price":"150","stop_price":null,"status":"accepted","extended_hours":false,"legs":null,"trail_percent":null,"trail_price":null,"hwm":null,"subtag":null,"source":null}},"OptionOrderResponse":{"value":{"id":"30a077fa-96f6-4f20-a052-4b921ee2f243","client_order_id":"58cd43a7-029e-457e-b77f-cd4f61f00f2a","created_at":"2023-12-12T21:35:49.102449524Z","updated_at":"2023-12-12T21:35:49.102504673Z","submitted_at":"2023-12-12T21:35:49.056332248Z","filled_at":null,"expired_at":null,"canceled_at":null,"failed_at":null,"replaced_at":null,"replaced_by":null,"replaces":null,"asset_id":"98359ef7-5124-49f3-85ea-5cf02df6defa","symbol":"AAPL250620C00100000","asset_class":"us_option","notional":null,"qty":"2","filled_qty":"0","filled_avg_price":null,"order_class":"simple","order_type":"limit","type":"limit","side":"buy","time_in_force":"day","limit_price":"10","stop_price":null,"status":"pending_new","extended_hours":false,"legs":null,"trail_percent":null,"trail_price":null,"hwm":null,"subtag":null,"source":null}},"CryptoOrderResponse":{"value":{"id":"38e482f3-79a8-4f75-a057-f07a1ec6a397","client_order_id":"5b5d3d67-06ad-4ffa-af65-a117d0fc5a59","created_at":"2023-12-12T22:36:51.337711497Z","updated_at":"2023-12-12T22:36:51.337754768Z","submitted_at":"2023-12-12T22:36:51.313261061Z","filled_at":null,"expired_at":null,"canceled_at":null,"failed_at":null,"replaced_at":null,"replaced_by":null,"replaces":null,"asset_id":"a1733398-6acc-4e92-af24-0d0667f78713","symbol":"ETH/USD","asset_class":"crypto","notional":null,"qty":"0.02","filled_qty":"0","filled_avg_price":null,"order_class":"","order_type":"limit","type":"limit","side":"buy","time_in_force":"gtc","limit_price":"2100","stop_price":null,"status":"pending_new","extended_hours":false,"legs":null,"trail_percent":null,"trail_price":null,"hwm":null,"subtag":null,"source":null}},"MultilegOptionsOrderResponse":{"value":{"id":"83f37e9f-6b1f-49ed-8fc6-3e6af716323f","client_order_id":"646b1fe6-b212-4f54-94c6-429e7bcdee04","created_at":"2024-12-10T16:15:53.677230742Z","updated_at":"2024-12-10T16:15:53.725139688Z","submitted_at":"2024-12-10T16:15:53.684952901Z","filled_at":"2024-12-10T16:15:53.694Z","expired_at":null,"canceled_at":null,"failed_at":null,"replaced_at":null,"replaced_by":null,"replaces":null,"asset_id":"","symbol":"","asset_class":"","notional":null,"qty":"1","filled_qty":"1","filled_avg_price":"1.28","order_class":"mleg","order_type":"limit","type":"limit","side":"","time_in_force":"day","limit_price":"10","stop_price":null,"status":"filled","extended_hours":false,"legs":[{"id":"df4ff24a-c58a-4e37-8b9f-ef32b83a11f2","client_order_id":"cc8cc104-fe43-476c-b25c-f62650fb73f9","created_at":"2024-12-10T16:15:53.677230742Z","updated_at":"2024-12-10T16:15:53.725091158Z","submitted_at":"2024-12-10T16:15:53.684952901Z","filled_at":"2024-12-10T16:15:53.694Z","expired_at":null,"canceled_at":null,"failed_at":null,"replaced_at":null,"replaced_by":null,"replaces":null,"asset_id":"f0ea14b2-8a49-4e9b-89d1-894c6e518a76","symbol":"AAPL241213C00250000","asset_class":"us_option","notional":null,"qty":"3","filled_qty":"3","filled_avg_price":"0.43","order_class":"mleg","order_type":"","type":"","side":"buy","position_intent":"buy_to_open","time_in_force":"day","limit_price":null,"stop_price":null,"status":"filled","extended_hours":false,"legs":null,"trail_percent":null,"trail_price":null,"hwm":null,"subtag":null,"source":null,"expires_at":"2024-12-10T21:00:00Z","ratio_qty":"3"},{"id":"ecd91110-c34d-4e9d-a7bf-a9c27c40f8b5","client_order_id":"0bd2d36d-4af2-4dfb-8418-333a5d5026fa","created_at":"2024-12-10T16:15:53.677230742Z","updated_at":"2024-12-10T16:15:53.708983759Z","submitted_at":"2024-12-10T16:15:53.684952901Z","filled_at":"2024-12-10T16:15:53.694Z","expired_at":null,"canceled_at":null,"failed_at":null,"replaced_at":null,"replaced_by":null,"replaces":null,"asset_id":"f89940db-eeb1-46e6-8f9b-bb1f27a0b395","symbol":"AAPL241213C00260000","asset_class":"us_option","notional":null,"qty":"1","filled_qty":"1","filled_avg_price":"0.01","order_class":"mleg","order_type":"","type":"","side":"sell","position_intent":"sell_to_open","time_in_force":"day","limit_price":null,"stop_price":null,"status":"filled","extended_hours":false,"legs":null,"trail_percent":null,"trail_price":null,"hwm":null,"subtag":null,"source":null,"expires_at":"2024-12-10T21:00:00Z","ratio_qty":"1"}],"trail_percent":null,"trail_price":null,"hwm":null,"subtag":null,"source":null}}}},"security":[{"API_Key":[],"API_Secret":[]}],"x-readme":{"explorer-enabled":true,"proxy-enabled":false}}
```

---

## File: `src/alpaca_mcp_server/specs/market-data-api.json`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/src/alpaca_mcp_server/specs/market-data-api.json`

```json
{"openapi":"3.0.0","info":{"title":"Market Data API","description":"Access real-time and historical market data for US equities, options, crypto, and foreign exchange data through the Alpaca REST and WebSocket APIs. There are APIs for Stock Pricing, Option Pricing, Crypto Pricing, Forex, Logos, Fixed income, Corporate Actions, Screener, and News.\n","version":"1.1","contact":{"name":"Alpaca Support","email":"support@alpaca.markets","url":"https://alpaca.markets/support"},"termsOfService":"https://s3.amazonaws.com/files.alpaca.markets/disclosures/library/TermsAndConditions.pdf","license":{"name":"Creative Commons Attribution Share Alike 4.0 International","url":"https://spdx.org/licenses/CC-BY-SA-4.0.html"}},"servers":[{"description":"Production","url":"https://data.alpaca.markets"},{"description":"Sandbox","url":"https://data.sandbox.alpaca.markets"}],"security":[{"apiKey":[],"apiSecret":[]}],"tags":[{"name":"Stock","description":"Endpoints for stocks."},{"name":"Option","description":"Endpoints for option data."},{"name":"Crypto","description":"Endpoints for cryptocurrencies."},{"name":"Crypto perpetual futures","description":"Endpoints for crypto perpetual futures."},{"name":"Fixed income","description":"Endpoints for fixed income data."},{"name":"Forex","description":"Endpoints for forex currency rates."},{"name":"Logos","description":"Endpoints for getting company logo images."},{"name":"Screener","description":"Endpoints for most active stocks and top movers."},{"name":"News","description":"Endpoints for getting news articles about the stock market."},{"name":"Corporate actions","description":"Corporate actions (splits, dividends, etc.)."}],"paths":{"/v1/corporate-actions":{"get":{"summary":"Corporate actions","tags":["Corporate actions"],"parameters":[{"$ref":"#/components/parameters/cas_symbols"},{"$ref":"#/components/parameters/cas_cusips"},{"$ref":"#/components/parameters/cas_types"},{"$ref":"#/components/parameters/cas_start"},{"$ref":"#/components/parameters/cas_end"},{"$ref":"#/components/parameters/cas_ids"},{"$ref":"#/components/parameters/cas_limit"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/corporate_actions_resp"}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CorporateActions","description":"This endpoint provides data about the corporate actions for each given symbol over a specified time period.\n\n> ⚠️ Warning\n>\n> Currently Alpaca has no guarantees on the creation time of corporate actions. There may be delays in receiving corporate actions from our data providers, and there may be delays in processing and making them available via this API. As a result, corporate actions may not be available immediately after they are announced.\n"}},"/v1beta1/fixed_income/latest/prices":{"get":{"summary":"Latest prices","tags":["Fixed income"],"parameters":[{"$ref":"#/components/parameters/isins"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/fixed_income_latest_prices_resp"},"examples":{"prices":{"value":{"prices":{"US912797KJ59":{"t":"2025-02-14T20:58:00.648Z","p":99.6459,"ytm":4.249,"ytw":4.249},"US912797KS58":{"t":"2025-02-14T20:58:00.648Z","p":99.3193,"ytm":4.2245,"ytw":4.2245},"US912797LB15":{"t":"2025-02-14T20:58:00.648Z","p":98.9927,"ytm":4.2165,"ytw":4.2165}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"FixedIncomeLatestPrices","description":"This endpoint returns the latest prices for the given fixed income securities.\n"}},"/v1beta1/forex/latest/rates":{"get":{"summary":"Latest rates for currency pairs","tags":["Forex"],"parameters":[{"$ref":"#/components/parameters/forex_currency_pairs"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/forex_latest_rates_resp"},"examples":{"USDJPY":{"value":{"rates":{"USDJPY":{"bp":127.752,"mp":127.779,"ap":128.112,"t":"2022-05-20T05:38:41.311530885Z"}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"LatestRates","description":"Get the latest forex rates for the given currency pairs.\n"}},"/v1beta1/forex/rates":{"get":{"summary":"Historical rates for currency pairs","tags":["Forex"],"parameters":[{"$ref":"#/components/parameters/forex_currency_pairs"},{"$ref":"#/components/parameters/forex_timeframe"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/sort"},{"$ref":"#/components/parameters/page_token"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/forex_rates_resp"},"examples":{"USDJPY":{"value":{"next_page_token":"VVNESlBZfDIwMjItMDEtMDNUMDA6MDM6MDBa","rates":{"USDJPY":[{"bp":114.192,"mp":115.144,"ap":115.18,"t":"2022-01-03T00:01:00Z"},{"bp":114.189,"mp":115.138,"ap":115.185,"t":"2022-01-03T00:02:00Z"},{"bp":115.122,"mp":115.131,"ap":115.148,"t":"2022-01-03T00:03:00Z"}]}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"Rates","description":"Get historical forex rates for the given currency pairs in the given time interval and at the given timeframe (snapshot frequency).\n"}},"/v1beta1/logos/{symbol}":{"get":{"summary":"Logos","tags":["Logos"],"parameters":[{"$ref":"#/components/parameters/symbol"},{"name":"placeholder","in":"query","description":"If true, returns a placeholder image when no logo is available. Defaults to true.","schema":{"type":"boolean","default":true}}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"image/png":{"schema":{"type":"string","format":"binary"}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"Logos","description":"Get the image of the company logo for the given symbol."}},"/v1beta1/news":{"get":{"summary":"News articles","parameters":[{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/news_sort"},{"name":"symbols","in":"query","schema":{"type":"string","example":"AAPL,TSLA,BTCUSD"},"description":"A comma-separated list of symbols for which to query news."},{"name":"limit","in":"query","schema":{"type":"integer","minimum":1,"maximum":50},"description":"Limit of news items to be returned for a result page.","example":10},{"name":"include_content","in":"query","schema":{"type":"boolean"},"description":"Boolean indicator to include content for news articles (if available)."},{"name":"exclude_contentless","in":"query","schema":{"type":"boolean"},"description":"Boolean indicator to exclude news articles that do not contain content."},{"$ref":"#/components/parameters/page_token"}],"responses":{"200":{"description":"OK","content":{"application/json":{"examples":{"news-response-example":{"value":{"news":[{"id":24843171,"headline":"Apple Leader in Phone Sales in China for Second Straight Month in November With 23.6% Share, According to Market Research Data","author":"Charles Gross","created_at":"2021-12-31T11:08:42Z","updated_at":"2021-12-31T11:08:43Z","summary":"This headline-only article is meant to show you why a stock is moving, the most difficult aspect of stock trading","content":"<p>This headline-only article is meant to show you why a stock is moving, the most difficult aspect of stock trading....</p>","url":"https://www.benzinga.com/news/21/12/24843171/apple-leader-in-phone-sales-in-china-for-second-straight-month-in-november-with-23-6-share-according","images":[],"symbols":["AAPL"],"source":"benzinga"}],"next_page_token":"MTY0MDk0ODkyMzAwMDAwMDAwMHwyNDg0MzE3MQ=="}}},"schema":{"$ref":"#/components/schemas/news_resp"}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"News","description":"Returns the latest news articles across stocks and crypto. By default, returns the latest 10 news articles.\n","tags":["News"]}},"/v1beta1/options/bars":{"get":{"summary":"Historical bars","tags":["Option"],"parameters":[{"$ref":"#/components/parameters/option_symbols"},{"$ref":"#/components/parameters/timeframe"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/option_bars_resp"},"examples":{"bars":{"value":{"bars":{"AAPL240419P00140000":[{"t":"2024-01-18T05:00:00Z","o":0.38,"h":0.38,"l":0.34,"c":0.34,"v":12,"n":7,"vw":0.3525}]},"next_page_token":"QUFQTHxNfDIwMjItMDEtMDNUMDk6MDA6MDAuMDAwMDAwMDAwWg=="}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"optionBars","description":"The historical option bars API provides aggregates for a list of option symbols between the specified dates.\n\nThe returned results are sorted by symbol first, then by bar timestamp.\nThis means that you are likely to see only one symbol in your first response if there are enough bars for that symbol to hit the limit you requested.\n\nIn these situations, if you keep requesting again with the `next_page_token` from the previous response, you will eventually reach the other symbols if any bars were found for them."}},"/v1beta1/options/meta/conditions/{ticktype}":{"get":{"summary":"Condition codes","tags":["Option"],"parameters":[{"name":"ticktype","in":"path","description":"The type of ticks.","required":true,"schema":{"type":"string","enum":["trade","quote"]}}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/option_conditions"}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"OptionMetaConditions","description":"Returns the mapping between the condition codes and names."}},"/v1beta1/options/meta/exchanges":{"get":{"summary":"Exchange codes","tags":["Option"],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/option_exchanges"}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"OptionMetaExchanges","description":"Returns the mapping between the option exchange codes and the corresponding exchange names."}},"/v1beta1/options/quotes/latest":{"get":{"summary":"Latest quotes","tags":["Option"],"parameters":[{"$ref":"#/components/parameters/option_symbols"},{"$ref":"#/components/parameters/option_feed"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/option_latest_quotes_resp"},"examples":{"quotes":{"value":{"quotes":{"AAPL240419P00140000":{"t":"2024-02-28T15:30:28.046330624Z","ax":"w","ap":0.16,"as":669,"bx":"W","bp":0.15,"bs":164,"c":"A"},"AAPL250321C00190000":{"t":"2024-02-28T15:47:13.663636224Z","ax":"X","ap":17,"as":622,"bx":"X","bp":16.75,"bs":368,"c":" "}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"OptionLatestQuotes","description":"The latest multi-quotes endpoint provides the latest bid and ask prices for each given contract symbol.\n"}},"/v1beta1/options/snapshots":{"get":{"summary":"Snapshots","tags":["Option"],"parameters":[{"$ref":"#/components/parameters/option_symbols"},{"$ref":"#/components/parameters/option_feed"},{"$ref":"#/components/parameters/option_updated_since"},{"$ref":"#/components/parameters/option_limit"},{"$ref":"#/components/parameters/page_token"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/option_snapshots_resp"},"examples":{"snapshots":{"value":{"snapshots":{"AAPL240426C00162500":{"greeks":{"delta":0.7521304109871954,"gamma":0.06241426404871288,"rho":0.009910739032549095,"theta":-0.2847623059595503,"vega":0.047540520834498785},"impliedVolatility":0.3372405712050441,"latestQuote":{"ap":4.3,"as":91,"ax":"B","bp":4.15,"bs":16,"bx":"C","c":"A","t":"2024-04-22T19:59:59.992734208Z"},"latestTrade":{"c":"I","p":4.1,"s":1,"t":"2024-04-22T19:57:32.589554432Z","x":"A"}}},"next_page_token":null}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"OptionSnapshots","description":"The snapshots endpoint provides the latest trade, latest quote and greeks for each given contract symbol.\n"}},"/v1beta1/options/snapshots/{underlying_symbol}":{"get":{"summary":"Option chain","tags":["Option"],"parameters":[{"$ref":"#/components/parameters/option_underlying_symbol"},{"$ref":"#/components/parameters/option_feed"},{"$ref":"#/components/parameters/option_limit"},{"$ref":"#/components/parameters/option_updated_since"},{"$ref":"#/components/parameters/page_token"},{"name":"type","in":"query","description":"Filter contracts by the type (call or put).","schema":{"type":"string","enum":["call","put"]}},{"name":"strike_price_gte","in":"query","description":"Filter contracts with strike price greater than or equal to the specified value.","schema":{"type":"number","format":"double"}},{"name":"strike_price_lte","in":"query","description":"Filter contracts with strike price less than or equal to the specified value.","schema":{"type":"number","format":"double"}},{"name":"expiration_date","in":"query","description":"Filter contracts by the exact expiration date (format: YYYY-MM-DD).","schema":{"type":"string","format":"date"}},{"name":"expiration_date_gte","in":"query","description":"Filter contracts with expiration date greater than or equal to the specified date.","schema":{"type":"string","format":"date"}},{"name":"expiration_date_lte","in":"query","description":"Filter contracts with expiration date less than or equal to the specified date.","schema":{"type":"string","format":"date"}},{"name":"root_symbol","in":"query","description":"Filter contracts by the root symbol.","schema":{"type":"string"},"example":"AAPL1"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/option_snapshots_resp"},"examples":{"snapshots":{"value":{"snapshots":{"AAPL240426C00162500":{"greeks":{"delta":0.7521304109871954,"gamma":0.06241426404871288,"rho":0.009910739032549095,"theta":-0.2847623059595503,"vega":0.047540520834498785},"impliedVolatility":0.3372405712050441,"latestQuote":{"ap":4.3,"as":91,"ax":"B","bp":4.15,"bs":16,"bx":"C","c":"A","t":"2024-04-22T19:59:59.992734208Z"},"latestTrade":{"c":"I","p":4.1,"s":1,"t":"2024-04-22T19:57:32.589554432Z","x":"A"}}},"next_page_token":null}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"OptionChain","description":"The option chain endpoint provides the latest trade, latest quote, and greeks for each contract symbol of the underlying symbol.\n"}},"/v1beta1/options/trades":{"get":{"summary":"Historical trades","tags":["Option"],"parameters":[{"$ref":"#/components/parameters/option_symbols"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/option_trades_resp"},"examples":{"trades":{"value":{"trades":{"AAPL240112C00182500":[{"t":"2024-01-18T15:03:44.56339456Z","x":"B","p":0.37,"s":1,"c":"I"},{"t":"2024-01-18T16:02:38.994758144Z","x":"C","p":0.34,"s":1,"c":"g"}]},"next_page_token":"QUFQTHwyMDIyLTAxLTAzVDA5OjAwOjAwLjI0NDgzOTY4MFp8UHwwOTIyMzM3MjAzNjg1NDc3NTgxMA=="}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"OptionTrades","description":"The historical option trades API provides trade data for a list of contract symbols between the specified dates.\n\nThe returned results are sorted by symbol first then by trade timestamp.\nThis means that you are likely to see only one symbol in your first response if there are enough trades for that symbol to hit the limit you requested.\n\nIn these situations, if you keep requesting again with the `next_page_token` from the previous response, you will eventually reach the other symbols if any trades were found for them."}},"/v1beta1/options/trades/latest":{"get":{"summary":"Latest trades","tags":["Option"],"parameters":[{"$ref":"#/components/parameters/option_symbols"},{"$ref":"#/components/parameters/option_feed"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/option_latest_trades_resp"},"examples":{"trades":{"value":{"trades":{"AAPL250321C00190000":{"t":"2024-02-28T15:26:12.728701696Z","x":"B","p":17.15,"s":900,"c":"e"}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"OptionLatestTrades","description":"The latest multi-trades endpoint provides the latest historical trade data for multiple given contract symbols.\n"}},"/v1beta1/screener/stocks/most-actives":{"get":{"summary":"Most active stocks","tags":["Screener"],"parameters":[{"$ref":"#/components/parameters/most_actives_by"},{"$ref":"#/components/parameters/most_actives_top"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/most_actives_resp"}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"MostActives","description":"Returns the most active stocks by volume or trade count based on real time SIP data. By default, returns the top 10 symbols by volume.\n"}},"/v1beta1/screener/{market_type}/movers":{"get":{"summary":"Top market movers","tags":["Screener"],"parameters":[{"$ref":"#/components/parameters/movers_market_type"},{"$ref":"#/components/parameters/movers_top"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/movers_resp"},"examples":{"movers":{"value":{"gainers":[{"symbol":"AGRI","percent_change":145.56,"change":2.46,"price":4.15},{"symbol":"GRCYW","percent_change":85.63,"change":0.03,"price":0.0594}],"losers":[{"symbol":"MTACW","percent_change":-63.07,"change":-0.26,"price":0.1502},{"symbol":"TIG","percent_change":-51.21,"change":-3.61,"price":3.435}],"market_type":"stocks","last_updated":"2022-03-10T17:53:30.088309839Z"}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"Movers","description":"Returns the top market movers (gainers and losers) based on real time SIP data.\nThe change for each symbol is calculated from the previous closing price and the latest closing price.\n\nFor stocks, the endpoint resets at market open. Until then, it shows the previous market day's movers.\nThe data is split-adjusted. Only tradable symbols in exchanges are included.\n\nFor crypto, the endpoint resets at midnight."}},"/v1beta1/crypto-perps/{loc}/latest/bars":{"get":{"summary":"Latest bars","tags":["Crypto perpetual futures"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_perp_loc"},{"$ref":"#/components/parameters/crypto_perp_symbols"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_latest_bars_resp"},"examples":{"bars":{"value":{"bars":{"BTCUSDT.P":{"t":"2022-05-27T10:18:00Z","o":28999,"h":29003,"l":28999,"c":29003,"v":0.01,"n":4,"vw":29001}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoPerpLatestBars","description":"The latest bars endpoint returns the latest bar data for the crypto perpetual futures symbols provided.\n"}},"/v1beta1/crypto-perps/{loc}/latest/pricing":{"get":{"summary":"Latest pricing","tags":["Crypto perpetual futures"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_perp_loc"},{"$ref":"#/components/parameters/crypto_perp_symbols"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_perp_latest_futures_pricing_resp"},"examples":{"pricing":{"value":{"pricing":{"BTCUSDT.P":{"t":"2022-05-27T10:18:00Z","ft":"2022-05-27T10:18:00Z","oi":90.7367,"ip":50702.8,"mp":50652.3553,"fr":0.000565699}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoPerpLatestFuturesPricing","description":"The latest futures pricing endpoint returns the latest pricing data for the crypto perpetual futures symbols provided.\n"}},"/v1beta1/crypto-perps/{loc}/latest/orderbooks":{"get":{"summary":"Latest orderbook","tags":["Crypto perpetual futures"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_perp_loc"},{"$ref":"#/components/parameters/crypto_perp_symbols"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_latest_orderbooks_resp"},"examples":{"orderbooks":{"value":{"orderbooks":{"BTCUSDT.P":{"t":"2022-06-24T08:00:14.137774336Z","b":[{"p":20846,"s":0.1902},{"p":20350,"s":0}],"a":[{"p":20902,"s":0.0097},{"p":21444,"s":0}]}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoPerpLatestOrderbooks","description":"The latest orderbook endpoint returns the latest bid and ask orderbook for the crypto perpetual futures symbols provided.\n"}},"/v1beta1/crypto-perps/{loc}/latest/quotes":{"get":{"summary":"Latest quotes","tags":["Crypto perpetual futures"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_perp_loc"},{"$ref":"#/components/parameters/crypto_perp_symbols"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_latest_quotes_resp"},"examples":{"quotes":{"value":{"quotes":{"ETHUSDT.P":{"t":"2022-05-26T11:47:18.499478272Z","bp":1817,"bs":4.76,"ap":1817.7,"as":6.137},"BTCUSDT.P":{"t":"2022-05-26T11:47:18.44347136Z","bp":29058,"bs":0.3544,"ap":29059,"as":3.252}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoPerpLatestQuotes","description":"The latest quotes endpoint returns the latest bid and ask prices for the crypto perpetual futures symbols provided.\n"}},"/v1beta1/crypto-perps/{loc}/latest/trades":{"get":{"summary":"Latest trades","tags":["Crypto perpetual futures"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_perp_loc"},{"$ref":"#/components/parameters/crypto_perp_symbols"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_latest_trades_resp"},"examples":{"trades":{"value":{"trades":{"BTCUSDT.P":{"t":"2022-05-18T12:01:00.537052Z","p":29791,"s":0.0016,"tks":"S","i":31455289},"ETHUSDT.P":{"t":"2022-05-18T12:01:00.363547Z","p":2027.6,"s":0.06,"tks":"S","i":31455287}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoPerpLatestTrades","description":"The latest trades endpoint returns the latest trade data for the crypto perpetual futures symbols provided.\n"}},"/v1beta3/crypto/{loc}/bars":{"get":{"summary":"Historical bars","tags":["Crypto"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_historical_loc"},{"$ref":"#/components/parameters/crypto_symbols"},{"$ref":"#/components/parameters/timeframe"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_bars_resp"},"examples":{"bars":{"value":{"bars":{"BTC/USD":[{"t":"2022-05-27T10:18:00Z","o":28999,"h":29003,"l":28999,"c":29003,"v":0.01,"n":4,"vw":29001}]},"next_page_token":"MTY0MDk0ODkyMzAwMDAwMDAwMHwyNDg0MzE3MQ=="}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoBars","description":"The crypto bars API provides historical aggregates for a list of crypto symbols between the specified dates.\n"}},"/v1beta3/crypto/{loc}/latest/bars":{"get":{"summary":"Latest bars","tags":["Crypto"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_latest_loc"},{"$ref":"#/components/parameters/crypto_symbols"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_latest_bars_resp"},"examples":{"bars":{"value":{"bars":{"BTC/USD":{"t":"2022-05-27T10:18:00Z","o":28999,"h":29003,"l":28999,"c":29003,"v":0.01,"n":4,"vw":29001}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoLatestBars","description":"The latest multi-bars endpoint returns the latest minute-aggregated historical bar data for each of the crypto symbols provided.\n"}},"/v1beta3/crypto/{loc}/latest/orderbooks":{"get":{"summary":"Latest orderbook","tags":["Crypto"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_latest_loc"},{"$ref":"#/components/parameters/crypto_symbols"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_latest_orderbooks_resp"},"examples":{"orderbooks":{"value":{"orderbooks":{"BTC/USD":{"t":"2022-06-24T08:00:14.137774336Z","b":[{"p":20846,"s":0.1902},{"p":20350,"s":0}],"a":[{"p":20902,"s":0.0097},{"p":21444,"s":0}]}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoLatestOrderbooks","description":"The latest orderbook endpoint returns the latest bid and ask orderbook for the crypto symbols provided.\n"}},"/v1beta3/crypto/{loc}/latest/quotes":{"get":{"summary":"Latest quotes","tags":["Crypto"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_latest_loc"},{"$ref":"#/components/parameters/crypto_symbols"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_latest_quotes_resp"},"examples":{"quotes":{"value":{"quotes":{"ETH/USD":{"t":"2022-05-26T11:47:18.499478272Z","bp":1817,"bs":4.76,"ap":1817.7,"as":6.137},"BTC/USD":{"t":"2022-05-26T11:47:18.44347136Z","bp":29058,"bs":0.3544,"ap":29059,"as":3.252}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoLatestQuotes","description":"The latest quotes endpoint returns the latest bid and ask prices for the crypto symbols provided.\n"}},"/v1beta3/crypto/{loc}/latest/trades":{"get":{"summary":"Latest trades","tags":["Crypto"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_latest_loc"},{"$ref":"#/components/parameters/crypto_symbols"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_latest_trades_resp"},"examples":{"trades":{"value":{"trades":{"BTC/USD":{"t":"2022-05-18T12:01:00.537052Z","p":29791,"s":0.0016,"tks":"S","i":31455289},"ETH/USD":{"t":"2022-05-18T12:01:00.363547Z","p":2027.6,"s":0.06,"tks":"S","i":31455287}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoLatestTrades","description":"The latest trades endpoint returns the latest trade data for the crypto symbols provided.\n"}},"/v1beta3/crypto/{loc}/quotes":{"get":{"summary":"Historical quotes","tags":["Crypto"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_historical_loc"},{"$ref":"#/components/parameters/crypto_symbols"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_quotes_resp"},"examples":{"quotes":{"value":{"quotes":{"BTC/USD":[{"t":"2022-05-26T11:47:18.44347136Z","bp":29058,"bs":0.3544,"ap":29059,"as":3.252}],"ETH/USD":[{"t":"2022-05-26T11:47:18.499478272Z","bp":1817,"bs":4.76,"ap":1817.7,"as":6.137}]},"next_page_token":null}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoQuotes","description":"The crypto quotes API provides historical quote data for a list of crypto symbols between the specified dates.\nThe oldest date to retrieve historical quotes of us-1 location is 14th October, 2025 12AM UTC."}},"/v1beta3/crypto/{loc}/snapshots":{"get":{"summary":"Snapshots","tags":["Crypto"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_latest_loc"},{"$ref":"#/components/parameters/crypto_symbols"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_snapshots_resp"},"examples":{"snapshots":{"value":{"snapshots":{"BTC/USD":{"dailyBar":{"c":31744,"h":31807,"l":31416,"n":438,"o":31660,"t":"2022-05-31T05:00:00Z","v":67.3518,"vw":31582.7034526175},"latestQuote":{"ap":31742,"as":0.395,"bp":31741,"bs":0.395,"t":"2022-05-31T11:55:58.507608832Z"},"latestTrade":{"i":32396097,"p":31744,"s":0.0543,"t":"2022-05-31T11:53:45.027481Z","tks":"B"},"minuteBar":{"c":31744,"h":31744,"l":31744,"n":2,"o":31744,"t":"2022-05-31T11:53:00Z","v":0.0886,"vw":31744},"prevDailyBar":{"c":31649,"h":32251,"l":30251,"n":8221,"o":30310,"t":"2022-05-30T05:00:00Z","v":1856.4065,"vw":30877.2751897281}}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoSnapshots","description":"The snapshots endpoint returns the latest trade, latest quote, latest minute bar, latest daily bar, and previous daily bar data for crypto symbols.\n"}},"/v1beta3/crypto/{loc}/trades":{"get":{"summary":"Historical trades","tags":["Crypto"],"security":[],"parameters":[{"$ref":"#/components/parameters/crypto_historical_loc"},{"$ref":"#/components/parameters/crypto_symbols"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/crypto_trades_resp"},"examples":{"trades":{"value":{"trades":{"BTC/USD":[{"t":"2022-05-18T12:01:00.537052Z","p":29791,"s":0.0016,"tks":"S","i":31455289}],"ETH/USD":[{"t":"2022-05-18T12:01:00.363547Z","p":2027.6,"s":0.06,"tks":"S","i":31455287},{"t":"2022-05-18T12:01:00.363547Z","p":2027.6,"s":0.136,"tks":"S","i":31455288}]},"next_page_token":null}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"CryptoTrades","description":"The crypto trades API provides historical trade data for a list of crypto symbols between the specified dates.\n"}},"/v2/stocks/auctions":{"get":{"summary":"Historical auctions","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbols"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/stock_asof"},{"$ref":"#/components/parameters/stock_auction_feed"},{"$ref":"#/components/parameters/stock_currency"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_auctions_resp"},"examples":{"auction":{"value":{"auctions":{"AAPL":[{"d":"2022-10-12","o":[{"c":"Q","p":139.12,"t":"2022-10-12T13:30:00.188390144Z","x":"P"},{"c":"O","p":138.99,"t":"2022-10-12T13:30:01.474665705Z","x":"Q"},{"c":"Q","p":138.99,"t":"2022-10-12T13:30:01.475216565Z","x":"Q"}],"c":[{"c":"6","p":138.36,"t":"2022-10-12T20:00:00.120649216Z","x":"P"},{"c":"M","p":138.36,"t":"2022-10-12T20:00:00.125925888Z","x":"P"},{"c":"6","p":138.34,"t":"2022-10-12T20:00:00.875570864Z","x":"Q"},{"c":"M","p":138.34,"t":"2022-10-12T20:00:00.875603021Z","x":"Q"}]},{"d":"2022-10-13","o":[{"c":"Q","p":134.8,"t":"2022-10-13T13:30:00.20304384Z","x":"P"},{"c":"O","p":135,"t":"2022-10-13T13:30:01.688322951Z","x":"Q"},{"c":"Q","p":135,"t":"2022-10-13T13:30:01.699259366Z","x":"Q"}],"c":[{"c":"M","p":142.94,"t":"2022-10-13T20:00:00.166980864Z","x":"P"}]}],"TSLA":[{"d":"2022-10-12","o":[{"c":"Q","p":215.39,"t":"2022-10-12T13:30:00.065736192Z","x":"P"},{"c":"O","p":215.79,"t":"2022-10-12T13:30:01.349399539Z","x":"Q"},{"c":"Q","p":215.79,"t":"2022-10-12T13:30:01.349965972Z","x":"Q"}],"c":[{"c":"M","p":217.23,"t":"2022-10-12T20:00:00.124164096Z","x":"P"},{"c":"6","p":217.24,"t":"2022-10-12T20:00:00.469874365Z","x":"Q"},{"c":"M","p":217.24,"t":"2022-10-12T20:00:00.469912641Z","x":"Q"}]},{"d":"2022-10-13","o":[{"c":"Q","p":208.37,"t":"2022-10-13T13:30:00.068034304Z","x":"P"},{"c":"O","p":208.49,"t":"2022-10-13T13:30:01.079567733Z","x":"Q"},{"c":"Q","p":208.49,"t":"2022-10-13T13:30:01.090802222Z","x":"Q"}],"c":[{"c":"M","p":221.7,"t":"2022-10-13T20:00:00.152902912Z","x":"P"}]}]},"next_page_token":null}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockAuctions","description":"The historical auctions endpoint provides auction prices for a list of stock symbols between the specified dates.\n"}},"/v2/stocks/bars":{"get":{"summary":"Historical bars","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbols"},{"$ref":"#/components/parameters/timeframe"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/stock_adjustment"},{"$ref":"#/components/parameters/stock_asof"},{"$ref":"#/components/parameters/stock_historical_feed"},{"$ref":"#/components/parameters/stock_currency"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_bars_resp"},"examples":{"bars":{"value":{"bars":{"AAPL":[{"t":"2022-01-03T09:00:00Z","o":178.26,"h":178.26,"l":178.21,"c":178.21,"v":1118,"n":65,"vw":178.235733}]},"next_page_token":"QUFQTHxNfDIwMjItMDEtMDNUMDk6MDA6MDAuMDAwMDAwMDAwWg=="}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockBars","description":"The historical stock bars API provides aggregates for a list of stock symbols between the specified dates.\n\nThe returned results are sorted by symbol first, then by bar timestamp. This means that you are likely to see only one symbol in your first response if there are enough bars for that symbol to hit the limit you requested.\n\nIn these situations, if you keep requesting again with the `next_page_token` from the previous response, you will eventually reach the other symbols if any bars were found for them."}},"/v2/stocks/bars/latest":{"get":{"summary":"Latest bars","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbols"},{"$ref":"#/components/parameters/stock_latest_feed"},{"$ref":"#/components/parameters/stock_currency"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_latest_bars_resp"},"examples":{"bars":{"value":{"bars":{"TSLA":{"t":"2022-08-17T08:57:00Z","o":914.3,"h":914.3,"l":914.3,"c":914.3,"v":751,"n":20,"vw":914.294634},"AAPL":{"t":"2022-08-17T08:58:00Z","o":172.81,"h":172.81,"l":172.78,"c":172.79,"v":1002,"n":20,"vw":172.791417}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockLatestBars","description":"The latest bars endpoint provides the latest minute bar for the given ticker symbols.\n"}},"/v2/stocks/meta/conditions/{ticktype}":{"get":{"summary":"Condition codes","tags":["Stock"],"parameters":[{"name":"ticktype","in":"path","description":"The type of ticks.","required":true,"schema":{"type":"string","enum":["trade","quote"]}},{"name":"tape","in":"query","description":"The one character name of the tape.","required":true,"schema":{"type":"string","enum":["A","B","C"]}}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_conditions"}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockMetaConditions","description":"Returns the mapping between the condition codes and names."}},"/v2/stocks/meta/exchanges":{"get":{"summary":"Exchange codes","tags":["Stock"],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_exchanges"}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockMetaExchanges","description":"Returns the mapping between the stock exchange codes and the corresponding exchange names.\n"}},"/v2/stocks/quotes":{"get":{"summary":"Historical quotes","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbols"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/stock_asof"},{"$ref":"#/components/parameters/stock_historical_feed"},{"$ref":"#/components/parameters/stock_currency"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_quotes_resp"},"examples":{"quotes":{"value":{"quotes":{"AAPL":[{"t":"2022-01-03T09:00:00.028160898Z","ax":" ","ap":0,"as":0,"bx":"Q","bp":177.92,"bs":4,"c":["Y"],"z":"C"},{"t":"2022-01-03T09:00:00.028294451Z","ax":"Q","ap":178.8,"as":4,"bx":"Q","bp":177.92,"bs":4,"c":["R"],"z":"C"}]},"next_page_token":"QUFQTHwyMDIyLTAxLTAzVDA5OjAwOjAwLjAyODI5NDQ1MVp8MjM3NjQ0Qzg="}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockQuotes","description":"The historical stock quotes API provides quote data for a list of stock symbols between the specified dates.\n\nThe returned results are sorted by symbol first, then by the quote timestamp. This means that you are likely to see only one symbol in your first response if there are enough quotes for that symbol to hit the limit you requested.\n\nIn these situations, if you keep requesting again with the `next_page_token` from the previous response, you will eventually reach the other symbols if any quotes were found for them."}},"/v2/stocks/quotes/latest":{"get":{"summary":"Latest quotes","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbols"},{"$ref":"#/components/parameters/stock_latest_feed"},{"$ref":"#/components/parameters/stock_currency"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_latest_quotes_resp"},"examples":{"quotes":{"value":{"quotes":{"AAPL":{"t":"2022-08-17T10:07:40.286587431Z","ax":"Q","ap":172.7,"as":1,"bx":"Q","bp":172.62,"bs":2,"c":["R"],"z":"C"},"TSLA":{"t":"2022-08-17T10:07:49.387064037Z","ax":"Q","ap":911.6,"as":1,"bx":"K","bp":911.3,"bs":1,"c":["R"],"z":"C"}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockLatestQuotes","description":"The latest quotes endpoint provides the latest best bid and ask prices for the given ticker symbols.\n"}},"/v2/stocks/snapshots":{"get":{"summary":"Snapshots","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbols"},{"$ref":"#/components/parameters/stock_latest_feed"},{"$ref":"#/components/parameters/stock_currency"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_snapshots_resp"},"examples":{"snapshots":{"value":{"AAPL":{"latestTrade":{"t":"2022-08-17T10:18:24.114694956Z","x":"Q","p":172.61,"s":160,"c":["@","T"],"i":1011,"z":"C"},"latestQuote":{"t":"2022-08-17T10:18:27.052763263Z","ax":"Q","ap":172.7,"as":5,"bx":"Q","bp":172.6,"bs":2,"c":["R"],"z":"C"},"minuteBar":{"t":"2022-08-17T10:16:00Z","o":172.69,"h":172.69,"l":172.69,"c":172.69,"v":106,"n":3,"vw":172.688113},"dailyBar":{"t":"2022-08-16T04:00:00Z","o":172.62,"h":173.71,"l":171.6618,"c":173.03,"v":56457696,"n":515139,"vw":172.743391},"prevDailyBar":{"t":"2022-08-15T04:00:00Z","o":171.5,"h":173.39,"l":171.345,"c":173.19,"v":54091719,"n":501626,"vw":172.625371}},"TSLA":{"latestTrade":{"t":"2022-08-17T10:13:12.952851456Z","x":"P","p":911.99,"s":100,"c":["@","T"],"i":2047,"z":"C"},"latestQuote":{"t":"2022-08-17T10:18:23.84717767Z","ax":"P","ap":911.75,"as":4,"bx":"Q","bp":911.31,"bs":1,"c":["R"],"z":"C"},"minuteBar":{"t":"2022-08-17T10:13:00Z","o":911.99,"h":911.99,"l":911.99,"c":911.99,"v":740,"n":64,"vw":911.780405},"dailyBar":{"t":"2022-08-16T04:00:00Z","o":935,"h":944,"l":908.65,"c":919.69,"v":29378774,"n":805572,"vw":925.215087},"prevDailyBar":{"t":"2022-08-15T04:00:00Z","o":905.32,"h":939.4,"l":903.69,"c":927.96,"v":29786389,"n":825109,"vw":923.982755}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockSnapshots","description":"The snapshot endpoint for multiple tickers provides the latest trade, latest quote, minute bar, daily bar, and previous daily bar data for each given ticker symbol.\n"}},"/v2/stocks/trades":{"get":{"summary":"Historical trades","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbols"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/stock_asof"},{"$ref":"#/components/parameters/stock_historical_feed"},{"$ref":"#/components/parameters/stock_currency"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_trades_resp"},"examples":{"trades":{"value":{"trades":{"AAPL":[{"t":"2022-01-03T09:00:00.086175744Z","x":"P","p":178.26,"s":246,"c":["@","T"],"i":1,"z":"C"},{"t":"2022-01-03T09:00:00.24483968Z","x":"P","p":178.26,"s":1,"c":["@","F","T","I"],"i":2,"z":"C"}]},"next_page_token":"QUFQTHwyMDIyLTAxLTAzVDA5OjAwOjAwLjI0NDgzOTY4MFp8UHwwOTIyMzM3MjAzNjg1NDc3NTgxMA=="}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockTrades","description":"The historical stock trades API provides trade data for a list of stock symbols between the specified dates.\n\nThe returned results are sorted by symbol first then by trade timestamp. This means that you are likely to see only one symbol in your first response if there are enough trades for that symbol to hit the limit you requested.\n\nIn these situations, if you keep requesting again with the `next_page_token` from the previous response, you will eventually reach the other symbols if any trades were found for them."}},"/v2/stocks/trades/latest":{"get":{"summary":"Latest trades","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbols"},{"$ref":"#/components/parameters/stock_latest_feed"},{"$ref":"#/components/parameters/stock_currency"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_latest_trades_resp"},"examples":{"trades":{"value":{"trades":{"AAPL":{"t":"2022-08-17T09:50:43.361102308Z","x":"Q","p":172.78,"s":100,"c":["@","F","T"],"i":826,"z":"C"}}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockLatestTrades","description":"The latest trades endpoint provides the latest trades for the given ticker symbols.\n\nTrades with any conditions that causes them to not update the bar price are excluded. For example a trade with condition `I` (odd lot) will never appear on this endpoint. You can find the complete list of excluded conditions in [this FAQ](https://docs.alpaca.markets/docs/market-data-faq#how-are-bars-aggregated)."}},"/v2/stocks/{symbol}/auctions":{"get":{"summary":"Historical auctions (single)","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbol"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/stock_asof"},{"$ref":"#/components/parameters/stock_auction_feed"},{"$ref":"#/components/parameters/stock_currency"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_auctions_resp_single"},"examples":{"auctions":{"value":{"auctions":[{"d":"2022-10-13","o":[{"c":"Q","p":208.37,"t":"2022-10-13T13:30:00.068034304Z","x":"P"},{"c":"O","p":208.49,"t":"2022-10-13T13:30:01.079567733Z","x":"Q"},{"c":"Q","p":208.49,"t":"2022-10-13T13:30:01.090802222Z","x":"Q"}],"c":[{"c":"M","p":221.7,"t":"2022-10-13T20:00:00.152902912Z","x":"P"}]}],"next_page_token":null,"symbol":"TSLA"}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockAuctionSingle","description":"The historical auctions endpoint provides auction prices for the given stock symbol between the specified dates.\n"}},"/v2/stocks/{symbol}/bars":{"get":{"summary":"Historical bars (single symbol)","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbol"},{"$ref":"#/components/parameters/timeframe"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/stock_adjustment"},{"$ref":"#/components/parameters/stock_asof"},{"$ref":"#/components/parameters/stock_historical_feed"},{"$ref":"#/components/parameters/stock_currency"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_bars_resp_single"},"examples":{"bars":{"value":{"bars":[{"t":"2022-01-03T09:00:00Z","o":178.26,"h":178.26,"l":178.21,"c":178.21,"v":1118,"n":65,"vw":178.235733}],"symbol":"AAPL","next_page_token":"QUFQTHxNfDIwMjItMDEtMDNUMDk6MDA6MDAuMDAwMDAwMDAwWg=="}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockBarSingle","description":"The historical stock bars API provides aggregates for the stock symbol between the specified dates."}},"/v2/stocks/{symbol}/bars/latest":{"get":{"summary":"Latest bar (single symbol)","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbol"},{"$ref":"#/components/parameters/stock_latest_feed"},{"$ref":"#/components/parameters/stock_currency"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_latest_bars_resp_single"},"examples":{"bar":{"value":{"bar":{"t":"2022-08-17T09:07:00Z","o":172.98,"h":173.04,"l":172.98,"c":173,"v":2748,"n":49,"vw":173.007817},"symbol":"AAPL"}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockLatestBarSingle","description":"The latest bar endpoint returns the latest minute bar for the given ticker symbol.\n"}},"/v2/stocks/{symbol}/quotes":{"get":{"summary":"Historical quotes (single symbol)","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbol"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/stock_asof"},{"$ref":"#/components/parameters/stock_historical_feed"},{"$ref":"#/components/parameters/stock_currency"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_quotes_resp_single"},"examples":{"quotes":{"value":{"quotes":[{"t":"2022-01-03T09:00:00.028160898Z","ax":" ","ap":0,"as":0,"bx":"Q","bp":177.92,"bs":4,"c":["Y"],"z":"C"},{"t":"2022-01-03T09:00:00.028294451Z","ax":"Q","ap":178.8,"as":4,"bx":"Q","bp":177.92,"bs":4,"c":["R"],"z":"C"}],"symbol":"AAPL","next_page_token":"QUFQTHwyMDIyLTAxLTAzVDA5OjAwOjAwLjAyODI5NDQ1MVp8MjM3NjQ0Qzg="}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockQuoteSingle","description":"The historical stock quotes API provides quote data for a stock symbol between the specified dates."}},"/v2/stocks/{symbol}/quotes/latest":{"get":{"summary":"Latest quote (single symbol)","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbol"},{"$ref":"#/components/parameters/stock_latest_feed"},{"$ref":"#/components/parameters/stock_currency"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_latest_quotes_resp_single"},"examples":{"quotes":{"value":{"symbol":"AAPL","quote":{"t":"2022-08-17T10:09:34.055031265Z","ax":"Q","ap":172.7,"as":1,"bx":"Q","bp":172.6,"bs":2,"c":["R"],"z":"C"}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockLatestQuoteSingle","description":"The latest quote endpoint provides the latest best bid and ask prices for a given ticker symbol.\n"}},"/v2/stocks/{symbol}/snapshot":{"get":{"summary":"Snapshot (single symbol)","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbol"},{"$ref":"#/components/parameters/stock_latest_feed"},{"$ref":"#/components/parameters/stock_currency"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_snapshots_resp_single"},"examples":{"snapshot":{"value":{"symbol":"AAPL","latestTrade":{"t":"2022-08-17T10:19:30.735811394Z","x":"Q","p":172.55,"s":229,"c":["@","T"],"i":1040,"z":"C"},"latestQuote":{"t":"2022-08-17T10:19:30.805564086Z","ax":"Q","ap":172.65,"as":1,"bx":"P","bp":172.51,"bs":1,"c":["R"],"z":"C"},"minuteBar":{"t":"2022-08-17T10:18:00Z","o":172.65,"h":172.65,"l":172.6,"c":172.6,"v":3746,"n":57,"vw":172.618377},"dailyBar":{"t":"2022-08-16T04:00:00Z","o":172.62,"h":173.71,"l":171.6618,"c":173.03,"v":56457696,"n":515139,"vw":172.743391},"prevDailyBar":{"t":"2022-08-15T04:00:00Z","o":171.5,"h":173.39,"l":171.345,"c":173.19,"v":54091719,"n":501626,"vw":172.625371}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockSnapshotSingle","description":"The snapshot endpoint provides the latest trade, latest quote, minute bar, daily bar, and previous daily bar data for a given ticker symbol.\n"}},"/v2/stocks/{symbol}/trades":{"get":{"summary":"Historical trades (single symbol)","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbol"},{"$ref":"#/components/parameters/start"},{"$ref":"#/components/parameters/end"},{"$ref":"#/components/parameters/limit"},{"$ref":"#/components/parameters/stock_asof"},{"$ref":"#/components/parameters/stock_historical_feed"},{"$ref":"#/components/parameters/stock_currency"},{"$ref":"#/components/parameters/page_token"},{"$ref":"#/components/parameters/sort"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_trades_resp_single"},"examples":{"trades":{"value":{"trades":[{"t":"2022-01-03T17:00:00.029591476Z","x":"Q","p":181.47,"s":1,"c":["@","I"],"i":73833,"z":"C"},{"t":"2022-01-03T17:00:00.029591476Z","x":"Q","p":181.47,"s":1,"c":["@","I"],"i":73834,"z":"C"}],"symbol":"AAPL","next_page_token":"QUFQTHwyMDIyLTAxLTAzVDE3OjAwOjAwLjAyOTU5MTQ3Nlp8UXwwOTIyMzM3MjAzNjg1NDg0OTY0Mg=="}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockTradeSingle","description":"The historical stock trades API provides trade data for a stock symbol between the specified dates."}},"/v2/stocks/{symbol}/trades/latest":{"get":{"summary":"Latest trade (single symbol)","tags":["Stock"],"parameters":[{"$ref":"#/components/parameters/stock_symbol"},{"$ref":"#/components/parameters/stock_latest_feed"},{"$ref":"#/components/parameters/stock_currency"}],"responses":{"200":{"description":"OK","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}},"content":{"application/json":{"schema":{"$ref":"#/components/schemas/stock_latest_trades_resp_single"},"examples":{"trade":{"value":{"symbol":"AAPL","trade":{"t":"2022-08-17T09:53:16.845580544Z","x":"P","p":172.6,"s":100,"c":["@","T"],"i":689,"z":"C"}}}}}}},"400":{"$ref":"#/components/responses/400"},"401":{"$ref":"#/components/responses/401"},"403":{"$ref":"#/components/responses/403"},"429":{"$ref":"#/components/responses/429"},"500":{"$ref":"#/components/responses/500"}},"operationId":"StockLatestTradeSingle","description":"The latest trade endpoint provides the latest trade for the given ticker symbol.\n\nTrades with any conditions that causes them to not update the bar price are excluded. For example a trade with condition `I` (odd lot) will never appear on this endpoint. You can find the complete list of excluded conditions in [this FAQ](https://docs.alpaca.markets/docs/market-data-faq#how-are-bars-aggregated)."}}},"components":{"securitySchemes":{"apiKey":{"type":"apiKey","in":"header","name":"APCA-API-KEY-ID"},"apiSecret":{"type":"apiKey","in":"header","name":"APCA-API-SECRET-KEY"}},"parameters":{"cas_symbols":{"name":"symbols","description":"A comma-separated list of symbols.","in":"query","schema":{"type":"string"},"example":"AAPL,TSLA"},"cas_cusips":{"name":"cusips","description":"A comma-separated list of CUSIPs.","in":"query","schema":{"type":"string"},"example":"037833100,88160R101"},"cas_types":{"name":"types","in":"query","schema":{"type":"string"},"example":"forward_split,reverse_split","description":"A comma-separated list of types. If not provided, search all types.\n\nThe following types are supported:\n  - reverse_split\n  - forward_split\n  - unit_split\n  - cash_dividend\n  - stock_dividend\n  - spin_off\n  - cash_merger\n  - stock_merger\n  - stock_and_cash_merger\n  - redemption\n  - name_change\n  - worthless_removal\n  - rights_distribution\n"},"cas_start":{"name":"start","in":"query","schema":{"type":"string","format":"date"},"examples":{"date":{"value":"2024-08-14"}},"description":"The inclusive start of the interval. The corporate actions are sorted by their `process_date`. Format: YYYY-MM-DD. Default: current day.\n"},"cas_end":{"name":"end","in":"query","schema":{"type":"string","format":"date"},"examples":{"date":{"value":"2024-08-25","summary":"Date"}},"description":"The inclusive end of the interval. The corporate actions are sorted by their `process_date`. Format: YYYY-MM-DD. Default: current day.\n"},"cas_ids":{"name":"ids","description":"A comma-separated list of corporate action IDs. This parameter is mutually exclusive with all other filters (symbols, types, start, end).\n","in":"query","schema":{"type":"string"},"example":"1dbc7685-9517-4a77-a236-8527d49cefdc,f8489167-4e4b-431d-a0be-6017ae1cf08a"},"cas_limit":{"name":"limit","in":"query","schema":{"type":"integer","minimum":1,"maximum":1000,"default":100},"description":"Maximum number of corporate actions to return in a response.\nThe limit applies to the total number of data points, not the count per symbol!\nUse `next_page_token` to fetch the next set of corporate actions.\n"},"page_token":{"name":"page_token","in":"query","schema":{"type":"string"},"description":"The pagination token from which to continue. The value to pass here is returned in specific requests when more data is available, usually because of a response result limit.\n"},"sort":{"name":"sort","in":"query","description":"Sort data in ascending or descending order.","schema":{"$ref":"#/components/schemas/sort"}},"isins":{"name":"isins","description":"A comma-separated list of ISINs with a limit of 1000.","in":"query","required":true,"schema":{"type":"string"},"example":"US912797KJ59,US912797KS58,US912797LB15"},"forex_currency_pairs":{"name":"currency_pairs","in":"query","required":true,"schema":{"$ref":"#/components/schemas/forex_currency_pairs"}},"forex_timeframe":{"name":"timeframe","in":"query","required":false,"schema":{"$ref":"#/components/schemas/forex_timeframe"}},"start":{"name":"start","in":"query","required":false,"schema":{"type":"string","format":"date-time"},"examples":{"RFC-3339 second":{"value":"2024-01-03T00:00:00Z","summary":"RFC-3339 date-time with second accuracy"},"RFC-3339 nanosecond":{"value":"2024-01-03T01:02:03.123456789Z","summary":"RFC-3339 date-time with nanosecond accuracy"},"RFC-3339 with timezone":{"value":"2024-01-03T09:30:00-04:00","summary":"RFC-3339 date-time with time zone"},"date":{"value":"2024-01-03","summary":"Date"}},"description":"The inclusive start of the interval. Format: RFC-3339 or YYYY-MM-DD.\nDefault: the beginning of the current day, but at least 15 minutes ago if the user doesn't have real-time access for the feed.\n"},"end":{"name":"end","in":"query","required":false,"schema":{"type":"string","format":"date-time"},"examples":{"RFC-3339 second":{"value":"2024-01-04T00:00:00Z","summary":"RFC-3339 date-time with second accuracy"},"RFC-3339 nanosecond":{"value":"2024-01-04T01:02:03.123456789Z","summary":"RFC-3339 date-time with nanosecond accuracy"},"RFC-3339 with timezone":{"value":"2024-01-04T09:30:00-04:00","summary":"RFC-3339 date-time with time zone"},"date":{"value":"2024-01-04","summary":"Date"}},"description":"The inclusive end of the interval. Format: RFC-3339 or YYYY-MM-DD.\nDefault: the current time if the user has a real-time access for the feed, otherwise 15 minutes before the current time.\n"},"limit":{"name":"limit","in":"query","required":false,"schema":{"type":"integer","minimum":1,"maximum":10000,"default":1000},"description":"The maximum number of data points to return in the response page.\nThe API may return less, even if there are more available data points in the requested interval.\nAlways check the `next_page_token` for more pages.\nThe limit applies to the total number of data points, not per symbol!\n"},"symbol":{"name":"symbol","description":"A unique series of letters assigned to a security for trading purposes.","in":"path","required":true,"schema":{"type":"string"},"example":"AAPL"},"news_sort":{"name":"sort","in":"query","description":"Sort articles by updated date.","schema":{"type":"string","enum":["asc","desc"],"default":"desc"}},"option_symbols":{"name":"symbols","description":"A comma-separated list of contract symbols with a limit of 100.","in":"query","required":true,"schema":{"type":"string"},"example":"AAPL241220C00300000,AAPL240315C00225000"},"timeframe":{"name":"timeframe","in":"query","schema":{"type":"string"},"required":true,"x-go-name":"TimeFrame","example":"1Min","description":"The timeframe represented by each bar in aggregation.\nYou can use any of the following values:\n - `[1-59]Min` or `[1-59]T`, e.g. `5Min` or `5T` creates 5-minute aggregations\n - `[1-23]Hour` or `[1-23]H`, e.g. `12Hour` or `12H` creates 12-hour aggregations\n - `1Day` or `1D` creates 1-day aggregations\n - `1Week` or `1W` creates 1-week aggregations\n - `[1,2,3,4,6,12]Month` or `[1,2,3,4,6,12]M`, e.g. `3Month` or `3M` creates 3-month aggregations\n"},"option_feed":{"name":"feed","in":"query","description":"The source feed of the data. `opra` is the official OPRA feed, `indicative` is a free indicative feed where trades are delayed and quotes are modified. Default: `opra` if the user has a subscription, otherwise `indicative`.\n","schema":{"$ref":"#/components/schemas/option_feed"}},"option_updated_since":{"name":"updated_since","in":"query","required":false,"schema":{"type":"string","format":"date-time"},"description":"Filter to snapshots that were updated since this timestamp, meaning that the timestamp of the trade or the quote is greater than or equal to this value.\nFormat: RFC-3339 or YYYY-MM-DD. If missing, all values are returned.\n"},"option_limit":{"name":"limit","in":"query","schema":{"type":"integer","minimum":1,"maximum":1000,"default":100},"description":"Number of maximum snapshots to return in a response.\nThe limit applies to the total number of data points, not the number per symbol!\nUse `next_page_token` to fetch the next set of responses.\n"},"option_underlying_symbol":{"name":"underlying_symbol","description":"The financial instrument on which an option contract is based or derived.","in":"path","required":true,"schema":{"type":"string"},"example":"AAPL"},"most_actives_by":{"name":"by","in":"query","required":false,"schema":{"type":"string","enum":["volume","trades"],"default":"volume"},"description":"The metric used for ranking the most active stocks."},"most_actives_top":{"name":"top","in":"query","required":false,"schema":{"type":"integer","format":"int32","default":10,"minimum":1,"maximum":100},"description":"The number of top most active stocks to fetch per day."},"movers_market_type":{"name":"market_type","in":"path","required":true,"schema":{"$ref":"#/components/schemas/market_type"},"description":"Screen-specific market (stocks or crypto)."},"movers_top":{"name":"top","in":"query","required":false,"schema":{"type":"integer","format":"int32","default":10,"minimum":1,"maximum":50},"description":"Number of top market movers to fetch (gainers and losers). Will return this number of results for each. By default, 10 gainers and 10 losers.\n"},"crypto_perp_loc":{"name":"loc","in":"path","description":"Crypto perpetual location.","required":true,"schema":{"$ref":"#/components/schemas/crypto_perp_loc"}},"crypto_perp_symbols":{"name":"symbols","description":"A comma-separated list of crypto symbols.","in":"query","required":true,"schema":{"type":"string"},"example":"BTCUSDT.P,LTCUSDT.P"},"crypto_historical_loc":{"name":"loc","in":"path","description":"Crypto location from where the historical market data is retrieved.\n- `us`: Alpaca US\n- `us-1`: Kraken US\n- `eu-1`: Kraken EU\n","required":true,"schema":{"$ref":"#/components/schemas/crypto_historical_loc"}},"crypto_symbols":{"name":"symbols","description":"A comma-separated list of crypto symbols.","in":"query","required":true,"schema":{"type":"string"},"example":"BTC/USD,LTC/USD"},"crypto_latest_loc":{"name":"loc","in":"path","description":"Crypto location from where the latest market data is retrieved.\n- `us`: Alpaca US\n- `us-1`: Kraken US\n- `eu-1`: Kraken EU\n","required":true,"schema":{"$ref":"#/components/schemas/crypto_latest_loc"}},"stock_symbols":{"name":"symbols","description":"A comma-separated list of stock symbols.","in":"query","required":true,"schema":{"type":"string"},"example":"AAPL,TSLA"},"stock_asof":{"name":"asof","in":"query","description":"The as-of date of the queried stock symbol(s). Format: YYYY-MM-DD. Default: current day.\n\nThis date is used to identify the underlying entity of the provided symbol(s), so that name changes for this entity can be found. Data for past symbol(s) is returned if the query date range spans the name change.\n\nThe special value of \"-\" means symbol mapping is skipped. Data is returned based on the symbol alone without looking up previous names. The same happens if the queried symbol is not found on the given `asof` date.\n\nExample: FB was renamed to META in 2022-06-09. Querying META with an `asof` date after 2022-06-09 will also yield FB data. The data for the FB ticker will be labeled as META because they are considered the same underlying entity as of 2022-06-09. Querying FB with an `asof` date after 2022-06-09 will only return data with the FB ticker, not with META. But with an `asof` date before 2022-06-09, META will also be returned (as FB).\n","schema":{"type":"string"}},"stock_auction_feed":{"name":"feed","in":"query","description":"Only `sip` is valid for auctions.","schema":{"$ref":"#/components/schemas/stock_auction_feed"}},"stock_currency":{"name":"currency","in":"query","description":"The currency of all prices in ISO 4217 format. Default: USD.\n","schema":{"type":"string"}},"stock_adjustment":{"name":"adjustment","in":"query","description":"Specifies the adjustments for the bars.\n\n - `raw`: no adjustments\n - `split`: adjust price and volume for forward and reverse stock splits\n - `dividend`: adjust price for cash dividends\n - `spin-off`: adjust price for spin-offs\n - `all`: apply all above adjustments\n\nYou can combine multiple adjustments by separating them with a comma, e.g. `split,spin-off`.\n","schema":{"type":"string","default":"raw"}},"stock_historical_feed":{"name":"feed","in":"query","description":"The source feed of the data.\n - `sip`: all US exchanges\n - `iex`: Investors EXchange\n - `boats`: Blue Ocean ATS, overnight US trading data\n - `otc`: over-the-counter exchanges\n","schema":{"$ref":"#/components/schemas/stock_historical_feed"}},"stock_latest_feed":{"name":"feed","in":"query","description":"The source feed of the data.\n\n - `sip`: all US exchanges\n - `iex`: Investors EXchange\n - `delayed_sip`: SIP with a 15 minute delay\n - `boats`: Blue Ocean, overnight US trading data\n - `overnight`: derived overnight US trading data\n - `otc`: over-the-counter exchanges\n\nDefault: `sip` if the user has the unlimited subscription, otherwise `iex`.\n","schema":{"$ref":"#/components/schemas/stock_latest_feed"}},"stock_symbol":{"name":"symbol","in":"path","description":"The symbol to query.","required":true,"schema":{"type":"string"},"example":"AAPL"}},"schemas":{"sort":{"type":"string","description":"Sort data in ascending or descending order.","enum":["asc","desc"],"default":"asc","x-go-name":"TypeSort"},"ca_id":{"type":"string","format":"uuid","description":"The internal Alpaca identifier of the corporate action."},"process_date":{"type":"string","format":"date","description":"The date when the corporate action is processed by Alpaca."},"ex_date":{"type":"string","format":"date","description":"The ex-date marks the cutoff point for shareholders to be credited."},"record_date":{"type":"string","format":"date","description":"The date shareholders must own shares to receive the benefit."},"payable_date":{"type":"string","format":"date","description":"The date when the corporate action benefit is paid or distributed."},"reverse_split":{"type":"object","description":"Reverse split.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"symbol":{"type":"string"},"old_cusip":{"type":"string"},"new_cusip":{"type":"string"},"new_rate":{"type":"number","format":"double"},"old_rate":{"type":"number","format":"double"},"process_date":{"$ref":"#/components/schemas/process_date"},"ex_date":{"$ref":"#/components/schemas/ex_date"},"record_date":{"$ref":"#/components/schemas/record_date"},"payable_date":{"$ref":"#/components/schemas/payable_date"}},"required":["id","symbol","old_cusip","new_cusip","new_rate","old_rate","process_date","ex_date"],"example":{"ex_date":"2023-08-24","id":"913de862-c02c-46dc-a89c-fc8779a50d30","new_cusip":"60879E200","new_rate":1,"old_cusip":"60879E101","old_rate":50,"process_date":"2023-08-24","record_date":"2023-08-24","symbol":"MNTS"}},"due_bill_redemption_date":{"type":"string","format":"date","description":"The date when due bill obligations are redeemed."},"forward_split":{"type":"object","description":"Forward split.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"symbol":{"type":"string"},"cusip":{"type":"string"},"new_rate":{"type":"number","format":"double"},"old_rate":{"type":"number","format":"double"},"process_date":{"$ref":"#/components/schemas/process_date"},"ex_date":{"$ref":"#/components/schemas/ex_date"},"record_date":{"$ref":"#/components/schemas/record_date"},"payable_date":{"$ref":"#/components/schemas/payable_date"},"due_bill_redemption_date":{"$ref":"#/components/schemas/due_bill_redemption_date"}},"required":["id","symbol","cusip","new_rate","old_rate","process_date","ex_date"],"example":{"cusip":"816851109","due_bill_redemption_date":"2023-08-23","ex_date":"2023-08-22","id":"189bd849-ab9f-4b4d-aaaa-a6d415fd976d","new_rate":2,"old_rate":1,"payable_date":"2023-08-21","process_date":"2023-08-22","record_date":"2023-08-14","symbol":"SRE"}},"effective_date":{"type":"string","format":"date","description":"The effective date marks the cutoff point for shareholders to be credited."},"unit_split":{"type":"object","description":"Unit split.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"old_symbol":{"type":"string"},"old_cusip":{"type":"string"},"old_rate":{"type":"number","format":"double"},"new_symbol":{"type":"string"},"new_cusip":{"type":"string"},"new_rate":{"type":"number","format":"double"},"alternate_symbol":{"type":"string"},"alternate_cusip":{"type":"string"},"alternate_rate":{"type":"number","format":"double"},"process_date":{"$ref":"#/components/schemas/process_date"},"effective_date":{"$ref":"#/components/schemas/effective_date"},"payable_date":{"$ref":"#/components/schemas/payable_date"}},"required":["id","old_symbol","old_cusip","old_rate","new_symbol","new_cusip","new_rate","alternate_symbol","alternate_cusip","alternate_rate","process_date","effective_date"],"example":{"alternate_cusip":"G5391L110","alternate_rate":0.3333,"alternate_symbol":"LVROW","effective_date":"2023-03-01","id":"3e68e87e-ae95-4d68-91d1-715d52ef143a","new_cusip":"G5391L102","new_rate":1,"new_symbol":"LVRO","old_cusip":"G8990L119","old_rate":1,"old_symbol":"TPBAU","process_date":"2023-03-01"}},"stock_dividend":{"type":"object","description":"Stock dividend.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"symbol":{"type":"string"},"cusip":{"type":"string"},"rate":{"type":"number","format":"double"},"process_date":{"$ref":"#/components/schemas/process_date"},"ex_date":{"$ref":"#/components/schemas/ex_date"},"record_date":{"$ref":"#/components/schemas/record_date"},"payable_date":{"$ref":"#/components/schemas/payable_date"}},"required":["id","symbol","cusip","rate","process_date","ex_date"],"example":{"cusip":"605015106","ex_date":"2023-05-19","id":"3ae94c30-2d37-473a-bf29-5f7b4ab6d3ca","payable_date":"2023-05-05","process_date":"2023-05-19","rate":0.05,"record_date":"2023-05-22","symbol":"MSBC"}},"cash_dividend":{"type":"object","description":"Cash dividend.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"symbol":{"type":"string"},"cusip":{"type":"string"},"rate":{"type":"number","format":"double"},"special":{"type":"boolean"},"foreign":{"type":"boolean"},"process_date":{"$ref":"#/components/schemas/process_date"},"ex_date":{"$ref":"#/components/schemas/ex_date"},"record_date":{"$ref":"#/components/schemas/record_date"},"payable_date":{"$ref":"#/components/schemas/payable_date"},"due_bill_on_date":{"type":"string","format":"date"},"due_bill_off_date":{"type":"string","format":"date"}},"required":["id","symbol","cusip","rate","special","foreign","process_date","ex_date"],"example":{"cusip":"319829107","ex_date":"2023-05-04","foreign":false,"id":"11cfd108-292e-4cc6-bfbf-5999cdbc4029","payable_date":"2023-05-19","process_date":"2023-05-19","rate":0.125,"record_date":"2023-05-05","special":false,"symbol":"FCF"}},"spin_off":{"type":"object","description":"Spin-off.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"source_symbol":{"type":"string"},"source_cusip":{"type":"string"},"source_rate":{"type":"number","format":"double"},"new_symbol":{"type":"string"},"new_cusip":{"type":"string"},"new_rate":{"type":"number","format":"double"},"process_date":{"$ref":"#/components/schemas/process_date"},"ex_date":{"$ref":"#/components/schemas/ex_date"},"record_date":{"$ref":"#/components/schemas/record_date"},"payable_date":{"$ref":"#/components/schemas/payable_date"},"due_bill_redemption_date":{"$ref":"#/components/schemas/due_bill_redemption_date"}},"required":["id","source_symbol","source_cusip","source_rate","new_symbol","new_cusip","new_rate","process_date","ex_date"],"example":{"ex_date":"2023-08-15","id":"82e602f6-35bc-4651-a5dd-f6d88ff37c55","new_cusip":"85237B101","new_rate":1,"new_symbol":"SRM","process_date":"2023-08-15","record_date":"2023-08-15","source_rate":19.35,"source_cusip":"48208F105","source_symbol":"JUPW"}},"cash_merger":{"type":"object","description":"Cash merger.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"acquirer_symbol":{"type":"string"},"acquirer_cusip":{"type":"string"},"acquiree_symbol":{"type":"string"},"acquiree_cusip":{"type":"string"},"rate":{"type":"number","format":"double"},"process_date":{"$ref":"#/components/schemas/process_date"},"effective_date":{"$ref":"#/components/schemas/effective_date"},"payable_date":{"$ref":"#/components/schemas/payable_date"}},"required":["id","acquiree_symbol","acquiree_cusip","rate","process_date","effective_date"],"example":{"acquiree_cusip":"Y2687W108","acquiree_symbol":"GLOP","effective_date":"2023-07-17","id":"3772bbd7-4ad5-44d4-9cc0-f69156a2f8f5","payable_date":"2023-07-17","process_date":"2023-07-17","rate":5.37}},"stock_merger":{"type":"object","description":"Stock merger.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"acquirer_symbol":{"type":"string"},"acquirer_cusip":{"type":"string"},"acquirer_rate":{"type":"number","format":"double"},"acquiree_symbol":{"type":"string"},"acquiree_cusip":{"type":"string"},"acquiree_rate":{"type":"number","format":"double"},"process_date":{"$ref":"#/components/schemas/process_date"},"effective_date":{"$ref":"#/components/schemas/effective_date"},"payable_date":{"$ref":"#/components/schemas/payable_date"}},"required":["id","acquirer_symbol","acquirer_cusip","acquirer_rate","acquiree_symbol","acquiree_cusip","acquiree_rate","process_date","effective_date"],"example":{"acquiree_cusip":"53223X107","acquiree_rate":1,"acquiree_symbol":"LSI","acquirer_cusip":"30225T102","acquirer_rate":0.895,"acquirer_symbol":"EXR","effective_date":"2023-07-20","id":"728f8cb2-a00e-4bc7-ad14-d15fe82bbcff","payable_date":"2023-07-20","process_date":"2023-07-20"}},"stock_and_cash_merger":{"type":"object","description":"Stock and cash merger.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"acquirer_symbol":{"type":"string"},"acquirer_cusip":{"type":"string"},"acquirer_rate":{"type":"number","format":"double"},"acquiree_symbol":{"type":"string"},"acquiree_cusip":{"type":"string"},"acquiree_rate":{"type":"number","format":"double"},"cash_rate":{"type":"number","format":"double"},"process_date":{"$ref":"#/components/schemas/process_date"},"effective_date":{"$ref":"#/components/schemas/effective_date"},"payable_date":{"$ref":"#/components/schemas/payable_date"}},"required":["id","acquirer_symbol","acquirer_cusip","acquirer_rate","acquiree_symbol","acquiree_cusip","acquiree_rate","cash_rate","process_date","effective_date"],"example":{"acquiree_cusip":"561409103","acquiree_rate":1,"acquiree_symbol":"MLVF","acquirer_cusip":"31931U102","acquirer_rate":0.7733,"acquirer_symbol":"FRBA","cash_rate":7.8,"effective_date":"2023-07-18","id":"e5248356-2c06-42cf-aeb9-1595bd616cdb","payable_date":"2023-07-18","process_date":"2023-07-18"}},"redemption":{"type":"object","description":"Redemption.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"symbol":{"type":"string"},"cusip":{"type":"string"},"rate":{"type":"number","format":"double"},"process_date":{"$ref":"#/components/schemas/process_date"},"payable_date":{"$ref":"#/components/schemas/payable_date"}},"required":["id","symbol","cusip","rate","process_date"],"example":{"cusip":"687305102","id":"395da031-0e57-4918-a6fb-64a7c713aca4","payable_date":"2023-06-13","process_date":"2023-06-13","rate":0.141134,"symbol":"ORPHY"}},"name_change":{"type":"object","description":"Name change.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"old_symbol":{"type":"string"},"old_cusip":{"type":"string"},"new_symbol":{"type":"string"},"new_cusip":{"type":"string"},"process_date":{"$ref":"#/components/schemas/process_date"}},"required":["id","old_symbol","old_cusip","new_symbol","new_cusip","process_date"],"example":{"id":"5a774c35-edec-4532-a812-a56d0bbb623a","new_cusip":"Y9390M103","new_symbol":"VFS","old_cusip":"G11537100","old_symbol":"BSAQ","process_date":"2023-08-15"}},"worthless_removal":{"type":"object","description":"Worthless removal.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"symbol":{"type":"string"},"cusip":{"type":"string"},"process_date":{"$ref":"#/components/schemas/process_date"}},"required":["id","symbol","cusip","process_date"],"example":{"cusip":"078771300","id":"106c2149-ee04-4d2e-a943-98dbb4d21a3c","symbol":"BLPH","process_date":"2024-12-19"}},"expiration_date":{"type":"string","format":"date"},"rights_distribution":{"type":"object","description":"Rights distribution.","properties":{"id":{"$ref":"#/components/schemas/ca_id"},"source_symbol":{"type":"string"},"source_cusip":{"type":"string"},"new_symbol":{"type":"string"},"new_cusip":{"type":"string"},"rate":{"type":"number","format":"double"},"process_date":{"$ref":"#/components/schemas/process_date"},"ex_date":{"$ref":"#/components/schemas/ex_date"},"record_date":{"$ref":"#/components/schemas/record_date"},"payable_date":{"$ref":"#/components/schemas/payable_date"},"expiration_date":{"$ref":"#/components/schemas/expiration_date"}},"required":["id","source_symbol","source_cusip","new_symbol","new_cusip","rate","process_date","ex_date","payable_date"],"example":{"ex_date":"2024-04-17","expiration_date":"2024-05-14","id":"69794cfd-0adc-4e11-9211-9210a9cf8932","new_cusip":"454089111","new_symbol":"IFN.RTWI","payable_date":"2024-04-19","process_date":"2024-04-19","rate":1,"record_date":"2024-04-18","source_cusip":"454089103","source_symbol":"IFN"}},"corporate_actions":{"type":"object","properties":{"reverse_splits":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/reverse_split"}},"forward_splits":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/forward_split"}},"unit_splits":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/unit_split"}},"stock_dividends":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/stock_dividend"}},"cash_dividends":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/cash_dividend"}},"spin_offs":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/spin_off"}},"cash_mergers":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/cash_merger"}},"stock_mergers":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/stock_merger"}},"stock_and_cash_mergers":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/stock_and_cash_merger"}},"redemptions":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/redemption"}},"name_changes":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/name_change"}},"worthless_removals":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/worthless_removal"}},"rights_distributions":{"type":"array","x-go-type-skip-optional-pointer":true,"items":{"$ref":"#/components/schemas/rights_distribution"}}}},"next_page_token":{"type":"string","description":"Pagination token for the next page.","nullable":true},"corporate_actions_resp":{"type":"object","properties":{"corporate_actions":{"$ref":"#/components/schemas/corporate_actions"},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["corporate_actions","next_page_token"]},"timestamp":{"type":"string","description":"Timestamp in RFC-3339 format with nanosecond precision.","format":"date-time","x-go-name":"Timestamp"},"fixed_income_price":{"type":"object","description":"The price of the instrument as a percentage of its par value.","example":{"t":"2025-02-14T20:58:00.648Z","p":99.6459,"ytm":4.249,"ytw":4.249},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"p":{"type":"number","format":"double","description":"Price","x-go-name":"Price"},"ytm":{"type":"number","format":"double","description":"Yield to maturity.","x-go-name":"YieldToMaturity"},"ytw":{"type":"number","format":"double","description":"Yield to worst.","x-go-name":"YieldToWorst"}},"required":["t","p"]},"fixed_income_latest_prices_resp":{"type":"object","properties":{"prices":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/fixed_income_price"}}},"required":["prices"]},"forex_currency_pairs":{"type":"string","description":"A comma-separated string with currency pairs.","example":"USDJPY,USDMXN","x-go-name":"TypeCurrencyPairs"},"forex_rate":{"description":"A foreign exchange rate between two currencies at a given time.","type":"object","example":{"bp":127.702,"mp":127.757,"ap":127.763,"t":"2022-04-20T18:23:00Z"},"properties":{"bp":{"type":"number","format":"double","x-go-name":"BidPrice","description":"The last bid price value of the currency at the end of the timeframe."},"mp":{"type":"number","format":"double","x-go-name":"MidPrice","description":"The last mid price value of the currency at the end of the timeframe."},"ap":{"type":"number","format":"double","x-go-name":"AskPrice","description":"The last ask price value of the currency at the end of the timeframe."},"t":{"type":"string","format":"date-time","x-go-name":"Timestamp","description":"Timestamp of the rate."}},"required":["bp","mp","ap","t"]},"forex_latest_rates_resp":{"description":"The response object of the latest forex rates.","type":"object","properties":{"rates":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/forex_rate"}}},"required":["rates"]},"forex_timeframe":{"type":"string","default":"1Min","description":"The sampling interval of the currency rates. For example, 5S returns forex rates sampled every five seconds.\nYou can use the following values:\n - `5Sec` or `5S`\n - `1Min` or `1T`\n - `1Day` or `1D`\n"},"forex_rates_resp":{"type":"object","properties":{"rates":{"type":"object","additionalProperties":{"type":"array","items":{"$ref":"#/components/schemas/forex_rate"}}},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["rates","next_page_token"]},"news_image":{"description":"A model representing images for a news article. Simply a URL to the image along with a size parameter suggesting the display size of the image.","type":"object","properties":{"size":{"type":"string","minLength":1,"description":"Possible values for size are thumb, small and large.","example":"thumb","enum":["thumb","small","large"]},"url":{"type":"string","minLength":1,"description":"URL to image from news article.","format":"uri"}},"required":["size","url"]},"news":{"description":"Model representing a news article.","type":"object","properties":{"id":{"type":"integer","format":"int64","description":"News article ID."},"headline":{"type":"string","minLength":1,"description":"Headline or title of the article."},"author":{"type":"string","minLength":1,"description":"Original author of news article."},"created_at":{"type":"string","format":"date-time","description":"Date article was created (RFC-3339)."},"updated_at":{"type":"string","format":"date-time","description":"Date article was updated (RFC-3339)."},"summary":{"type":"string","minLength":1,"description":"Summary text for the article (may be first sentence of content)."},"content":{"type":"string","minLength":1,"description":"Content of the news article (might contain HTML)."},"url":{"type":"string","format":"uri","description":"URL of article (if applicable).","nullable":true},"images":{"type":"array","uniqueItems":true,"description":"List of images (URLs) related to given article (may be empty).","items":{"$ref":"#/components/schemas/news_image"}},"symbols":{"type":"array","description":"List of related or mentioned symbols.","items":{"type":"string"}},"source":{"type":"string","minLength":1,"description":"Source where the news originated from (e.g. Benzinga)."}},"required":["id","headline","author","created_at","updated_at","summary","content","images","symbols","source"]},"news_resp":{"type":"object","properties":{"news":{"type":"array","items":{"$ref":"#/components/schemas/news"}},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["news","next_page_token"]},"option_bar":{"type":"object","description":"OHLC aggregate of all the trades in a given interval.","example":{"t":"2024-01-18T05:00:00Z","o":0.28,"h":0.28,"l":0.23,"c":0.23,"v":224,"n":26,"vw":0.245045},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"o":{"type":"number","format":"double","description":"Opening price.","x-go-name":"Open"},"h":{"type":"number","format":"double","description":"High price.","x-go-name":"High"},"l":{"type":"number","format":"double","description":"Low price.","x-go-name":"Low"},"c":{"type":"number","format":"double","description":"Closing price.","x-go-name":"Close"},"v":{"type":"integer","format":"int64","description":"Bar volume.","x-go-name":"Volume"},"n":{"type":"integer","format":"int64","description":"Trade count in the bar.","x-go-name":"TradeCount"},"vw":{"type":"number","format":"double","description":"Volume weighted average price.","x-go-name":"VWAP"}},"required":["t","o","h","l","c","v","n","vw"]},"option_bars_resp":{"type":"object","properties":{"bars":{"type":"object","additionalProperties":{"type":"array","items":{"$ref":"#/components/schemas/option_bar"}}},"next_page_token":{"$ref":"#/components/schemas/next_page_token"},"currency":{"type":"string"}},"required":["bars","next_page_token"]},"option_conditions":{"type":"object","additionalProperties":{"type":"string"},"example":{"a":"SLAN - Single Leg Auction Non ISO","e":"SLFT - Single Leg Floor Trade","g":"MLAT - Multi Leg Auction"}},"option_exchanges":{"type":"object","additionalProperties":{"type":"string"},"example":{"A":"NYSE American Options","Q":"Nasdaq Options"}},"option_feed":{"type":"string","enum":["opra","indicative"],"default":"opra"},"option_quote":{"type":"object","description":"The best bid and ask information for a given option.\n","example":{"t":"2024-02-28T15:30:28.046330624Z","ax":"w","ap":0.16,"as":669,"bx":"W","bp":0.15,"bs":164,"c":"A"},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"bx":{"type":"string","description":"Bid exchange.","x-go-name":"BidExchange"},"bp":{"type":"number","format":"double","description":"Bid price.","x-go-name":"BidPrice"},"bs":{"type":"integer","format":"uint32","description":"Bid size.","x-go-name":"BidSize"},"ax":{"type":"string","description":"Ask exchange.","x-go-name":"AskExchange"},"ap":{"type":"number","format":"double","description":"Ask price.","x-go-name":"AskPrice"},"as":{"type":"integer","format":"uint32","description":"Ask size.","x-go-name":"AskSize"},"c":{"type":"string","description":"Quote condition.","x-go-name":"Condition"}},"required":["t","bx","bp","bs","ap","as","ax","c"]},"option_latest_quotes_resp":{"type":"object","properties":{"quotes":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/option_quote"}}},"required":["quotes"]},"option_greeks":{"type":"object","description":"The greeks for the contract calculated using the Black-Scholes model.","properties":{"delta":{"type":"number","format":"double"},"gamma":{"type":"number","format":"double"},"theta":{"type":"number","format":"double"},"vega":{"type":"number","format":"double"},"rho":{"type":"number","format":"double"}},"required":["delta","gamma","theta","vega","rho"]},"option_trade":{"type":"object","description":"An option trade.","example":{"t":"2024-01-18T15:03:44.56339456Z","x":"B","p":0.37,"s":1,"c":"I"},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"x":{"type":"string","x-go-name":"Exchange"},"p":{"type":"number","format":"double","description":"Trade price.","x-go-name":"Price"},"s":{"type":"integer","format":"uint32","description":"Trade size.","x-go-name":"Size"},"c":{"type":"string","description":"Trade condition.","x-go-name":"Condition"}},"required":["t","x","p","s","c"]},"option_snapshot":{"type":"object","description":"A snapshot provides the latest trade and latest quote.","properties":{"dailyBar":{"$ref":"#/components/schemas/option_bar"},"greeks":{"$ref":"#/components/schemas/option_greeks"},"impliedVolatility":{"description":"Implied volatility calculated using the Black-Scholes model.","format":"double","type":"number"},"latestQuote":{"$ref":"#/components/schemas/option_quote"},"latestTrade":{"$ref":"#/components/schemas/option_trade"},"minuteBar":{"$ref":"#/components/schemas/option_bar"},"prevDailyBar":{"$ref":"#/components/schemas/option_bar"}}},"option_snapshots_resp":{"type":"object","properties":{"snapshots":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/option_snapshot"}},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["snapshots","next_page_token"]},"option_trades_resp":{"type":"object","properties":{"trades":{"type":"object","additionalProperties":{"type":"array","items":{"$ref":"#/components/schemas/option_trade"}}},"currency":{"type":"string"},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["trades","next_page_token"]},"option_latest_trades_resp":{"type":"object","properties":{"trades":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/option_trade"}}},"required":["trades"]},"most_active":{"description":"A stock that is most active by either volume or trade count.","type":"object","example":{"symbol":"AAPL","volume":122709184,"trade_count":639626},"properties":{"symbol":{"type":"string"},"volume":{"type":"integer","format":"int64","description":"Cumulative volume for the current trading day."},"trade_count":{"type":"integer","format":"int64","description":"Cumulative trade count for the current trading day."}},"required":["symbol","volume","trade_count"]},"most_actives_resp":{"type":"object","properties":{"most_actives":{"type":"array","description":"List of top N most active symbols.","items":{"$ref":"#/components/schemas/most_active"}},"last_updated":{"type":"string","description":"Time when the most actives were last computed. Formatted as a RFC-3339 date-time with nanosecond precision.\n"}},"required":["most_actives","last_updated"]},"market_type":{"type":"string","enum":["stocks","crypto"],"description":"Market type (stocks or crypto)."},"mover":{"title":"Mover","type":"object","description":"A symbol whose price moved significantly.","example":{"symbol":"AGRI","percent_change":145.56,"change":2.46,"price":4.15},"properties":{"symbol":{"type":"string","description":"Symbol of market moving asset."},"percent_change":{"type":"number","format":"double","description":"Percentage difference change for the day."},"change":{"type":"number","format":"double","description":"Difference in change for the day."},"price":{"type":"number","format":"double","description":"Current price of market moving asset."}},"required":["symbol","percent_change","change","price"]},"movers_resp":{"type":"object","description":"Contains list of market movers.","properties":{"gainers":{"type":"array","description":"List of top N gainers.","items":{"$ref":"#/components/schemas/mover"}},"losers":{"description":"List of top N losers.","type":"array","items":{"$ref":"#/components/schemas/mover"}},"market_type":{"$ref":"#/components/schemas/market_type"},"last_updated":{"type":"string","description":"Time when the movers were last computed. Formatted as a RFC-3339 date-time with nanosecond precision.\n"}},"required":["gainers","losers","market_type","last_updated"]},"crypto_perp_loc":{"type":"string","enum":["global"],"description":"Crypto perpetual location.","x-go-name":"TypePerpLoc"},"crypto_bar":{"type":"object","description":"OHLC aggregate of all the trades in a given interval.","example":{"t":"2022-05-27T10:18:00Z","o":28999,"h":29003,"l":28999,"c":29003,"v":0.01,"n":4,"vw":29001},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"o":{"type":"number","format":"double","description":"Opening price.","x-go-name":"Open"},"h":{"type":"number","format":"double","description":"High price.","x-go-name":"High"},"l":{"type":"number","format":"double","description":"Low price.","x-go-name":"Low"},"c":{"type":"number","format":"double","description":"Closing price.","x-go-name":"Close"},"v":{"type":"number","format":"double","description":"Bar volume.","x-go-name":"Volume"},"n":{"type":"integer","format":"int64","description":"Trade count in the bar.","x-go-name":"TradeCount"},"vw":{"type":"number","format":"double","description":"Volume weighted average price.","x-go-name":"VWAP"}},"required":["t","o","h","l","c","v","n","vw"]},"crypto_latest_bars_resp":{"type":"object","properties":{"bars":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/crypto_bar"}}},"required":["bars"]},"crypto_perp_futures_pricing":{"type":"object","description":"Crypto perpetual futures pricing data.","example":{"t":"2022-05-27T10:18:00Z","ft":"2022-05-27T10:18:00Z","oi":90.7367,"ip":50702.8,"mp":50652.3553,"fr":0.000565699},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"ft":{"type":"string","format":"date-time","description":"Next funding time","x-go-name":"NextFundingTime"},"oi":{"type":"number","format":"double","description":"Open interest.","x-go-name":"OpenInterest"},"ip":{"type":"number","format":"double","description":"Index price.","x-go-name":"IndexPrice"},"mp":{"type":"number","format":"double","description":"Mark price.","x-go-name":"MarkPrice"},"fr":{"type":"number","format":"double","description":"Funding rate.","x-go-name":"FundingRate"}},"required":["t","ft","oi","ip","mp","fr"]},"crypto_perp_latest_futures_pricing_resp":{"type":"object","properties":{"pricing":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/crypto_perp_futures_pricing"}}},"required":["pricing"]},"crypto_orderbook_entry":{"type":"object","description":"A single entry in a crypto orderbook.","example":{"p":20846,"s":0.1902},"properties":{"p":{"type":"number","format":"double","description":"Price.","x-go-name":"Price"},"s":{"type":"number","format":"double","description":"Size.","x-go-name":"Size"}},"required":["p","s"]},"crypto_orderbook":{"type":"object","description":"Snapshot of the orderbook.","example":{"t":"2022-06-24T08:00:14.137774336Z","b":[{"p":20846,"s":0.1902},{"p":20350,"s":0}],"a":[{"p":20902,"s":0.0097},{"p":21444,"s":0}]},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"b":{"type":"array","items":{"$ref":"#/components/schemas/crypto_orderbook_entry"},"x-go-name":"Bids"},"a":{"type":"array","items":{"$ref":"#/components/schemas/crypto_orderbook_entry"},"x-go-name":"Asks"}},"required":["t","b","a"]},"crypto_latest_orderbooks_resp":{"type":"object","properties":{"orderbooks":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/crypto_orderbook"}}},"required":["orderbooks"]},"crypto_quote":{"type":"object","description":"The best bid and ask information for a given security.","example":{"t":"2022-05-26T11:47:18.44347136Z","bp":29058,"bs":0.3544,"ap":29059,"as":3.252},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"bp":{"type":"number","format":"double","description":"Bid price.","x-go-name":"BidPrice"},"bs":{"type":"number","format":"double","description":"Bid size.","x-go-name":"BidSize"},"ap":{"type":"number","format":"double","description":"Ask price.","x-go-name":"AskPrice"},"as":{"type":"number","format":"double","description":"Ask size.","x-go-name":"AskSize"}},"required":["t","bp","bs","ap","as"]},"crypto_latest_quotes_resp":{"type":"object","properties":{"quotes":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/crypto_quote"}}},"required":["quotes"]},"crypto_trade":{"type":"object","description":"A crypto trade.","example":{"t":"2022-05-18T12:00:05.225055Z","p":29798,"s":0.1209,"tks":"S","i":31455277},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"p":{"type":"number","format":"double","description":"Trade price.","x-go-name":"Price"},"s":{"type":"number","format":"double","description":"Trade size.","x-go-name":"Size"},"i":{"type":"integer","format":"int64","description":"Trade ID.","x-go-name":"ID"},"tks":{"type":"string","description":"Taker side: B for buyer, S for seller\n","x-go-name":"TakerSide"}},"required":["t","p","s","i","tks"]},"crypto_latest_trades_resp":{"type":"object","properties":{"trades":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/crypto_trade"}}},"required":["trades"]},"crypto_historical_loc":{"type":"string","enum":["us","us-1","us-2","eu-1","bs-1"],"description":"Crypto location from where the historical market data is retrieved.","x-go-name":"TypeHistoricalLoc"},"crypto_bars_resp":{"type":"object","properties":{"bars":{"type":"object","additionalProperties":{"type":"array","items":{"$ref":"#/components/schemas/crypto_bar"}}},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["bars","next_page_token"]},"crypto_latest_loc":{"type":"string","enum":["us","us-1","us-2","eu-1","bs-1"],"description":"Crypto location from where the latest market data is retrieved.","x-go-name":"TypeLatestLoc"},"crypto_quotes_resp":{"type":"object","properties":{"quotes":{"type":"object","additionalProperties":{"type":"array","items":{"$ref":"#/components/schemas/crypto_quote"}}},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["quotes","next_page_token"]},"crypto_snapshot":{"type":"object","description":"A snapshot provides the latest trade, latest quote, latest minute bar, latest daily bar and previous daily bar.\n","properties":{"dailyBar":{"$ref":"#/components/schemas/crypto_bar"},"latestQuote":{"$ref":"#/components/schemas/crypto_quote"},"latestTrade":{"$ref":"#/components/schemas/crypto_trade"},"minuteBar":{"$ref":"#/components/schemas/crypto_bar"},"prevDailyBar":{"$ref":"#/components/schemas/crypto_bar"}}},"crypto_snapshots_resp":{"type":"object","properties":{"snapshots":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/crypto_snapshot"}}},"required":["snapshots"]},"crypto_trades_resp":{"type":"object","properties":{"trades":{"type":"object","additionalProperties":{"type":"array","items":{"$ref":"#/components/schemas/crypto_trade"}}},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["trades","next_page_token"]},"stock_auction_feed":{"type":"string","default":"sip"},"date":{"type":"string","description":"Date in RFC-3339.","format":"date","x-go-name":"Date"},"stock_auction":{"type":"object","description":"An auction\n","example":{"t":"2022-10-13T13:30:01.688322951Z","x":"Q","c":"O","p":135},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"x":{"type":"string","description":"Exchange code. See `v2/stocks/meta/exchanges` for more details."},"p":{"type":"number","format":"double","description":"Auction price.","x-go-name":"Price"},"s":{"type":"integer","format":"int64","description":"Auction trade size.","x-go-name":"Size"},"c":{"description":"The condition flag indicating that this is an auction. See `v2/stocks/meta/conditions/trade` for more details.\n","type":"string","x-go-name":"Condition"}},"required":["t","x","p","c"]},"stock_daily_auctions":{"type":"object","description":"Opening and closing auction prices for a given day.\n","properties":{"d":{"$ref":"#/components/schemas/date"},"o":{"type":"array","description":"Opening auctions.","items":{"$ref":"#/components/schemas/stock_auction"},"x-go-name":"Opens"},"c":{"type":"array","description":"Closing auctions. Every price / exchange / condition triplet is only shown once, with its earliest timestamp.","items":{"$ref":"#/components/schemas/stock_auction"},"x-go-name":"Closes"}},"required":["d","o","c"]},"stock_auctions_resp":{"type":"object","properties":{"auctions":{"type":"object","additionalProperties":{"type":"array","items":{"$ref":"#/components/schemas/stock_daily_auctions"}}},"currency":{"type":"string"},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["auctions","next_page_token"]},"stock_historical_feed":{"type":"string","enum":["iex","otc","sip","boats"],"default":"sip"},"stock_bar":{"type":"object","description":"OHLC aggregate of all the trades in a given interval.\n","example":{"t":"2022-01-03T09:00:00Z","o":178.26,"h":178.34,"l":177.76,"c":178.08,"v":60937,"n":1727,"vw":177.954244},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"o":{"type":"number","format":"double","description":"Opening price.","x-go-name":"Open"},"h":{"type":"number","format":"double","description":"High price.","x-go-name":"High"},"l":{"type":"number","format":"double","description":"Low price.","x-go-name":"Low"},"c":{"type":"number","format":"double","description":"Closing price.","x-go-name":"Close"},"v":{"type":"integer","format":"int64","description":"Bar volume.","x-go-name":"Volume"},"n":{"type":"integer","format":"int64","description":"Trade count in the bar.","x-go-name":"TradeCount"},"vw":{"type":"number","format":"double","description":"Volume weighted average price.","x-go-name":"VWAP"}},"required":["t","o","h","l","c","v","n","vw"]},"stock_bars_resp":{"type":"object","properties":{"bars":{"type":"object","additionalProperties":{"type":"array","items":{"$ref":"#/components/schemas/stock_bar"}}},"next_page_token":{"$ref":"#/components/schemas/next_page_token"},"currency":{"type":"string"}},"required":["bars","next_page_token"]},"stock_latest_feed":{"type":"string","enum":["delayed_sip","iex","otc","sip","boats","overnight"]},"stock_latest_bars_resp":{"type":"object","properties":{"bars":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/stock_bar"}},"currency":{"type":"string"}},"required":["bars"]},"stock_conditions":{"type":"object","additionalProperties":{"type":"string"},"example":{"@":"Regular Sale","A":"Acquisition","B":"Bunched Trade"}},"stock_exchanges":{"type":"object","additionalProperties":{"type":"string"},"example":{"N":"New York Stock Exchange","V":"IEX"}},"stock_tape":{"type":"string","description":"- A: New York Stock Exchange\n- B: NYSE Arca, Bats, IEX and other regional exchanges\n- C: NASDAQ\n- N: Overnight\n- O: OTC\n","x-go-name":"Tape","enum":["A","B","C","N","O"]},"stock_quote":{"type":"object","description":"The best bid and ask information for a given security.","example":{"t":"2021-02-06T13:35:08.946977536Z","ax":"C","ap":387.7,"as":1,"bx":"N","bp":387.67,"bs":1,"c":["R"],"z":"C"},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"bx":{"type":"string","description":"Bid exchange. See `v2/stocks/meta/exchanges` for more details.","x-go-name":"BidExchange"},"bp":{"type":"number","format":"double","description":"Bid price. 0 means the security has no active bid.","x-go-name":"BidPrice"},"bs":{"type":"integer","format":"uint32","description":"Bid size in shares (round lots prior to November 3, 2025).","x-go-name":"BidSize"},"ax":{"type":"string","description":"Ask exchange. See `v2/stocks/meta/exchanges` for more details.","x-go-name":"AskExchange"},"ap":{"type":"number","format":"double","description":"Ask price. 0 means the security has no active ask.","x-go-name":"AskPrice"},"as":{"type":"integer","format":"uint32","description":"Ask size in shares (round lots prior to November 3, 2025).","x-go-name":"AskSize"},"c":{"description":"Condition flags. See `v2/stocks/meta/conditions/quote` for more details. If the array contains one flag, it applies to both the bid and ask. If the array contains two flags, the first one applies to the bid and the second one to the ask.\n","type":"array","items":{"type":"string"},"x-go-name":"Conditions"},"z":{"$ref":"#/components/schemas/stock_tape"}},"required":["t","bx","bp","bs","ap","as","ax","c","z"]},"stock_quotes_resp":{"type":"object","properties":{"quotes":{"type":"object","additionalProperties":{"type":"array","items":{"$ref":"#/components/schemas/stock_quote"}}},"currency":{"type":"string"},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["quotes","next_page_token"]},"stock_latest_quotes_resp":{"type":"object","properties":{"quotes":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/stock_quote"}},"currency":{"type":"string"}},"required":["quotes"]},"stock_trade":{"type":"object","description":"A stock trade.","example":{"t":"2022-01-03T09:00:00.086175744Z","x":"P","p":178.26,"s":246,"c":["@","T"],"i":1,"z":"C"},"properties":{"t":{"$ref":"#/components/schemas/timestamp"},"x":{"type":"string","description":"Exchange code. See `v2/stocks/meta/exchanges` for more details.","x-go-name":"Exchange"},"p":{"type":"number","format":"double","description":"Trade price.","x-go-name":"Price"},"s":{"type":"integer","format":"uint32","description":"Trade size.","x-go-name":"Size"},"i":{"type":"integer","format":"uint64","description":"Trade ID sent by the exchange.","x-go-name":"ID"},"c":{"description":"Condition flags. See `v2/stocks/meta/conditions/trade` for more details.","type":"array","items":{"type":"string"},"x-go-name":"Conditions"},"z":{"$ref":"#/components/schemas/stock_tape"},"u":{"type":"string","x-go-name":"Update","description":"Update to the trade. This field is optional, if it's missing, the trade is valid. Otherwise, it can have these values:\n - canceled: indicates that the trade has been canceled\n - incorrect: indicates that the trade has been corrected and the given trade is no longer valid\n - corrected: indicates that this trade is the correction of a previous (incorrect) trade\n"}},"required":["t","i","x","p","s","c","z"]},"stock_snapshot":{"type":"object","description":"A snapshot provides the latest trade, latest quote, latest minute bar, current daily bar and previous daily bar.\n","properties":{"dailyBar":{"$ref":"#/components/schemas/stock_bar"},"latestQuote":{"$ref":"#/components/schemas/stock_quote"},"latestTrade":{"$ref":"#/components/schemas/stock_trade"},"minuteBar":{"$ref":"#/components/schemas/stock_bar"},"prevDailyBar":{"$ref":"#/components/schemas/stock_bar"}}},"stock_snapshots_resp":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/stock_snapshot"}},"stock_trades_resp":{"type":"object","properties":{"trades":{"type":"object","additionalProperties":{"type":"array","items":{"$ref":"#/components/schemas/stock_trade"}}},"currency":{"type":"string"},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["trades","next_page_token"]},"stock_latest_trades_resp":{"type":"object","properties":{"trades":{"type":"object","additionalProperties":{"$ref":"#/components/schemas/stock_trade"}},"currency":{"type":"string"}},"required":["trades"]},"stock_auctions_resp_single":{"type":"object","properties":{"symbol":{"type":"string"},"auctions":{"type":"array","items":{"$ref":"#/components/schemas/stock_daily_auctions"}},"currency":{"type":"string"},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["auctions","next_page_token","symbol"]},"stock_bars_resp_single":{"type":"object","properties":{"symbol":{"type":"string"},"bars":{"type":"array","items":{"$ref":"#/components/schemas/stock_bar"}},"currency":{"type":"string"},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["bars","next_page_token","symbol"]},"stock_latest_bars_resp_single":{"type":"object","properties":{"bar":{"$ref":"#/components/schemas/stock_bar"},"symbol":{"type":"string"},"currency":{"type":"string"}},"required":["bar","symbol"]},"stock_quotes_resp_single":{"type":"object","properties":{"symbol":{"type":"string"},"quotes":{"type":"array","items":{"$ref":"#/components/schemas/stock_quote"}},"currency":{"type":"string"},"next_page_token":{"$ref":"#/components/schemas/next_page_token"}},"required":["quotes","next_page_token","symbol"]},"stock_latest_quotes_resp_single":{"type":"object","properties":{"quote":{"$ref":"#/components/schemas/stock_quote"},"symbol":{"type":"string"},"currency":{"type":"string"}},"required":["quote","symbol"]},"stock_snapshots_resp_single":{"allOf":[{"type":"object","properties":{"symbol":{"type":"string"},"currency":{"type":"string"}}},{"$ref":"#/components/schemas/stock_snapshot"}]},"stock_trades_resp_single":{"type":"object","properties":{"symbol":{"type":"string"},"trades":{"type":"array","items":{"$ref":"#/components/schemas/stock_trade"}},"next_page_token":{"$ref":"#/components/schemas/next_page_token"},"currency":{"type":"string"}},"required":["trades","next_page_token","symbol"]},"stock_latest_trades_resp_single":{"type":"object","properties":{"trade":{"$ref":"#/components/schemas/stock_trade"},"symbol":{"type":"string"},"currency":{"type":"string"}},"required":["trade","symbol"]}},"headers":{"ratelimit_limit":{"schema":{"type":"integer"},"example":100,"description":"Request limit per minute."},"ratelimit_remaining":{"schema":{"type":"integer"},"example":90,"description":"Request limit per minute remaining."},"ratelimit_reset":{"schema":{"type":"integer"},"example":1674044551,"description":"The UNIX epoch when the remaining quota changes."}},"responses":{"400":{"description":"One of the request parameters is invalid. See the returned message for details.\n","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}}},"401":{"description":"Authentication headers are missing or invalid. Make sure you authenticate your request with a valid API key.\n"},"403":{"description":"The requested resource is forbidden.\n"},"429":{"description":"Too many requests. You hit the rate limit. Use the X-RateLimit-... response headers to make sure you're under the rate limit.\n","headers":{"X-RateLimit-Limit":{"$ref":"#/components/headers/ratelimit_limit"},"X-RateLimit-Remaining":{"$ref":"#/components/headers/ratelimit_remaining"},"X-RateLimit-Reset":{"$ref":"#/components/headers/ratelimit_reset"}}},"500":{"description":"Internal server error. We recommend retrying these later. If the issue persists, please contact us on [Slack](https://alpaca.markets/slack) or on the [Community Forum](https://forum.alpaca.markets/).\n"}}}}
```

---

## File: `tests/conftest.py`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/tests/conftest.py`

```python
"""Shared fixtures for the Alpaca MCP Server test suite."""

from __future__ import annotations

import os

import pytest
from fastmcp.client import Client

from alpaca_mcp_server.server import build_server


@pytest.fixture(autouse=True, scope="session")
async def _cleanup_paper_account():
    """Cancel stale orders and close orphan positions before the suite runs.

    Ensures a clean slate even if a previous CI run crashed mid-test.
    Silently skips when paper API credentials are absent.
    """
    if not (os.environ.get("ALPACA_API_KEY") and os.environ.get("ALPACA_SECRET_KEY")):
        yield
        return

    os.environ.setdefault("ALPACA_PAPER_TRADE", "true")
    server = build_server()
    async with Client(transport=server) as mcp:
        await mcp.call_tool("cancel_all_orders", {})
        await mcp.call_tool("close_all_positions", {})
        # close_all_positions may queue sell orders when market is closed;
        # cancel them so they don't trigger wash-trade rejections in tests.
        await mcp.call_tool("cancel_all_orders", {})
    yield
```

---

## File: `tests/test_integrity.py`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/tests/test_integrity.py`

```python
"""
Data integrity checks across toolsets, names, and OpenAPI specs.

Catches drift after spec updates: stale operationIds, missing ToolOverride
entries, and duplicate tool names.
"""

from __future__ import annotations

import json
from pathlib import Path

from alpaca_mcp_server.names import TOOLS, TOOL_NAMES, TOOL_DESCRIPTIONS
from alpaca_mcp_server.toolsets import OVERRIDE_OPERATION_IDS, TOOLSETS

SPECS_DIR = Path(__file__).resolve().parent.parent / "src" / "alpaca_mcp_server" / "specs"


def _load_operation_ids(spec_name: str) -> set[str]:
    """Extract all operationIds from a bundled OpenAPI spec."""
    spec = json.loads((SPECS_DIR / f"{spec_name}.json").read_text())
    ids: set[str] = set()
    for methods in spec["paths"].values():
        for details in methods.values():
            if isinstance(details, dict) and "operationId" in details:
                ids.add(details["operationId"])
    return ids


TRADING_OPS = _load_operation_ids("trading-api")
MARKET_DATA_OPS = _load_operation_ids("market-data-api")

SPEC_OPS = {
    "trading": TRADING_OPS,
    "market-data": MARKET_DATA_OPS,
}


def test_all_toolset_operation_ids_exist_in_specs():
    """Every operationId referenced in TOOLSETS must exist in its spec."""
    missing: list[str] = []
    for ts_name, ts_config in TOOLSETS.items():
        spec_ops = SPEC_OPS[ts_config["spec"]]
        for op_id in ts_config["operations"]:
            if op_id not in spec_ops:
                missing.append(f"{ts_name}/{op_id} not in {ts_config['spec']} spec")
    assert not missing, f"Stale operationIds:\n" + "\n".join(missing)


def test_override_operation_ids_exist_in_spec():
    """Every OVERRIDE_OPERATION_ID must exist in some spec."""
    all_spec_ops = TRADING_OPS | MARKET_DATA_OPS
    missing = OVERRIDE_OPERATION_IDS - all_spec_ops
    assert not missing, f"Override operationIds not in any spec: {missing}"


def test_all_non_override_operations_have_tool_overrides():
    """Every auto-generated operationId must have a ToolOverride in names.py."""
    all_ops: set[str] = set()
    for ts_config in TOOLSETS.values():
        all_ops.update(ts_config["operations"])

    need_override = all_ops - OVERRIDE_OPERATION_IDS
    missing = need_override - set(TOOLS.keys())
    assert not missing, (
        f"operationIds in toolsets.py without ToolOverride in names.py:\n"
        + "\n".join(sorted(missing))
    )


def test_no_orphan_tool_overrides():
    """Every ToolOverride key should be referenced by a toolset or an override."""
    all_ops: set[str] = set()
    for ts_config in TOOLSETS.values():
        all_ops.update(ts_config["operations"])
    all_ops.update(OVERRIDE_OPERATION_IDS)

    orphans = set(TOOLS.keys()) - all_ops
    assert not orphans, (
        f"ToolOverride entries in names.py not referenced by any toolset:\n"
        + "\n".join(sorted(orphans))
    )


def test_tool_names_are_unique():
    """No two operationIds should map to the same MCP tool name."""
    seen: dict[str, str] = {}
    dupes: list[str] = []
    for op_id, override in TOOLS.items():
        if override.name in seen:
            dupes.append(f"{override.name!r} used by both {seen[override.name]} and {op_id}")
        seen[override.name] = op_id
    assert not dupes, f"Duplicate tool names:\n" + "\n".join(dupes)


def test_all_descriptions_non_empty():
    """Every ToolOverride must have a non-empty description."""
    empty = [op_id for op_id, t in TOOLS.items() if not t.description.strip()]
    assert not empty, f"Empty descriptions: {empty}"


def test_derived_lookups_match_tools():
    """TOOL_NAMES and TOOL_DESCRIPTIONS must stay in sync with TOOLS."""
    assert set(TOOL_NAMES.keys()) == set(TOOLS.keys())
    assert set(TOOL_DESCRIPTIONS.keys()) == set(TOOLS.keys())
    for op_id, t in TOOLS.items():
        assert TOOL_NAMES[op_id] == t.name
        assert TOOL_DESCRIPTIONS[op_id] == t.description
```

---

## File: `tests/test_server_construction.py`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/tests/test_server_construction.py`

```python
"""
Layer 1: Server construction tests — no network, no real credentials.

Verifies that build_server() produces the expected set of MCP tools
from the bundled OpenAPI specs. Catches FastMCP API breakage, spec
parsing failures, and toolset/names misconfiguration.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastmcp.client import Client

from alpaca_mcp_server.server import build_server

DUMMY_ENV = {
    "ALPACA_API_KEY": "test-key",
    "ALPACA_SECRET_KEY": "test-secret",
    "ALPACA_PAPER_TRADE": "true",
}

EXPECTED_TOOLS = {
    # Account
    "get_account_info",
    "get_account_config",
    "update_account_config",
    "get_portfolio_history",
    "get_account_activities",
    "get_account_activities_by_type",
    # Trading: Orders
    "get_orders",
    "get_order_by_id",
    "get_order_by_client_id",
    "replace_order_by_id",
    "cancel_order_by_id",
    "cancel_all_orders",
    # Trading: Positions
    "get_all_positions",
    "get_open_position",
    "close_position",
    "close_all_positions",
    "exercise_options_position",
    "do_not_exercise_options_position",
    # Watchlists
    "get_watchlists",
    "create_watchlist",
    "get_watchlist_by_id",
    "update_watchlist_by_id",
    "delete_watchlist_by_id",
    "add_asset_to_watchlist_by_id",
    "remove_asset_from_watchlist_by_id",
    # Assets & Market Info
    "get_all_assets",
    "get_asset",
    "get_option_contracts",
    "get_option_contract",
    "get_calendar",
    "get_clock",
    "get_corporate_action_announcements",
    "get_corporate_action_announcement",
    # Stock Data
    "get_stock_bars",
    "get_stock_quotes",
    "get_stock_trades",
    "get_stock_latest_bar",
    "get_stock_latest_quote",
    "get_stock_latest_trade",
    "get_stock_snapshot",
    "get_most_active_stocks",
    "get_market_movers",
    # Crypto Data
    "get_crypto_bars",
    "get_crypto_quotes",
    "get_crypto_trades",
    "get_crypto_latest_bar",
    "get_crypto_latest_quote",
    "get_crypto_latest_trade",
    "get_crypto_snapshot",
    "get_crypto_latest_orderbook",
    # Options Data
    "get_option_bars",
    "get_option_trades",
    "get_option_latest_trade",
    "get_option_latest_quote",
    "get_option_snapshot",
    "get_option_chain",
    "get_option_exchange_codes",
    # Corporate Actions (Market Data)
    "get_corporate_actions",
    # Order Overrides
    "place_stock_order",
    "place_crypto_order",
    "place_option_order",
}


async def _list_tools(env: dict | None = None) -> list:
    """Build server with given env and return its tool list."""
    use_env = env or DUMMY_ENV
    with patch.dict(os.environ, use_env, clear=False):
        server = build_server()
    async with Client(transport=server) as c:
        return await c.list_tools()


async def test_tool_count():
    """Server must expose exactly 61 tools."""
    tools = await _list_tools()
    assert len(tools) == 61, f"Expected 61 tools, got {len(tools)}"


async def test_tool_names_match():
    """Every expected tool name must be present, with no extras."""
    tools = await _list_tools()
    actual = {t.name for t in tools}
    missing = EXPECTED_TOOLS - actual
    extra = actual - EXPECTED_TOOLS
    assert not missing, f"Missing tools: {sorted(missing)}"
    assert not extra, f"Unexpected tools: {sorted(extra)}"


async def test_all_tools_have_descriptions():
    """Every tool must have a non-empty description."""
    tools = await _list_tools()
    empty = [t.name for t in tools if not t.description or not t.description.strip()]
    assert not empty, f"Tools with empty descriptions: {sorted(empty)}"


async def test_order_tools_have_destructive_hint():
    """Order placement tools must be annotated as destructive."""
    tools = await _list_tools()
    order_tools = [t for t in tools if t.name.startswith("place_")]
    assert len(order_tools) == 3
    for t in order_tools:
        annotations = t.annotations
        assert annotations is not None, f"{t.name} missing annotations"
        assert annotations.destructiveHint is True, (
            f"{t.name} should have destructiveHint=True"
        )


async def test_toolset_filtering():
    """ALPACA_TOOLSETS should limit which tools are exposed."""
    tools = await _list_tools({**DUMMY_ENV, "ALPACA_TOOLSETS": "account"})
    names = {t.name for t in tools}
    assert "get_account_info" in names
    assert "place_stock_order" not in names
    assert "get_stock_bars" not in names
```

---

## File: `tests/test_paper_integration.py`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/tests/test_paper_integration.py`

```python
"""
Layer 3: Paper API integration tests — real network calls to Alpaca paper.

Requires ALPACA_API_KEY and ALPACA_SECRET_KEY env vars pointing at a
paper trading account. The entire module is skipped when credentials
are absent.

Run with:
    ALPACA_API_KEY=... ALPACA_SECRET_KEY=... pytest -m integration

These tests use limit orders at absurd prices to avoid fills, and
clean up any orders they create.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid

import pytest
from fastmcp.client import Client

from alpaca_mcp_server.server import build_server

_has_credentials = bool(
    os.environ.get("ALPACA_API_KEY") and os.environ.get("ALPACA_SECRET_KEY")
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _has_credentials, reason="Paper API credentials not set"),
]


def _to_dict(obj) -> dict | list | str:
    """Coerce Pydantic models, dicts, or other objects into plain dicts."""
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, list):
        return [_to_dict(item) for item in obj]
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return obj


def _parse(result) -> dict | list | str:
    """Extract usable data from a CallToolResult."""
    if hasattr(result, "data") and result.data is not None:
        return _to_dict(result.data)
    for block in result.content:
        if hasattr(block, "text"):
            try:
                return json.loads(block.text)
            except (json.JSONDecodeError, TypeError):
                return block.text
    return str(result)


async def _call(tool_name: str, args: dict | None = None) -> dict | list | str:
    """Build server, call a tool, return parsed result.

    A fresh server + client per call avoids event-loop conflicts on Python 3.10.
    """
    os.environ.setdefault("ALPACA_PAPER_TRADE", "true")
    server = build_server()
    async with Client(transport=server) as c:
        raw = await c.call_tool(tool_name, args or {})
    return _parse(raw)


# ── Account ─────────────────────────────────────────────────────────────


async def test_get_account_info():
    result = await _call("get_account_info")
    assert isinstance(result, dict), f"Unexpected type: {type(result)}"
    assert "account_number" in result
    assert "buying_power" in result
    assert "status" in result


async def test_get_portfolio_history():
    result = await _call("get_portfolio_history", {
        "period": "1W",
        "timeframe": "1D",
    })
    assert isinstance(result, dict)
    assert "equity" in result or "timestamp" in result


async def test_get_account_config():
    result = await _call("get_account_config")
    assert isinstance(result, dict)


async def test_get_account_activities():
    result = await _call("get_account_activities")
    assert isinstance(result, (dict, list))


async def test_get_account_activities_by_type():
    result = await _call("get_account_activities_by_type", {
        "activity_type": "FILL",
    })
    assert isinstance(result, (dict, list))


# ── Market Data: Stocks ─────────────────────────────────────────────────


async def test_get_stock_bars():
    result = await _call("get_stock_bars", {
        "symbols": "AAPL",
        "timeframe": "1Day",
        "days": 3,
        "limit": 10,
    })
    assert isinstance(result, dict)
    assert "bars" in result or "AAPL" in str(result)


async def test_get_stock_quotes():
    result = await _call("get_stock_quotes", {
        "symbols": "AAPL",
        "days": 0,
        "hours": 0,
        "minutes": 5,
        "limit": 5,
    })
    assert isinstance(result, dict)


async def test_get_stock_trades():
    result = await _call("get_stock_trades", {
        "symbols": "AAPL",
        "days": 0,
        "hours": 0,
        "minutes": 5,
        "limit": 5,
    })
    assert isinstance(result, dict)


async def test_get_stock_latest_bar():
    result = await _call("get_stock_latest_bar", {"symbols": "AAPL"})
    assert isinstance(result, dict)


async def test_get_stock_latest_quote():
    result = await _call("get_stock_latest_quote", {"symbols": "AAPL"})
    assert isinstance(result, dict)


async def test_get_stock_latest_trade():
    result = await _call("get_stock_latest_trade", {"symbols": "AAPL"})
    assert isinstance(result, dict)


async def test_get_stock_snapshot():
    result = await _call("get_stock_snapshot", {"symbols": "AAPL"})
    assert isinstance(result, dict)


async def test_get_most_active_stocks():
    result = await _call("get_most_active_stocks")
    assert isinstance(result, dict)
    assert "most_actives" in result


async def test_get_market_movers():
    result = await _call("get_market_movers", {"market_type": "stocks"})
    assert isinstance(result, dict)


# ── Market Data: Crypto ─────────────────────────────────────────────────


async def test_get_crypto_bars():
    result = await _call("get_crypto_bars", {
        "symbols": "BTC/USD",
        "timeframe": "1Hour",
        "days": 1,
        "limit": 10,
    })
    assert isinstance(result, dict)


async def test_get_crypto_quotes():
    result = await _call("get_crypto_quotes", {
        "symbols": "BTC/USD",
        "days": 0,
        "hours": 0,
        "minutes": 5,
        "limit": 5,
    })
    assert isinstance(result, dict)


async def test_get_crypto_trades():
    result = await _call("get_crypto_trades", {
        "symbols": "BTC/USD",
        "days": 0,
        "hours": 0,
        "minutes": 5,
        "limit": 5,
    })
    assert isinstance(result, dict)


async def test_get_crypto_latest_bar():
    result = await _call("get_crypto_latest_bar", {"symbols": "BTC/USD", "loc": "us"})
    assert isinstance(result, dict)


async def test_get_crypto_latest_quote():
    result = await _call("get_crypto_latest_quote", {"symbols": "BTC/USD", "loc": "us"})
    assert isinstance(result, dict)


async def test_get_crypto_latest_trade():
    result = await _call("get_crypto_latest_trade", {"symbols": "BTC/USD", "loc": "us"})
    assert isinstance(result, dict)


async def test_get_crypto_snapshot():
    result = await _call("get_crypto_snapshot", {"symbols": "BTC/USD", "loc": "us"})
    assert isinstance(result, dict)


async def test_get_crypto_latest_orderbook():
    result = await _call("get_crypto_latest_orderbook", {"symbols": "BTC/USD", "loc": "us"})
    assert isinstance(result, dict)


# ── Market Data: Options ────────────────────────────────────────────────


async def test_get_option_chain():
    result = await _call("get_option_chain", {"underlying_symbol": "AAPL"})
    assert isinstance(result, dict)


async def test_get_option_exchange_codes():
    result = await _call("get_option_exchange_codes")
    assert isinstance(result, dict)


async def test_get_option_contracts():
    result = await _call("get_option_contracts", {
        "underlying_symbols": "AAPL",
    })
    assert isinstance(result, dict)


async def _find_option_symbol() -> str | None:
    """Find a real AAPL option symbol from the chain."""
    chain = await _call("get_option_chain", {"underlying_symbol": "AAPL"})
    if not isinstance(chain, dict):
        return None
    snapshots = chain.get("snapshots") or {}
    if not snapshots:
        return None
    return next(iter(snapshots))


async def test_get_option_latest_quote():
    symbol = await _find_option_symbol()
    if not symbol:
        pytest.skip("No option chain data available for AAPL")
    result = await _call("get_option_latest_quote", {"symbols": symbol})
    assert isinstance(result, dict)


async def test_get_option_latest_trade():
    symbol = await _find_option_symbol()
    if not symbol:
        pytest.skip("No option chain data available for AAPL")
    result = await _call("get_option_latest_trade", {"symbols": symbol})
    assert isinstance(result, dict)


async def test_get_option_snapshot():
    symbol = await _find_option_symbol()
    if not symbol:
        pytest.skip("No option chain data available for AAPL")
    result = await _call("get_option_snapshot", {"symbols": symbol})
    assert isinstance(result, dict)


async def test_get_option_bars():
    symbol = await _find_option_symbol()
    if not symbol:
        pytest.skip("No option chain data available for AAPL")
    result = await _call("get_option_bars", {"symbols": symbol, "timeframe": "1D"})
    assert isinstance(result, dict)


async def test_get_option_trades():
    symbol = await _find_option_symbol()
    if not symbol:
        pytest.skip("No option chain data available for AAPL")
    result = await _call("get_option_trades", {"symbols": symbol})
    assert isinstance(result, dict)


async def test_get_option_contract():
    symbol = await _find_option_symbol()
    if not symbol:
        pytest.skip("No option chain data available for AAPL")
    result = await _call("get_option_contract", {"symbol_or_id": symbol})
    assert isinstance(result, dict)


# ── Market Data: Corporate Actions ──────────────────────────────────────


async def test_get_corporate_actions():
    result = await _call("get_corporate_actions", {
        "types": "cash_dividend",
        "date_from": "2025-01-01",
        "date_to": "2025-01-31",
    })
    assert isinstance(result, dict)


# ── Assets & Market Info ────────────────────────────────────────────────


async def test_get_asset():
    result = await _call("get_asset", {"symbol_or_asset_id": "AAPL"})
    assert isinstance(result, dict)
    assert result.get("symbol") == "AAPL" or "AAPL" in str(result)


async def test_get_all_assets():
    result = await _call("get_all_assets", {
        "status": "active",
        "asset_class": "us_equity",
    })
    assert isinstance(result, (dict, list))


async def test_get_clock():
    result = await _call("get_clock")
    assert isinstance(result, dict)
    assert "is_open" in result


async def test_get_calendar():
    result = await _call("get_calendar")
    assert isinstance(result, (dict, list))


async def test_get_corporate_action_announcements():
    result = await _call("get_corporate_action_announcements", {
        "ca_types": "dividend",
        "since": "2025-01-01",
        "until": "2025-01-31",
    })
    assert isinstance(result, (dict, list))


# ── Orders: Place + Fetch + Replace + Cancel ────────────────────────────


async def test_place_and_cancel_stock_order():
    """Place a limit buy at $1 (won't fill), fetch by ID, then cancel."""
    os.environ.setdefault("ALPACA_PAPER_TRADE", "true")
    server = build_server()
    async with Client(transport=server) as mcp:
        order = _parse(await mcp.call_tool("place_stock_order", {
            "symbol": "AAPL",
            "side": "buy",
            "qty": "1",
            "type": "limit",
            "time_in_force": "day",
            "limit_price": "1.00",
        }))
        assert isinstance(order, dict), f"Order response: {order}"
        assert "error" not in order, f"Order placement failed: {order}"
        order_id = order.get("id")
        assert order_id, f"No order ID in response: {order}"

        try:
            single = _parse(await mcp.call_tool("get_order_by_id", {
                "order_id": order_id,
            }))
            assert isinstance(single, dict)
            assert single.get("id") == order_id
        finally:
            await mcp.call_tool("cancel_order_by_id", {"order_id": order_id})


async def test_place_with_client_order_id():
    """Place with client_order_id, fetch by client ID, then cancel."""
    client_oid = f"mcp-test-{uuid.uuid4().hex[:12]}"
    os.environ.setdefault("ALPACA_PAPER_TRADE", "true")
    server = build_server()
    async with Client(transport=server) as mcp:
        order = _parse(await mcp.call_tool("place_stock_order", {
            "symbol": "MSFT",
            "side": "buy",
            "qty": "1",
            "type": "limit",
            "time_in_force": "day",
            "limit_price": "1.00",
            "client_order_id": client_oid,
        }))
        assert isinstance(order, dict)
        assert "error" not in order, f"Order failed: {order}"
        order_id = order.get("id")

        try:
            by_client = _parse(await mcp.call_tool("get_order_by_client_id", {
                "client_order_id": client_oid,
            }))
            assert isinstance(by_client, dict)
            assert by_client.get("client_order_id") == client_oid
        finally:
            await mcp.call_tool("cancel_order_by_id", {"order_id": order_id})


async def test_replace_order():
    """Place a limit order, replace it with a new price, then cancel."""
    os.environ.setdefault("ALPACA_PAPER_TRADE", "true")
    server = build_server()
    async with Client(transport=server) as mcp:
        order = _parse(await mcp.call_tool("place_stock_order", {
            "symbol": "GOOG",
            "side": "buy",
            "qty": "1",
            "type": "limit",
            "time_in_force": "day",
            "limit_price": "1.00",
        }))
        assert "error" not in order, f"Order failed: {order}"
        order_id = order["id"]
        cancel_id = order_id

        try:
            # Wait for the order to leave pending_new (API rejects replace on pending_new)
            for _ in range(10):
                current = _parse(await mcp.call_tool("get_order_by_id", {"order_id": order_id}))
                if current.get("status") != "pending_new":
                    break
                await asyncio.sleep(0.5)

            replaced = _parse(await mcp.call_tool("replace_order_by_id", {
                "order_id": order_id,
                "qty": "2",
                "limit_price": "1.50",
            }))
            assert isinstance(replaced, dict)
            cancel_id = replaced.get("id", order_id)
        finally:
            await mcp.call_tool("cancel_order_by_id", {"order_id": cancel_id})


async def test_get_orders():
    result = await _call("get_orders", {"status": "all", "limit": 5})
    assert isinstance(result, (dict, list))


async def test_place_and_cancel_crypto_order():
    """Place a limit buy for BTC/USD at $20k (won't fill at ~$80k), then cancel."""
    os.environ.setdefault("ALPACA_PAPER_TRADE", "true")
    server = build_server()
    async with Client(transport=server) as mcp:
        order = _parse(await mcp.call_tool("place_crypto_order", {
            "symbol": "BTC/USD",
            "side": "buy",
            "qty": "0.001",
            "type": "limit",
            "time_in_force": "gtc",
            "limit_price": "20000.00",
        }))
        assert isinstance(order, dict), f"Order response: {order}"
        assert "error" not in order, f"Order placement failed: {order}"
        order_id = order.get("id")
        assert order_id, f"No order ID in response: {order}"

        try:
            single = _parse(await mcp.call_tool("get_order_by_id", {
                "order_id": order_id,
            }))
            assert isinstance(single, dict)
        finally:
            await mcp.call_tool("cancel_order_by_id", {"order_id": order_id})


# ── Positions ───────────────────────────────────────────────────────────


async def test_get_all_positions():
    result = await _call("get_all_positions")
    assert isinstance(result, (dict, list))


# ── Watchlists (full CRUD) ──────────────────────────────────────────────


async def test_watchlist_full_crud():
    """Create, list, update, add/remove asset, then delete."""
    wl_name = f"mcp-test-{uuid.uuid4().hex[:8]}"
    os.environ.setdefault("ALPACA_PAPER_TRADE", "true")
    server = build_server()
    async with Client(transport=server) as mcp:
        created = _parse(await mcp.call_tool("create_watchlist", {
            "name": wl_name,
            "symbols": ["AAPL"],
        }))
        assert isinstance(created, dict), f"Create response: {created}"
        wl_id = created.get("id")
        assert wl_id, f"No watchlist ID: {created}"

        try:
            # get_watchlists
            all_wl = _parse(await mcp.call_tool("get_watchlists", {}))
            assert isinstance(all_wl, (dict, list))

            # get_watchlist_by_id
            fetched = _parse(await mcp.call_tool("get_watchlist_by_id", {
                "watchlist_id": wl_id,
            }))
            assert isinstance(fetched, dict)

            # update_watchlist_by_id
            updated = _parse(await mcp.call_tool("update_watchlist_by_id", {
                "watchlist_id": wl_id,
                "name": wl_name + "-updated",
            }))
            assert isinstance(updated, dict)

            # add_asset_to_watchlist_by_id
            added = _parse(await mcp.call_tool("add_asset_to_watchlist_by_id", {
                "watchlist_id": wl_id,
                "symbol": "MSFT",
            }))
            assert isinstance(added, dict)

            # remove_asset_from_watchlist_by_id
            removed = _parse(await mcp.call_tool("remove_asset_from_watchlist_by_id", {
                "watchlist_id": wl_id,
                "symbol": "MSFT",
            }))
            assert isinstance(removed, dict)
        finally:
            await mcp.call_tool("delete_watchlist_by_id", {
                "watchlist_id": wl_id,
            })


# ── Cancel All Orders ───────────────────────────────────────────────────


async def test_cancel_all_orders():
    """Place 3 limit orders, cancel all at once, verify none remain."""
    os.environ.setdefault("ALPACA_PAPER_TRADE", "true")
    server = build_server()
    symbols = ["TSLA", "AMZN", "META"]
    async with Client(transport=server) as mcp:
        order_ids = []
        for i in range(3):
            order = _parse(await mcp.call_tool("place_stock_order", {
                "symbol": symbols[i],
                "side": "buy",
                "qty": "1",
                "type": "limit",
                "time_in_force": "day",
                "limit_price": str(1.00 + i * 0.01),
            }))
            assert "error" not in order, f"Order {i} failed: {order}"
            order_ids.append(order["id"])

        try:
            result = _parse(await mcp.call_tool("cancel_all_orders", {}))
            assert isinstance(result, (dict, list))
        except Exception:
            for oid in order_ids:
                try:
                    await mcp.call_tool("cancel_order_by_id", {"order_id": oid})
                except Exception:
                    pass
            raise


# ── Positions: Open + Get + Close ───────────────────────────────────────


async def test_position_lifecycle():
    """Buy 1 share at market, check position, close it.

    Skipped when market is closed (order won't fill immediately).
    """
    import asyncio

    os.environ.setdefault("ALPACA_PAPER_TRADE", "true")
    server = build_server()
    async with Client(transport=server) as mcp:
        clock = _parse(await mcp.call_tool("get_clock", {}))
        if not clock.get("is_open"):
            pytest.skip("Market is closed — position tests require fills")

        order = _parse(await mcp.call_tool("place_stock_order", {
            "symbol": "AAPL",
            "side": "buy",
            "qty": "1",
            "type": "market",
            "time_in_force": "day",
        }))
        assert "error" not in order, f"Market order failed: {order}"
        order_id = order["id"]

        # Wait briefly for fill
        await asyncio.sleep(2)

        filled = _parse(await mcp.call_tool("get_order_by_id", {
            "order_id": order_id,
        }))
        if filled.get("status") != "filled":
            await mcp.call_tool("cancel_order_by_id", {"order_id": order_id})
            pytest.skip("Order did not fill in time")

        try:
            # get_open_position
            pos = _parse(await mcp.call_tool("get_open_position", {
                "symbol_or_asset_id": "AAPL",
            }))
            assert isinstance(pos, dict)
            assert pos.get("symbol") == "AAPL" or "AAPL" in str(pos)

            # close_position
            closed = _parse(await mcp.call_tool("close_position", {
                "symbol_or_asset_id": "AAPL",
            }))
            assert isinstance(closed, dict)
        except Exception:
            try:
                await mcp.call_tool("close_position", {
                    "symbol_or_asset_id": "AAPL",
                })
            except Exception:
                pass
            raise


async def test_close_all_positions():
    """Call close_all_positions — safe even with no open positions."""
    result = await _call("close_all_positions")
    assert isinstance(result, (dict, list))


# ── Account Config: Toggle + Restore ────────────────────────────────────


async def test_update_account_config():
    """Toggle trade_confirm_email, verify it changed, then restore."""
    os.environ.setdefault("ALPACA_PAPER_TRADE", "true")
    server = build_server()
    async with Client(transport=server) as mcp:
        original = _parse(await mcp.call_tool("get_account_config", {}))
        assert isinstance(original, dict)
        orig_value = original.get("trade_confirm_email", "all")

        new_value = "none" if orig_value == "all" else "all"

        try:
            updated = _parse(await mcp.call_tool("update_account_config", {
                "trade_confirm_email": new_value,
            }))
            assert isinstance(updated, dict)
            assert updated.get("trade_confirm_email") == new_value
        finally:
            await mcp.call_tool("update_account_config", {
                "trade_confirm_email": orig_value,
            })
```

---

## File: `charts/alpaca-mcp-server/.helmignore`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/charts/alpaca-mcp-server/.helmignore`

```text
# Patterns to ignore when building packages.
# This supports shell glob matching, relative path matching, and
# negation (prefixed with !). Only one pattern per line.
.DS_Store
# Common VCS dirs
.git/
.gitignore
.bzr/
.bzrignore
.hg/
.hgignore
.svn/
# Common backup files
*.swp
*.bak
*.tmp
*.orig
*~
# Various IDEs
.project
.idea/
*.tmproj
.vscode/
```

---

## File: `charts/alpaca-mcp-server/Chart.yaml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/charts/alpaca-mcp-server/Chart.yaml`

```yaml
apiVersion: v2
name: mcp-server
description: A Helm chart for Kubernetes

# A chart can be either an 'application' or a 'library' chart.
#
# Application charts are a collection of templates that can be packaged into versioned archives
# to be deployed.
#
# Library charts provide useful utilities or functions for the chart developer. They're included as
# a dependency of application charts to inject those utilities and functions into the rendering
# pipeline. Library charts do not define any templates and therefore cannot be deployed.
type: application

# This is the chart version. This version number should be incremented each time you make changes
# to the chart and its templates, including the app version.
# Versions are expected to follow Semantic Versioning (https://semver.org/)
version: 0.1.0

# This is the version number of the application being deployed. This version number should be
# incremented each time you make changes to the application. Versions are not expected to
# follow Semantic Versioning. They should reflect the version the application is using.
# It is recommended to use it with quotes.
appVersion: "2.0.0"
```

---

## File: `charts/alpaca-mcp-server/values.yaml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/charts/alpaca-mcp-server/values.yaml`

```yaml
# Default values for mcp-server.
# This is a YAML-formatted file.
# Declare variables to be passed into your templates.

# This will set the replicaset count more information can be found here: https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/
replicaCount: 1

# This sets the container image more information can be found here: https://kubernetes.io/docs/concepts/containers/images/
image:
  repository: <mcp-server-image-repository>
  # This sets the pull policy for images.
  pullPolicy: IfNotPresent
  # Overrides the image tag whose default is the chart appVersion.
  tag: "<mcp-server-image-tag>"

# This sets the command to run in the container more information can be found here: https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/
command: ["alpaca-mcp-server"]
# This sets the arguments to pass to the command more information can be found here: https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/
args: ["serve", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]

# This is for the secrets for pulling an image from a private repository more information can be found here: https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/
imagePullSecrets: []
# This is to override the chart name.
nameOverride: ""
fullnameOverride: ""

# This section builds out the service account more information can be found here: https://kubernetes.io/docs/concepts/security/service-accounts/
serviceAccount:
  # Specifies whether a service account should be created
  create: true
  # Automatically mount a ServiceAccount's API credentials?
  automount: true
  # Annotations to add to the service account
  annotations: {}
  # The name of the service account to use.
  # If not set and create is true, a name is generated using the fullname template
  name: ""

# This is for setting Kubernetes Annotations to a Pod.
# For more information checkout: https://kubernetes.io/docs/concepts/overview/working-with-objects/annotations/
podAnnotations: {}
# This is for setting Kubernetes Labels to a Pod.
# For more information checkout: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/
podLabels: {}

podSecurityContext: {}
  # fsGroup: 2000

securityContext: {}
  # capabilities:
  #   drop:
  #   - ALL
  # readOnlyRootFilesystem: true
  # runAsNonRoot: true
  # runAsUser: 1000

# This is for setting up a service more information can be found here: https://kubernetes.io/docs/concepts/services-networking/service/
service:
  # This sets the service type more information can be found here: https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types
  type: ClusterIP
  # This sets the ports more information can be found here: https://kubernetes.io/docs/concepts/services-networking/service/#field-spec-ports
  port: 8000

# This block is for setting up the ingress for more information can be found here: https://kubernetes.io/docs/concepts/services-networking/ingress/
ingress:
  enabled: true
  className: "external-nginx"
  annotations: 
    cert-manager.io/cluster-issuer: "cert-manager-resources"
  hosts:
    - host: mcp.alpaca.markets
      paths:
        - path: /
          pathType: Prefix
  tls: 
    - secretName: cert-mcp.alpaca.markets
      hosts:
        - mcp.alpaca.markets

resources: 
  limits:
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

# This is to setup the liveness and readiness probes more information can be found here: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
# Using TCP socket probes since the MCP server requires specific HTTP headers (text/event-stream)
livenessProbe:
  tcpSocket:
    port: http
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
readinessProbe:
  tcpSocket:
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3

# This section is for setting up autoscaling more information can be found here: https://kubernetes.io/docs/concepts/workloads/autoscaling/
autoscaling:
  enabled: false
  minReplicas: 2
  maxReplicas: 100
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80

# Additional volumes on the output Deployment definition.
volumes: []
# - name: foo
#   secret:
#     secretName: mysecret
#     optional: false

# Additional volumeMounts on the output Deployment definition.
volumeMounts: []
# - name: foo
#   mountPath: "/etc/foo"
#   readOnly: true

nodeSelector: {}

tolerations: []

affinity: {}

# Environment variables configuration
env:
  # Sensitive environment variables (stored in Secret, can be encrypted with SOPS)
  secrets: 
    ALPACA_API_KEY: "<alpaca-api-key>"
    ALPACA_SECRET_KEY: "<alpaca-secret-key>"
```

---

## File: `charts/alpaca-mcp-server/templates/NOTES.txt`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/charts/alpaca-mcp-server/templates/NOTES.txt`

```text
1. Get the application URL by running these commands:
{{- if .Values.ingress.enabled }}
{{- range $host := .Values.ingress.hosts }}
  {{- range .paths }}
  http{{ if $.Values.ingress.tls }}s{{ end }}://{{ $host.host }}{{ .path }}
  {{- end }}
{{- end }}
{{- else if contains "NodePort" .Values.service.type }}
  export NODE_PORT=$(kubectl get --namespace {{ .Release.Namespace }} -o jsonpath="{.spec.ports[0].nodePort}" services {{ include "mcp-server.fullname" . }})
  export NODE_IP=$(kubectl get nodes --namespace {{ .Release.Namespace }} -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT
{{- else if contains "LoadBalancer" .Values.service.type }}
     NOTE: It may take a few minutes for the LoadBalancer IP to be available.
           You can watch its status by running 'kubectl get --namespace {{ .Release.Namespace }} svc -w {{ include "mcp-server.fullname" . }}'
  export SERVICE_IP=$(kubectl get svc --namespace {{ .Release.Namespace }} {{ include "mcp-server.fullname" . }} --template "{{"{{ range (index .status.loadBalancer.ingress 0) }}{{.}}{{ end }}"}}")
  echo http://$SERVICE_IP:{{ .Values.service.port }}
{{- else if contains "ClusterIP" .Values.service.type }}
  export POD_NAME=$(kubectl get pods --namespace {{ .Release.Namespace }} -l "app.kubernetes.io/name={{ include "mcp-server.name" . }},app.kubernetes.io/instance={{ .Release.Name }}" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace {{ .Release.Namespace }} $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace {{ .Release.Namespace }} port-forward $POD_NAME 8080:$CONTAINER_PORT
{{- end }}
```

---

## File: `charts/alpaca-mcp-server/templates/_helpers.tpl`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/charts/alpaca-mcp-server/templates/_helpers.tpl`

```gotemplate
{{/*
Expand the name of the chart.
*/}}
{{- define "mcp-server.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "mcp-server.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "mcp-server.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "mcp-server.labels" -}}
helm.sh/chart: {{ include "mcp-server.chart" . }}
{{ include "mcp-server.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "mcp-server.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mcp-server.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "mcp-server.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "mcp-server.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
```

---

## File: `charts/alpaca-mcp-server/templates/deployment.yaml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/charts/alpaca-mcp-server/templates/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "mcp-server.fullname" . }}
  labels:
    {{- include "mcp-server.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "mcp-server.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      {{- with .Values.podAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      labels:
        {{- include "mcp-server.labels" . | nindent 8 }}
        {{- with .Values.podLabels }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "mcp-server.serviceAccountName" . }}
      {{- with .Values.podSecurityContext }}
      securityContext:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
        - name: {{ .Chart.Name }}
          {{- with .Values.securityContext }}
          securityContext:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          {{- with .Values.command }}
          command:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.args }}
          args:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          ports:
            - name: http
              containerPort: {{ .Values.service.port }}
              protocol: TCP
          {{- with .Values.livenessProbe }}
          livenessProbe:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.readinessProbe }}
          readinessProbe:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- if .Values.env.secrets }}
          envFrom:
            - secretRef:
                name: {{ include "mcp-server.fullname" . }}-secrets
          {{- end }}
          {{- with .Values.resources }}
          resources:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.volumeMounts }}
          volumeMounts:
            {{- toYaml . | nindent 12 }}
          {{- end }}
      {{- with .Values.volumes }}
      volumes:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

---

## File: `charts/alpaca-mcp-server/templates/hpa.yaml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/charts/alpaca-mcp-server/templates/hpa.yaml`

```yaml
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "mcp-server.fullname" . }}
  labels:
    {{- include "mcp-server.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "mcp-server.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
    {{- end }}
    {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
    {{- end }}
{{- end }}
```

---

## File: `charts/alpaca-mcp-server/templates/ingress.yaml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/charts/alpaca-mcp-server/templates/ingress.yaml`

```yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "mcp-server.fullname" . }}
  labels:
    {{- include "mcp-server.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- with .Values.ingress.className }}
  ingressClassName: {{ . }}
  {{- end }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            {{- with .pathType }}
            pathType: {{ . }}
            {{- end }}
            backend:
              service:
                name: {{ include "mcp-server.fullname" $ }}
                port:
                  number: {{ $.Values.service.port }}
          {{- end }}
    {{- end }}
{{- end }}
```

---

## File: `charts/alpaca-mcp-server/templates/secrets.yaml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/charts/alpaca-mcp-server/templates/secrets.yaml`

```yaml
{{- if .Values.env.secrets }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "mcp-server.fullname" . }}-secrets
  labels:
    {{- include "mcp-server.labels" . | nindent 4 }}
type: Opaque
stringData:
  {{- range $key, $value := .Values.env.secrets }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
{{- end }}
```

---

## File: `charts/alpaca-mcp-server/templates/service.yaml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/charts/alpaca-mcp-server/templates/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "mcp-server.fullname" . }}
  labels:
    {{- include "mcp-server.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "mcp-server.selectorLabels" . | nindent 4 }}
```

---

## File: `charts/alpaca-mcp-server/templates/serviceaccount.yaml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/charts/alpaca-mcp-server/templates/serviceaccount.yaml`

```yaml
{{- if .Values.serviceAccount.create -}}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "mcp-server.serviceAccountName" . }}
  labels:
    {{- include "mcp-server.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
automountServiceAccountToken: {{ .Values.serviceAccount.automount }}
{{- end }}
```

---

## File: `charts/alpaca-mcp-server/templates/tests/test-connection.yaml`

Source URL: `https://raw.githubusercontent.com/alpacahq/alpaca-mcp-server/refs/heads/main/charts/alpaca-mcp-server/templates/tests/test-connection.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "mcp-server.fullname" . }}-test-connection"
  labels:
    {{- include "mcp-server.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": test
spec:
  containers:
    - name: wget
      image: busybox
      command: ['wget']
      args: ['{{ include "mcp-server.fullname" . }}:{{ .Values.service.port }}']
  restartPolicy: Never
```

---
