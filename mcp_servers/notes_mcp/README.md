# Mac Notes MCP

Model Context Protocol server for reading Mac Notes.

## Features

- Read specific notes by name
- Extract TODO items with completion status
- Parse notes by section headers
- List available notes in the Notes app
- Read-only (no modifications)

## Tools

### `read_note`

Read the full contents of a specific note.

**Parameters:**
- `note_name` (str): Name of the note to read

**Returns:** `Note` object with content and metadata

### `read_todos`

Parse and extract TODO items from a note.

**Parameters:**
- `note_name` (str): Name of the note containing TODOs

**Returns:** List of `TodoItem` objects with text and completion status

Looks for:
- `[ ] text` - unchecked TODO
- `[x] text` or `[X] text` - checked TODO
- `- [ ] text` - unchecked TODO (markdown format)
- `- [x] text` - checked TODO (markdown format)

### `get_available_notes`

List all notes in the Mac Notes app.

**Returns:** List of note names

### `parse_structured_note`

Parse a note into sections based on headers.

**Parameters:**
- `note_name` (str): Name of the note
- `section_marker` (str, default="##"): Marker for section headers

**Returns:** Dictionary of {section_name: [items]}

Example note:
```
## TODOs
[ ] Task 1
[ ] Task 2

## Priorities
- Important item
- Another item
```

## Setup

1. Create notes in Mac Notes app
2. Name them exactly as you'll reference them ("TODOs", "Priorities", etc.)
3. Use the TODO format: `[ ] item text` or `[x] item text`
4. Make sure Notes.app is running (or recently closed)
5. Grant Terminal permission to control Notes (System Preferences → Security & Privacy → Automation)

## Testing

```bash
# Test with MCP Inspector
npx @modelcontextprotocol/inspector python server.py

# Try reading your TODOs
# Use read_todos tool with note name "TODOs"
```

## Implementation Notes

- Uses AppleScript via subprocess (creative solution without official API)
- Read-only by design (no modifications to notes)
- Handles both checkbox and dash-bullet formats
- Graceful error handling for missing notes
- Fast execution (AppleScript is cached by macOS)

## Known Limitations

- Requires Notes.app to be running or recently closed
- AppleScript is slower than direct API access
- Very large notes (10000+ lines) may timeout
- Formatting in notes is stripped (returns plain text)
- Cannot access notes from shared iCloud folders (limitation of AppleScript)
- Requires Terminal permissions to control Notes

## Future Improvements

- Direct SQLite access to Notes database (faster)
- Support for nested sections
- Link resolution (if notes contain cross-references)
- Attachment detection
- Export notes to other formats
