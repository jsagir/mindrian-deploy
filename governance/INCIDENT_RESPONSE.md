# Incident Response Playbook - Mindrian AI Platform

> **Purpose:** Define clear procedures for responding to AI-related incidents.
> **Owner:** @jsagir
> **Last Updated:** 2026-01-30

---

## Severity Levels

| Level | Name | Description | Response Time | Examples |
|-------|------|-------------|---------------|----------|
| **P0** | Critical | System down, data breach, safety violation | 15 minutes | Bot provides harmful content, PII leak, prompt injection succeeded |
| **P1** | High | Major feature broken, incorrect advice given | 1 hour | Financial advice given, significant hallucination, disclaimer missing |
| **P2** | Medium | Quality degradation, minor boundary issue | 24 hours | Low quality responses, near-miss on forbidden content |
| **P3** | Low | Cosmetic issues, minor quality dips | 1 week | Formatting issues, slightly off-topic responses |

---

## P0 - Critical Incident Response

### Immediate Actions (0-15 minutes)

```
1. STOP THE BLEEDING
   □ Disable affected bot if causing active harm
   □ If data breach: Revoke affected credentials immediately
   □ Document: What happened? When? Who's affected?

2. NOTIFY
   □ Primary: @jsagir (owner)
   □ Secondary: [backup contact]
   □ If data breach: Legal/compliance as required

3. PRESERVE EVIDENCE
   □ Screenshot affected output
   □ Export relevant session logs
   □ Do NOT delete or modify evidence
```

### Investigation (15-60 minutes)

```
□ What was the user input that triggered this?
□ What was the exact AI output?
□ Which bot/agent was involved?
□ What were the session settings?
□ Is this reproducible?
□ How many users potentially affected?
```

### Resolution

```
□ Identify root cause
□ Implement fix (prompt change, code fix, config update)
□ Test fix thoroughly
□ Re-enable with monitoring
□ Notify affected users if appropriate
```

### Post-Incident (within 48 hours)

```
□ Complete incident report (template below)
□ Update forbidden uses if needed
□ Add test case to evaluation suite
□ Review for systemic issues
□ Share learnings (internal)
```

---

## P1 - High Priority Response

### Response Time: Within 1 hour

```
1. ASSESS
   □ What happened?
   □ Is it ongoing or one-time?
   □ User impact?

2. MITIGATE
   □ Can we add a temporary guard?
   □ Should we reduce bot capabilities temporarily?
   □ Need to notify users?

3. FIX
   □ Identify root cause
   □ Develop and test fix
   □ Deploy with monitoring

4. DOCUMENT
   □ Log in incident tracker
   □ Update prompt cards if behavior changed
   □ Add regression test
```

---

## P2 - Medium Priority Response

### Response Time: Within 24 hours

```
1. LOG
   □ Document the issue
   □ Categorize (quality, boundary, safety)

2. PRIORITIZE
   □ Is this part of a pattern?
   □ User impact assessment

3. SCHEDULE
   □ Add to next sprint/cycle
   □ Assign owner

4. TRACK
   □ Monitor for recurrence
   □ Close when resolved
```

---

## P3 - Low Priority Response

### Response Time: Within 1 week

```
1. LOG in issue tracker
2. BATCH with similar issues
3. FIX in regular maintenance
4. CLOSE with documentation
```

---

## Incident Report Template

```markdown
# Incident Report: [ID]

## Summary
**Date/Time:** YYYY-MM-DD HH:MM UTC
**Severity:** P0/P1/P2/P3
**Status:** Active/Resolved
**Duration:** X hours

## What Happened
[Brief description of the incident]

## Timeline
- HH:MM - Incident detected by [method]
- HH:MM - Response initiated by [person]
- HH:MM - Mitigation applied
- HH:MM - Root cause identified
- HH:MM - Fix deployed
- HH:MM - Incident closed

## Impact
- Users affected: [number]
- Sessions affected: [number]
- Data exposed: [yes/no, details if yes]

## Root Cause
[Detailed technical explanation]

## Resolution
[What was done to fix it]

## Prevention
[What changes will prevent recurrence]

## Action Items
- [ ] Action 1 - Owner - Due Date
- [ ] Action 2 - Owner - Due Date

## Lessons Learned
[Key takeaways for the team]
```

---

## Escalation Matrix

| Severity | Primary | Secondary | Executive |
|----------|---------|-----------|-----------|
| P0 | @jsagir (immediate) | [backup] | If data breach |
| P1 | @jsagir (1 hour) | [backup] | If >4 hours |
| P2 | @jsagir (24 hours) | - | - |
| P3 | [logged] | - | - |

---

## Communication Templates

### User Notification (if needed)

```
Subject: Important Notice About Your Mindrian Session

We identified an issue with a recent interaction that may have
provided [incorrect/inappropriate] information.

What happened: [brief, non-technical explanation]

What we're doing: [action taken]

What you should know: [any user action needed]

We apologize for any inconvenience and have implemented safeguards
to prevent similar issues.

If you have questions, please contact [support].
```

### Internal Alert

```
🚨 AI INCIDENT ALERT - [SEVERITY]

Bot: [bot_id]
Issue: [brief description]
Time: [timestamp]
Status: [investigating/mitigating/resolved]

Action needed: [what team members should do]

Lead: [person handling]
```

---

## Runbook: Common Scenarios

### Scenario: Prompt Injection Detected

```
1. Check if injection succeeded (did bot behavior change?)
2. If yes → P0, disable bot, investigate
3. If no → P1, log and monitor, strengthen defenses
4. Review injection pattern, add to blocked list
5. Test with similar patterns
```

### Scenario: Bot Gave Financial Advice

```
1. Assess specificity (general vs. specific recommendation)
2. If specific buy/sell advice → P0
3. If general but inappropriate → P1
4. Review prompt for boundary weakness
5. Add explicit rejection pattern
6. Consider user notification if specific advice given
```

### Scenario: Missing Disclaimer

```
1. Which bot? (pws_investment, grading, redteam)
2. How many responses missing disclaimer?
3. If pattern → P1, fix immediately
4. If one-off → P2, investigate
5. Add disclaimer check to monitoring
```

### Scenario: Quality Degradation

```
1. Is this model-side or prompt-side?
2. Check for recent changes (prompts, config)
3. If widespread → P1
4. If isolated → P2/P3
5. Compare to baseline quality metrics
6. Roll back recent changes if suspected
```

---

## Recovery Procedures

### Rollback Procedure

```bash
# 1. Identify last known good commit
git log --oneline -10

# 2. Revert to previous version
git revert [commit_hash]

# 3. Deploy
# [deployment command]

# 4. Verify
python scripts/health_check.py

# 5. Monitor
# Check monitoring dashboard
```

### Bot Disable Procedure

```python
# In mindrian_chat.py, add bot to disabled list
DISABLED_BOTS = ["bot_id_to_disable"]

# Or set in environment
# DISABLED_BOTS=bot_id_1,bot_id_2
```

### Emergency Contact Update

```
# Update .env with emergency mode
EMERGENCY_MODE=true
EMERGENCY_MESSAGE="System maintenance in progress. Some features may be limited."
```

---

## Review Schedule

| Review Type | Frequency | Owner |
|-------------|-----------|-------|
| Active incidents | Daily | On-call |
| P0/P1 post-mortems | Within 48h | @jsagir |
| Incident trends | Weekly | @jsagir |
| Playbook update | Quarterly | @jsagir |

---

## Appendix: Monitoring Integration

The AI Monitor (`governance/ai_monitor.py`) automatically detects and logs:
- Prompt injection attempts
- Boundary violations
- Missing disclaimers
- Quality degradation
- Hallucination risks

Alerts are stored in Supabase under `monitoring/{date}/{alert_id}.json`.

Access monitoring stats:
```python
from governance.ai_monitor import get_monitor

monitor = get_monitor()
stats = monitor.get_stats()
report = monitor.export_monitoring_report()
```

---

*Next Review: 2026-04-30*
