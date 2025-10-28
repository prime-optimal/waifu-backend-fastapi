#!/usr/bin/env python3
"""Test with explicit virtual try-on prompt to force face preservation."""

import asyncio
import json
from pathlib import Path

from src.app.settings import get_settings
from src.clients.ai_provider import AIProviderClient

# Explicit virtual try-on prompt that forces face preservation
explicit_prompt = """VIRTUAL TRY-ON REQUIREMENTS - CRITICAL:

FACE PRESERVATION (MANDATORY):
- Keep the EXACT same face from the user's photo
- Same facial features, same skin tone, same face shape
- Same hair style and hair color
- Same identity - this must be the SAME PERSON
- DO NOT change face, skin, or hair under any circumstances

COSTUME APPLICATION:
- Apply costume elements from reference images ONLY
- Add costume parts, accessories, makeup from references
- Transform outfit while preserving person's identity

TECHNICAL REQUIREMENTS:
- User face is PRIMARY reference - must be preserved exactly
- Costume images are SECONDARY references - for outfit only
- This is virtual try-on, not character creation
- Person should remain recognizable as themselves

VERIFICATION CHECKLIST:
✓ Same face? ✓ Same skin? ✓ Same hair? ✓ Same person?
If any answer is NO, this is NOT virtual try-on."""


async def test_explicit_prompt():
    """Test virtual try-on with explicit face preservation instructions"""

    settings = get_settings()
    client = AIProviderClient(
        base_url=str(settings.ai_provider_url), api_key=settings.ai_provider_api_key
    )

    try:
        # Load test images
        user_image_path = Path("tests/fixtures/test_images/user1.jpeg")
        costume_paths = [
            Path("tests/fixtures/test_images/bowsette-blurred.png"),
            Path("tests/fixtures/test_images/bowsette-crown.jpg"),
        ]

        # Verify images exist
        for img_path in [user_image_path] + costume_paths:
            if not img_path.exists():
                print(f"❌ Image not found: {img_path}")
                return

        print("🎯 TESTING EXPLICIT VIRTUAL TRY-ON PROMPT")
        print("=" * 60)
        print(f"User: {user_image_path}")
        print(f"Costumes: {[str(p) for p in costume_paths]}")
        print()

        for model in ["seedream-v4", "google:4@1"]:
            print(f"Testing with model: {model}")
            result = await client.generate_try_on(
                model_name=model,
                user_image_path=str(user_image_path),
                costume_reference_paths=[str(p) for p in costume_paths],
                prompt=explicit_prompt,
            )

            print("🎉 RESULT:")
            print(f"   Status: {result.status}")
            print(f"   Processing Time: {result.processing_time_ms}ms")

            if result.status == "success" and result.asset_url:
                print(f"   ✅ Generated image URL: {result.asset_url}")

                print()
                print("🔍 VERIFICATION INSTRUCTIONS:")
                print(f"1. Open: {Path(user_image_path).absolute()}")
                print(f"2. Open: {result.asset_url}")
                print("3. Compare: Is it the SAME PERSON?")
                print("4. Check: Same face? Same skin? Same hair?")
                print("5. If YES → Virtual try-on is working!")
                print("6. If NO → AI is still ignoring user image")
            else:
                print(f"   ❌ Failed: {result.error_reason}")
            print("-" * 40)

    except Exception as e:
        print(f"\n💥 EXCEPTION: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_explicit_prompt())
