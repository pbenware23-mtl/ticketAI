"""
Slack / Microsoft Teams entry point: parse messages from Slack events (e.g. support
channel, DM) or Teams incoming webhooks / bot messages.

Supports event payloads and simplified message payloads.
"""

from typing import Any

from ingestion.schema import TicketSource
from ingestion.sources.base import BaseSourceAdapter


class SlackTeamsAdapter(BaseSourceAdapter):
    """
    Normalize Slack or Teams payloads into ingestion kwargs.

    Detects Slack vs Teams from payload shape and sets TicketSource.SLACK or TEAMS.
    """

    def parse(self, payload: Any) -> dict[str, Any]:
        """
        Slack: event with text, user, channel_id, ts (source_id), thread_ts.
        Teams: activity with text, from/user, channelId, id.
        Or simplified: { "text", "user_id", "channel_id", "platform": "slack"|"teams" }
        """
        if isinstance(payload, dict):
            return self._parse_dict(payload)
        raise ValueError("Slack/Teams payload must be a dict")

    def _parse_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        platform = (d.get("platform") or "").lower()
        is_slack = "slack" in platform or "event" in d or "event_id" in d

        if is_slack:
            return self._parse_slack(d)
        return self._parse_teams(d)

    def _parse_slack(self, d: dict[str, Any]) -> dict[str, Any]:
        event = d.get("event") or d
        text = event.get("text") or d.get("text") or ""
        source_id = event.get("ts") or d.get("ts") or d.get("event_ts") or d.get("message_id")
        user_id = event.get("user") or d.get("user_id")
        channel_id = event.get("channel") or event.get("channel_id") or d.get("channel_id")

        return {
            "source": TicketSource.SLACK,
            "raw_text": text,
            "subject": "",  # Or use channel name as context
            "source_id": str(source_id) if source_id else None,
            "customer_id": str(user_id) if user_id else None,
            "channel_metadata": {
                "channel_id": channel_id,
                "thread_ts": event.get("thread_ts") or d.get("thread_ts"),
                "team_id": event.get("team") or d.get("team_id"),
            },
        }

    def _parse_teams(self, d: dict[str, Any]) -> dict[str, Any]:
        # Teams activity or simplified webhook payload
        msg = d.get("message")
        text = d.get("text") or ""
        if isinstance(msg, dict):
            text = text or msg.get("text") or ""
        elif isinstance(msg, str):
            text = text or msg

        source_id = d.get("id") or d.get("message_id")
        user = d.get("from") or d.get("user") or {}
        if isinstance(user, dict):
            user_id = user.get("id") or user.get("userId")
            name = user.get("name")
        else:
            user_id = d.get("user_id")
            name = d.get("user_name")

        return {
            "source": TicketSource.TEAMS,
            "raw_text": text,
            "subject": "",
            "source_id": str(source_id) if source_id else None,
            "customer_id": str(user_id) if user_id else None,
            "name": name,
            "channel_metadata": {
                "channel_id": d.get("channelId") or d.get("channel_id"),
                "conversation_id": d.get("conversation", {}).get("id") if isinstance(d.get("conversation"), dict) else d.get("conversation_id"),
            },
        }
