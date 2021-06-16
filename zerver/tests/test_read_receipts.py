import orjson

from zerver.actions.create_user import do_reactivate_user
from zerver.actions.users import do_deactivate_user
from zerver.lib.test_classes import ZulipTestCase


class TestReadReceipts(ZulipTestCase):
    def mark_message_read(self, message_id: int) -> None:
        result = self.client_post(
            "/json/messages/flags",
            {"messages": orjson.dumps([message_id]).decode(), "op": "add", "flag": "read"},
        )
        self.assert_json_success(result)

    def test_stream_message(self) -> None:
        hamlet = self.example_user("hamlet")
        othello = self.example_user("othello")

        message_id = self.send_stream_message(othello, "Verona", "read receipts")
        self.login("hamlet")

        result = self.client_get(f"/json/messages/{message_id}/read_receipts")
        self.assert_json_success(result)
        self.assertTrue(hamlet.id not in result.json()["user_ids"])

        self.mark_message_read(message_id)

        result = self.client_get(f"/json/messages/{message_id}/read_receipts")
        self.assert_json_success(result)
        self.assertTrue(hamlet.id in result.json()["user_ids"])

        sender_id = othello.id
        self.assertTrue(sender_id not in result.json()["user_ids"])

    def test_personal_message(self) -> None:
        hamlet = self.example_user("hamlet")
        othello = self.example_user("othello")

        message_id = self.send_personal_message(othello, hamlet)
        self.login("hamlet")

        result = self.client_get(f"/json/messages/{message_id}/read_receipts")
        self.assert_json_success(result)
        self.assertTrue(hamlet.id not in result.json()["user_ids"])

        self.mark_message_read(message_id)

        result = self.client_get(f"/json/messages/{message_id}/read_receipts")
        self.assert_json_success(result)
        self.assertTrue(hamlet.id in result.json()["user_ids"])

        sender_id = othello.id
        self.assertTrue(sender_id not in result.json()["user_ids"])

    def test_huddle_message(self) -> None:
        hamlet = self.example_user("hamlet")
        othello = self.example_user("othello")
        cordelia = self.example_user("cordelia")

        message_id = self.send_huddle_message(othello, [hamlet, cordelia])
        self.login("hamlet")

        result = self.client_get(f"/json/messages/{message_id}/read_receipts")
        self.assert_json_success(result)
        self.assertTrue(hamlet.id not in result.json()["user_ids"])

        self.mark_message_read(message_id)

        result = self.client_get(f"/json/messages/{message_id}/read_receipts")
        self.assert_json_success(result)
        self.assertTrue(hamlet.id in result.json()["user_ids"])

    def test_inaccessible_stream_message(self) -> None:
        othello = self.example_user("othello")

        private_stream = "private stream"
        self.make_stream(stream_name=private_stream, invite_only=True)
        self.subscribe(othello, private_stream)

        message_id = self.send_stream_message(othello, private_stream, "read receipts")

        self.login("hamlet")
        result = self.client_get(f"/json/messages/{message_id}/read_receipts")
        self.assert_json_error(result, "Invalid message(s)")

    def test_filter_deactivated_users(self) -> None:
        hamlet = self.example_user("hamlet")
        othello = self.example_user("othello")

        message_id = self.send_stream_message(othello, "Verona", "read receipts")

        # Login as hamlet and mark message as read.
        self.login("hamlet")
        self.mark_message_read(message_id)
        self.logout()

        # Login as cordelia and make sure hamlet is in read receipts before deactivation.
        self.login("cordelia")
        result = self.client_get(f"/json/messages/{message_id}/read_receipts")
        self.assert_json_success(result)
        self.assertTrue(hamlet.id in result.json()["user_ids"])

        # Deactivate hamlet and verify hamlet is not in read receipts.
        do_deactivate_user(hamlet, acting_user=None)
        result = self.client_get(f"/json/messages/{message_id}/read_receipts")
        self.assert_json_success(result)
        self.assertTrue(hamlet.id not in result.json()["user_ids"])

        # Reactivate hamlet and verify hamlet appears again in read recipts.
        do_reactivate_user(hamlet, acting_user=None)
        result = self.client_get(f"/json/messages/{message_id}/read_receipts")
        self.assert_json_success(result)
        self.assertTrue(hamlet.id in result.json()["user_ids"])

    def test_send_read_receipts_privacy_setting(self) -> None:
        hamlet = self.example_user("hamlet")
        othello = self.example_user("othello")
        cordelia = self.example_user("cordelia")

        message_id = self.send_stream_message(othello, "Verona", "read receipts")

        self.login("hamlet")
        self.mark_message_read(message_id)
        self.logout()

        self.login("cordelia")
        self.mark_message_read(message_id)
        self.logout()

        self.login("aaron")
        result = self.client_get(f"/json/messages/{message_id}/read_receipts")
        self.assert_json_success(result)
        self.assertIn(hamlet.id, result.json()["user_ids"])
        self.assertIn(cordelia.id, result.json()["user_ids"])

        # Disable read receipts setting; confirm Cordelia no longer appears.
        cordelia.send_read_receipts = False
        cordelia.save()

        self.login("aaron")
        result = self.client_get(f"/json/messages/{message_id}/read_receipts")
        self.assert_json_success(result)
        self.assertIn(hamlet.id, result.json()["user_ids"])
        self.assertNotIn(cordelia.id, result.json()["user_ids"])
