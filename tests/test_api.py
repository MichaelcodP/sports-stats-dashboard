import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()


async def test_api():
    api_key = os.getenv("THESPORTSDB_API_KEY")
    print(f"Current API key: {api_key}")

    base_url = "https://www.thesportsdb.com/api/v1/json/3"

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test searchteams endpoint
        print("\nTesting searchteams.php with Arsenal...")

        # Without API key
        try:
            response = await client.get(
                f"{base_url}/searchteams.php", params={"t": "Arsenal"}
            )
            print(f"Without API key - Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {data}")
            else:
                print(f"Response text: {response.text}")
        except Exception as e:
            print(f"Error without API key: {e}")

        # With API key (even if placeholder)
        try:
            params = {"t": "Arsenal"}
            if api_key:
                params["APIkey"] = api_key
            response = await client.get(f"{base_url}/searchteams.php", params=params)
            print(f"With API key - Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {data}")
            else:
                print(f"Response text: {response.text}")
        except Exception as e:
            print(f"Error with API key: {e}")


if __name__ == "__main__":
    asyncio.run(test_api())
