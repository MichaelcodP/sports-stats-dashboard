from app.services.mock_data import MockSportsData


def test_mock_data():
    # Test getting mock matches
    matches = MockSportsData.get_mock_matches("133604", 3)

    print("Mock matches data:")
    for i, match in enumerate(matches):
        print(f"Match {i}:")
        print(f"  Home: {match['strHomeTeam']}")
        print(f"  Away: {match['strAwayTeam']}")
        print(
            f"  Home Score: {match['intHomeScore']} (type: {type(match['intHomeScore'])})"
        )
        print(
            f"  Away Score: {match['intAwayScore']} (type: {type(match['intAwayScore'])})"
        )
        print()


if __name__ == "__main__":
    test_mock_data()
