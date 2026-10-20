import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activities(monkeypatch):
    test_activities = {
        "Robotics": {
            "description": "Build and program robots",
            "schedule": "Mondays, 3:30 PM",
            "max_participants": 10,
            "participants": ["alex@example.com"],
        },
        "Open Studio": {
            "description": "Make art together",
            "schedule": "Fridays, 3:30 PM",
            "max_participants": 12,
            "participants": [],
        },
    }
    monkeypatch.setattr(app_module, "activities", test_activities)
    return test_activities


@pytest.fixture
def client(activities):
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_current_activities(client, activities):
    # Arrange
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_participant(client, activities):
    # Arrange
    email = "sam@example.com"

    # Act
    response = client.post(
        "/activities/Robotics/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Signed up sam@example.com for Robotics"}
    assert activities["Robotics"]["participants"] == [
        "alex@example.com",
        email,
    ]


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    # Act
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "sam@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_for_duplicate_participant(client, activities):
    # Arrange
    participants_before = activities["Robotics"]["participants"].copy()

    # Act
    response = client.post(
        "/activities/Robotics/signup",
        params={"email": "alex@example.com"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities["Robotics"]["participants"] == participants_before


def test_unregister_removes_participant(client, activities):
    # Arrange
    email = "alex@example.com"

    # Act
    response = client.delete(
        "/activities/Robotics/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Unregistered alex@example.com from Robotics"}
    assert activities["Robotics"]["participants"] == []


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    # Act
    response = client.delete(
        "/activities/Unknown/signup",
        params={"email": "alex@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_unregistered_participant(client):
    # Arrange
    # Act
    response = client.delete(
        "/activities/Robotics/signup",
        params={"email": "not-signed-up@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_removes_all_duplicate_entries(client, activities):
    # Arrange
    email = "alex@example.com"
    activities["Robotics"]["participants"].append(email)

    # Act
    response = client.delete(
        "/activities/Robotics/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email not in activities["Robotics"]["participants"]