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

1. **Fetch Unread Emails**
   - Use Gmail MCP to list unread emails from last 24 hours
   - For each email, note: sender, subject, snippet, timestamp

2. **Score Each Email for Priority**
   Assign a priority score (0-10) based on:
   - Contains questions or requests? (+3)
   - Sender is known important (CEO, manager, key client)? (+2)
   - Urgent language (ASAP, deadline, urgent)? (+2)
   - Waiting on their reply from others? (+1)
   - Has attachments? (+1)
   - Requires specific action/decision? (+2)

3. **Fetch Today's Calendar Events**
   - Use Calendar MCP to get all events for today
   - Note: time, title, duration, description
   - Identify back-to-back meetings or time blocks

4. **Identify Calendar Constraints**
   - Time blocks that limit deep work
   - Upcoming deadlines mentioned in calendar
   - Travel time requirements

5. **Return Structured Data**

   Format as JSON:
   ```json
   {
     "timestamp": "ISO 8601",
     "emails": [
       {
         "priority_score": 9,
         "sender": "alice@company.com",
         "subject": "Q2 Planning - Need Your Input",
         "key_signals": ["question", "urgent", "decision_needed"],
         "action_required": "Reply with timeline",
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
       "key_observations": "Multiple emails awaiting response, tight calendar"
     }
   }
   ```

6. **Be Thorough**
   - Check all unread emails (don't limit to first 5)
   - Accurately score based on content signals
   - Note any time-sensitive items
   - Identify dependencies (emails waiting on other emails)

Return the complete JSON structure with all emails analyzed and calendar mapped."""

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
