"""
Prompt Engineering Module
Uses OpenAI GPT to transform plain narrative text segments into
rich, visually descriptive image generation prompts.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

client = None


def _get_client() -> OpenAI:
    """Lazy-initialize the OpenAI client."""
    global client
    if client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Set it with: export OPENAI_API_KEY=your_key_here"
            )
        client = OpenAI(api_key=api_key)
    return client


# Available visual styles for user selection
VISUAL_STYLES = {
    "cinematic": "cinematic photography, dramatic lighting, film grain, shallow depth of field, 35mm lens",
    "digital_art": "digital art, vibrant colors, clean lines, high detail, modern illustration",
    "watercolor": "delicate watercolor painting, soft edges, gentle color washes, artistic, hand-painted feel",
    "comic_book": "comic book style, bold outlines, halftone dots, dynamic composition, speech bubbles optional",
    "photorealistic": "photorealistic, ultra HD, 8K resolution, natural lighting, lifelike detail",
    "minimalist": "minimalist illustration, flat design, limited color palette, clean geometric shapes",
    "oil_painting": "classic oil painting, rich textures, warm tones, Renaissance-inspired, gallery quality",
    "anime": "anime style, Japanese animation, expressive characters, vivid backgrounds, Studio Ghibli inspired",
}

DEFAULT_STYLE = "cinematic"

# Consistency suffix appended to all prompts for visual coherence across panels
CONSISTENCY_SUFFIX = "consistent color palette, cohesive visual style, same artistic tone throughout the series"


def engineer_prompt(
    segment_text: str,
    segment_index: int,
    total_segments: int,
    style: str = DEFAULT_STYLE,
    narrative_context: str = "",
) -> str:
    """
    Transform a plain text segment into a rich, visually descriptive
    image generation prompt using GPT.

    Args:
        segment_text: The original narrative text segment.
        segment_index: Index of this segment (for scene sequencing).
        total_segments: Total number of segments (for context).
        style: Visual style key from VISUAL_STYLES.
        narrative_context: The full original text for contextual understanding.

    Returns:
        An engineered image prompt string.
    """
    style_description = VISUAL_STYLES.get(style, VISUAL_STYLES[DEFAULT_STYLE])

    system_prompt = f"""You are an expert visual prompt engineer for AI image generation.
Your task is to transform a narrative text segment into a detailed, cinematic image generation prompt.

Rules:
1. DO NOT reproduce the original text verbatim. Transform it into a visual scene description.
2. Include: subject, action, setting/environment, lighting, mood/atmosphere, camera angle.
3. Be specific about colors, textures, and spatial composition.
4. The output should be a SINGLE paragraph — the image prompt only. No explanations.
5. Keep it under 120 words.
6. This is panel {segment_index + 1} of {total_segments} in a visual storyboard — maintain narrative flow.

Visual style to apply: {style_description}
Consistency requirement: {CONSISTENCY_SUFFIX}"""

    user_message = f"""Full narrative context:
\"{narrative_context}\"

Transform this specific segment (panel {segment_index + 1} of {total_segments}) into a visual image prompt:
\"{segment_text}\""""

    response = _get_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=200,
        temperature=0.8,
    )

    engineered = response.choices[0].message.content.strip()

    # Append style and consistency keywords if not already present
    if style_description.split(",")[0].strip().lower() not in engineered.lower():
        engineered += f" Style: {style_description}."

    return engineered


def engineer_all_prompts(
    segments: list[dict],
    style: str = DEFAULT_STYLE,
    full_text: str = "",
) -> list[dict]:
    """
    Engineer prompts for all segments in parallel.

    Args:
        segments: List of segment dicts from segmenter.
        style: Visual style key.
        full_text: Full original narrative text.

    Returns:
        List of dicts sorted by index with keys: index, original_text, engineered_prompt
    """
    results = [None] * len(segments)

    def _engineer_single(seg):
        prompt = engineer_prompt(
            segment_text=seg["text"],
            segment_index=seg["index"],
            total_segments=len(segments),
            style=style,
            narrative_context=full_text,
        )
        return {
            "index": seg["index"],
            "original_text": seg["text"],
            "engineered_prompt": prompt,
        }

    with ThreadPoolExecutor(max_workers=len(segments)) as executor:
        future_to_index = {
            executor.submit(_engineer_single, seg): seg["index"]
            for seg in segments
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            results[idx] = future.result()

    return results
