from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter()

BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"


@router.get("/match/{team1}/{team2}")
async def get_latest_match(team1: str, team2: str):
    """
    Returns data about the last match between two teams.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp1 = await client.get(
                f"{BASE_URL}/searchteams.php", params={"t": team1}
            )
            resp2 = await client.get(
                f"{BASE_URL}/searchteams.php", params={"t": team2}
            )

            data1 = resp1.json()
            data2 = resp2.json()

            if not data1.get("teams") or not data2.get("teams"):
                raise HTTPException(
                    status_code=404, detail="One or bothteams not found"
                )

            team1_id = data1["teams"][0]["idTeam"]
            team2_id = data2["teams"][0]["idTeam"]

            # fetch last events
            resp_last = await client.get(
                f"{BASE_URL}/eventslast.php", params={"id": team1_id}
            )
            last_events = resp_last.json().get("results", []) or []

            # find the last match between these teams
            latest_match = next(
                (
                    e
                    for e in last_events
                    if e["idHomeTeam"] == team2_id or
                    e["idAwayTeam"] == team2_id
                ),
                None,
            )

            # if no match found, try next events
            if not latest_match:
                resp_next = await client.get(
                    f"{BASE_URL}/eventsnext.php", params={"id": team1_id}
                )
                next_events = resp_next.json().get("events", []) or []

                latest_match = next(
                    (
                        e
                        for e in next_events
                        if e["idHomeTeam"] == team2_id or
                        e["idAwayTeam"] == team2_id
                    ),
                    None,
                )

            if not latest_match:
                raise HTTPException(
                    status_code=404,
                    detail="No recent or upcoming matches between these teams",
                )

            return {
                "home_team": latest_match["strHomeTeam"],
                "away_team": latest_match["strAwayTeam"],
                "home_score": latest_match["intHomeScore"],
                "away_score": latest_match["intAwayScore"],
                "date_event": latest_match["dateEvent"],
                "stadium": latest_match["strVenue"],
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/{name}")
async def search_team(name: str):
    """
    Returns info about a team by name.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/searchteams.php", params={"t": name}
            )
            data = resp.json()

        if not data.get("teams"):
            raise HTTPException(status_code=404, detail="Team not found")

        teams = [
            {
                "id": t["idTeam"],
                "name": t["strTeam"],
                "country": t.get("strCountry"),
                "league": t.get("strLeague"),
                "formed": t.get("intFormedYear"),
            }
            for t in data["teams"]
        ]
        return {"results": teams}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
