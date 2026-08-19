from backend.main import app
from fastapi.testclient import TestClient


def test_websocket_receives_connected_event():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/1") as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"
            assert "connection_id" in data


def test_websocket_receives_member_joined_event():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/1") as ws:
            connected = ws.receive_json()
            member_joined = ws.receive_json()
            assert connected["type"] == "connected"
            assert member_joined["type"] == "member_joined"
            assert connected["connection_id"] == member_joined["connection_id"]


def test_websocket_receives_others_member_joined_event():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/1") as ws_1:
            ws_1.receive_json()
            ws_1.receive_json()

            with client.websocket_connect("/ws/1") as ws_2:
                connected = ws_2.receive_json()
                ws_2.receive_json()
                member_joined = ws_1.receive_json()
                assert member_joined["type"] == "member_joined"
                assert (
                    member_joined["connection_id"]
                    == connected["connection_id"]
                )


def test_websocket_conversation_id_isolation():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/1") as ws_1:
            ws_1.receive_json()
            ws_1.receive_json()

            with client.websocket_connect("/ws/2") as ws_2:
                connected_ws_2 = ws_2.receive_json()
                ws_2.receive_json()

                ws_1.send_json(
                    {
                        "type": "message",
                        "text": "from_1"
                    }
                )

                ws_2.send_json(
                    {
                        "type": "message",
                        "text": "from_2"
                    }
                )

                event = ws_2.receive_json()
                assert event["type"] == "message"
                assert event["text"] == "from_2"
                assert event["sender_id"] == connected_ws_2["connection_id"]


def test_websocket_broadcasts_message_within_conversation_id():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/1") as ws_1:
            connected_ws_1 = ws_1.receive_json()
            ws_1.receive_json()

            with client.websocket_connect("/ws/1") as ws_2:
                ws_2.receive_json()
                ws_2.receive_json()
                ws_1.receive_json()

                ws_1.send_json(
                    {"type": "message", "text": "hello friend"}
                )

                event = ws_2.receive_json()
                assert event["type"] == "message"
                assert event["sender_id"] == connected_ws_1["connection_id"]
                assert event["text"] == "hello friend"


def test_websocket_invalid_message_text():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/1") as ws:
            ws.receive_json()
            ws.receive_json()

            ws.send_json({"type": "message", "text": ""})

            event = ws.receive_json()
            assert event["type"] == "error"
            assert event["code"] == "invalid_message"
            assert event["detail"] == "Invalid message"


def test_websocket_invalid_message_type():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/1") as ws:
            ws.receive_json()
            ws.receive_json()

            ws.send_json({"type": "typing", "text": "hello friend"})

            event = ws.receive_json()
            assert event["type"] == "error"
            assert event["code"] == "invalid_message"
            assert event["detail"] == "Invalid message"


def test_websocket_receives_member_left_event():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/1") as ws_1:
            ws_1.receive_json()
            ws_1.receive_json()

            with client.websocket_connect("/ws/1") as ws_2:
                connected_ws_2 = ws_2.receive_json()
                ws_2.receive_json()
                ws_1.receive_json()

            event = ws_1.receive_json()
            assert event["type"] == "member_left"
            assert event["connection_id"] == connected_ws_2["connection_id"]


def test_websocket_message_is_saved_to_database():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/1") as ws:
            ws.receive_json()
            ws.receive_json()

            ws.send_json({"type": "message", "text": "persistent_message"})
            event = ws.receive_json()
            assert event["type"] == "message"
            message_id = event["message_id"]

            response = client.get("/conversations/1/messages")
            assert response.status_code == 200
            messages = response.json()

            assert len(messages) == 1
            assert messages[0]["conversation_id"] == 1
            assert messages[0]["text"] == "persistent_message"
            assert messages[0]["id"] == message_id
