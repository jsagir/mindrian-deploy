"""
AI Monitoring Module - Production Oversight
============================================

Monitors AI behavior in production for:
- Silent failures (answers that sound right but aren't)
- Safety boundary violations
- Quality degradation
- Drift detection
- Performance metrics

Integrates with:
- Supabase for log storage
- Daily summary emails
- Alert system for P0/P1 issues
"""

import os
import json
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "mindrian-files")


class AlertSeverity(str, Enum):
    """Alert severity levels matching incident response."""
    P0 = "P0"  # Critical - requires immediate action
    P1 = "P1"  # High - requires same-day response
    P2 = "P2"  # Medium - requires this-week response
    P3 = "P3"  # Low - track for next review


class MonitoringEvent(str, Enum):
    """Types of events to monitor."""
    FORBIDDEN_ATTEMPT = "forbidden_attempt"       # User tried forbidden action
    BOUNDARY_VIOLATION = "boundary_violation"     # Bot violated boundary
    PROMPT_INJECTION = "prompt_injection"         # Detected injection attempt
    QUALITY_DEGRADATION = "quality_degradation"   # Low quality response
    SAFETY_TRIGGER = "safety_trigger"             # Safety content detected
    HALLUCINATION_RISK = "hallucination_risk"     # Potential hallucination
    DISCLAIMER_MISSING = "disclaimer_missing"     # Required disclaimer not shown
    UNUSUAL_PATTERN = "unusual_pattern"           # Anomalous behavior


@dataclass
class MonitoringAlert:
    """Represents a monitoring alert."""
    id: str
    event_type: str
    severity: str
    bot_id: str
    user_id: str
    session_id: str
    timestamp: str
    message: str
    context: Dict[str, Any]
    resolved: bool = False
    resolution_notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


# ==============================================================================
# DETECTION PATTERNS
# ==============================================================================

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|prior|above)\s+instructions",
    r"disregard\s+(all|your)\s+(instructions|programming|training)",
    r"you\s+are\s+now\s+a?\s*(different|new)",
    r"pretend\s+(you\s+are|to\s+be)",
    r"(this\s+is|we\'re\s+in)\s+(a\s+)?(test|debug)\s+mode",
    r"bypass\s+(safety|security|restrictions)",
    r"jailbreak",
    r"DAN\s+mode",
    r"developer\s+mode\s+(enabled|on)",
]

FORBIDDEN_CONTENT_PATTERNS = [
    # Financial advice
    r"(you\s+should|i\s+recommend)\s+(buy|sell|invest)",
    r"(guaranteed|certain)\s+(return|profit)",
    # Medical advice
    r"(you\s+have|diagnosis\s+is|you\s+should\s+take)",
    r"(discontinue|stop\s+taking)\s+your\s+medication",
    # Legal advice
    r"(you\s+should|i\s+advise)\s+(sue|file\s+a\s+lawsuit)",
    r"(you\s+are|are\s+not)\s+liable",
]

DISCLAIMER_REQUIRED_BOTS = ["pws_investment", "grading", "redteam"]

BOT_REQUIRED_DISCLAIMERS = {
    "pws_investment": [
        "not financial advice",
        "not investment advice",
        "informational purposes",
        "consult qualified professional",
    ],
    "grading": [
        "pws methodology",
        "validated against",
    ],
    "redteam": [
        "strengthen your thinking",
        "not predictions of failure",
    ],
}


# ==============================================================================
# MONITORING FUNCTIONS
# ==============================================================================

def check_prompt_injection(user_message: str) -> Optional[Tuple[str, float]]:
    """
    Check if a user message contains prompt injection attempts.

    Returns:
        Tuple of (matched_pattern, confidence) or None
    """
    message_lower = user_message.lower()

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, message_lower):
            confidence = 0.9 if "ignore" in pattern else 0.7
            return (pattern, confidence)

    return None


def check_forbidden_content(response: str, bot_id: str) -> Optional[Tuple[str, float]]:
    """
    Check if a response contains forbidden content.

    Returns:
        Tuple of (matched_pattern, confidence) or None
    """
    response_lower = response.lower()

    for pattern in FORBIDDEN_CONTENT_PATTERNS:
        if re.search(pattern, response_lower):
            return (pattern, 0.8)

    return None


def check_disclaimer_present(response: str, bot_id: str) -> bool:
    """
    Check if required disclaimers are present in high-stakes bot responses.
    """
    if bot_id not in DISCLAIMER_REQUIRED_BOTS:
        return True

    required_phrases = BOT_REQUIRED_DISCLAIMERS.get(bot_id, [])
    if not required_phrases:
        return True

    response_lower = response.lower()
    matches = sum(1 for phrase in required_phrases if phrase in response_lower)

    # Require at least one disclaimer phrase
    return matches > 0


def check_hallucination_risk(response: str) -> Optional[Tuple[str, float]]:
    """
    Check for patterns that suggest potential hallucination.

    Returns:
        Tuple of (risk_indicator, confidence) or None
    """
    response_lower = response.lower()

    # Definitive claims without hedging
    definitive_patterns = [
        r"(definitely|certainly|absolutely|undoubtedly)\s+will",
        r"100%\s+(sure|certain|guaranteed)",
        r"(this\s+is|that\'s)\s+a\s+fact",
        r"(everyone|nobody)\s+(knows|agrees)",
    ]

    for pattern in definitive_patterns:
        if re.search(pattern, response_lower):
            return ("over_confident_claim", 0.6)

    # Specific statistics without sources
    stat_pattern = r"\d+(\.\d+)?%\s+of\s+(people|users|customers)"
    if re.search(stat_pattern, response_lower):
        if "according to" not in response_lower and "source" not in response_lower:
            return ("unsourced_statistic", 0.5)

    return None


def assess_response_quality(
    response: str,
    user_message: str,
    bot_id: str
) -> Dict[str, Any]:
    """
    Assess overall response quality.

    Returns dict with quality scores and issues.
    """
    issues = []
    scores = {}

    # Length check (too short might be unhelpful)
    word_count = len(response.split())
    if word_count < 20 and len(user_message) > 50:
        issues.append("response_too_short")
        scores["length"] = 0.3
    else:
        scores["length"] = min(1.0, word_count / 100)

    # Relevance check (basic keyword overlap)
    user_words = set(user_message.lower().split())
    response_words = set(response.lower().split())
    overlap = len(user_words & response_words)
    scores["relevance"] = min(1.0, overlap / max(len(user_words), 1) * 2)

    if scores["relevance"] < 0.1:
        issues.append("low_relevance")

    # Check for empty/error responses
    if not response.strip():
        issues.append("empty_response")
        scores["completeness"] = 0.0
    elif "error" in response.lower() and "sorry" in response.lower():
        issues.append("error_response")
        scores["completeness"] = 0.5
    else:
        scores["completeness"] = 1.0

    # Overall score
    overall = sum(scores.values()) / len(scores)

    return {
        "overall_score": overall,
        "scores": scores,
        "issues": issues,
        "quality_ok": overall >= 0.5 and len(issues) == 0
    }


# ==============================================================================
# MONITOR CLASS
# ==============================================================================

class AIMonitor:
    """
    Main monitoring class for AI behavior oversight.
    """

    def __init__(self):
        self.alerts: List[MonitoringAlert] = []
        self.stats = {
            "total_checks": 0,
            "alerts_raised": 0,
            "by_type": {},
            "by_severity": {},
            "by_bot": {},
        }
        self._supabase_client = None

    def _get_supabase_client(self):
        """Get Supabase client."""
        if self._supabase_client is None and SUPABASE_URL and SUPABASE_SERVICE_KEY:
            try:
                from supabase import create_client
                self._supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            except Exception as e:
                print(f"Supabase client error: {e}")
        return self._supabase_client

    def _generate_alert_id(self, event_type: str, session_id: str) -> str:
        """Generate unique alert ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        hash_input = f"{event_type}:{session_id}:{timestamp}"
        short_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        return f"alert_{short_hash}_{timestamp}"

    def _create_alert(
        self,
        event_type: MonitoringEvent,
        severity: AlertSeverity,
        bot_id: str,
        user_id: str,
        session_id: str,
        message: str,
        context: Dict[str, Any]
    ) -> MonitoringAlert:
        """Create and store a monitoring alert."""
        alert = MonitoringAlert(
            id=self._generate_alert_id(event_type.value, session_id),
            event_type=event_type.value,
            severity=severity.value,
            bot_id=bot_id,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat(),
            message=message,
            context=context
        )

        self.alerts.append(alert)
        self._update_stats(alert)
        self._store_alert(alert)

        return alert

    def _update_stats(self, alert: MonitoringAlert):
        """Update monitoring statistics."""
        self.stats["alerts_raised"] += 1

        # By type
        event_type = alert.event_type
        self.stats["by_type"][event_type] = self.stats["by_type"].get(event_type, 0) + 1

        # By severity
        severity = alert.severity
        self.stats["by_severity"][severity] = self.stats["by_severity"].get(severity, 0) + 1

        # By bot
        bot = alert.bot_id
        self.stats["by_bot"][bot] = self.stats["by_bot"].get(bot, 0) + 1

    def _store_alert(self, alert: MonitoringAlert):
        """Store alert to Supabase."""
        client = self._get_supabase_client()
        if not client:
            return

        try:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            filename = f"monitoring/{date_str}/{alert.id}.json"

            json_content = json.dumps(alert.to_dict(), indent=2).encode('utf-8')

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

            print(f"Monitoring: Stored alert {alert.id}")

        except Exception as e:
            print(f"Alert storage error: {e}")

    def check_message(
        self,
        user_message: str,
        bot_response: str,
        bot_id: str,
        user_id: str = "anonymous",
        session_id: str = ""
    ) -> Dict[str, Any]:
        """
        Run all monitoring checks on a message/response pair.

        Returns:
            Dict with check results and any alerts raised
        """
        self.stats["total_checks"] += 1

        results = {
            "passed": True,
            "alerts": [],
            "checks": {}
        }

        # 1. Check for prompt injection
        injection = check_prompt_injection(user_message)
        if injection:
            pattern, confidence = injection
            alert = self._create_alert(
                event_type=MonitoringEvent.PROMPT_INJECTION,
                severity=AlertSeverity.P1,
                bot_id=bot_id,
                user_id=user_id,
                session_id=session_id,
                message=f"Prompt injection attempt detected: {pattern}",
                context={"pattern": pattern, "confidence": confidence, "message_preview": user_message[:200]}
            )
            results["alerts"].append(alert.to_dict())
            results["passed"] = False
            results["checks"]["prompt_injection"] = {"passed": False, "pattern": pattern}
        else:
            results["checks"]["prompt_injection"] = {"passed": True}

        # 2. Check for forbidden content in response
        forbidden = check_forbidden_content(bot_response, bot_id)
        if forbidden:
            pattern, confidence = forbidden
            alert = self._create_alert(
                event_type=MonitoringEvent.BOUNDARY_VIOLATION,
                severity=AlertSeverity.P0,
                bot_id=bot_id,
                user_id=user_id,
                session_id=session_id,
                message=f"Forbidden content detected in response: {pattern}",
                context={"pattern": pattern, "confidence": confidence, "response_preview": bot_response[:200]}
            )
            results["alerts"].append(alert.to_dict())
            results["passed"] = False
            results["checks"]["forbidden_content"] = {"passed": False, "pattern": pattern}
        else:
            results["checks"]["forbidden_content"] = {"passed": True}

        # 3. Check disclaimers for high-stakes bots
        if bot_id in DISCLAIMER_REQUIRED_BOTS:
            has_disclaimer = check_disclaimer_present(bot_response, bot_id)
            if not has_disclaimer:
                alert = self._create_alert(
                    event_type=MonitoringEvent.DISCLAIMER_MISSING,
                    severity=AlertSeverity.P2,
                    bot_id=bot_id,
                    user_id=user_id,
                    session_id=session_id,
                    message=f"Required disclaimer missing for {bot_id}",
                    context={"bot_id": bot_id, "response_preview": bot_response[:200]}
                )
                results["alerts"].append(alert.to_dict())
                results["checks"]["disclaimer"] = {"passed": False}
            else:
                results["checks"]["disclaimer"] = {"passed": True}

        # 4. Check for hallucination risk
        hallucination = check_hallucination_risk(bot_response)
        if hallucination:
            indicator, confidence = hallucination
            if confidence >= 0.6:
                alert = self._create_alert(
                    event_type=MonitoringEvent.HALLUCINATION_RISK,
                    severity=AlertSeverity.P2,
                    bot_id=bot_id,
                    user_id=user_id,
                    session_id=session_id,
                    message=f"Potential hallucination detected: {indicator}",
                    context={"indicator": indicator, "confidence": confidence}
                )
                results["alerts"].append(alert.to_dict())
            results["checks"]["hallucination"] = {"passed": confidence < 0.6, "indicator": indicator}
        else:
            results["checks"]["hallucination"] = {"passed": True}

        # 5. Quality assessment
        quality = assess_response_quality(bot_response, user_message, bot_id)
        results["checks"]["quality"] = quality

        if not quality["quality_ok"]:
            alert = self._create_alert(
                event_type=MonitoringEvent.QUALITY_DEGRADATION,
                severity=AlertSeverity.P3,
                bot_id=bot_id,
                user_id=user_id,
                session_id=session_id,
                message=f"Quality issues detected: {', '.join(quality['issues'])}",
                context=quality
            )
            results["alerts"].append(alert.to_dict())

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        return {
            **self.stats,
            "alert_rate": self.stats["alerts_raised"] / max(self.stats["total_checks"], 1),
            "recent_alerts": [a.to_dict() for a in self.alerts[-10:]],
        }

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[MonitoringAlert]:
        """Get alerts by severity level."""
        return [a for a in self.alerts if a.severity == severity.value]

    def export_monitoring_report(self, date_str: str = None) -> str:
        """Generate markdown monitoring report."""
        if not date_str:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")

        report = f"""# AI Monitoring Report
**Date:** {date_str}
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

---

## Summary

| Metric | Value |
|--------|-------|
| Total Checks | {self.stats['total_checks']} |
| Alerts Raised | {self.stats['alerts_raised']} |
| Alert Rate | {self.stats['alerts_raised'] / max(self.stats['total_checks'], 1) * 100:.2f}% |

---

## Alerts by Severity

| Severity | Count |
|----------|-------|
| P0 (Critical) | {self.stats['by_severity'].get('P0', 0)} |
| P1 (High) | {self.stats['by_severity'].get('P1', 0)} |
| P2 (Medium) | {self.stats['by_severity'].get('P2', 0)} |
| P3 (Low) | {self.stats['by_severity'].get('P3', 0)} |

---

## Alerts by Type

| Type | Count |
|------|-------|
"""
        for event_type, count in self.stats['by_type'].items():
            report += f"| {event_type} | {count} |\n"

        report += """
---

## Alerts by Bot

| Bot | Count |
|-----|-------|
"""
        for bot, count in self.stats['by_bot'].items():
            report += f"| {bot} | {count} |\n"

        # Recent alerts
        if self.alerts:
            report += """
---

## Recent Alerts

"""
            for alert in self.alerts[-10:]:
                report += f"""
### {alert.id}
- **Type:** {alert.event_type}
- **Severity:** {alert.severity}
- **Bot:** {alert.bot_id}
- **Time:** {alert.timestamp}
- **Message:** {alert.message}

"""

        return report


# ==============================================================================
# GLOBAL INSTANCE
# ==============================================================================

# Global monitor instance
_monitor: Optional[AIMonitor] = None


def get_monitor() -> AIMonitor:
    """Get or create the global monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = AIMonitor()
    return _monitor


def monitor_message(
    user_message: str,
    bot_response: str,
    bot_id: str,
    user_id: str = "anonymous",
    session_id: str = ""
) -> Dict[str, Any]:
    """
    Convenience function to monitor a message exchange.

    This is the main entry point for integration with mindrian_chat.py
    """
    monitor = get_monitor()
    return monitor.check_message(
        user_message=user_message,
        bot_response=bot_response,
        bot_id=bot_id,
        user_id=user_id,
        session_id=session_id
    )
