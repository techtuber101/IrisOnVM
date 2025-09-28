from core.agentpress.tool import ToolResult, openapi_schema, usage_example
from core.sandbox.tool_base import SandboxToolsBase
from core.agentpress.thread_manager import ThreadManager
from core.utils.logger import logger
from typing import List, Dict, Optional
import json
import os
from datetime import datetime
import re
import html
from .presentation_styles_config import get_style_config, get_all_styles

class SandboxPresentationTool(SandboxToolsBase):
    """
    Per-slide HTML presentation tool for creating professional presentations.
    Each slide is managed individually with 1920x1080 dimensions.
    Supports iterative slide creation, editing, and presentation assembly.
    """
    
    def __init__(self, project_id: str, thread_manager: ThreadManager):
        super().__init__(project_id, thread_manager)
        self.workspace_path = "/workspace"
        self.presentations_dir = "presentations"

    async def _ensure_presentations_dir(self):
        """Ensure the presentations directory exists"""
        full_path = f"{self.workspace_path}/{self.presentations_dir}"
        try:
            await self.sandbox.fs.create_folder(full_path, "755")
        except:
            pass

    async def _ensure_presentation_dir(self, presentation_name: str):
        """Ensure a specific presentation directory exists"""
        safe_name = self._sanitize_filename(presentation_name)
        presentation_path = f"{self.workspace_path}/{self.presentations_dir}/{safe_name}"
        try:
            await self.sandbox.fs.create_folder(presentation_path, "755")
        except:
            pass
        return safe_name, presentation_path

    def _sanitize_filename(self, name: str) -> str:
        """Convert presentation name to safe filename"""
        return "".join(c for c in name if c.isalnum() or c in "-_").lower()

    def _get_style_config(self, style_name: str) -> Dict:
        """Get style configuration for a given style name"""
        return get_style_config(style_name)

    def _get_absolute_url(self, file_path: Optional[str]) -> Optional[str]:
        """Construct an absolute sandbox URL for a workspace-relative file path."""
        if not file_path:
            return None

        sandbox_url = getattr(self.sandbox, 'sandbox_url', None) or getattr(self, '_sandbox_url', None)
        if not sandbox_url:
            # Fallback to localhost if sandbox_url is not set
            sandbox_url = 'http://localhost:8082'
            logger.warning(f"Sandbox URL not available, using fallback: {sandbox_url}")

        trimmed_path = file_path
        if trimmed_path.startswith('/workspace/'):
            trimmed_path = trimmed_path[len('/workspace/'):]
        trimmed_path = trimmed_path.lstrip('/')
        return f"{sandbox_url.rstrip('/')}/{trimmed_path}"

    async def _regenerate_presentation_manifest(
        self,
        presentation_name: str,
        safe_name: str,
        presentation_path: str,
        metadata: Dict,
        persist: bool = False
    ) -> tuple[Dict, List[tuple[int, Dict]]]:
        """Rebuild slide ordering metadata and attach useful preview URLs."""

        slides: Dict[str, Dict] = metadata.get("slides", {}) or {}
        sorted_slides = sorted(((int(slide_num), slide_data) for slide_num, slide_data in slides.items()), key=lambda x: x[0])

        presentation_rel_path = f"{self.presentations_dir}/{safe_name}"
        total_slides = len(sorted_slides)
        metadata["total_slides"] = total_slides
        metadata["slides_order"] = [slide_num for slide_num, _ in sorted_slides]
        metadata["presentation_name"] = presentation_name
        metadata.setdefault("title", presentation_name)
        metadata.setdefault("description", "")
        metadata["presentation_path"] = presentation_rel_path
        metadata["metadata_file"] = f"{presentation_rel_path}/metadata.json"
        metadata["metadata_url"] = self._get_absolute_url(metadata["metadata_file"])

        now_iso = datetime.now().isoformat()
        if persist:
            metadata["updated_at"] = now_iso

        regenerated_slides: Dict[str, Dict] = {}
        for index, (slide_num, slide_data) in enumerate(sorted_slides, start=1):
            filename = slide_data.get("filename") or f"slide_{slide_num:02d}.html"
            relative_file_path = slide_data.get("file_path") or f"{presentation_rel_path}/{filename}"

            slide_data.setdefault("title", f"Slide {slide_num}")
            slide_data["filename"] = filename
            slide_data["file_path"] = relative_file_path
            slide_data["preview_url"] = f"/workspace/{relative_file_path}"
            slide_data["absolute_preview_url"] = self._get_absolute_url(relative_file_path)
            slide_data.setdefault("created_at", now_iso)
            if persist:
                slide_data["updated_at"] = now_iso
            else:
                slide_data.setdefault("updated_at", slide_data.get("created_at", now_iso))

            slide_data["slide_number"] = slide_num
            slide_data["position"] = index
            slide_data["previous_slide"] = sorted_slides[index - 2][0] if index > 1 else None
            slide_data["next_slide"] = sorted_slides[index][0] if index < total_slides else None

            regenerated_slides[str(slide_num)] = slide_data

        metadata["slides"] = regenerated_slides

        index_rel_path = f"{presentation_rel_path}/index.html"
        metadata["index_file"] = index_rel_path
        metadata["index_preview_url"] = f"/workspace/{index_rel_path}"
        metadata["index_url"] = self._get_absolute_url(index_rel_path)
        
        # Add absolute URLs for all slides
        for slide_num, slide_data in metadata["slides"].items():
            if "file_path" in slide_data:
                slide_data["absolute_preview_url"] = self._get_absolute_url(slide_data["file_path"])
        
        if persist:
            metadata["index_generated_at"] = now_iso

        return metadata, sorted_slides

    async def _generate_presentation_index(
        self,
        presentation_name: str,
        safe_name: str,
        presentation_path: str,
        metadata: Dict,
        slide_items: List[tuple[int, Dict]]
    ) -> None:
        """Create or update an interactive index.html viewer for a presentation."""

        title = metadata.get("title", presentation_name)
        total_slides = metadata.get("total_slides", len(slide_items))
        index_file_path = f"{presentation_path}/index.html"

        if not slide_items:
            empty_html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>{html.escape(title)} – Presentation Viewer</title>
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 40px;
            background: linear-gradient(135deg, #f6f8fb 0%, #eef1f8 100%);
            color: #0f172a;
        }}
        .empty-state {{
            max-width: 620px;
            margin: 0 auto;
            background: white;
            border-radius: 24px;
            padding: 48px;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
            text-align: center;
        }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 1rem;
            letter-spacing: -0.02em;
        }}
        p {{
            margin-bottom: 0.75rem;
            color: #475569;
            font-size: 1rem;
        }}
        .cta {{
            margin-top: 1.5rem;
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: #2563eb;
            color: white;
            border-radius: 999px;
            text-decoration: none;
            font-weight: 600;
            letter-spacing: 0.01em;
        }}
    </style>
</head>
<body>
    <div class=\"empty-state\">
        <h1>{html.escape(title)}</h1>
        <p>No slides have been created yet.</p>
        <p>Use the <code>create_slide</code> tool to add your first slide to this presentation.</p>
        <a class=\"cta\" href=\"#\">Start creating</a>
    </div>
</body>
</html>"""
            await self.sandbox.fs.upload_file(empty_html.encode("utf-8"), index_file_path)
            return

        slide_buttons = []
        for idx, (slide_num, slide_data) in enumerate(slide_items):
            slide_title = html.escape(slide_data.get("title", f"Slide {slide_num}"))
            filename = html.escape(slide_data.get("filename", f"slide_{slide_num:02d}.html"))
            slide_buttons.append(
                f"<button class=\"slide-item\" data-index=\"{idx}\" data-src=\"{filename}\">"
                f"<span class=\"slide-number\">{slide_num:02d}</span>"
                f"<span class=\"slide-title\">{slide_title}</span>"
                "</button>"
            )

        slides_payload = [
            {
                "filename": slide_data.get("filename", f"slide_{slide_num:02d}.html"),
                "title": slide_data.get("title", f"Slide {slide_num}"),
                "number": slide_num
            }
            for slide_num, slide_data in slide_items
        ]

        slides_json = json.dumps(slides_payload)
        first_slide_filename = html.escape(slide_items[0][1].get("filename", ""))

        index_html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>{html.escape(title)} – Presentation Viewer</title>
    <style>
        :root {{
            color-scheme: light;
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f8fafc;
            color: #0f172a;
        }}
        header {{
            padding: 24px 32px;
            background: white;
            border-bottom: 1px solid rgba(15, 23, 42, 0.08);
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
            position: sticky;
            top: 0;
            z-index: 5;
        }}
        header h1 {{
            margin: 0;
            font-size: 1.75rem;
            letter-spacing: -0.02em;
        }}
        header p {{
            margin: 8px 0 0;
            color: #475569;
        }}
        .layout {{
            flex: 1;
            display: flex;
            gap: 0;
            min-height: 0;
        }}
        aside {{
            width: 320px;
            border-right: 1px solid rgba(15, 23, 42, 0.08);
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(12px);
            padding: 20px;
            overflow-y: auto;
        }}
        .slide-list {{
            display: grid;
            gap: 12px;
        }}
        .slide-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            border-radius: 12px;
            background: white;
            border: 1px solid rgba(15, 23, 42, 0.06);
            cursor: pointer;
            text-align: left;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
            transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
        }}
        .slide-item:hover {{
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
        }}
        .slide-item.active {{
            border-color: #2563eb;
            box-shadow: 0 16px 30px rgba(37, 99, 235, 0.18);
        }}
        .slide-number {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 12px;
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            color: white;
            font-weight: 600;
            letter-spacing: 0.04em;
        }}
        .slide-title {{
            font-weight: 600;
            color: #0f172a;
            letter-spacing: -0.01em;
        }}
        main {{
            flex: 1;
            padding: 24px 32px 32px;
            display: flex;
            flex-direction: column;
            min-height: 0;
        }}
        .viewer {{
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            background: radial-gradient(circle at top, rgba(37, 99, 235, 0.08), rgba(12, 74, 110, 0.04));
            border-radius: 24px;
            border: 1px solid rgba(15, 23, 42, 0.06);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
            padding: 24px;
            overflow: hidden;
            position: relative;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
            border-radius: 16px;
            background: white;
            aspect-ratio: 16 / 9;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.18);
        }}
        .viewer::after {{
            content: '';
            position: absolute;
            inset: 18px;
            border-radius: 20px;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.55);
            pointer-events: none;
        }}
        .controls {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 18px;
            gap: 12px;
        }}
        .controls button {{
            border: none;
            border-radius: 12px;
            padding: 10px 18px;
            background: #2563eb;
            color: white;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            letter-spacing: 0.02em;
            box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2);
            transition: transform 0.12s ease, box-shadow 0.12s ease;
        }}
        .controls button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 12px 26px rgba(37, 99, 235, 0.25);
        }}
        .controls button.secondary {{
            background: white;
            color: #2563eb;
            border: 1px solid rgba(37, 99, 235, 0.35);
            box-shadow: none;
        }}
        @media (max-width: 1024px) {{
            aside {{
                display: none;
            }}
            .layout {{
                flex-direction: column;
            }}
            main {{
                padding: 16px;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>{html.escape(title)}</h1>
        <p>{total_slides} slide{'s' if total_slides != 1 else ''} • Generated {datetime.now().strftime('%b %d, %Y')}</p>
    </header>
    <div class=\"layout\">
        <aside>
            <div class=\"slide-list\">
                {''.join(slide_buttons)}
            </div>
        </aside>
        <main>
            <div class=\"viewer\">
                <iframe id=\"slide-frame\" src=\"{first_slide_filename}\" allowfullscreen></iframe>
            </div>
            <div class=\"controls\">
                <button id=\"prev-btn\" class=\"secondary\">◀ Previous</button>
                <div id=\"status\">Slide 1 of {total_slides}</div>
                <button id=\"next-btn\">Next ▶</button>
            </div>
        </main>
    </div>
    <script>
        const slides = {slides_json};
        const slideFrame = document.getElementById('slide-frame');
        const status = document.getElementById('status');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const slideButtons = Array.from(document.querySelectorAll('.slide-item'));
        let currentIndex = 0;

        function updateViewer(index) {{
            const slide = slides[index];
            if (!slide) return;
            slideFrame.src = slide.filename;
            status.textContent = `Slide ${{index + 1}} of ${{slides.length}}`;
            slideButtons.forEach(btn => btn.classList.remove('active'));
            if (slideButtons[index]) {{
                slideButtons[index].classList.add('active');
            }}
            currentIndex = index;
            prevBtn.disabled = index === 0;
            nextBtn.disabled = index === slides.length - 1;
        }}

        slideButtons.forEach((button, index) => {{
            button.addEventListener('click', () => updateViewer(index));
        }});

        prevBtn.addEventListener('click', () => {{
            if (currentIndex > 0) {{
                updateViewer(currentIndex - 1);
            }}
        }});

        nextBtn.addEventListener('click', () => {{
            if (currentIndex < slides.length - 1) {{
                updateViewer(currentIndex + 1);
            }}
        }});

        document.addEventListener('keydown', (event) => {{
            if (event.key === 'ArrowLeft') {{
                prevBtn.click();
            }} else if (event.key === 'ArrowRight') {{
                nextBtn.click();
            }}
        }});

        updateViewer(0);
    </script>
</body>
</html>"""

        await self.sandbox.fs.upload_file(index_html.encode("utf-8"), index_file_path)

    def _create_slide_html(self, slide_content: str, slide_number: int, total_slides: int, presentation_title: str, style: str = "default") -> str:
        """Create a complete HTML document for a single slide with proper 1920x1080 dimensions"""
        
        # Get style configuration
        style_config = self._get_style_config(style)
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{presentation_title} - Slide {slide_number}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="{style_config['font_import']}" rel="stylesheet">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1"></script>
    <style>
        /* Base styling and 1920x1080 slide container */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            margin: 0;
            padding: 0;
            font-family: {style_config['font_family']};
            color: {style_config['text_color']};
        }}
        
        .slide-container {{
            /* CRITICAL: Standard presentation dimensions */
            width: 1920px;
            height: 1080px;
            max-width: 100vw;
            max-height: 100vh;
            position: relative;
            background: {style_config['background']};
            color: {style_config['text_color']};
            overflow: hidden;
            
            /* Auto-scale to fit viewport while maintaining aspect ratio */
            transform-origin: center center;
            transform: scale(min(100vw / 1920px, 100vh / 1080px));
        }}
        
        /* Slide number indicator */
        .slide-number {{
            position: absolute;
            bottom: 30px;
            right: 30px;
            font-size: 18px;
            color: {style_config['text_color']};
            opacity: 0.7;
            font-weight: 500;
            z-index: 1000;
        }}
        
        /* Common presentation elements with style theming */
        .slide-title {{
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 30px;
            color: {style_config['primary_color']};
        }}
        
        .slide-subtitle {{
            font-size: 32px;
            margin-bottom: 40px;
            color: {style_config['text_color']};
        }}
        
        .slide-content {{
            font-size: 24px;
            line-height: 1.6;
            color: {style_config['text_color']};
        }}
        
        .accent-bar {{
            width: 100px;
            height: 4px;
            background-color: {style_config['accent_color']};
            margin: 20px 0;
        }}
        
        /* Primary color elements */
        .primary-color {{
            color: {style_config['primary_color']};
        }}
        
        .primary-bg {{
            background-color: {style_config['primary_color']};
        }}
        
        /* Accent color elements */
        .accent-color {{
            color: {style_config['accent_color']};
        }}
        
        .accent-bg {{
            background-color: {style_config['accent_color']};
        }}
        
        /* Style-aware text color */
        .text-color {{
            color: {style_config['text_color']};
        }}
        
        /* Responsive images */
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }}
        
        /* List styling */
        ul, ol {{
            margin: 20px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin: 10px 0;
            font-size: 20px;
            line-height: 1.5;
            color: {style_config['text_color']};
        }}
        
        /* Style-specific enhancements */
        .card {{
            background: {'rgba(255, 255, 255, 0.1)' if 'gradient' in style_config['background'] or style_config['background'].startswith('#1') or style_config['background'].startswith('#0') else 'rgba(0, 0, 0, 0.05)'};
            border-radius: 12px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }}
        
        .highlight {{
            background: {style_config['accent_color']};
            color: {'#FFFFFF' if style_config['accent_color'].startswith('#') else style_config['text_color']};
            padding: 4px 12px;
            border-radius: 6px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="slide-container">
        {slide_content}
        <div class="slide-number">{slide_number}{f" / {total_slides}" if total_slides > 0 else ""}</div>
    </div>
</body>
</html>"""
        return html_template

    async def _load_presentation_metadata(self, presentation_path: str):
        """Load presentation metadata, create if doesn't exist"""
        metadata_path = f"{presentation_path}/metadata.json"
        try:
            metadata_content = await self.sandbox.fs.download_file(metadata_path)
            return json.loads(metadata_content.decode())
        except:
            # Create default metadata
            return {
                "presentation_name": "",
                "title": "Presentation", 
                "description": "",
                "slides": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

    async def _save_presentation_metadata(self, presentation_path: str, metadata: Dict):
        """Save presentation metadata"""
        metadata["updated_at"] = datetime.now().isoformat()
        metadata_path = f"{presentation_path}/metadata.json"
        try:
            await self.sandbox.fs.upload_file(json.dumps(metadata, indent=2).encode(), metadata_path)
            logger.info(f"Successfully saved metadata to {metadata_path}")
        except Exception as e:
            logger.error(f"Failed to save metadata to {metadata_path}: {e}")
            raise

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "create_slide",
            "description": "Create or update a single slide in a presentation. Each slide is saved as a standalone HTML file with 1920x1080 dimensions (16:9 aspect ratio). Perfect for iterative slide creation and editing. Use 'presentation_styles' tool first to see available styles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "presentation_name": {
                        "type": "string",
                        "description": "Name of the presentation (creates folder if doesn't exist)"
                    },
                    "slide_number": {
                        "type": "integer",
                        "description": "Slide number (1-based). If slide exists, it will be updated."
                    },
                    "slide_title": {
                        "type": "string",
                        "description": "Title of this specific slide (for reference and navigation)"
                    },
                    "content": {
                                    "type": "string",
                        "description": "HTML content for the slide body. Should include all styling within the content. The content will be placed inside a 1920x1080 slide container with CSS frameworks (Tailwind, FontAwesome, D3, Chart.js) available. Use professional styling with good typography, spacing, and visual hierarchy. You can use style-aware CSS classes: .primary-color, .primary-bg, .accent-color, .accent-bg, .text-color, .card, .highlight"
                                },
                    "presentation_title": {
                                    "type": "string",
                        "description": "Main title of the presentation (used in HTML title and navigation)",
                        "default": "Presentation"
                    },
                    "style": {
                        "type": "string",
                        "description": "Visual style theme for the slide. Use 'presentation_styles' tool to see all available options. Examples: 'velvet', 'glacier', 'ember', 'sage', 'obsidian', 'coral', 'platinum', 'aurora', 'midnight', 'citrus', or 'default'",
                        "default": "default"
                    }
                },
                "required": ["presentation_name", "slide_number", "slide_title", "content"]
            }
        }
    })
    @usage_example('''
Create individual slides for a presentation about "Modern Web Development":

<function_calls>
<invoke name="create_slide">
<parameter name="presentation_name">modern_web_development</parameter>
<parameter name="slide_number">1</parameter>
<parameter name="slide_title">Title Slide</parameter>
<parameter name="presentation_title">Modern Web Development Trends 2024</parameter>
<parameter name="content"><div style='background: linear-gradient(135deg, #005A9C 0%, #FF6B00 100%); height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; color: white; padding: 80px;'><h1 style='font-size: 72px; font-weight: bold; margin-bottom: 30px;'>Modern Web Development</h1><div style='width: 150px; height: 6px; background: white; margin: 30px auto;'></div><h2 style='font-size: 36px; margin-bottom: 40px; opacity: 0.9;'>Trends & Technologies 2024</h2><p style='font-size: 24px; opacity: 0.8;'>Building Tomorrow's Web Today</p></div></parameter>
</invoke>
</function_calls>

Then create the next slide:

        <function_calls>
<invoke name="create_slide">
<parameter name="presentation_name">modern_web_development</parameter>
<parameter name="slide_number">2</parameter>
<parameter name="slide_title">Frontend Frameworks</parameter>
<parameter name="presentation_title">Modern Web Development Trends 2024</parameter>
<parameter name="content"><div style='display: flex; height: 100%; padding: 0;'><div style='width: 60%; padding: 80px; display: flex; flex-direction: column; justify-content: center;'><h1 style='font-size: 48px; font-weight: bold; color: #005A9C; margin-bottom: 20px;'>Frontend Frameworks</h1><div style='width: 100px; height: 4px; background: #FF6B00; margin-bottom: 40px;'></div><div style='font-size: 22px; line-height: 1.8;'><div style='margin-bottom: 25px; display: flex; align-items: center;'><i class='fab fa-react' style='color: #61DAFB; font-size: 28px; margin-right: 15px;'></i><div><strong>React</strong> - Component-based UI library</div></div><div style='margin-bottom: 25px; display: flex; align-items: center;'><i class='fab fa-vuejs' style='color: #4FC08D; font-size: 28px; margin-right: 15px;'></i><div><strong>Vue.js</strong> - Progressive framework</div></div></div></div><div style='width: 40%; background: #f8f9fa; display: flex; align-items: center; justify-content: center; padding: 40px;'><div style='text-align: center;'><div style='font-size: 64px; margin-bottom: 30px;'>📱</div><h3 style='font-size: 28px; color: #005A9C;'>Modern Tools</h3></div></div></div></parameter>
        </invoke>
        </function_calls>

This approach allows you to:
- Create slides one at a time
- Edit existing slides by using the same slide number
- Build presentations iteratively
- Mix and match different slide designs
- Each slide is a standalone HTML file with full styling
    ''')
    async def create_slide(
        self,
        presentation_name: str,
        slide_number: int,
        slide_title: str,
        content: str,
        presentation_title: str = "Presentation",
        style: str = "default"
    ) -> ToolResult:
        """Create or update a single slide in a presentation"""
        try:
            await self._ensure_sandbox()
            await self._ensure_presentations_dir()
            
            # Validation
            if not presentation_name:
                return self.fail_response("Presentation name is required.")
            
            if slide_number < 1:
                return self.fail_response("Slide number must be 1 or greater.")
            
            if not slide_title:
                return self.fail_response("Slide title is required.")
            
            if not content:
                return self.fail_response("Slide content is required.")
            
            # Ensure presentation directory exists
            safe_name, presentation_path = await self._ensure_presentation_dir(presentation_name)
            
            # Load or create metadata
            metadata = await self._load_presentation_metadata(presentation_path)
            metadata["presentation_name"] = presentation_name
            if presentation_title != "Presentation":  # Only update if explicitly provided
                metadata["title"] = presentation_title
            
            # Create slide HTML
            slide_html = self._create_slide_html(
                slide_content=content,
                slide_number=slide_number,
                total_slides=0,  # Will be updated when regenerating navigation
                presentation_title=presentation_title,
                style=style
            )
            
            # Save slide file
            slide_filename = f"slide_{slide_number:02d}.html"
            slide_path = f"{presentation_path}/{slide_filename}"
            await self.sandbox.fs.upload_file(slide_html.encode(), slide_path)
            
            # Update metadata
            if "slides" not in metadata:
                metadata["slides"] = {}
            
            metadata["slides"][str(slide_number)] = {
                "title": slide_title,
                "filename": slide_filename,
                "file_path": f"{self.presentations_dir}/{safe_name}/{slide_filename}",
                "preview_url": f"/workspace/{self.presentations_dir}/{safe_name}/{slide_filename}",
                "absolute_preview_url": self._get_absolute_url(f"{self.presentations_dir}/{safe_name}/{slide_filename}"),
                "style": style,
                "created_at": datetime.now().isoformat()
            }
            
            metadata, ordered_slides = await self._regenerate_presentation_manifest(
                presentation_name,
                safe_name,
                presentation_path,
                metadata,
                persist=True
            )

            # Persist metadata with refreshed manifest
            try:
                await self._save_presentation_metadata(presentation_path, metadata)
                logger.info(f"Successfully saved metadata for presentation '{presentation_name}'")
            except Exception as e:
                logger.error(f"Failed to save metadata for presentation '{presentation_name}': {e}")
                # Continue execution but log the error

            index_error: Optional[str] = None
            try:
                await self._generate_presentation_index(
                    presentation_name,
                    safe_name,
                    presentation_path,
                    metadata,
                    ordered_slides
                )
            except Exception as idx_error:
                logger.warning(f"Failed to generate presentation index for '{presentation_name}': {idx_error}")
                index_error = str(idx_error)

            slide_metadata = metadata["slides"][str(slide_number)]
            presentation_rel_path = f"{self.presentations_dir}/{safe_name}"
            metadata_file = metadata.get("metadata_file")

            response_payload = {
                "message": f"Slide {slide_number} '{slide_title}' created/updated successfully with '{style}' style",
                "presentation_name": presentation_name,
                "presentation_path": presentation_rel_path,
                "slide_number": slide_number,
                "slide_title": slide_title,
                "slide_file": slide_metadata.get("file_path"),
                "preview_url": slide_metadata.get("preview_url"),
                "absolute_preview_url": slide_metadata.get("absolute_preview_url"),
                "style": style,
                "total_slides": metadata.get("total_slides", len(metadata.get("slides", {}))),
                "index_file": metadata.get("index_file"),
                "index_url": metadata.get("index_url"),
                "metadata_file": metadata_file,
                "metadata_url": metadata.get("metadata_url"),
                "sandbox_url": getattr(self.sandbox, 'sandbox_url', 'http://localhost:8082'),
                "note": "Slide saved as standalone HTML file with 1920x1080 dimensions"
            }

            if index_error:
                response_payload["index_generation_error"] = index_error

            return self.success_response(response_payload)
            
        except Exception as e:
            return self.fail_response(f"Failed to create slide: {str(e)}")

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "list_slides",
            "description": "List all slides in a presentation, showing their titles and order",
            "parameters": {
                "type": "object",
                "properties": {
                    "presentation_name": {
                        "type": "string",
                        "description": "Name of the presentation to list slides for"
                    }
                },
                "required": ["presentation_name"]
            }
        }
    })
    async def list_slides(self, presentation_name: str) -> ToolResult:
        """List all slides in a presentation"""
        try:
            await self._ensure_sandbox()
            
            if not presentation_name:
                return self.fail_response("Presentation name is required.")
            
            safe_name = self._sanitize_filename(presentation_name)
            presentation_path = f"{self.workspace_path}/{self.presentations_dir}/{safe_name}"
            
            # Load metadata
            metadata = await self._load_presentation_metadata(presentation_path)
            metadata, ordered_slides = await self._regenerate_presentation_manifest(
                presentation_name,
                safe_name,
                presentation_path,
                metadata,
                persist=False
            )

            if not metadata.get("slides"):
                return self.success_response({
                    "message": f"No slides found in presentation '{presentation_name}'",
                    "presentation_name": presentation_name,
                    "slides": [],
                    "total_slides": 0,
                    "presentation_path": f"{self.presentations_dir}/{safe_name}",
                    "metadata_file": metadata.get("metadata_file"),
                    "metadata_url": metadata.get("metadata_url"),
                    "index_file": metadata.get("index_file"),
                    "index_url": metadata.get("index_url")
                })
            
            slides_info = []
            for slide_num, slide_data in ordered_slides:
                slides_info.append({
                    "slide_number": slide_num,
                    "title": slide_data.get("title"),
                    "filename": slide_data.get("filename"),
                    "preview_url": slide_data.get("preview_url"),
                    "absolute_preview_url": slide_data.get("absolute_preview_url"),
                    "style": slide_data.get("style"),
                    "position": slide_data.get("position"),
                    "created_at": slide_data.get("created_at"),
                    "updated_at": slide_data.get("updated_at"),
                    "next_slide": slide_data.get("next_slide"),
                    "previous_slide": slide_data.get("previous_slide")
                })

            # Ensure metadata enhancements are persisted for legacy decks
            try:
                await self._save_presentation_metadata(presentation_path, metadata)
            except Exception as save_error:
                logger.warning(f"Unable to persist presentation metadata refresh for '{presentation_name}': {save_error}")

            return self.success_response({
                "message": f"Found {len(slides_info)} slides in presentation '{presentation_name}'",
                "presentation_name": presentation_name,
                "presentation_title": metadata.get("title", "Presentation"),
                "slides": slides_info,
                "total_slides": len(slides_info),
                "presentation_path": f"{self.presentations_dir}/{safe_name}",
                "metadata_file": metadata.get("metadata_file"),
                "metadata_url": metadata.get("metadata_url"),
                "index_file": metadata.get("index_file"),
                "index_url": metadata.get("index_url")
            })
            
        except Exception as e:
            return self.fail_response(f"Failed to list slides: {str(e)}")

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "delete_slide",
            "description": "Delete a specific slide from a presentation",
            "parameters": {
                "type": "object",
                "properties": {
                    "presentation_name": {
                        "type": "string",
                        "description": "Name of the presentation"
                    },
                    "slide_number": {
                        "type": "integer",
                        "description": "Slide number to delete (1-based)"
                    }
                },
                "required": ["presentation_name", "slide_number"]
            }
        }
    })
    async def delete_slide(self, presentation_name: str, slide_number: int) -> ToolResult:
        """Delete a specific slide from a presentation"""
        try:
            await self._ensure_sandbox()
            
            if not presentation_name:
                return self.fail_response("Presentation name is required.")
            
            if slide_number < 1:
                return self.fail_response("Slide number must be 1 or greater.")
            
            safe_name = self._sanitize_filename(presentation_name)
            presentation_path = f"{self.workspace_path}/{self.presentations_dir}/{safe_name}"
            
            # Load metadata
            metadata = await self._load_presentation_metadata(presentation_path)
            
            if not metadata.get("slides") or str(slide_number) not in metadata["slides"]:
                return self.fail_response(f"Slide {slide_number} not found in presentation '{presentation_name}'")
            
            # Get slide info before deletion
            slide_info = metadata["slides"][str(slide_number)]
            slide_filename = slide_info["filename"]
            
            # Delete slide file
            slide_path = f"{presentation_path}/{slide_filename}"
            try:
                await self.sandbox.fs.delete_file(slide_path)
            except:
                pass  # File might not exist
            
            # Remove from metadata
            del metadata["slides"][str(slide_number)]
            
            metadata, ordered_slides = await self._regenerate_presentation_manifest(
                presentation_name,
                safe_name,
                presentation_path,
                metadata,
                persist=True
            )

            await self._save_presentation_metadata(presentation_path, metadata)

            index_error: Optional[str] = None
            try:
                await self._generate_presentation_index(
                    presentation_name,
                    safe_name,
                    presentation_path,
                    metadata,
                    ordered_slides
                )
            except Exception as idx_error:
                logger.warning(f"Failed to refresh presentation index after deleting slide from '{presentation_name}': {idx_error}")
                index_error = str(idx_error)
            
            response_payload = {
                "message": f"Slide {slide_number} '{slide_info['title']}' deleted successfully",
                "presentation_name": presentation_name,
                "deleted_slide": slide_number,
                "deleted_title": slide_info['title'],
                "remaining_slides": len(metadata.get("slides", {})),
                "total_slides": metadata.get("total_slides", 0),
                "presentation_path": f"{self.presentations_dir}/{safe_name}",
                "metadata_file": metadata.get("metadata_file"),
                "metadata_url": metadata.get("metadata_url"),
                "index_file": metadata.get("index_file"),
                "index_url": metadata.get("index_url")
            }

            if index_error:
                response_payload["index_generation_error"] = index_error

            return self.success_response(response_payload)
            
        except Exception as e:
            return self.fail_response(f"Failed to delete slide: {str(e)}")



    @openapi_schema({
        "type": "function",
        "function": {
            "name": "presentation_styles",
            "description": "Get available presentation styles with their descriptions and visual characteristics. Use this to show users different style options before creating slides.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    })
    async def presentation_styles(self) -> ToolResult:
        """Get available presentation styles with descriptions and examples"""
        try:
            styles = get_all_styles()
            
            return self.success_response({
                "message": f"Found {len(styles)} presentation styles available",
                "styles": styles,
                "usage_tip": "Choose a style and use it with the 'style' parameter in create_slide"
            })
            
        except Exception as e:
            return self.fail_response(f"Failed to get presentation styles: {str(e)}")

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "export_presentation",
            "description": "Export a presentation to a downloadable format (currently PPTX). Generates the latest slides manifest before exporting so the deck matches the current workspace state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "presentation_name": {
                        "type": "string",
                        "description": "Name of the presentation to export"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["pptx"],
                        "description": "Export format. Currently only 'pptx' is supported.",
                        "default": "pptx"
                    }
                },
                "required": ["presentation_name"]
            }
        }
    })
    async def export_presentation(self, presentation_name: str, format: str = "pptx") -> ToolResult:
        """Convert the HTML presentation into a downloadable PPTX package."""
        try:
            await self._ensure_sandbox()

            if format.lower() != "pptx":
                return self.fail_response("Only PPTX export is supported at this time.")

            if not presentation_name:
                return self.fail_response("Presentation name is required.")

            safe_name = self._sanitize_filename(presentation_name)
            presentation_path = f"{self.workspace_path}/{self.presentations_dir}/{safe_name}"

            metadata = await self._load_presentation_metadata(presentation_path)
            if not metadata.get("slides"):
                return self.fail_response(f"Presentation '{presentation_name}' has no slides to export.")

            metadata, ordered_slides = await self._regenerate_presentation_manifest(
                presentation_name,
                safe_name,
                presentation_path,
                metadata,
                persist=True
            )

            await self._save_presentation_metadata(presentation_path, metadata)

            try:
                await self._generate_presentation_index(
                    presentation_name,
                    safe_name,
                    presentation_path,
                    metadata,
                    ordered_slides
                )
            except Exception as idx_error:
                logger.warning(f"Failed to refresh presentation index before export for '{presentation_name}': {idx_error}")

            payload = json.dumps({
                "presentation_path": presentation_path,
                "download": False
            })

            curl_cmd = (
                "curl -s -X POST 'http://localhost:8080/presentation/convert-to-pptx' "
                "-H 'Content-Type: application/json' "
                f"-d '{payload}'"
            )

            response = await self.sandbox.process.exec(curl_cmd, timeout=180)
            if response.exit_code != 0:
                logger.error(f"PPTX export command failed: {response}")
                return self.fail_response(f"PPTX export failed with exit code {response.exit_code}")

            try:
                export_result = json.loads(response.result)
            except json.JSONDecodeError as decode_error:
                logger.error(f"Failed to parse PPTX export response: {response.result}")
                return self.fail_response(f"PPTX export returned invalid JSON: {decode_error}")

            if not export_result.get("success"):
                return self.fail_response(export_result.get("detail") or export_result.get("message") or "PPTX export failed")

            pptx_rel_url = export_result.get("pptx_url")
            pptx_filename = export_result.get("filename")
            pptx_absolute_url = self._get_absolute_url(pptx_rel_url)

            export_record = {
                "format": "pptx",
                "filename": pptx_filename,
                "pptx_url": pptx_rel_url,
                "absolute_url": pptx_absolute_url,
                "exported_at": datetime.now().isoformat()
            }
            metadata.setdefault("exports", []).append(export_record)
            metadata["last_export"] = export_record
            await self._save_presentation_metadata(presentation_path, metadata)

            return self.success_response({
                "message": export_result.get("message", "PPTX generated successfully"),
                "presentation_name": presentation_name,
                "total_slides": export_result.get("total_slides"),
                "pptx_path": pptx_rel_url,
                "pptx_filename": pptx_filename,
                "pptx_url": pptx_absolute_url or pptx_rel_url,
                "index_url": metadata.get("index_url"),
                "metadata_url": metadata.get("metadata_url"),
                "exports_recorded": len(metadata.get("exports", []))
            })

        except Exception as e:
            logger.error(f"Unexpected error exporting presentation '{presentation_name}': {e}", exc_info=True)
            return self.fail_response(f"Failed to export presentation: {str(e)}")

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "list_presentations",
            "description": "List all available presentations in the workspace",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    })
    async def list_presentations(self) -> ToolResult:
        """List all presentations in the workspace"""
        try:
            await self._ensure_sandbox()
            presentations_path = f"{self.workspace_path}/{self.presentations_dir}"
            
            try:
                files = await self.sandbox.fs.list_files(presentations_path)
                presentations = []
                
                for file_info in files:
                    if file_info.is_directory:
                        directory_path = f"{presentations_path}/{file_info.name}"
                        metadata = await self._load_presentation_metadata(directory_path)
                        metadata, ordered_slides = await self._regenerate_presentation_manifest(
                            metadata.get("presentation_name", file_info.name),
                            file_info.name,
                            directory_path,
                            metadata,
                            persist=False
                        )

                        try:
                            await self._save_presentation_metadata(directory_path, metadata)
                        except Exception as save_error:
                            logger.warning(f"Unable to persist metadata refresh for presentation '{file_info.name}': {save_error}")

                        first_slide = ordered_slides[0][1] if ordered_slides else None
                        presentations.append({
                            "folder": file_info.name,
                            "title": metadata.get("title", "Unknown Title"),
                            "description": metadata.get("description", ""),
                            "total_slides": metadata.get("total_slides", len(metadata.get("slides", {}))),
                            "created_at": metadata.get("created_at", "Unknown"),
                            "updated_at": metadata.get("updated_at", "Unknown"),
                            "index_url": metadata.get("index_url"),
                            "metadata_url": metadata.get("metadata_url"),
                            "presentation_path": f"{self.presentations_dir}/{file_info.name}",
                            "primary_preview_url": first_slide.get("absolute_preview_url") if first_slide else None,
                            "primary_preview_path": first_slide.get("preview_url") if first_slide else None
                        })
                
                return self.success_response({
                    "message": f"Found {len(presentations)} presentations",
                    "presentations": presentations,
                    "presentations_directory": f"/workspace/{self.presentations_dir}"
                })
                
            except Exception as e:
                return self.success_response({
                    "message": "No presentations found",
                    "presentations": [],
                    "presentations_directory": f"/workspace/{self.presentations_dir}",
                    "note": "Create your first slide using create_slide"
                })
                
        except Exception as e:
            return self.fail_response(f"Failed to list presentations: {str(e)}")

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "delete_presentation",
            "description": "Delete an entire presentation and all its files",
            "parameters": {
                "type": "object",
                "properties": {
                    "presentation_name": {
                        "type": "string",
                        "description": "Name of the presentation to delete"
                    }
                },
                "required": ["presentation_name"]
            }
        }
    })
    async def delete_presentation(self, presentation_name: str) -> ToolResult:
        """Delete a presentation and all its files"""
        try:
            await self._ensure_sandbox()
            
            if not presentation_name:
                return self.fail_response("Presentation name is required.")
            
            safe_name = self._sanitize_filename(presentation_name)
            presentation_path = f"{self.workspace_path}/{self.presentations_dir}/{safe_name}"
            
            try:
                await self.sandbox.fs.delete_folder(presentation_path)
                return self.success_response({
                    "message": f"Presentation '{presentation_name}' deleted successfully",
                    "deleted_path": f"{self.presentations_dir}/{safe_name}"
                })
            except Exception as e:
                return self.fail_response(f"Presentation '{presentation_name}' not found or could not be deleted: {str(e)}")
                
        except Exception as e:
            return self.fail_response(f"Failed to delete presentation: {str(e)}")
