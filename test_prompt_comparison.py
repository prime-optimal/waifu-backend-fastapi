#!/usr/bin/env python3
"""Compare original vs explicit prompt for virtual try-on."""

import asyncio
import base64
from pathlib import Path

from src.app.settings import get_settings
from src.clients.ai_provider import AIProviderClient

# Original simple prompt
original_prompt = "Virtual try-on with the costume references"

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


async def compare_prompts():
    """Compare original vs explicit prompt effectiveness"""

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

        print("🔬 PROMPT COMPARISON TEST")
        print("=" * 60)
        print(f"User: {user_image_path}")
        print(f"Costumes: {[str(p) for p in costume_paths]}")
        print(f"Model: google:4@1 (chosen for better performance)")
        print()

        prompts_to_test = [
            ("Original Simple Prompt", original_prompt),
            ("Explicit Face Preservation Prompt", explicit_prompt),
        ]

        results = []

        for prompt_name, prompt_text in prompts_to_test:
            print(f"🧪 Testing: {prompt_name}")
            print(f"📝 Prompt: {prompt_text[:100]}...")
            print()

            result = await client.generate_try_on(
                model_name="google:4@1",
                user_image_path=str(user_image_path),
                costume_reference_paths=[str(p) for p in costume_paths],
                prompt=prompt_text,
            )

            print("🎉 RESULT:")
            print(f"   Status: {result.status}")
            print(f"   Processing Time: {result.processing_time_ms}ms")

            if result.status == "success" and result.asset_url:
                # Save the image for comparison
                filename = f"comparison_{prompt_name.lower().replace(' ', '_')}.png"
                output_path = Path("generated_images") / filename

                # Extract base64 data and save
                if result.asset_url.startswith("data:image/"):
                    header, encoded = result.asset_url.split(",", 1)
                    image_data = base64.b64decode(encoded)
                    output_path.write_bytes(image_data)
                    print(f"   ✅ Saved to: {output_path}")
                    print(f"   File size: {len(image_data) / 1024:.1f} KB")

                results.append(
                    {
                        "name": prompt_name,
                        "status": result.status,
                        "time": result.processing_time_ms,
                        "file": output_path,
                    }
                )
            else:
                print(f"   ❌ Failed: {result.error_reason}")
                results.append(
                    {
                        "name": prompt_name,
                        "status": result.status,
                        "time": result.processing_time_ms,
                        "file": None,
                    }
                )

            print("-" * 40)

        # Summary comparison
        print("\n📊 COMPARISON SUMMARY:")
        print("=" * 60)

        for result in results:
            status_emoji = "✅" if result["status"] == "success" else "❌"
            print(f"{status_emoji} {result['name']}")
            print(f"   Status: {result['status']}")
            print(f"   Time: {result['time']}ms")
            if result["file"]:
                print(f"   File: {result['file']}")
            print()

        print("🔍 MANUAL VERIFICATION INSTRUCTIONS:")
        print("1. Open the original user image:")
        print(f"   {user_image_path.absolute()}")
        print()
        print("2. Compare generated images:")
        for result in results:
            if result["file"]:
                print(f"   {result['name']}: {result['file'].absolute()}")
        print()
        print("3. CRITICAL QUESTIONS:")
        print("   ✓ Which one preserves the face better?")
        print("   ✓ Which one maintains the same person?")
        print("   ✓ Which one actually performs virtual try-on?")
        print("   ✓ Is the explicit prompt making a difference?")

    except Exception as e:
        print(f"\n💥 EXCEPTION: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(compare_prompts())
