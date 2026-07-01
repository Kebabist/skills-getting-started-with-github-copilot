from copy import deepcopy
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from app import app, activities


client = TestClient(app)


def _reset_activities(snapshot):
    activities.clear()
    activities.update(deepcopy(snapshot))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


def test_signup_adds_participant_and_rejects_duplicates():
    snapshot = deepcopy(activities)

    try:
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Signed up newstudent@mergington.edu for Chess Club"
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

        duplicate_response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )

        assert duplicate_response.status_code == 400
        assert duplicate_response.json()["detail"] == "Student already signed up for this activity"
    finally:
        _reset_activities(snapshot)


def test_signup_returns_404_for_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_deletes_signed_up_student():
    snapshot = deepcopy(activities)

    try:
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "michael@mergington.edu"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Removed michael@mergington.edu from Chess Club"
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
    finally:
        _reset_activities(snapshot)


def test_remove_participant_returns_404_when_not_signed_up():
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "missing@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"