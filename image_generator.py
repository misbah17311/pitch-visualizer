"""
Image Generation Module
Uses OpenAI DALL-E 3 to generate images from engineered prompts.
Supports parallel generation for faster storyboard creation.
"""

import os
import uuid
import requests
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


def generate_image(prompt: str, output_dir: str = "static/images", size: str = "1024x1024") -> dict:
    """
    Generate an image from an engineered prompt using DALL-E 3.

    Args:
        prompt: The engineered image prompt.
        output_dir: Directory to save the generated image.
        size: Image size (1024x1024, 1024x1792, 1792x1024).

    Returns:
        dict with keys: file_path, url, revised_prompt
    """
    os.makedirs(output_dir, exist_ok=True)

    response = _get_client().images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    revised_prompt = response.data[0].revised_prompt

    # Download and save the image locally
    filename = f"panel_{uuid.uuid4().hex[:8]}.png"
    file_path = os.path.join(output_dir, filename)

    img_response = requests.get(image_url, timeout=60)
    img_response.raise_for_status()

    with open(file_path, "wb") as f:
        f.write(img_response.content)

    return {
        "file_path": file_path,
        "filename": filename,
        "url": image_url,
        "revised_prompt": revised_prompt,
    }


def generate_all_images(
    prompts: list[dict],
    output_dir: str = "static/images",
) -> list[dict]:
    """
    Generate images for all engineered prompts in parallel.

    Args:
        prompts: List of dicts from prompt_engineer.engineer_all_prompts().
        output_dir: Directory to save images.

    Returns:
        List of dicts sorted by index with keys: index, original_text,
        engineered_prompt, image_path, image_filename, revised_prompt
    """
    results = [None] * len(prompts)

    def _generate_single(item):
        image = generate_image(
            prompt=item["engineered_prompt"],
            output_dir=output_dir,
        )
        return {
            "index": item["index"],
            "original_text": item["original_text"],
            "engineered_prompt": item["engineered_prompt"],
            "image_path": image["file_path"],
            "image_filename": image["filename"],
            "revised_prompt": image["revised_prompt"],
        }

    with ThreadPoolExecutor(max_workers=len(prompts)) as executor:
        future_to_index = {
            executor.submit(_generate_single, item): item["index"]
            for item in prompts
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            results[idx] = future.result()

    return results
