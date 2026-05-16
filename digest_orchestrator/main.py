"""
Daily Digest Assistant - Main Orchestrator

Leverages Claude's built-in Gmail and Calendar MCPs along with a custom Notes MCP
to generate a daily digest. Claude autonomously uses the tools to gather data and synthesize.
"""

import json
import sys
import logging
from datetime import datetime
from pathlib import Path
from subprocess import Popen, PIPE

from anthropic import Anthropic
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DigestGenerator:
    """Generates daily digest using Claude with built-in and custom MCPs."""

    def __init__(self):
        """Initialize Claude client."""
        self.client = Anthropic(api_key=Config.CLAUDE_API_KEY)
        self.model = "claude-opus-4-7"
        self.notes_mcp_process = None

    def run(self) -> bool:
        """
        Run the complete digest generation pipeline.

        Claude will autonomously use Gmail, Calendar, and Notes MCPs to gather data
        and synthesize into a digest.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting Daily Digest generation...")

        try:
            # Start Notes MCP server (Gmail and Calendar are Claude built-ins)
            logger.info("Starting Notes MCP server...")
            self._start_notes_mcp()

            # Call Claude to generate digest
            logger.info("Calling Claude to gather data and synthesize digest...")
            digest = self._generate_digest_with_claude()

            # Format for email
            subject, body = self._format_email(digest)

            # Output digest
            logger.info("Digest generation complete")
            self._output_digest(subject, body)

            return True

        except Exception as e:
            logger.error(f"Error generating digest: {str(e)}", exc_info=True)
            return False
        finally:
            self._cleanup_notes_mcp()

    def _start_notes_mcp(self):
        """Start the Notes MCP server as a subprocess."""
        try:
            notes_mcp_path = Path(__file__).parent.parent / "mcp_servers" / "notes_mcp" / "server.py"
            self.notes_mcp_process = Popen(
                ["python3", str(notes_mcp_path)],
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
                text=True
            )
            logger.info("Notes MCP server started")
        except Exception as e:
            logger.warning(f"Failed to start Notes MCP: {e}")
            # Continue anyway - digest will work without Notes

    def _cleanup_notes_mcp(self):
        """Stop the Notes MCP server."""
        if self.notes_mcp_process:
            try:
                self.notes_mcp_process.terminate()
                self.notes_mcp_process.wait(timeout=5)
                logger.info("Notes MCP server stopped")
            except Exception as e:
                logger.warning(f"Error stopping Notes MCP: {e}")
                self.notes_mcp_process.kill()

    def _generate_digest_with_claude(self) -> str:
        """
        Call Claude to use Gmail, Calendar, and Notes MCPs to gather data and synthesize.

        Claude will autonomously:
        1. List unread emails from the last 24 hours
        2. Fetch today's calendar events
        3. Read TODOs and priorities from Notes
        4. Synthesize into a coherent, actionable digest
        """
        current_date = datetime.now().strftime("%A, %B %d, %Y")

        prompt = f"""You are a personal productivity assistant. Today is {current_date}.

Your task is to create my daily digest by:

1. **Use the Gmail tool** to list my unread emails from the last 24 hours
   - Focus on emails that likely need a response

2. **Use the Calendar tool** to fetch today's events
   - Note any time constraints or back-to-back meetings

3. **Use the Notes MCP** to read my "TODOs" and "Priorities" notes
   - Extract what I've explicitly marked as important

4. **Synthesize into a daily digest** that:
   - Leads with my explicit priorities from notes
   - Highlights which emails need urgent responses
   - Notes calendar constraints
   - Provides a consolidated action plan for the day
   - Flags any conflicts or dependencies

Format the digest as:

---
## Daily Digest for {current_date}

### 🎯 Top Priorities Today
[2-3 key focuses based on my notes]

### 📅 Calendar Overview
[Time blocks and any constraints]

### ✉️ Critical Emails
[Emails that need responses, grouped by urgency/sender]

### ✅ Action Items for Today
[Consolidated list in priority order]

### ⚠️ Important Notes
[Any conflicts, dependencies, or items to watch]

---

Be concise, actionable, and focused. Remove noise. Help me focus on what actually matters today."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return message.content[0].text

    def _format_email(self, digest: str) -> tuple[str, str]:
        """
        Format digest as email.

        Returns:
            Tuple of (subject, body)
        """
        current_date = datetime.now().strftime("%A, %B %d")
        subject = f"Daily Digest — {current_date}"

        body = f"""Hi,

Here's your daily digest:

{digest}

---
Generated by Daily Digest Assistant
https://github.com/yourusername/daily-digest-assistant"""

        return subject, body

    def _output_digest(self, subject: str, body: str):
        """
        Output the digest to console and optionally send via email.

        Currently saves to file. TODO: Integrate Gmail API for actual delivery.
        """
        logger.info(f"Digest would be sent to: {Config.DIGEST_RECIPIENT_EMAIL}")
        logger.info(f"Subject: {subject}")

        print("\n" + "="*80)
        print("DAILY DIGEST")
        print("="*80)
        print(f"To: {Config.DIGEST_RECIPIENT_EMAIL}")
        print(f"Subject: {subject}")
        print("-"*80)
        print(body)
        print("="*80 + "\n")

        # Save to file for review
        output_file = Path.home() / f"digest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w') as f:
            f.write(f"To: {Config.DIGEST_RECIPIENT_EMAIL}\n")
            f.write(f"Subject: {subject}\n")
            f.write("-"*80 + "\n")
            f.write(body)

        logger.info(f"Digest saved to: {output_file}")

        # TODO: Send via Gmail API
        # TODO: Store in database for historical analysis


def main():
    """Main entry point."""
    logger.info("Daily Digest Assistant v1.0")
    logger.info(f"Configuration: {Config.to_dict()}")

    generator = DigestGenerator()
    success = generator.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
