"""
Image Generation for Mindrian using Gemini Imagen 3
Generates images from text prompts using Google's Imagen models.
"""

import os
import io
import base64
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from google import genai
from google.genai import types

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")

# Available models
IMAGEN_MODELS = {
    "fast": "gemini-2.0-flash-exp",  # Fast, efficient for quick generations
    "quality": "imagen-3.0-generate-002",  # Higher quality output
}

# Default model
DEFAULT_MODEL = "fast"

# Aspect ratio options
ASPECT_RATIOS = {
    "square": "1:1",
    "landscape": "16:9",
    "portrait": "9:16",
    "wide": "21:9",
    "photo": "4:3",
}

# Image size options
IMAGE_SIZES = {
    "small": "1024x1024",
    "medium": "1536x1536",
    "large": "2048x2048",
}

# Gemini client singleton
_client = None


def get_client():
    """Get or create Gemini client."""
    global _client
    if _client is None and GOOGLE_API_KEY:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


async def generate_image(
    prompt: str,
    model: str = DEFAULT_MODEL,
    aspect_ratio: str = "square",
    negative_prompt: Optional[str] = None,
    style_preset: Optional[str] = None,
) -> Tuple[Optional[bytes], Optional[str], Dict[str, Any]]:
    """
    Generate an image from a text prompt using Gemini Imagen.

    Args:
        prompt: Text description of the image to generate
        model: Model to use ("fast" or "quality")
        aspect_ratio: Aspect ratio ("square", "landscape", "portrait", "wide", "photo")
        negative_prompt: Things to avoid in the image
        style_preset: Optional style hint (e.g., "photorealistic", "illustration", "3d render")

    Returns:
        Tuple of (image_bytes, mime_type, metadata)
        Returns (None, None, error_metadata) on failure
    """
    client = get_client()
    if not client:
        return None, None, {"error": "Gemini client not configured. Check GOOGLE_API_KEY."}

    # Build the full prompt
    full_prompt = prompt
    if style_preset:
        full_prompt = f"{style_preset} style: {prompt}"
    if negative_prompt:
        full_prompt += f". Avoid: {negative_prompt}"

    # Get aspect ratio
    ratio = ASPECT_RATIOS.get(aspect_ratio, "1:1")

    metadata = {
        "prompt": prompt,
        "full_prompt": full_prompt,
        "model": model,
        "aspect_ratio": ratio,
        "style_preset": style_preset,
        "negative_prompt": negative_prompt,
        "timestamp": datetime.utcnow().isoformat(),
    }

    try:
        # Use the flash model with image generation capability
        model_name = IMAGEN_MODELS.get(model, IMAGEN_MODELS["fast"])

        # For gemini-2.0-flash-exp, we use a different approach
        if "flash" in model_name or "gemini" in model_name:
            # Use multimodal generation with image output
            response = client.models.generate_content(
                model=model_name,
                contents=f"Generate an image: {full_prompt}",
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )

            # Extract image from response
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data
                        image_bytes = image_data.data
                        mime_type = image_data.mime_type or "image/png"

                        metadata["success"] = True
                        metadata["size_bytes"] = len(image_bytes)
                        return image_bytes, mime_type, metadata

            # Check if there's text response (model might explain why it can't generate)
            text_response = ""
            if response.text:
                text_response = response.text

            metadata["error"] = f"No image generated. Model response: {text_response[:200] if text_response else 'Empty response'}"
            return None, None, metadata

        else:
            # For dedicated imagen model
            response = client.models.generate_images(
                model=model_name,
                prompt=full_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=ratio,
                ),
            )

            if response.generated_images:
                image = response.generated_images[0]
                image_bytes = image.image.image_bytes
                mime_type = "image/png"

                metadata["success"] = True
                metadata["size_bytes"] = len(image_bytes)
                return image_bytes, mime_type, metadata

            metadata["error"] = "No image generated"
            return None, None, metadata

    except Exception as e:
        error_msg = str(e)
        metadata["error"] = error_msg
        metadata["success"] = False

        # Provide helpful error messages
        if "safety" in error_msg.lower() or "blocked" in error_msg.lower():
            metadata["user_message"] = "The prompt was blocked by safety filters. Please try a different description."
        elif "quota" in error_msg.lower() or "rate" in error_msg.lower():
            metadata["user_message"] = "Rate limit reached. Please wait a moment and try again."
        elif "not found" in error_msg.lower() or "not supported" in error_msg.lower():
            metadata["user_message"] = "Image generation model not available. Please try again later."
        else:
            metadata["user_message"] = f"Image generation failed: {error_msg[:100]}"

        return None, None, metadata


async def generate_image_variations(
    prompt: str,
    count: int = 2,
    model: str = DEFAULT_MODEL,
    aspect_ratio: str = "square",
) -> List[Tuple[Optional[bytes], Optional[str], Dict[str, Any]]]:
    """
    Generate multiple image variations from a prompt.

    Args:
        prompt: Text description
        count: Number of variations (1-4)
        model: Model to use
        aspect_ratio: Aspect ratio

    Returns:
        List of (image_bytes, mime_type, metadata) tuples
    """
    count = min(max(count, 1), 4)  # Limit to 1-4
    results = []

    for i in range(count):
        # Add slight variation to prompt
        varied_prompt = prompt if i == 0 else f"{prompt} (variation {i+1})"
        result = await generate_image(varied_prompt, model, aspect_ratio)
        results.append(result)

    return results


def save_image_to_temp(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """
    Save image bytes to a temporary file.

    Args:
        image_bytes: Raw image data
        mime_type: MIME type of the image

    Returns:
        Path to the temporary file
    """
    ext = ".png" if "png" in mime_type else ".jpg" if "jpeg" in mime_type or "jpg" in mime_type else ".webp"

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
        f.write(image_bytes)
        return f.name


def image_to_base64(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """
    Convert image bytes to base64 data URL.

    Args:
        image_bytes: Raw image data
        mime_type: MIME type

    Returns:
        Base64 data URL string
    """
    b64 = base64.b64encode(image_bytes).decode('utf-8')
    return f"data:{mime_type};base64,{b64}"


def detect_image_generation_intent(message: str) -> Tuple[bool, Optional[str]]:
    """
    Detect if a message is requesting image generation.

    Args:
        message: User message text

    Returns:
        Tuple of (is_image_request, extracted_prompt)
    """
    message_lower = message.lower().strip()

    # Direct commands
    generation_triggers = [
        "generate an image",
        "create an image",
        "draw me",
        "draw a",
        "make an image",
        "generate image",
        "create image",
        "make a picture",
        "visualize",
        "illustrate",
        "/imagine",
        "/generate",
        "/draw",
    ]

    for trigger in generation_triggers:
        if trigger in message_lower:
            # Extract the prompt after the trigger
            idx = message_lower.find(trigger)
            prompt = message[idx + len(trigger):].strip()
            # Clean up common prefixes
            for prefix in ["of ", "a ", "an ", ": ", "that shows "]:
                if prompt.lower().startswith(prefix):
                    prompt = prompt[len(prefix):]
            return True, prompt if prompt else None

    # Check for "of" pattern: "image of X", "picture of X"
    image_of_patterns = ["image of", "picture of", "illustration of", "drawing of", "photo of"]
    for pattern in image_of_patterns:
        if pattern in message_lower:
            idx = message_lower.find(pattern)
            prompt = message[idx + len(pattern):].strip()
            return True, prompt if prompt else None

    return False, None


def get_style_presets() -> Dict[str, str]:
    """Get available style presets with descriptions."""
    return {
        "photorealistic": "Realistic photograph style",
        "illustration": "Digital illustration style",
        "watercolor": "Watercolor painting style",
        "oil_painting": "Oil painting style",
        "3d_render": "3D rendered style",
        "anime": "Anime/manga style",
        "sketch": "Pencil sketch style",
        "pixel_art": "Pixel art style",
        "minimalist": "Minimalist, clean style",
        "vintage": "Vintage/retro style",
    }


def is_image_generation_configured() -> bool:
    """Check if image generation is configured."""
    return bool(GOOGLE_API_KEY)
