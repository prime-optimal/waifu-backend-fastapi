"""Standalone script to verify database connection."""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app.settings import get_settings  # noqa: E402
from src.db.database import Database  # noqa: E402


async def main() -> int:
    """Verify database connection and print results."""
    settings = get_settings()

    print(f"Database URL: {settings.database_url}")
    print(f"Environment: {settings.environment}")
    print()

    db = Database(str(settings.database_url))

    try:
        print("Attempting to connect to database...")
        result = await db.verify_connection()

        if result["success"]:
            print("✅ Database connection successful!")
            return 0
        else:
            print(f"❌ Database connection failed: {result['error']}")
            return 1
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return 1
    finally:
        await db.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
