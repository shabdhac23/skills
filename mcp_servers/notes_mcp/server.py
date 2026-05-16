"""
Mac Notes MCP Server

Provides tools for reading notes from the Mac Notes app.
Designed for the Daily Digest Assistant to extract TODOs and priorities.

Note: Uses AppleScript to access Mac Notes since the app lacks a public API.
This demonstrates creative integration with system applications.
"""

import subprocess
import json
from typing import Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Initialize MCP server
mcp = FastMCP("notes-mcp")


class Note(BaseModel):
    """Representation of a Mac Note."""
    name: str = Field(description="Note title")
    content: str = Field(description="Note body content")
    modified: str = Field(description="Last modified date")


class TodoItem(BaseModel):
    """Extracted TODO item from a note."""
    text: str = Field(description="The TODO item text")
    checked: bool = Field(description="Whether the TODO is marked as done")


def run_applescript(script: str) -> str:
    """Execute AppleScript and return output."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            raise RuntimeError(f"AppleScript error: {result.stderr}")
        return result.stdout.strip()
    except Exception as e:
        raise ValueError(f"Failed to execute AppleScript: {str(e)}")


def list_available_notes() -> list[str]:
    """Get list of all note names in the Notes app."""
    script = """
    tell application "Notes"
        set note_names to {}
        repeat with aFolder in folders
            repeat with aNote in notes of aFolder
                set end of note_names to name of aNote
            end repeat
        end repeat
        return note_names as text
    end tell
    """
    try:
        output = run_applescript(script)
        # Output is comma-separated
        if not output:
            return []
        return [name.strip() for name in output.split(",")]
    except:
        return []


@mcp.tool()
def read_note(
    note_name: str = Field(description="Name of the note to read")
) -> Note:
    """
    Read the contents of a specific note from Mac Notes.

    Returns the full note content, which can then be parsed for TODOs and priorities.
    """
    script = f"""
    tell application "Notes"
        set target_note to missing value
        repeat with aFolder in folders
            repeat with aNote in notes of aFolder
                if name of aNote is "{note_name}" then
                    set target_note to aNote
                    exit repeat
                end if
            end repeat
            if target_note is not missing value then
                exit repeat
            end if
        end repeat

        if target_note is missing value then
            error "Note '{note_name}' not found"
        end if

        set note_content to body of target_note
        set modified_date to modification date of target_note
        return {{name of target_note, note_content, modified_date}}
    end tell
    """
    try:
        output = run_applescript(script)
        # Parse the output (AppleScript returns a list representation)
        # This is a simplified version - in practice you might need more robust parsing
        lines = output.split("\n")

        if "not found" in output:
            raise ValueError(f"Note '{note_name}' not found in Mac Notes")

        return Note(
            name=note_name,
            content=output if output else "",
            modified=str(lines[-1]) if lines else ""
        )
    except Exception as e:
        raise ValueError(f"Error reading note: {str(e)}")


@mcp.tool()
def read_todos(
    note_name: str = Field(description="Name of the note containing TODOs")
) -> list[TodoItem]:
    """
    Read and parse TODO items from a note.

    Looks for lines starting with "[ ]" (unchecked) or "[x]" (checked).
    Returns a list of parsed TODO items with their completion status.
    """
    try:
        note = read_note(note_name)
        todos = []

        for line in note.content.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check for unchecked TODO: [ ] text
            if line.startswith("[ ]"):
                text = line[3:].strip()
                if text:
                    todos.append(TodoItem(text=text, checked=False))

            # Check for checked TODO: [x] text or [X] text
            elif line.startswith("[x]") or line.startswith("[X]"):
                text = line[3:].strip()
                if text:
                    todos.append(TodoItem(text=text, checked=True))

            # Alternative format: - [ ] or - [x]
            elif line.startswith("- [ ]"):
                text = line[5:].strip()
                if text:
                    todos.append(TodoItem(text=text, checked=False))

            elif line.startswith("- [x]") or line.startswith("- [X]"):
                text = line[5:].strip()
                if text:
                    todos.append(TodoItem(text=text, checked=True))

        return todos

    except Exception as e:
        raise ValueError(f"Error reading TODOs from note: {str(e)}")


@mcp.tool()
def get_available_notes() -> list[str]:
    """
    List all available notes in the Mac Notes app.

    Useful for discovering note names to pass to read_note() or read_todos().
    """
    try:
        notes = list_available_notes()
        if not notes:
            return ["(No notes found - make sure Notes app is running)"]
        return notes
    except Exception as e:
        raise ValueError(f"Error listing notes: {str(e)}")


@mcp.tool()
def parse_structured_note(
    note_name: str = Field(description="Name of the note to parse"),
    section_marker: str = Field(
        default="##",
        description="Marker for section headers (default: ##)"
    )
) -> dict[str, list[str]]:
    """
    Parse a note into sections based on markers.

    Useful for notes that organize information into sections.
    Sections are identified by lines starting with the section marker.

    Example note:
    ## TODOs
    [ ] Task 1
    [ ] Task 2

    ## Priorities
    - High priority item
    - Medium priority item
    """
    try:
        note = read_note(note_name)
        sections = {}
        current_section = "general"
        current_items = []

        for line in note.content.split("\n"):
            stripped = line.strip()

            # Check if this is a section header
            if stripped.startswith(section_marker):
                # Save previous section
                if current_items:
                    sections[current_section] = current_items
                # Start new section
                current_section = stripped[len(section_marker):].strip().lower()
                current_items = []
            elif stripped and not stripped.startswith("#"):
                current_items.append(stripped)

        # Save final section
        if current_items:
            sections[current_section] = current_items

        return sections

    except Exception as e:
        raise ValueError(f"Error parsing note structure: {str(e)}")


if __name__ == "__main__":
    # Run MCP server
    mcp.run(transport="stdio")
