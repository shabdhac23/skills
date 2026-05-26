# Daily Digest Assistant

A pragmatic daily assistant that synthesizes your email, calendar, and notes into a prioritized action digest delivered each morning.

## Features

- **Email Intelligence**: Claude reads your unread emails and identifies which need replies
- **Calendar Awareness**: Extracts today's events and time commitments
- **Notes Integration**: Reads your "TODOs" and "Priorities" notes from Mac Notes
- **Intelligent Synthesis**: Claude's reasoning connects disparate sources to create coherent priorities
- **Daily Delivery**: Automated morning email with your action plan

## Architecture

```
Gmail (Claude Built-in MCP)  ┐
                              ├─→ Claude AI ─→ Daily Digest
Google Calendar (Built-in)   ├─→ (autonomous tool use)
Mac Notes MCP (Custom) ──────┘
```

### Why This Design?

**Smart Tool Composition**: Instead of building Gmail and Calendar MCPs from scratch, this project leverages Claude's built-in integrations. This demonstrates:
- Pragmatic engineering (don't reinvent the wheel)
- Ability to compose existing tools effectively
- Focus on the unique value (Notes integration + synthesis logic)

**Custom Notes MCP**: Since Mac Notes has no official API, we built a custom MCP using AppleScript—a creative solution that showcases problem-solving.

## Quick Start

### 1. Prerequisites

- Python 3.9+
- macOS (for Notes integration)
- Claude Code or standalone Claude API access
- Claude API key

### 2. Setup

```bash
git clone <your-repo>
cd daily-digest-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r digest_orchestrator/requirements.txt
pip install -r mcp_servers/notes_mcp/requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with:
#   - CLAUDE_API_KEY (from Anthropic)
#   - DIGEST_RECIPIENT_EMAIL (your email)
```

### 4. Prepare Mac Notes

Create two notes in your Mac Notes app:
- **"TODOs"**: Use `[ ] item` format for tasks
- **"Priorities"**: List your key priorities for the day

### 5. Test

```bash
python3 digest_orchestrator/main.py
```

You'll see a digest printed to console and saved to `~/digest_*.txt`.

### 6. Schedule (Optional)

See [SETUP.md](docs/SETUP.md) for scheduling options:
- Claude Code `/schedule` command
- macOS Launchd
- Cron job

## How It Works

1. **Orchestrator starts** → launches Notes MCP server
2. **Claude autonomously uses tools**:
   - Lists your unread emails (Gmail MCP)
   - Fetches today's events (Calendar MCP)
   - Reads your TODOs and priorities (Notes MCP)
3. **Claude synthesizes** → connects data across sources, identifies priorities
4. **Digest delivered** → printed, saved to file, ready to email

## Project Structure

```
.
├── README.md                    # This file
├── BUILD_SUMMARY.md             # Implementation details
├── .env.example                 # Configuration template
├── .gitignore
│
├── mcp_servers/
│   └── notes_mcp/              # Custom MCP (Gmail & Calendar built-in)
│       ├── server.py           # AppleScript integration
│       ├── requirements.txt
│       └── README.md
│
├── digest_orchestrator/        # Main application
│   ├── main.py                 # Orchestrator (starts MCPs, calls Claude)
│   ├── config.py               # Configuration management
│   └── requirements.txt
│
├── docs/
│   ├── SETUP.md               # Detailed setup guide
│   └── ARCHITECTURE.md         # Design decisions
│
└── .claude/
    └── launch.json            # Claude Code scheduler config
```

## Key Design Decisions

### ✅ Uses Claude's Built-In MCPs
Rather than rebuilding Gmail and Calendar MCPs, we use Claude's official integrations. This is pragmatic and demonstrates good engineering judgment.

### ✅ Custom Notes MCP
Mac Notes lacks an official API, so we built our own using AppleScript—creative problem-solving that shows resourcefulness.

### ✅ Claude Autonomous Tool Use
Instead of orchestrating tools manually, Claude independently decides which tools to use, what parameters to pass, and how to synthesize results. This showcases AI integration patterns.

### ✅ Graceful Degradation
If any source fails, the digest continues with available data. Errors are logged but non-fatal.

## Real-World Use

This actually works as a daily assistant:
- Morning email with a prioritized action plan
- Aware of time constraints (calendar-aware)
- Connected to explicit priorities (notes)
- Intelligent filtering (Claude identifies urgent emails)

## Limitations & Future Work

**Current Limitations:**
- Saves to file instead of emailing (TODO: Gmail API integration)
- Notes must be formatted with `[ ]` checkboxes
- Requires Notes.app to be running

**Future Enhancements:**
- Email delivery via Gmail API
- Database storage for digest history
- Historical analysis dashboard
- Additional integrations (Slack, GitHub, Jira)

## Technology Stack

- **Language**: Python 3.9+
- **AI**: Claude API (Anthropic)
- **MCPs**: FastMCP (Notes), Claude built-ins (Gmail, Calendar)
- **APIs**: Google OAuth 2.0
- **System**: AppleScript for Mac Notes integration
- **Config**: python-dotenv

## License

MIT

## Questions?

Check [BUILD_SUMMARY.md](BUILD_SUMMARY.md) for implementation details, or [SETUP.md](docs/SETUP.md) for troubleshooting.
