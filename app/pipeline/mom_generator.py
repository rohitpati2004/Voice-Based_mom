import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class LocalMoMGenerator:
    def __init__(self):
        self._summarizer = None

    def _load_transformer(self):
        if self._summarizer is None:
            try:
                from transformers import pipeline
                logger.info("Initializing local HuggingFace summarization pipeline...")
                self._summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
            except Exception as e:
                logger.warning(f"Transformer model unavailable ({e}). Using robust extractive NLP engine.")
                self._summarizer = "extractive"

    def generate_mom(self, transcript: List[Dict[str, Any]], statistics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates structured Minutes of Meeting (MoM) locally without external LLM APIs.
        """
        if not transcript:
            return {
                "meeting_title": "Audio Meeting Recording",
                "summary": "No spoken text was transcribed from the recording.",
                "key_discussion_points": [],
                "decisions": [],
                "action_items": []
            }

        full_text = " ".join([seg["text"] for seg in transcript])
        
        # 1. Executive Summary Generation
        summary = self._generate_summary(full_text, transcript)

        # 2. Key Discussion Points
        key_points = self._extract_key_points(transcript)

        # 3. Decisions Made
        decisions = self._extract_decisions(transcript)

        # 4. Action Items & Responsibilities
        action_items = self._extract_action_items(transcript)

        return {
            "meeting_title": "Voice Meeting Minutes",
            "summary": summary,
            "key_discussion_points": key_points,
            "decisions": decisions,
            "action_items": action_items
        }

    def _generate_summary(self, full_text: str, transcript: List[Dict[str, Any]]) -> str:
        if len(full_text.strip()) < 50:
            return full_text

        self._load_transformer()

        if self._summarizer != "extractive" and hasattr(self._summarizer, "__call__"):
            try:
                # Limit input text length for Transformer model
                truncated = full_text[:1024]
                summary_output = self._summarizer(truncated, max_length=150, min_length=30, do_sample=False)
                return summary_output[0]["summary_text"]
            except Exception as e:
                logger.warning(f"Summarizer pipeline error: {e}. Switching to extractive NLP.")

        # Extractive Summarization Fallback
        sentences = re.split(r'(?<=[.!?])\s+', full_text)
        if len(sentences) <= 3:
            return full_text

        # Pick key representative sentences across meeting phases
        first = sentences[0]
        mid = sentences[len(sentences) // 2]
        last = sentences[-1]
        
        summary_sentences = list(dict.fromkeys([first, mid, last]))
        return " ".join(summary_sentences)

    def _extract_key_points(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        key_points = []
        topic_keywords = [
            ("Project Architecture & Requirements", ["architecture", "pipeline", "requirement", "system", "design", "module"]),
            ("Language & Speech Processing", ["multilingual", "hindi", "odia", "english", "speech", "asr", "whisper", "diarization"]),
            ("Implementation & Integration", ["code", "integration", "api", "database", "model", "deploy", "build"]),
            ("Testing & Documentation", ["test", "documentation", "sample", "recordings", "report", "action"])
        ]

        categorized = {title: [] for title, _ in topic_keywords}
        categorized["General Discussion"] = []

        for seg in transcript:
            text_lower = seg["text"].lower()
            matched = False
            for title, keywords in topic_keywords:
                if any(kw in text_lower for kw in keywords):
                    categorized[title].append(f"{seg['speaker']} ({seg.get('language', 'En')}): {seg['text']}")
                    matched = True
                    break
            if not matched and len(seg["text"]) > 20:
                categorized["General Discussion"].append(f"{seg['speaker']}: {seg['text']}")

        for title, points in categorized.items():
            if points:
                key_points.append({
                    "topic": title,
                    "points": points[:3]  # Top 3 key points per category
                })

        return key_points

    def _extract_decisions(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        decision_keywords = ["decided", "agreed", "finalized", "approved", "confirm", "will use", "settled", "resolv", "हम तय", "ସିଦ୍ଧାନ୍ତ"]
        decisions = []

        for seg in transcript:
            text_lower = seg["text"].lower()
            if any(kw in text_lower for kw in decision_keywords):
                decisions.append({
                    "speaker": seg["speaker"],
                    "timestamp": f"{int(seg['start']//60):02d}:{int(seg['start']%60):02d}",
                    "decision": seg["text"]
                })

        if not decisions:
            # Generate default structured decisions from key statements if none explicitly matched
            for seg in transcript:
                if any(w in seg["text"].lower() for w in ["will", "must", "target", "complete", "करेंगे", "କରିବା"]):
                    decisions.append({
                        "speaker": seg["speaker"],
                        "timestamp": f"{int(seg['start']//60):02d}:{int(seg['start']%60):02d}",
                        "decision": seg["text"]
                    })

        return decisions[:5]

    def _extract_action_items(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        action_keywords = ["action", "todo", "assign", "will handle", "will complete", "responsible", "by tomorrow", "task", "handle", "manage"]
        action_items = []

        for seg in transcript:
            text_lower = seg["text"].lower()
            if any(kw in text_lower for kw in action_keywords):
                action_items.append({
                    "assignee": seg["speaker"],
                    "task": seg["text"],
                    "status": "Pending",
                    "timestamp": f"{int(seg['start']//60):02d}:{int(seg['start']%60):02d}"
                })

        if not action_items and len(transcript) > 0:
            # Fallback action item extraction from speaker segments containing commitments
            for seg in transcript:
                if len(seg["text"]) > 15:
                    action_items.append({
                        "assignee": seg["speaker"],
                        "task": f"Follow up on statement: '{seg['text']}'",
                        "status": "Pending",
                        "timestamp": f"{int(seg['start']//60):02d}:{int(seg['start']%60):02d}"
                    })

        return action_items[:5]
