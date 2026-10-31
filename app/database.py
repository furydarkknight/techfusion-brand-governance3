import datetime
from typing import List, Dict, Any, Optional

class Database:
    def __init__(self):
        self.guidelines = [
            {
                "id": "GL-TONE-01",
                "category": "tone",
                "name": "Empathetic & Authoritative Voice",
                "description": "Maintain a warm, professional, respectful tone. Avoid arrogant claims, hyperbole, panic-inducing language, or condescending phrasing.",
                "rules": [
                    "Do not use hype terms like 'unmatched miracle', 'industry-destroying', 'crush the competition'.",
                    "Acknowledge user challenges with empathy rather than blame.",
                    "Keep claims measured and grounded in verifiable value."
                ],
                "severity": "warning",
                "version": "v2.1",
                "status": "active"
            },
            {
                "id": "GL-TONE-02",
                "category": "tone",
                "name": "Inclusive & Respectful Phrasing",
                "description": "Ensure communication is gender-neutral, accessible, and universally respectful.",
                "rules": [
                    "Avoid gendered idioms such as 'man-hours' or 'you guys'.",
                    "Use neutral, professional address such as 'team', 'engineers', 'person-hours'."
                ],
                "severity": "warning",
                "version": "v1.4",
                "status": "active"
            },
            {
                "id": "GL-TERM-01",
                "category": "terminology",
                "name": "Enterprise Approved Nomenclature",
                "description": "Standardize brand terminology across all marketing, engineering, and sales collateral.",
                "rules": [
                    "Replace 'cheap' with 'cost-effective' or 'economical'.",
                    "Replace 'foolproof' with 'resilient' or 'reliable'.",
                    "Replace 'blacklist/whitelist' with 'denylist/allowlist'.",
                    "Replace 'sanity check' with 'quick verification' or 'smoke check'."
                ],
                "severity": "critical",
                "version": "v3.0",
                "status": "active"
            },
            {
                "id": "GL-CLAIM-01",
                "category": "claims",
                "name": "Substantiated Claims & Fact Verification",
                "description": "Every statistical metric, performance guarantee, and certification must match the central Approved Facts repository.",
                "rules": [
                    "Absolute claims like '100% bug-free', 'zero latency' or '#1 in the entire world' are strictly prohibited unless certified.",
                    "Performance SLA references must accurately state 99.99%, not unverified 100%.",
                    "Customer count citations must match current verified metric (42,000+ active enterprise teams)."
                ],
                "severity": "critical",
                "version": "v2.3",
                "status": "active"
            },
            {
                "id": "GL-VIS-01",
                "category": "visual",
                "name": "Brand Asset & Color Palette Standards",
                "description": "All visual representations must adhere to primary brand palette (#4F46E5 indigo, #06B6D4 cyan) and logo spacing.",
                "rules": [
                    "Do not use obsolete brand red (#EF4444) as primary hero accent.",
                    "Logos require minimum 24px safe padding margins.",
                    "Imagery must include descriptive accessibility alt-text."
                ],
                "severity": "warning",
                "version": "v2.0",
                "status": "active"
            },
            {
                "id": "GL-A11Y-01",
                "category": "accessibility",
                "name": "WCAG 2.1 AA Readability & Inclusion",
                "description": "Ensure public content is understandable and accessible to diverse audiences.",
                "rules": [
                    "Maintain Flesch-Kincaid Reading Grade between Grade 7 and Grade 11.",
                    "Avoid overly dense run-on sentences exceeding 35 words.",
                    "Avoid cryptic acronyms without first defining them."
                ],
                "severity": "warning",
                "version": "v1.2",
                "status": "active"
            }
        ]

        self.approved_facts = [
            {
                "id": "FACT-01",
                "topic": "Customer Base",
                "verified_claim": "Over 42,000 active enterprise organizations across 85 countries trust TechFusion.",
                "keywords": ["customers", "active organizations", "users", "enterprise clients", "countries"],
                "approved_by": "VP of Revenue Operations",
                "last_verified": "2026-01-15",
                "evidence_doc": "SEC-Q4-2025-Metrics.pdf"
            },
            {
                "id": "FACT-02",
                "topic": "Compliance & Security",
                "verified_claim": "TechFusion holds SOC2 Type II, ISO 27001, and HIPAA compliance certifications verified annually.",
                "keywords": ["soc2", "iso 27001", "hipaa", "compliance", "security", "encryption"],
                "approved_by": "Chief Information Security Officer",
                "last_verified": "2026-01-10",
                "evidence_doc": "Audit-SOC2-TypeII-2026.pdf"
            },
            {
                "id": "FACT-03",
                "topic": "Availability SLA",
                "verified_claim": "Maintains a 99.99% multi-region cloud availability SLA backed by contractual financial credits.",
                "keywords": ["sla", "availability", "uptime", "99.99%", "99.99", "reliability"],
                "approved_by": "Head of Cloud Infrastructure",
                "last_verified": "2026-02-01",
                "evidence_doc": "Infrastructure-SLA-Agreement-v4.pdf"
            },
            {
                "id": "FACT-04",
                "topic": "Encryption Standards",
                "verified_claim": "Zero-trust end-to-end data encryption using AES-256 for data at rest and TLS 1.3 for data in transit.",
                "keywords": ["encryption", "aes-256", "tls 1.3", "zero-trust", "data security"],
                "approved_by": "Lead Cryptographic Architect",
                "last_verified": "2026-01-20",
                "evidence_doc": "Cryptographic-Controls-Standard.pdf"
            },
            {
                "id": "FACT-05",
                "topic": "Customer Support Performance",
                "verified_claim": "Average customer issue resolution time is under 18 minutes with 24/7 dedicated tier-3 technical support.",
                "keywords": ["support", "resolution time", "18 minutes", "24/7 support", "response time"],
                "approved_by": "Director of Customer Success",
                "last_verified": "2026-02-12",
                "evidence_doc": "Support-KPI-Q1-2026.pdf"
            }
        ]

        self.terminology_map = [
            {"term": "cheap", "replacement": "cost-effective", "reason": "Demeans product quality perception; use value-focused phrasing."},
            {"term": "foolproof", "replacement": "resilient & dependable", "reason": "Overpromises infallibility and insults user capability."},
            {"term": "blacklist", "replacement": "denylist", "reason": "Inclusive terminology standard according to GL-TERM-01."},
            {"term": "whitelist", "replacement": "allowlist", "reason": "Inclusive terminology standard according to GL-TERM-01."},
            {"term": "sanity check", "replacement": "quick verification", "reason": "Non-inclusive cognitive idiom; use clear functional descriptions."},
            {"term": "man-hours", "replacement": "person-hours", "reason": "Gendered language violation per GL-TONE-02."},
            {"term": "you guys", "replacement": "everyone", "reason": "Gendered and informal idiom for enterprise audience."},
            {"term": "game-changing miracle", "replacement": "significant architectural leap", "reason": "Excessive sensational hyperbole degrades brand credibility."},
            {"term": "crush the competition", "replacement": "deliver unmatched enterprise value", "reason": "Aggressive, combative phrasing conflicts with brand humility."},
            {"term": "100% bug-free", "replacement": "rigorously tested with 99.99% reliability", "reason": "Legally indefensible engineering guarantee."}
        ]

        # Initial drafts for judges to inspect right away
        self.drafts = [
            {
                "id": "DRAFT-2026-001",
                "title": "Spring 2026 Enterprise Release Announcement",
                "content": (
                    "Hey you guys! TechFusion is thrilled to drop our game-changing miracle update today! "
                    "Our new platform is 100% bug-free and will completely crush the competition. "
                    "We currently serve over 100,000 customers worldwide with zero downtime ever recorded. "
                    "Best of all, our pricing is cheap and our setup is totally foolproof! "
                    "Before deployment, our engineers do a quick sanity check and update the server blacklist."
                ),
                "author": "Yash Singhla (Creator)",
                "created_at": "2026-10-24 14:30:00",
                "status": "CHANGES_REQUESTED",
                "score": 42,
                "findings_count": 8,
                "history": [
                    {"timestamp": "2026-10-24 14:30:00", "user": "Yash Singhla", "action": "Submitted Draft v1 for Review"},
                    {"timestamp": "2026-10-24 14:35:12", "user": "TechFusion AI Engine", "action": "Automated Brand Audit complete (Score: 42/100)"},
                    {"timestamp": "2026-10-24 15:10:00", "user": "Aditya Sharma (Reviewer)", "action": "Requested Revisions: Flagged 3 unverified claims and 5 tone violations."}
                ],
                "comments": [
                    {
                        "id": "c1",
                        "author": "Aditya Sharma (Brand Lead)",
                        "role": "Reviewer",
                        "timestamp": "2026-10-24 15:08:22",
                        "text": "Yash, we cannot claim '100% bug-free' or '100,000 customers'. Our verified active count is 42,000+ per SEC filings. Also please swap the outdated terminology."
                    },
                    {
                        "id": "c2",
                        "author": "Yash Singhla",
                        "role": "Creator",
                        "timestamp": "2026-10-24 15:15:40",
                        "text": "Understood Aditya! I will use the 1-click suggested corrections and submit v2 for approval."
                    }
                ]
            },
            {
                "id": "DRAFT-2026-002",
                "title": "Cloud Security Whitepaper Executive Summary",
                "content": (
                    "TechFusion provides enterprise organizations with zero-trust encryption and continuous compliance. "
                    "We hold annual SOC2 Type II, ISO 27001, and HIPAA certifications. "
                    "Our cloud architecture maintains a 99.99% multi-region availability SLA backed by contractual guarantees. "
                    "Over 42,000 active enterprise organizations trust TechFusion to govern their digital brand presence."
                ),
                "author": "Rishit Negi (Creator)",
                "created_at": "2026-10-25 09:15:00",
                "status": "APPROVED",
                "score": 98,
                "findings_count": 0,
                "history": [
                    {"timestamp": "2026-10-25 09:15:00", "user": "Rishit Negi", "action": "Submitted Draft v1"},
                    {"timestamp": "2026-10-25 09:15:30", "user": "TechFusion AI Engine", "action": "Automated Brand Audit complete (Score: 98/100)"},
                    {"timestamp": "2026-10-25 09:45:00", "user": "Ramandeep Singh (Manager)", "action": "Approved for publication with zero outstanding issues."}
                ],
                "comments": [
                    {
                        "id": "c3",
                        "author": "Ramandeep Singh (Manager)",
                        "role": "Manager",
                        "timestamp": "2026-10-25 09:44:30",
                        "text": "Exemplary adherence to verified claims and tone guidelines. Approved for immediate syndication."
                    }
                ]
            }
        ]

        self.audit_log = [
            {"id": "LOG-101", "timestamp": "2026-10-26 09:30:12", "user": "Yash Singhla", "action": "Updated Brand Guideline GL-CLAIM-01 to version 2.3"},
            {"id": "LOG-102", "timestamp": "2026-10-26 09:45:00", "user": "Rishit Negi", "action": "Added Approved Fact FACT-05 (Customer Support Response Time)"},
            {"id": "LOG-103", "timestamp": "2026-10-26 10:12:44", "user": "Ramandeep Singh", "action": "Approved Whitepaper DRAFT-2026-002"},
            {"id": "LOG-104", "timestamp": "2026-10-26 10:20:18", "user": "Aditya Sharma", "action": "Initiated Governance Drift Analysis across all team assets"}
        ]

        self.insights = {
            "total_reviews": 142,
            "overall_compliance_rate": 87.4,
            "avg_time_to_approval_hours": 3.8,
            "recurring_issues": [
                {"name": "Unsupported Superlatives / Claims", "count": 54, "percentage": 38.0, "guideline": "GL-CLAIM-01"},
                {"name": "Non-Approved Terminology", "count": 39, "percentage": 27.5, "guideline": "GL-TERM-01"},
                {"name": "Aggressive / Overly Casual Tone", "count": 28, "percentage": 19.7, "guideline": "GL-TONE-01"},
                {"name": "Missing Alt-Text & WCAG Readability", "count": 21, "percentage": 14.8, "guideline": "GL-A11Y-01"}
            ],
            "drift_by_department": [
                {"department": "Product Marketing", "compliance": 79.2, "flagged": 46},
                {"department": "Social & Growth", "compliance": 74.5, "flagged": 58},
                {"department": "Technical Documentation", "compliance": 96.1, "flagged": 8},
                {"department": "Executive Communications", "compliance": 92.4, "flagged": 14}
            ]
        }

    def get_guidelines(self) -> List[Dict[str, Any]]:
        return self.guidelines

    def add_guideline(self, guideline: Dict[str, Any]) -> Dict[str, Any]:
        self.guidelines.append(guideline)
        self.log_action("Admin", f"Created new brand guideline {guideline['id']}: {guideline['name']}")
        return guideline

    def update_guideline(self, gid: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for g in self.guidelines:
            if g["id"] == gid:
                g.update(data)
                self.log_action("Admin", f"Updated brand guideline {gid}")
                return g
        return None

    def get_facts(self) -> List[Dict[str, Any]]:
        return self.approved_facts

    def add_fact(self, fact: Dict[str, Any]) -> Dict[str, Any]:
        self.approved_facts.append(fact)
        self.log_action("Admin", f"Added verified fact {fact['id']}: {fact['topic']}")
        return fact

    def get_drafts(self) -> List[Dict[str, Any]]:
        return self.drafts

    def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        for d in self.drafts:
            if d["id"] == draft_id:
                return d
        return None

    def save_draft(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        for idx, d in enumerate(self.drafts):
            if d["id"] == draft["id"]:
                self.drafts[idx] = draft
                return draft
        self.drafts.insert(0, draft)
        return draft

    def log_action(self, user: str, action: str):
        log_entry = {
            "id": f"LOG-{len(self.audit_log) + 101}",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user,
            "action": action
        }
        self.audit_log.insert(0, log_entry)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return self.audit_log

    def get_insights(self) -> Dict[str, Any]:
        return self.insights

db = Database()
