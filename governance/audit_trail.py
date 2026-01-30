"""
Audit Trail - Response Logging and Traceability
================================================

Logs every AI decision with:
- Input/output
- Model and prompt version
- Risk tier
- Monitoring results
- Timestamp and session info

Storage: Supabase (audit/{date}/{id}.json)
Retention: Configurable per risk tier
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "mindrian-files")


@dataclass
class AuditEntry:
    """A single audit log entry."""
    id: str
    timestamp: str

    # Session context
    session_id: str
    user_id: str
    bot_id: str

    # Request/Response
    user_message: str
    bot_response: str
    response_length: int

    # Model info (from prompt cards)
    model_name: str
    model_version: str
    prompt_version: str

    # Risk classification
    risk_tier: int
    human_oversight_required: bool

    # Monitoring results
    monitoring_passed: bool
    monitoring_alerts: List[str]

    # Additional context
    phase: str = ""
    tools_used: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tools_used is None:
            self.tools_used = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_redacted(self) -> Dict:
        """Return redacted version for logging (hide PII)."""
        data = self.to_dict()
        # Redact user_id
        if self.user_id and "@" in self.user_id:
            parts = self.user_id.split("@")
            data["user_id"] = f"{parts[0][:2]}***@{parts[1]}"
        # Truncate messages for log display
        data["user_message"] = self.user_message[:200] + "..." if len(self.user_message) > 200 else self.user_message
        data["bot_response"] = self.bot_response[:200] + "..." if len(self.bot_response) > 200 else self.bot_response
        return data


class AuditTrail:
    """
    Manages audit logging for AI responses.
    """

    def __init__(self):
        self.entries: List[AuditEntry] = []
        self._supabase_client = None

        # Retention policies by risk tier (days)
        self.retention = {
            0: 7,    # Internal - 1 week
            1: 30,   # Low impact - 1 month
            2: 90,   # Business - 3 months
            3: 365,  # High stakes - 1 year
        }

    def _get_supabase_client(self):
        """Get Supabase client."""
        if self._supabase_client is None and SUPABASE_URL and SUPABASE_SERVICE_KEY:
            try:
                from supabase import create_client
                self._supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            except Exception as e:
                print(f"Supabase client error: {e}")
        return self._supabase_client

    def _generate_audit_id(self, session_id: str) -> str:
        """Generate unique audit entry ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        hash_input = f"{session_id}:{timestamp}"
        short_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        return f"audit_{short_hash}"

    def log(
        self,
        session_id: str,
        user_id: str,
        bot_id: str,
        user_message: str,
        bot_response: str,
        model_name: str = "gemini-2.0-flash",
        model_version: str = "2.0",
        prompt_version: str = "1.0.0",
        risk_tier: int = 1,
        human_oversight_required: bool = False,
        monitoring_passed: bool = True,
        monitoring_alerts: List[str] = None,
        phase: str = "",
        tools_used: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> AuditEntry:
        """
        Log an AI response to the audit trail.

        This is the main entry point for audit logging.
        Call after every AI response.
        """
        entry = AuditEntry(
            id=self._generate_audit_id(session_id),
            timestamp=datetime.utcnow().isoformat(),
            session_id=session_id,
            user_id=user_id,
            bot_id=bot_id,
            user_message=user_message,
            bot_response=bot_response,
            response_length=len(bot_response),
            model_name=model_name,
            model_version=model_version,
            prompt_version=prompt_version,
            risk_tier=risk_tier,
            human_oversight_required=human_oversight_required,
            monitoring_passed=monitoring_passed,
            monitoring_alerts=monitoring_alerts or [],
            phase=phase,
            tools_used=tools_used or [],
            metadata=metadata or {}
        )

        self.entries.append(entry)
        self._store_entry(entry)

        # Log summary
        status = "✅" if monitoring_passed else "⚠️"
        print(f"📋 Audit: {entry.id} | {bot_id} | T{risk_tier} | {status}")

        return entry

    def _store_entry(self, entry: AuditEntry):
        """Store audit entry to Supabase."""
        client = self._get_supabase_client()
        if not client:
            return

        try:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            filename = f"audit/{date_str}/{entry.id}.json"

            json_content = json.dumps(entry.to_dict(), indent=2).encode('utf-8')

            try:
                client.storage.from_(SUPABASE_BUCKET).upload(
                    path=filename,
                    file=json_content,
                    file_options={"content-type": "application/json"}
                )
            except Exception as upload_error:
                if "Duplicate" in str(upload_error) or "already exists" in str(upload_error).lower():
                    client.storage.from_(SUPABASE_BUCKET).update(
                        path=filename,
                        file=json_content,
                        file_options={"content-type": "application/json"}
                    )

        except Exception as e:
            print(f"Audit storage error: {e}")

    def get_entries_by_session(self, session_id: str) -> List[AuditEntry]:
        """Get all audit entries for a session."""
        return [e for e in self.entries if e.session_id == session_id]

    def get_entries_by_user(self, user_id: str) -> List[AuditEntry]:
        """Get all audit entries for a user."""
        return [e for e in self.entries if e.user_id == user_id]

    def get_entries_by_bot(self, bot_id: str) -> List[AuditEntry]:
        """Get all audit entries for a bot."""
        return [e for e in self.entries if e.bot_id == bot_id]

    def get_alerts(self) -> List[AuditEntry]:
        """Get entries that raised monitoring alerts."""
        return [e for e in self.entries if not e.monitoring_passed]

    def get_high_risk_entries(self) -> List[AuditEntry]:
        """Get entries from high-stakes bots (Tier 3)."""
        return [e for e in self.entries if e.risk_tier >= 3]

    def get_stats(self) -> Dict[str, Any]:
        """Get audit statistics."""
        total = len(self.entries)
        if total == 0:
            return {"total": 0, "message": "No audit entries"}

        alerts = sum(1 for e in self.entries if not e.monitoring_passed)
        high_risk = sum(1 for e in self.entries if e.risk_tier >= 3)

        # By bot
        by_bot = {}
        for e in self.entries:
            by_bot[e.bot_id] = by_bot.get(e.bot_id, 0) + 1

        # By tier
        by_tier = {}
        for e in self.entries:
            tier_key = f"tier_{e.risk_tier}"
            by_tier[tier_key] = by_tier.get(tier_key, 0) + 1

        return {
            "total": total,
            "with_alerts": alerts,
            "high_risk": high_risk,
            "alert_rate": alerts / total * 100,
            "by_bot": by_bot,
            "by_tier": by_tier,
        }

    def export_report(self, date_str: str = None) -> str:
        """Generate markdown audit report."""
        if not date_str:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")

        stats = self.get_stats()

        report = f"""# Audit Trail Report
**Date:** {date_str}
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

---

## Summary

| Metric | Value |
|--------|-------|
| Total Entries | {stats.get('total', 0)} |
| With Alerts | {stats.get('with_alerts', 0)} |
| High Risk (Tier 3) | {stats.get('high_risk', 0)} |
| Alert Rate | {stats.get('alert_rate', 0):.2f}% |

---

## By Risk Tier

| Tier | Count |
|------|-------|
"""
        for tier, count in stats.get('by_tier', {}).items():
            report += f"| {tier} | {count} |\n"

        report += """
---

## By Bot

| Bot | Count |
|-----|-------|
"""
        for bot, count in stats.get('by_bot', {}).items():
            report += f"| {bot} | {count} |\n"

        # Entries with alerts
        alert_entries = self.get_alerts()
        if alert_entries:
            report += """
---

## Entries With Alerts

"""
            for entry in alert_entries[-10:]:
                report += f"""
### {entry.id}
- **Bot:** {entry.bot_id}
- **Tier:** {entry.risk_tier}
- **Alerts:** {', '.join(entry.monitoring_alerts)}
- **Time:** {entry.timestamp}

"""

        return report


# ==============================================================================
# GLOBAL INSTANCE AND INTEGRATION
# ==============================================================================

# Global audit trail instance
_audit_trail: Optional[AuditTrail] = None


def get_audit_trail() -> AuditTrail:
    """Get or create the global audit trail instance."""
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = AuditTrail()
    return _audit_trail


def log_response(
    session_id: str,
    user_id: str,
    bot_id: str,
    user_message: str,
    bot_response: str,
    **kwargs
) -> AuditEntry:
    """
    Convenience function to log a response.

    This is the main integration point for mindrian_chat.py
    """
    audit = get_audit_trail()
    return audit.log(
        session_id=session_id,
        user_id=user_id,
        bot_id=bot_id,
        user_message=user_message,
        bot_response=bot_response,
        **kwargs
    )


# ==============================================================================
# INTEGRATION WITH PROMPT CARDS
# ==============================================================================

def get_prompt_card_info(bot_id: str) -> Dict[str, Any]:
    """
    Load prompt card info for audit logging.

    Returns model name, version, and prompt version.
    """
    import yaml
    from pathlib import Path

    card_path = Path(__file__).parent / "prompt_cards" / f"{bot_id}.yaml"

    defaults = {
        "model_name": "gemini-2.0-flash",
        "model_version": "2.0",
        "prompt_version": "1.0.0",
        "risk_tier": 1,
    }

    if not card_path.exists():
        return defaults

    try:
        with open(card_path, 'r') as f:
            card = yaml.safe_load(f)

        return {
            "model_name": card.get("model", defaults["model_name"]),
            "model_version": card.get("model_version", defaults["model_version"]),
            "prompt_version": card.get("prompt_version", defaults["prompt_version"]),
            "risk_tier": card.get("risk_tier", defaults["risk_tier"]),
        }
    except Exception as e:
        print(f"Error loading prompt card: {e}")
        return defaults


def create_audit_entry_from_response(
    session_id: str,
    user_id: str,
    bot_id: str,
    user_message: str,
    bot_response: str,
    monitoring_result: Dict[str, Any] = None,
    phase: str = "",
    tools_used: List[str] = None
) -> AuditEntry:
    """
    Create a complete audit entry with prompt card info and monitoring results.

    This is the full integration function that:
    1. Loads prompt card info (model, version, risk tier)
    2. Incorporates monitoring results
    3. Creates and stores the audit entry
    """
    # Get prompt card info
    card_info = get_prompt_card_info(bot_id)

    # Process monitoring results
    monitoring_passed = True
    monitoring_alerts = []

    if monitoring_result:
        monitoring_passed = monitoring_result.get("passed", True)
        alerts = monitoring_result.get("alerts", [])
        monitoring_alerts = [a.get("message", str(a)) for a in alerts]

    # Check if human oversight required
    from governance.risk_tiers import requires_human_oversight
    try:
        human_oversight = requires_human_oversight(bot_id)
    except Exception:
        human_oversight = card_info.get("risk_tier", 1) >= 3

    return log_response(
        session_id=session_id,
        user_id=user_id,
        bot_id=bot_id,
        user_message=user_message,
        bot_response=bot_response,
        model_name=card_info["model_name"],
        model_version=card_info["model_version"],
        prompt_version=card_info["prompt_version"],
        risk_tier=card_info["risk_tier"],
        human_oversight_required=human_oversight,
        monitoring_passed=monitoring_passed,
        monitoring_alerts=monitoring_alerts,
        phase=phase,
        tools_used=tools_used
    )
