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
   - EXCLUDE (filter out from display):
     * Marketing/newsletter senders
     * Google Flights alerts and similar travel automation
     * Shipping notifications ("out for delivery", "package arrived", "tracking", etc.)
     * Automated alerts (except payment/billing)

2. **Fetch Important Emails (Gmail's Automatic Detection + Exclusions)**
   - Use Gmail MCP to list emails Gmail has marked as important: is:important
   - EXCLUDE:
     * Marketing/newsletter emails (keywords: "unsubscribe", "marketing", "promotional")
     * Google Flights alerts (from: google-flights, noreply@flights.google.com)
     * Automated alerts EXCEPT billing/payments (exclude: alerts, notifications from non-billing sources)
   - For each remaining important email:
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

4. **Fetch Today's and Tomorrow's Calendar Events**
   - Use Calendar MCP to get all events for today
   - Use Calendar MCP to get all events for tomorrow
   - For each event note: time, title, duration, description
   - For tomorrow's events, identify any prep needed (from description or title)

5. **Identify Prep Requirements**
   - Look at tomorrow's events for anything requiring preparation
   - Check descriptions for notes about prep, materials, or pre-work
   - Highlight any events that might need advance action

6. **Return Structured Data**

   Format as JSON with today's and tomorrow's calendar:
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
     "today_calendar": [
       {
         "time": "10:00-11:00 AM",
         "title": "Team Standup",
         "duration_minutes": 60
       }
     ],
     "tomorrow_calendar": [
       {
         "time": "2:00-3:00 PM",
         "title": "Client Presentation",
         "duration_minutes": 60,
         "prep_needed": "Prepare slides on Q2 metrics"
       }
     ],
     "analysis": {
       "most_urgent_email": "alice@company.com - Q2 Planning",
       "tomorrow_prep": "Client presentation - slides needed",
       "key_observations": "2 important emails awaiting response, 1 prep item for tomorrow"
     }
   }
   ```

7. **Gmail Query Tips**
   - Use `is:important` to get emails Gmail has flagged as important
   - Use `-from:google-flights-noreply@google.com` to exclude Google Flights
   - Exclude shipping: `-(out for delivery OR package arrived OR tracking number OR shipment)`
   - Use query: `is:important -from:google-flights -from:noreply@flights.google.com -(unsubscribe OR marketing OR newsletter OR promotional OR "out for delivery" OR "package arrived" OR tracking)`
   - For unread: `is:unread -(unsubscribe OR marketing OR newsletter OR promotional OR google-flights OR "out for delivery")`
   - INCLUDE billing/payment emails even if automated

8. **Be Thorough**
   - Check ALL unread emails (with filters applied)
   - Check ALL emails Gmail marks as important (with filters applied)
   - Accurately score based on content signals
   - For needs_action: note how long each has been waiting for response
   - Identify dependencies and time-sensitive items
   - Apply exclusion filters consistently

Return the complete JSON structure with needs_action section populated with important emails awaiting your response (after applying filters)."""

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
