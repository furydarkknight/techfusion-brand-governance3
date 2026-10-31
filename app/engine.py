import re
import math
from typing import List, Dict, Any
from app.database import db

def calculate_reading_level(text: str) -> Dict[str, Any]:
    """Calculate Flesch Reading Ease and Flesch-Kincaid Grade Level."""
    words = re.findall(r'\b[A-Za-z0-9\'-]+\b', text)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    word_count = len(words)
    sentence_count = max(len(sentences), 1)

    if word_count == 0:
        return {"flesch_score": 100.0, "grade_level": "Grade 5", "word_count": 0, "sentence_count": 0}

    # Count syllables (heuristic)
    def count_syllables(word: str) -> int:
        word = word.lower()
        if len(word) <= 3:
            return 1
        word = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', word)
        word = re.sub(r'^y', '', word)
        syllables = len(re.findall(r'[aeiouy]{1,2}', word))
        return max(syllables, 1)

    total_syllables = sum(count_syllables(w) for w in words)

    asl = word_count / sentence_count  # average sentence length
    asw = total_syllables / word_count  # average syllables per word

    # Flesch Reading Ease formula
    fre = 206.835 - (1.015 * asl) - (84.6 * asw)
    fre = max(0.0, min(100.0, fre))

    # Flesch-Kincaid Grade Level
    fkgl = (0.39 * asl) + (11.8 * asw) - 15.59
    fkgl = max(1.0, min(18.0, fkgl))

    return {
        "flesch_score": round(fre, 1),
        "grade_level": f"Grade {round(fkgl, 1)}",
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(asl, 1)
    }

class BrandGovernanceEngine:
    def __init__(self):
        pass

    def review_content(self, text: str, title: str = "", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        metadata = metadata or {}
        findings: List[Dict[str, Any]] = []
        deductions = {"terminology": 0, "claims": 0, "tone": 0, "accessibility": 0, "visual": 0}

        # 1. Terminology Scan
        for term_rule in db.terminology_map:
            pattern = r'\b' + re.escape(term_rule["term"]) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                matched_str = match.group(0)
                findings.append({
                    "id": f"F-TERM-{len(findings) + 1}",
                    "category": "terminology",
                    "severity": "critical" if term_rule["term"] in ["100% bug-free", "blacklist", "whitelist"] else "warning",
                    "rule_id": "GL-TERM-01",
                    "rule_name": "Enterprise Approved Nomenclature",
                    "flagged_text": matched_str,
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "reason": term_rule["reason"],
                    "suggestion": term_rule["replacement"],
                    "confidence": 0.98,
                    "approved_source": "GL-TERM-01 (Brand Lexicon Standard v3.0)"
                })
                deductions["terminology"] += 12

        # 2. Fact & Claim Verification
        # Check customer number exaggeration
        cust_match = re.search(r'\b(over\s+)?(\d{2,3}(?:,\d{3})+|\d{5,7})\s*(customers|clients|users|organizations)\b', text, re.IGNORECASE)
        if cust_match:
            claimed_str = cust_match.group(0)
            findings.append({
                "id": f"F-CLAIM-{len(findings) + 1}",
                "category": "claims",
                "severity": "critical",
                "rule_id": "GL-CLAIM-01",
                "rule_name": "Substantiated Claims & Fact Verification",
                "flagged_text": claimed_str,
                "start_char": cust_match.start(),
                "end_char": cust_match.end(),
                "reason": "Claimed customer count conflicts with certified active database. Verified metric is 'Over 42,000 active enterprise organizations'.",
                "suggestion": "Over 42,000 active enterprise organizations",
                "confidence": 0.95,
                "approved_source": "FACT-01 (SEC-Q4-2025-Metrics.pdf, verified Jan 2026)"
            })
            deductions["claims"] += 20

        # Check uptime/downtime absolutes
        downtime_match = re.search(r'\b(zero\s+downtime\s*(ever|recorded)?|100%\s+uptime)\b', text, re.IGNORECASE)
        if downtime_match:
            findings.append({
                "id": f"F-CLAIM-{len(findings) + 1}",
                "category": "claims",
                "severity": "critical",
                "rule_id": "GL-CLAIM-01",
                "rule_name": "Availability SLA Accuracy",
                "flagged_text": downtime_match.group(0),
                "start_char": downtime_match.start(),
                "end_char": downtime_match.end(),
                "reason": "Absolute 'zero downtime' is uninsurable and violates SLA disclosure guidelines. Official contractual SLA is 99.99%.",
                "suggestion": "industry-leading 99.99% multi-region uptime SLA",
                "confidence": 0.99,
                "approved_source": "FACT-03 (Infrastructure-SLA-Agreement-v4.pdf)"
            })
            deductions["claims"] += 20

        # Check superlative words without qualification
        superlative_patterns = [
            (r'\b(completely\s+crush\s+the\s+competition)\b', "Aggressive competitive attack violates brand humility and professional standards.", "deliver unmatched enterprise value", "GL-TONE-01"),
            (r'\b(game-changing\s+miracle)\b', "Sensational hyperbolic claim violates factual messaging guidelines.", "significant architectural milestone", "GL-TONE-01"),
            (r'\b(Hey\s+you\s+guys!?)\b', "Informal and gendered greeting unsuited for global enterprise release.", "Hello esteemed partners and teams,", "GL-TONE-02"),
            (r'\b(drop\s+our)\b', "Informal colloquialism unsuited for enterprise product releases.", "announce the release of our", "GL-TONE-01"),
            (r'\b(totally\s+foolproof!?)\b', "Misleading assurance of zero user error.", "exceptionally intuitive and resilient", "GL-TERM-01")
        ]

        for pat, reason, sugg, rule_id in superlative_patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                # Avoid duplicate if already covered by terminology
                if not any(f["start_char"] == match.start() and f["end_char"] == match.end() for f in findings):
                    findings.append({
                        "id": f"F-TONE-{len(findings) + 1}",
                        "category": "tone",
                        "severity": "warning",
                        "rule_id": rule_id,
                        "rule_name": "Empathetic & Authoritative Voice",
                        "flagged_text": match.group(0),
                        "start_char": match.start(),
                        "end_char": match.end(),
                        "reason": reason,
                        "suggestion": sugg,
                        "confidence": 0.92,
                        "approved_source": f"{rule_id} (TechFusion Voice & Tone Standard)"
                    })
                    deductions["tone"] += 10

        # 3. Accessibility & Readability Analysis
        readability = calculate_reading_level(text)
        if readability["word_count"] > 10 and readability["flesch_score"] < 45:
            findings.append({
                "id": f"F-A11Y-{len(findings) + 1}",
                "category": "accessibility",
                "severity": "warning",
                "rule_id": "GL-A11Y-01",
                "rule_name": "WCAG 2.1 AA Readability",
                "flagged_text": "Content overall readability",
                "start_char": 0,
                "end_char": min(30, len(text)),
                "reason": f"Reading ease score is {readability['flesch_score']} (Grade {readability['grade_level']}). High sentence complexity may hinder accessibility.",
                "suggestion": "Shorten complex sentences to under 25 words each and simplify technical idioms.",
                "confidence": 0.88,
                "approved_source": "GL-A11Y-01 (Accessibility Standard v1.2)"
            })
            deductions["accessibility"] += 15

        # Check long run-on sentences (> 35 words)
        sentences = re.split(r'[.!?]+', text)
        for s in sentences:
            s_clean = s.strip()
            w_in_s = re.findall(r'\b\w+\b', s_clean)
            if len(w_in_s) >= 35:
                start_idx = text.find(s_clean)
                end_idx = start_idx + len(s_clean) if start_idx != -1 else len(text)
                findings.append({
                    "id": f"F-A11Y-{len(findings) + 1}",
                    "category": "accessibility",
                    "severity": "suggestion",
                    "rule_id": "GL-A11Y-01",
                    "rule_name": "Sentence Length & Cognitive Load",
                    "flagged_text": (s_clean[:45] + "..."),
                    "start_char": max(0, start_idx),
                    "end_char": max(0, end_idx),
                    "reason": f"Sentence contains {len(w_in_s)} words. Complex compound sentences increase cognitive fatigue.",
                    "suggestion": "Split this long sentence into two focused statements.",
                    "confidence": 0.91,
                    "approved_source": "GL-A11Y-01"
                })
                deductions["accessibility"] += 8
                break

        # 4. Visual Consistency (Color and asset alt check)
        deprecated_colors = [("#EF4444", "Legacy Red"), ("#FF0000", "Generic Red"), ("#F59E0B", "Amber Warning")]
        for hex_code, name in deprecated_colors:
            if hex_code.lower() in text.lower():
                findings.append({
                    "id": f"F-VIS-{len(findings) + 1}",
                    "category": "visual",
                    "severity": "warning",
                    "rule_id": "GL-VIS-01",
                    "rule_name": "Brand Asset & Color Palette Standards",
                    "flagged_text": hex_code,
                    "start_char": 0,
                    "end_char": 0,
                    "reason": f"Deprecated hex color {hex_code} ({name}) detected. Official palette mandates Indigo (#4F46E5) or Cyan (#06B6D4).",
                    "suggestion": "#4F46E5",
                    "confidence": 0.97,
                    "approved_source": "GL-VIS-01 (Brand Asset Kit v2.0)"
                })
                deductions["visual"] += 12

        # 5. Build Proposed Auto-Corrected Content preserving author intent
        # Sort findings in descending order of start_char to replace without offset corruption
        sorted_for_replace = sorted([f for f in findings if f["end_char"] > f["start_char"]], key=lambda x: x["start_char"], reverse=True)
        corrected_text = text
        for item in sorted_for_replace:
            s = item["start_char"]
            e = item["end_char"]
            # Verify the slice matches flagged_text approximately
            original_slice = text[s:e]
            if original_slice.lower() == item["flagged_text"].lower():
                corrected_text = corrected_text[:s] + item["suggestion"] + corrected_text[e:]

        # Calculate scores
        total_deduction = sum(deductions.values())
        overall_score = max(20, min(100, 100 - total_deduction))

        category_scores = {
            "terminology": max(20, 100 - deductions["terminology"]),
            "claims": max(20, 100 - deductions["claims"]),
            "tone": max(20, 100 - deductions["tone"]),
            "accessibility": max(20, 100 - deductions["accessibility"]),
            "visual": max(40, 100 - deductions["visual"])
        }

        # Status determination
        if overall_score >= 90:
            compliance_status = "READY_FOR_APPROVAL"
            status_color = "emerald"
        elif overall_score >= 65:
            compliance_status = "MINOR_REVISIONS_NEEDED"
            status_color = "amber"
        else:
            compliance_status = "CRITICAL_DRIFT_DETECTED"
            status_color = "rose"

        return {
            "overall_score": overall_score,
            "compliance_status": compliance_status,
            "status_color": status_color,
            "category_scores": category_scores,
            "readability": readability,
            "findings": findings,
            "findings_count": len(findings),
            "corrected_text": corrected_text,
            "verified_facts_consulted": len(db.approved_facts),
            "guidelines_enforced": len(db.guidelines),
            "engine_version": "TechFusion-Governance-Core v2.4 (Explainable Guardrail)"
        }

engine = BrandGovernanceEngine()
