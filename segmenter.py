"""
Narrative Segmentation Module
Uses spaCy to break input text into logical scenes/segments.
"""

import spacy

nlp = spacy.load("en_core_web_sm")


def segment_text(text: str, min_segments: int = 3) -> list[dict]:
    """
    Break a block of narrative text into logical segments.

    Uses spaCy sentence segmentation and merges very short sentences
    to ensure meaningful visual scenes.

    Args:
        text: Input narrative text (paragraph of 3-5 sentences).
        min_segments: Minimum number of segments to produce.

    Returns:
        List of dicts with keys: index, text, sentence_count
    """
    doc = nlp(text.strip())
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    if not sentences:
        return []

    # If we already have enough sentences, each becomes a segment
    if len(sentences) >= min_segments:
        return [
            {"index": i, "text": s, "sentence_count": 1}
            for i, s in enumerate(sentences)
        ]

    # If fewer sentences than min_segments, try splitting on clauses
    # (semicolons, em-dashes, colons, or conjunctions)
    segments = []
    for sent in sentences:
        parts = _split_clauses(sent)
        segments.extend(parts)

    # Ensure at least min_segments
    if len(segments) < min_segments:
        # Return whatever we have — the text is just too short
        return [
            {"index": i, "text": s, "sentence_count": 1}
            for i, s in enumerate(segments)
        ]

    return [
        {"index": i, "text": s.strip(), "sentence_count": 1}
        for i, s in enumerate(segments) if s.strip()
    ]


def _split_clauses(sentence: str) -> list[str]:
    """Split a sentence into clauses on semicolons, em-dashes, or colons."""
    import re
    parts = re.split(r'[;:—–]|\s-\s', sentence)
    # Only split if we get meaningful parts (>10 chars each)
    meaningful = [p.strip() for p in parts if len(p.strip()) > 10]
    if len(meaningful) >= 2:
        return meaningful
    return [sentence]
