# Setup Guide

Complete setup instructions for the Daily Digest Assistant.

## Prerequisites

- Python 3.9+
- macOS (for Notes.app integration)
- Claude Code with Gmail and Calendar MCPs enabled
- Claude API key (from Anthropic)

## Step 1: Clone and Install

```bash
git clone <your-repo>
cd daily-digest-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r digest_orchestrator/requirements.txt
pip install -r mcp_servers/notes_mcp/requirements.txt
```

## Step 2: Enable Gmail & Calendar MCPs

The Gmail and Calendar MCPs are built into Claude Code. You need to authenticate with Google:

### Option A: Via Claude Code (Recommended)

In Claude Code, use the MCP registry to connect Gmail and Calendar:

1. Open Claude Code settings
2. Find "MCP Integrations" or "Connected Services"
3. Search for "Gmail" and "Google Calendar"
4. Click "Connect" and follow the OAuth flow
5. Grant permissions for read-only email and calendar access

### Option B: Manual OAuth

If not using Claude Code, create OAuth credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API and Google Calendar API
4. Create OAuth 2.0 Desktop credentials
5. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env` (if needed)

For most users, Claude Code handles this automatically—proceed to Step 3.

## Step 3: Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit with your settings
nano .env
```

Required variables:
- `CLAUDE_API_KEY` - Get from [Anthropic API keys](https://console.anthropic.com/)
- `DIGEST_RECIPIENT_EMAIL` - Your email address (for digest delivery reference)

Optional customizations:
- `NOTES_TODO_NAME` - Name of your TODOs note (default: "TODOs")
- `NOTES_PRIORITIES_NAME` - Name of your priorities note (default: "Priorities")
- `DIGEST_TIMEZONE` - Your timezone (default: "America/Los_Angeles")

## Step 4: Prepare Your Notes

Create two notes in Mac Notes.app with specific formatting:

### Note 1: "TODOs"

Format tasks with checkboxes:

```
[ ] Complete project proposal
[ ] Review pull request
[x] Respond to email from Alice
[ ] Update documentation
[x] Call Mom
```

Supported formats:
- `[ ] unchecked task`
- `[x] completed task`
- `- [ ] markdown unchecked`
- `- [x] markdown completed`

### Note 2: "Priorities"

List your key priorities (any format works):

```
## This Week
- Finish Q2 planning
- Stakeholder communication
- Team reviews

## Today's Focus
- Deep work on architecture
- Customer feedback synthesis
```

**Important**: Note names must match exactly (case-sensitive in some systems). Default names are "TODOs" and "Priorities". If you use different names, update `.env`:

```bash
NOTES_TODO_NAME=My Tasks
NOTES_PRIORITIES_NAME=My Goals
```

## Step 5: Grant Notes Permissions

Mac requires you to grant Terminal (or your Python environment) permission to control Notes.app:

1. Open System Settings → Security & Privacy → Automation
2. Find "Terminal" (or your IDE) in the list
3. Enable "Notes" if it's not checked

Without this, the Notes MCP will fail.

## Step 6: Test Notes MCP

Test the custom Notes MCP in isolation:

```bash
cd mcp_servers/notes_mcp

# Install dependencies (if not done globally)
pip install -r requirements.txt

# Test with MCP Inspector
npx @modelcontextprotocol/inspector python server.py
```

In the Inspector:
1. Try the `get_available_notes` tool → should list your notes
2. Try `read_note` with name "TODOs" → should return your tasks
3. Try `read_todos` → should parse and return TODO items

If you see errors:
- **"Note not found"** → check note names match exactly
- **"Permission denied"** → grant Terminal access to Notes (Step 5)
- **"AppleScript error"** → make sure Notes.app is running

## Step 7: Test Full Pipeline

Run the digest orchestrator:

```bash
python3 digest_orchestrator/main.py
```

Expected flow:
```
2024-05-16 08:00:00 - INFO - Daily Digest Assistant v1.0
2024-05-16 08:00:01 - INFO - Starting Daily Digest generation...
2024-05-16 08:00:02 - INFO - Starting Notes MCP server...
2024-05-16 08:00:03 - INFO - Calling Claude to gather data and synthesize digest...
2024-05-16 08:00:05 - INFO - Digest generation complete
```

You should see:
1. A digest printed to console
2. A file saved to `~/digest_YYYYMMDD_HHMMSS.txt`
3. No errors in the log output

If you see Claude errors:
- **"API error"** → verify `CLAUDE_API_KEY` is valid
- **"Tool not found"** → ensure Gmail/Calendar MCPs are connected in Claude Code
- **"Rate limited"** → wait a minute and try again

## Step 8: Schedule Daily Runs

### Option A: Claude Code Scheduling (Recommended)

In Claude Code, use the schedule command:

```
/schedule daily-digest "Generate and send daily digest every weekday at 8am"
```

This will:
- Run `digest_orchestrator/main.py` at 8am weekdays
- Log output automatically
- Handle errors gracefully

### Option B: macOS Launchd

Create `~/Library/LaunchAgents/com.dailydigest.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dailydigest.assistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/shabdha/daily-digest-assistant/venv/bin/python3</string>
        <string>/Users/shabdha/daily-digest-assistant/digest_orchestrator/main.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
        <key>Weekday</key>
        <integer>1</integer>
    </dict>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
    <key>StandardOutPath</key>
    <string>/var/log/dailydigest.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/dailydigest-error.log</string>
</dict>
</plist>
```

Then load it:
```bash
launchctl load ~/Library/LaunchAgents/com.dailydigest.plist
```

Check status:
```bash
launchctl list | grep dailydigest
launchctl stop com.dailydigest.assistant
launchctl start com.dailydigest.assistant
```

### Option C: Cron

Add to your crontab (`crontab -e`):

```bash
# Run at 8am weekdays
0 8 * * 1-5 cd /Users/shabdha/daily-digest-assistant && /usr/bin/python3 -m digest_orchestrator.main >> /var/log/dailydigest.log 2>&1
```

## Step 9: Optional - Email Delivery

Currently the digest is saved to a file. To send via email:

### TODO: Gmail API Integration

Edit `digest_orchestrator/main.py` and implement:

```python
def _send_email_digest(self, subject: str, body: str):
    # Use Gmail API to send the digest
    service = build("gmail", "v1", credentials=creds)
    message = create_message(
        sender=self.config.DIGEST_SENDER_NAME,
        to=self.config.DIGEST_RECIPIENT_EMAIL,
        subject=subject,
        message_text=body
    )
    service.users().messages().send(userId="me", body=message).execute()
```

For now, you can:
- Manually copy digest text to email
- Set up a mail rule to forward daily digest emails
- Use IFTTT or Zapier to email the file

## Troubleshooting

### Notes MCP Issues

**"Permission denied" or "AppleScript error"**
- Go to System Settings → Security & Privacy → Automation
- Make sure Terminal (or your IDE) has permission to control Notes
- Restart Terminal

**"Note not found"**
- Check note names match exactly (case-sensitive)
- Verify notes are in Notes.app (not archived)
- Try `get_available_notes` to see what notes exist

**"AppleScript timed out"**
- Make sure Notes.app is running
- Try quitting and reopening Notes
- Check for very large notes (10000+ lines)

### Gmail/Calendar Issues

**"Tool not found" errors**
- Verify Gmail and Calendar MCPs are connected in Claude Code
- Try re-connecting the MCPs in Claude Code settings
- Restart Claude Code if needed

**"Not authenticated"**
- Re-authenticate with Google in Claude Code
- Make sure you granted the necessary permissions
- Try disconnecting and reconnecting the MCP

### Claude API Issues

**"Invalid API key"**
- Verify `CLAUDE_API_KEY` in `.env`
- Check key is valid in Anthropic console
- Try regenerating the API key

**"Rate limited"**
- Too many API calls too quickly
- Wait a few minutes and try again
- Consider adding a queue for scheduled runs

**"Timeout"**
- Claude inference took too long
- Try again later
- Check available API capacity

## Next Steps

1. Review the generated digests
2. Adjust `.env` settings as needed
3. Modify Claude's prompt in `main.py` to match your style
4. Schedule to run daily
5. Push to GitHub for your portfolio!

## Uninstalling

To remove scheduled tasks:

```bash
# If using Launchd
launchctl unload ~/Library/LaunchAgents/com.dailydigest.plist
rm ~/Library/LaunchAgents/com.dailydigest.plist

# If using cron
crontab -e  # and remove the line

# Clean up the project
rm -rf /Users/shabdha/daily-digest-assistant
```

## Support

- Check [ARCHITECTURE.md](ARCHITECTURE.md) for design explanations
- Check [BUILD_SUMMARY.md](../BUILD_SUMMARY.md) for implementation details
- Review logs in `/var/log/dailydigest.log` (if using Launchd)
- Run tests manually: `python3 digest_orchestrator/main.py`
