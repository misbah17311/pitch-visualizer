# The Pitch Visualizer

**From Words to Storyboard — AI-Powered Visual Storytelling**

A service that ingests a block of narrative text, deconstructs it into key scenes, generates rich image prompts via GPT, creates images via DALL-E 3, and presents the result as a multi-panel visual storyboard.

---

## Features

- **Narrative Segmentation**: Breaks text into logical scenes using spaCy NLP
- **LLM-Powered Prompt Engineering**: GPT transforms plain sentences into rich, cinematic image prompts (not verbatim)
- **AI Image Generation**: DALL-E 3 creates a unique image for each scene
- **Visual Storyboard**: Beautiful HTML page displaying panels with images and captions
- **User-Selectable Styles**: 8 visual styles (cinematic, digital art, watercolor, comic book, photorealistic, minimalist, oil painting, anime)
- **Visual Consistency**: Style keywords and consistency suffix appended to every prompt for cohesive panels
- **Dynamic Web UI**: Loading spinner, animated panel reveal, expandable prompt details
- **REST API**: Programmatic access via JSON endpoint

## Available Visual Styles

| Style | Description |
|-------|-------------|
| Cinematic | Dramatic lighting, film grain, shallow depth of field |
| Digital Art | Vibrant colors, clean lines, modern illustration |
| Watercolor | Soft edges, gentle color washes, hand-painted feel |
| Comic Book | Bold outlines, halftone dots, dynamic composition |
| Photorealistic | Ultra HD, natural lighting, lifelike detail |
| Minimalist | Flat design, limited color palette, geometric shapes |
| Oil Painting | Rich textures, warm tones, Renaissance-inspired |
| Anime | Japanese animation, expressive characters, Ghibli-inspired |

---

## Setup & Installation

### Prerequisites

- **Python 3.8+**
- **OpenAI API key** (for GPT prompt engineering + DALL-E 3 image generation)

### Step-by-Step Instructions

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd pitch-visualizer
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Download the spaCy language model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **Set your OpenAI API key**:
   ```bash
   # Option A: Environment variable
   export OPENAI_API_KEY=your_key_here

   # Option B: Copy .env.example and fill in your key
   cp .env.example .env
   # Then edit .env with your key
   ```

   > Get your API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

5. **Run the application**:
   ```bash
   python -m uvicorn app:app --host 0.0.0.0 --port 8001
   ```
   Then open [http://localhost:8001](http://localhost:8001) in your browser.

---

## Usage

### Web Interface

1. Open the web UI at `http://localhost:8001`
2. Paste your narrative text (e.g., a customer success story or sales pitch)
3. Select a visual style from the 8 options
4. Click **"Generate Storyboard"**
5. Wait for processing (segmentation → prompt engineering → image generation)
6. View your storyboard with images, captions, and expandable prompt details

### API

**POST `/api/generate`**

```bash
curl -X POST http://localhost:8001/api/generate \
  -d "text=A small bakery was struggling. They partnered with our platform. Within months, sales tripled." \
  -d "style=watercolor"
```

**Response:**
```json
{
  "text": "...",
  "style": "watercolor",
  "panels": [
    {
      "index": 0,
      "original_text": "A small bakery was struggling.",
      "engineered_prompt": "A quaint, weathered bakery on a quiet street corner...",
      "image_url": "/static/images/panel_abc12345.png",
      "revised_prompt": "..."
    }
  ]
}
```

**GET `/api/styles`** — Returns all available visual styles.

---

## Design Choices

### Narrative Segmentation: Why spaCy?

spaCy's sentence segmentation is linguistically aware — it handles abbreviations, decimal points, and edge cases better than simple regex splitting. The segmenter also supports clause-level splitting for texts with fewer sentences, ensuring we meet the 3+ segment requirement.

### Prompt Engineering Methodology

The core challenge is translating narrative text into **visually descriptive** prompts. Our approach:

1. **GPT as a visual translator**: Each text segment is sent to GPT-4o-mini with a system prompt that instructs it to act as a "visual prompt engineer." It must include subject, action, setting, lighting, mood, and camera angle.

2. **No verbatim reproduction**: The system prompt explicitly forbids using the original text directly. GPT must transform it into a scene description.

3. **Contextual awareness**: The full narrative is provided alongside each segment so GPT understands the overall story arc and maintains narrative flow across panels.

4. **Style injection**: The selected visual style keywords are included in the system prompt, ensuring every generated prompt carries the chosen aesthetic.

5. **Consistency enforcement**: A consistency suffix ("consistent color palette, cohesive visual style, same artistic tone") is appended to every prompt, encouraging DALL-E 3 to produce visually harmonious panels.

### Visual Consistency Across Panels

Achieving consistency is addressed at three levels:
- **Prompt-level**: Style keywords + consistency suffix in every prompt
- **Context-level**: Full narrative provided to GPT so it understands the story's visual progression
- **Model-level**: DALL-E 3's prompt-following capability naturally maintains style when given consistent descriptors

### API Key Management

The application requires a single API key: `OPENAI_API_KEY`. This key is used for:
- GPT-4o-mini (prompt engineering): ~200 tokens per segment
- DALL-E 3 (image generation): 1 image per segment

**Cost estimate**: ~$0.15–0.25 per storyboard (3-5 panels).

The key is read from the environment variable and never stored in code or logged. See `.env.example` for the expected format.

---

## Project Structure

```
pitch-visualizer/
├── app.py                  # FastAPI web application
├── segmenter.py            # spaCy-based narrative segmentation
├── prompt_engineer.py      # GPT-powered prompt engineering
├── image_generator.py      # DALL-E 3 image generation
├── requirements.txt        # Python dependencies
├── .env.example            # API key template
├── .gitignore
├── templates/
│   ├── index.html          # Input page with style selector
│   └── storyboard.html     # Storyboard result page
└── static/
    └── images/             # Generated panel images (auto-created)
```

## Tech Stack

- **Python 3.8+**
- **spaCy** — NLP-based narrative segmentation
- **OpenAI GPT-4o-mini** — LLM-powered prompt engineering
- **OpenAI DALL-E 3** — AI image generation
- **FastAPI** — Web framework and REST API
- **Jinja2** — HTML templating
- **Uvicorn** — ASGI server
