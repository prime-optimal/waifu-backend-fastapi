#!/usr/bin/env python3
"""Compare user image with generated results to verify virtual try-on is working."""

import os
from pathlib import Path


def check_images():
    """Check if generated images contain the user's face."""

    test_images_dir = Path("tests/fixtures/test_images")
    generated_dir = Path("generated_images")

    user_image = test_images_dir / "user1.jpeg"
    costume_refs = [
        test_images_dir / "bowsette-blurred.png",
        test_images_dir / "bowsette-crown.jpg",
        test_images_dir / "bowsette-horns.jpg",
        test_images_dir / "bowsette-wig.jpg",
        test_images_dir / "bowsette-front.jpg",
    ]

    generated_images = list(generated_dir.glob("*.png"))

    print("=== IMAGE COMPARISON FOR VIRTUAL TRY-ON VERIFICATION ===\n")

    print(f"👤 USER IMAGE: {user_image}")
    print(f"   File size: {user_image.stat().st_size / 1024:.1f} KB")
    print(f"   Please examine this image to see the user's face\n")

    print(f"🎭 COSTUME REFERENCE IMAGES:")
    for i, ref in enumerate(costume_refs[:3], 1):  # Show first 3
        if ref.exists():
            print(f"   {i}. {ref.name} - {ref.stat().st_size / 1024:.1f} KB")
    print()

    print(f"🎨 GENERATED IMAGES:")
    for img in generated_images:
        print(f"   📸 {img.name} - {img.stat().st_size / 1024:.1f} KB")
    print()

    print("=== VERIFICATION CHECKLIST ===")
    print("1. Look at user1.jpeg - memorize the person's face, hair, skin tone")
    print("2. Look at the generated images")
    print("3. Do the generated images contain the SAME PERSON's face?")
    print("4. Or are they just random people wearing the costume?")
    print()

    print("=== EXPECTED RESULT FOR WORKING VIRTUAL TRY-ON ===")
    print("✅ Generated images should have the SAME FACE as user1.jpeg")
    print("✅ Same hair color, skin tone, facial features")
    print("✅ Only the clothing/background should be different")
    print()

    print("=== WHAT WE'RE SEEING (LIKELY) ===")
    print("❌ Generated images have DIFFERENT people's faces")
    print("❌ Different hair color, skin tone, facial features")
    print("❌ This means the AI is ignoring the user image")
    print()

    print("=== FILES TO EXAMINE ===")
    print(f"User: {user_image.absolute()}")
    for img in generated_images:
        print(f"Generated: {img.absolute()}")

    print("\nOpen these image files in an image viewer to compare!")


if __name__ == "__main__":
    check_images()
