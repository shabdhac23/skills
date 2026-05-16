"""
Email & Calendar Prioritizer Skill

Analyzes unread emails and calendar events, returns prioritized list.
Designed to be called by the Daily Digest routine.
"""

from anthropic import Anthropic


def prioritize_emails_and_calendar():
    """
    Analyze unread emails and calendar events, return prioritized list.

    This skill:
    1. Fetches unread emails from Gmail
    2. Fetches today's calendar events
    3. Analyzes both for priority signals
    4. Returns structured, prioritized data

    Returns:
        dict: Prioritized emails and calendar items with analysis
    """

    client = Anthropic()

    prompt = """Analyze the user's emails and calendar to create a prioritized action list.

You have access to Gmail and Calendar MCPs. Follow these steps:

1. **Fetch Unread Emails (Last 24 Hours)**
   - Use Gmail MCP to list unread emails
   - For each email, note: sender, subject, snippet, timestamp

2. **Fetch Important Inbox Emails (No Recent Response)**
   - Use Gmail MCP to list all emails with the IMPORTANT label
   - For each email in IMPORTANT inbox:
     * Get the full thread/conversation
     * Check if the last message in the thread is from the sender (not you)
     * If last message is from them (no response from you), include in "needs_action"
     * Note: sender, subject, date received, last message date

3. **Score Each Email for Priority**
   Assign a priority score (0-10) based on:
   - Contains questions or requests? (+3)
   - Sender is known important (CEO, manager, key client)? (+2)
   - Urgent language (ASAP, deadline, urgent)? (+2)
   - Waiting on their reply from others? (+1)
   - Has attachments? (+1)
   - Requires specific action/decision? (+2)

4. **Fetch Today's Calendar Events**
   - Use Calendar MCP to get all events for today
   - Note: time, title, duration, description
   - Identify back-to-back meetings or time blocks

5. **Identify Calendar Constraints**
   - Time blocks that limit deep work
   - Upcoming deadlines mentioned in calendar
   - Travel time requirements

6. **Return Structured Data**

   Format as JSON:
   ```json
   {
     "timestamp": "ISO 8601",
     "needs_action": [
       {
         "sender": "alice@company.com",
         "subject": "Q2 Planning - Need Your Input",
         "last_message_date": "2026-05-16T14:30:00Z",
         "days_waiting": 2,
         "snippet": "..."
       }
     ],
     "unread_emails": [
       {
         "priority_score": 9,
         "sender": "bob@company.com",
         "subject": "Meeting Tomorrow",
         "key_signals": ["question", "urgent"],
         "action_required": "Confirm attendance",
         "snippet": "..."
       }
     ],
     "calendar": [
       {
         "time": "10:00-11:00 AM",
         "title": "Team Standup",
         "duration_minutes": 60,
         "notes": "Weekly sync"
       }
     ],
     "analysis": {
       "most_urgent_email": "alice@company.com - Q2 Planning",
       "time_constraints": "Back-to-back meetings 10am-12pm, 2pm-4pm",
       "deep_work_windows": "Before 10am, 12pm-2pm (lunch), after 4pm",
       "key_observations": "2 important emails awaiting your response, tight morning schedule"
     }
   }
   ```

7. **Be Thorough**
   - Check ALL unread emails and IMPORTANT inbox emails
   - Accurately score based on content signals
   - For needs_action: note how long each has been waiting for response
   - Identify dependencies and time-sensitive items

Return the complete JSON structure with needs_action section populated with important emails awaiting your response."""

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Parse the response
    response_text = message.content[0].text

    # Extract JSON from response
    import json
    import re

    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return data
        except json.JSONDecodeError:
            pass

    # If no JSON found, return the raw response wrapped
    return {
        "raw_analysis": response_text,
        "error": "Could not parse structured JSON"
    }


if __name__ == "__main__":
    import json
    result = prioritize_emails_and_calendar()
    print(json.dumps(result, indent=2))
