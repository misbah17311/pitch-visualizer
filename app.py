"""
The Pitch Visualizer — FastAPI Web Application
Ingests narrative text, segments it, engineers prompts, generates images,
and renders a visual storyboard.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

from segmenter import segment_text
from prompt_engineer import engineer_all_prompts, VISUAL_STYLES, DEFAULT_STYLE
from image_generator import generate_all_images

app = FastAPI(title="The Pitch Visualizer", description="From Words to Storyboard")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
IMAGES_DIR = os.path.join(STATIC_DIR, "images")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main input page."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "styles": VISUAL_STYLES,
        "default_style": DEFAULT_STYLE,
    })


@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, text: str = Form(...), style: str = Form(DEFAULT_STYLE)):
    """Full pipeline: segment → engineer prompts → generate images → render storyboard."""
    if not text.strip():
        return templates.TemplateResponse("index.html", {
            "request": request,
            "styles": VISUAL_STYLES,
            "default_style": DEFAULT_STYLE,
            "error": "Please enter some narrative text.",
        })

    if style not in VISUAL_STYLES:
        style = DEFAULT_STYLE

    # Step 1: Segment the narrative
    segments = segment_text(text)
    if len(segments) < 1:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "styles": VISUAL_STYLES,
            "default_style": DEFAULT_STYLE,
            "error": "Could not segment the text. Please provide at least 3 sentences.",
        })

    # Step 2: Engineer prompts via GPT
    prompts = engineer_all_prompts(segments, style=style, full_text=text)

    # Step 3: Generate images via DALL-E 3
    panels = generate_all_images(prompts, output_dir=IMAGES_DIR)

    # Step 4: Render storyboard
    return templates.TemplateResponse("storyboard.html", {
        "request": request,
        "text": text,
        "style": style,
        "style_name": style.replace("_", " ").title(),
        "panels": panels,
        "total_panels": len(panels),
    })


@app.post("/api/generate")
async def api_generate(text: str = Form(...), style: str = Form(DEFAULT_STYLE)):
    """
    API endpoint for programmatic access.
    Returns JSON with segments, prompts, and image URLs.
    """
    if not text.strip():
        return JSONResponse({"error": "Text input is required."}, status_code=400)

    if style not in VISUAL_STYLES:
        style = DEFAULT_STYLE

    segments = segment_text(text)
    prompts = engineer_all_prompts(segments, style=style, full_text=text)
    panels = generate_all_images(prompts, output_dir=IMAGES_DIR)

    return JSONResponse({
        "text": text,
        "style": style,
        "panels": [
            {
                "index": p["index"],
                "original_text": p["original_text"],
                "engineered_prompt": p["engineered_prompt"],
                "image_url": f"/static/images/{p['image_filename']}",
                "revised_prompt": p["revised_prompt"],
            }
            for p in panels
        ],
    })


@app.get("/api/styles")
async def api_styles():
    """Return available visual styles."""
    return JSONResponse({
        "styles": VISUAL_STYLES,
        "default": DEFAULT_STYLE,
    })
