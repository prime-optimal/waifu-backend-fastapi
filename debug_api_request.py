#!/usr/bin/env python3
"""Debug script to see exactly what's being sent to the AI API."""

import asyncio
import base64
import json
from pathlib import Path
from typing import Any

from src.app.settings import get_settings
from src.clients.ai_provider import AIProviderClient


class DebugAIProviderClient(AIProviderClient):
    """Extended AI provider client with detailed request/response logging."""

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Override to log the exact request being sent."""
        print(f"\n{'=' * 80}")
        print(f"🔍 API REQUEST DEBUG")
        print(f"{'=' * 80}")
        print(f"URL: {self.client.base_url}{path}")
        print(f"Headers: {self._get_headers()}")
        print(f"\n📤 PAYLOAD:")
        print(json.dumps(payload, indent=2))

        # Log references in detail
        if "references" in payload:
            print(f"\n📎 REFERENCES DETAIL:")
            for i, ref in enumerate(payload["references"]):
                print(f"  {i + 1}. ID: {ref['id']}")
                print(f"     Role: {ref['role']}")
                print(f"     Kind: {ref['kind']}")
                if ref["kind"] == "base64":
                    # Show first 100 chars of base64 data
                    data_preview = (
                        ref["value"][:100] + "..."
                        if len(ref["value"]) > 100
                        else ref["value"]
                    )
                    print(f"     Value: {data_preview}")
                else:
                    print(f"     Value: {ref['value']}")
                print()

        response = await self.client.post(
            path, json=payload, headers=self._get_headers()
        )

        print(f"📥 RESPONSE STATUS: {response.status_code}")
        print(f"📥 RESPONSE HEADERS: {dict(response.headers)}")

        if response.status_code >= 400:
            print(f"📥 ERROR RESPONSE: {response.text}")
            raise Exception(
                f"Service responded with {response.status_code}: {response.text}"
            )

        if not response.text:
            print("📥 EMPTY RESPONSE")
            raise Exception("Empty response from API")

        try:
            response_data = response.json()
            print(f"📥 RESPONSE DATA (first 500 chars): {response.text[:500]}...")
            return response_data
        except json.JSONDecodeError as e:
            print(f"📥 JSON DECODE ERROR: {e}")
            print(f"📥 RAW RESPONSE TEXT: {response.text}")
            raise


async def debug_api_request():
    """Debug the exact API request being sent."""

    # Load configuration
    settings = get_settings()
    api_url = str(settings.ai_provider_url)
    api_key = settings.ai_provider_api_key

    # Load test costume data
    costumes_path = Path("tests/fixtures/test_costumes.json")
    with open(costumes_path) as f:
        test_data = json.load(f)

    costume = test_data["test_costumes"][0]
    test_images_dir = Path("tests/fixtures/test_images")

    # Use user1.jpeg and first 2 costume reference images
    user_image_path = test_images_dir / "user1.jpeg"
    costume_paths = [
        test_images_dir / costume["reference_images"][0],  # bowsette-blurred.png
        test_images_dir / costume["reference_images"][1],  # bowsette-crown.jpg
    ]

    print(f"🖼️  INPUT IMAGES:")
    print(f"   User: {user_image_path}")
    print(f"   Costume 1: {costume_paths[0]}")
    print(f"   Costume 2: {costume_paths[1]}")

    # Create debug client
    client = DebugAIProviderClient(base_url=api_url, api_key=api_key)

    try:
        print(f"\n🎯 TESTING SINGLE MODEL (seedream-v4)")
        print(f"{'=' * 80}")

        result = await client.generate_try_on(
            model_name="seedream-v4",
            user_image_path=str(user_image_path),
            costume_reference_paths=[str(p) for p in costume_paths],
            prompt=costume["prompt"],
            seed=1001,
        )

        print(f"\n🎉 RESULT:")
        print(f"   Status: {result.status}")
        print(f"   Processing Time: {result.processing_time_ms}ms")
        if result.status == "success":
            print(f"   Asset URL length: {len(result.asset_url)} chars")
            # Save the result
            output_dir = Path("generated_images")
            output_dir.mkdir(exist_ok=True)
            filename = "debug_seedream-v4_result.png"
            filepath = output_dir / filename

            import base64

            if result.asset_url.startswith("data:image/png;base64,"):
                base64_data = result.asset_url.split("base64,")[1]
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(base64_data))
                print(f"   ✅ Saved to: {filepath}")
        else:
            print(f"   ❌ Error: {result.error_reason}")

    except Exception as e:
        print(f"\n💥 EXCEPTION: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(debug_api_request())
