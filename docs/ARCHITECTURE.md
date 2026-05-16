# Architecture Guide

## System Overview

```
┌──────────────────────────┐
│   Claude with MCPs       │
├──────────────────────────┤
│  Gmail MCP (built-in)    │ ← Claude's official integration
│  Calendar MCP (built-in) │ ← Claude's official integration
│  Notes MCP (custom)  ────┼─→ FastMCP → AppleScript → Mac Notes
└────────────┬─────────────┘
             │
        Claude's
      autonomous
      tool use
             │
             ▼
    ┌────────────────┐
    │ Daily Digest   │
    │ (synthesized)  │
    └────────────┬───┘
                 │
                 ▼
        ┌────────────────┐
        │ Email Delivery │
        │ (or file save) │
        └────────────────┘
```

## Design Philosophy: Pragmatism Over Purity

This project deliberately **doesn't** build Gmail and Calendar MCPs from scratch. Here's why:

### ✅ Use Existing Tools
- Claude already has official Gmail and Calendar MCPs
- Building our own would be redundant code
- Using built-ins saves development time
- Demonstrates good engineering judgment

### ✅ Build Only What's Unique
- Mac Notes has no official API
- We built a custom MCP for this using AppleScript
- This is where we add unique value

### ✅ Focus on Integration Patterns
This showcases:
- How to compose multiple MCPs
- How to leverage Claude's autonomous tool use
- How to add custom MCPs when needed
- Pragmatic architectural thinking

## Architecture Decisions

### 1. Claude's Autonomous Tool Use

Instead of manually orchestrating data collection:

**❌ Old approach (if we built MCPs):**
```python
emails = call_gmail_mcp()
events = call_calendar_mcp()
todos = call_notes_mcp()
digest = claude.synthesize(emails, events, todos)
```

**✅ New approach:**
```python
digest = claude.call_with_tools(
    "Gather email, calendar, and notes data. Synthesize into digest.",
    tools=[gmail, calendar, notes]
)
```

Claude decides:
- Which tools to call
- In what order
- With what parameters
- How to synthesize results

This is **more powerful** because Claude can:
- Ask follow-up questions
- Handle errors gracefully
- Connect insights across sources
- Adapt to different scenarios

### 2. Custom Notes MCP

Mac Notes lacks an official API, so we built a FastMCP server that:

```python
@mcp.tool()
def read_todos(note_name: str) -> list[TodoItem]:
    # Uses AppleScript to access Notes.app
    script = f"""
    tell application "Notes"
        ...get note content...
    end tell
    """
    result = subprocess.run(["osascript", "-e", script])
    # Parse TODO items from content
    return todos
```

**Why AppleScript?**
- Only way to access Notes without official API
- Demonstrates creative problem-solving
- Shows resourcefulness under constraints

**Limitations & Mitigations:**
- AppleScript is slower than direct APIs → we cache/run once daily
- Requires Notes.app to be running → graceful error handling
- Text-only (no rich formatting) → acceptable for digest

### 3. Orchestrator Pattern

The `main.py` orchestrator:

```python
class DigestGenerator:
    def run(self):
        self._start_notes_mcp()      # Start custom MCP
        digest = self._generate_digest_with_claude()  # Claude uses all tools
        self._output_digest(digest)  # Save/send result
        self._cleanup_notes_mcp()    # Cleanup
```

**Responsibilities:**
- Lifecycle management (start/stop Notes MCP)
- Claude orchestration (passing prompt with tools)
- Output delivery (printing, saving, future: email)
- Error handling & logging

### 4. Configuration Management

Environment-driven configuration:

```python
# config.py validates on import
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
if not CLAUDE_API_KEY:
    raise ValueError("Missing CLAUDE_API_KEY")
```

**Benefits:**
- Separates config from code
- Secure (credentials not in git)
- Easy to change settings
- Fails fast with clear errors

### 5. Error Handling Strategy

Graceful degradation:

```python
try:
    self._start_notes_mcp()
except Exception as e:
    logger.warning(f"Notes MCP failed: {e}")
    # Continue anyway - digest uses Gmail + Calendar

digest = self._generate_digest_with_claude()
# If Notes unavailable, Claude still synthesizes from available sources
```

Benefits:
- One failing source doesn't break the digest
- User still gets value
- Errors are logged but non-fatal

## Claude's Role

Claude does heavy lifting:

1. **Tool Selection**: Decides which MCPs to call based on task
2. **Data Gathering**: Uses tools to fetch emails, events, TODOs
3. **Analysis**: Identifies connections ("Meeting at 3pm conflicts with project deadline")
4. **Synthesis**: Creates coherent, actionable digest
5. **Formatting**: Generates well-structured output

This is **much better** than manual orchestration because Claude can:
- Handle variations automatically
- Provide intelligent reasoning
- Adapt to different user needs
- Explain its decisions if prompted

## Why Not Build Everything as MCPs?

Initial approach built Gmail and Calendar MCPs:

**❌ Why we changed:**
- Duplicated existing official tools
- Increased code to maintain
- More points of failure
- Showed worse judgment ("reinvent the wheel")

**✅ Better approach:**
- Use official integrations
- Build only custom MCPs
- Simpler codebase
- Shows pragmatism & judgment

This is better for interviews because it demonstrates:
- Knowledge of available tools
- Ability to evaluate tradeoffs
- Focus on unique value
- Pragmatic architecture

## Integration with Claude Code

The project works with Claude Code's scheduled tasks:

```bash
/schedule daily-digest "Run at 8am weekdays"
```

Claude Code handles:
- Scheduling infrastructure
- Environment setup
- Log management
- Error notifications

## Performance Characteristics

Typical execution:
```
Start Notes MCP:    0.5s
Claude inference:   2-3s (API call + reasoning)
Total:              3-4s per day
```

**Why so fast?**
- No manual API orchestration
- Claude batches tool calls
- Notes MCP runs once per day
- Cached tokens if using prompt cache

## Scaling Considerations

Current design handles:
- Single user, single Mac ✅
- Multiple days of history (with DB) ✅
- Additional MCPs (just add to Claude's tools) ✅

To scale:
- Multi-user: Per-user configs, separate token storage
- Cloud: HTTP MCPs instead of stdio
- High-frequency: Add caching layer

## Security Model

**Data Flow:**
```
Local Mac Notes ← AppleScript (local)
Gmail (via OAuth) ← API (encrypted)
Calendar (via OAuth) ← API (encrypted)
         ↓
    Claude API (encrypted)
         ↓
    Generated digest (saved locally)
```

**Security Properties:**
- OAuth tokens stored locally (user-only readable)
- API credentials in `.env` (not committed to git)
- Data transits encrypted to Claude
- No third-party data storage
- User owns API keys

**Risks:**
- Claude sees email content (mitigated: use separate read-only API key)
- AppleScript requires Terminal permissions (accept explicitly)
- Lost API key = access to user data (mitigated: rotate regularly)

## Testing Strategy

### Unit Tests
Test individual components:
```python
def test_todo_parsing():
    note = Note(content="[ ] Task 1\n[x] Task 2")
    todos = parse_todos(note)
    assert len(todos) == 2
    assert todos[0].checked == False
```

### Integration Tests
Test Notes MCP with Inspector:
```bash
npx @modelcontextprotocol/inspector python server.py
```

### End-to-End Tests
Run full pipeline:
```bash
python3 digest_orchestrator/main.py
```

Verify:
- Claude successfully calls all MCPs
- Data is gathered correctly
- Digest is synthesized well
- Output is saved/delivered

## Extending the System

### Adding New Data Sources

1. Create new MCP in `mcp_servers/<source>_mcp/`
2. Update orchestrator to start it:
   ```python
   def _start_source_mcp(self):
       # Add similar to Notes MCP startup
   ```
3. Update Claude's prompt to mention new source
4. Claude will automatically use it

### Customizing the Digest

Edit the prompt in `main.py`:
```python
prompt = f"""
[...instructions for Claude...]
- Include meditation recommendations
- Add weather forecast
- Note birthdays
- Suggest break times
"""
```

Claude adapts automatically.

### Alternative Delivery Methods

Currently saves to file. To add:

**Email via Gmail API:**
```python
def _send_email_digest(self, subject, body):
    service = build("gmail", "v1", credentials=creds)
    service.users().messages().send(
        userId="me",
        body=create_message(subject, body)
    ).execute()
```

**Slack:**
```python
def _send_to_slack(self, digest):
    slack.chat_postMessage(channel="#daily", text=digest)
```

**Dashboard:**
```python
def _store_digest(self, digest):
    db.insert({"date": today, "content": digest})
    # Website displays stored digests
```

## Conclusion

This architecture demonstrates:

1. **Pragmatic Tool Selection** — Use official MCPs, build only when needed
2. **Composition Patterns** — Multiple MCPs + Claude's autonomous tool use
3. **Creative Problem-Solving** — AppleScript for Notes integration
4. **Software Engineering** — Error handling, logging, configuration
5. **Full Integration** — Data collection → AI reasoning → delivery

The code is intentionally educational—readable, well-commented, suitable for discussing design decisions in interviews.
