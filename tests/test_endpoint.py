import asyncio
import httpx


async def test_endpoint():
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                "http://localhost:8001/api/analyze/team/Arsenal"
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("✅ Success!")
                print(f"Team: {data.get('team_name')}")
                print(f"Matches: {len(data.get('matches', []))}")
                print(f"Analysis length: {len(data.get('analysis', ''))}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")


if __name__ == "__main__":
    asyncio.run(test_endpoint())
