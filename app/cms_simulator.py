from typing import Dict, Any, List
from app.engine import engine

class CMSIntegrationSimulator:
    """
    Real-Time CMS & Browser Extensions / In-Context Simulation
    (Round 3 Delivered Improvement 3).
    Demonstrates frictionless brand governance inside Google Docs, Figma, and WordPress.
    Provides non-intrusive floating guardrail pills and 1-click inline corrections.
    """

    PLATFORM_PROFILES = {
        "google_docs": {
            "name": "Google Docs Workspace Add-on",
            "icon": "ph-file-text",
            "mode": "Live Document Sidebar & Floating Guardrail Pill",
            "latency_target": "< 15ms inline checking"
        },
        "figma": {
            "name": "Figma Design System Plugin",
            "icon": "ph-figma-logo",
            "mode": "Canvas Node Inspector & Design Lint Guard",
            "latency_target": "< 10ms frame inspection"
        },
        "wordpress": {
            "name": "WordPress / Gutenberg Block Guard",
            "icon": "ph-globe-hemisphere-west",
            "mode": "Pre-publish Validation Gate & Block Warning",
            "latency_target": "< 20ms save interception"
        }
    }

    def __init__(self):
        pass

    def check_in_context(self, text: str, platform: str = "google_docs", element_type: str = "body") -> Dict[str, Any]:
        """Performs instantaneous inline checking tailored to the host CMS environment."""
        profile = self.PLATFORM_PROFILES.get(platform, self.PLATFORM_PROFILES["google_docs"])
        
        # Run core review engine
        review = engine.review_content(text, title=f"In-Context CMS Draft ({profile['name']})")
        
        # Build non-intrusive inline widget pills
        inline_annotations = []
        for idx, f in enumerate(review["findings"]):
            inline_annotations.append({
                "annotation_id": f"INLINE-{idx + 1:02d}",
                "flagged_text": f["flagged_text"],
                "start_char": f["start_char"],
                "end_char": f["end_char"],
                "severity": f["severity"],
                "rule_name": f["rule_name"],
                "pill_label": f"Replace with: \"{f['suggestion']}\"",
                "suggestion": f["suggestion"],
                "citation": f["approved_source"],
                "reason": f["reason"]
            })

        can_publish = review["overall_score"] >= 80

        return {
            "platform": platform,
            "platform_profile": profile,
            "element_type": element_type,
            "overall_score": review["overall_score"],
            "can_publish": can_publish,
            "publish_gate_message": "Ready to publish without brand drift" if can_publish else "Brand drift detected: Fix high-severity issues before publishing.",
            "corrected_text": review["corrected_text"],
            "inline_annotations": inline_annotations,
            "findings_count": len(inline_annotations),
            "simulated_latency_ms": 7.4
        }

cms_simulator = CMSIntegrationSimulator()
