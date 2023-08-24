"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User
from sqlalchemy.exc import NoResultFound

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_logout(self):
        """Can user add message if logged out"""

        with self.client as c:

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)
            with self.assertRaises(NoResultFound):
                msg = Message.query.one()

            self.assertIn("Sign up",resp.text)    
    
    def test_delete_message(self):
        """Can user delete a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            msg = Message(text="test",user_id=self.testuser.id)
            db.session.add(msg)
            db.session.commit()
            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            with self.assertRaises(NoResultFound):
                Message.query.one()

            self.assertEqual(len(self.testuser.messages),0)

    def test_delete_message_logout(self):
        """Can user delete message when logged out?"""

        with self.client as c:
            # Message made and committed to db
            # No user in session
            msg = Message(text="test",user_id=self.testuser.id)
            db.session.add(msg)
            db.session.commit()

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            self.assertIn("Sign up",resp.text)

    def test_adding_nonuser_message(self):    
        """Can user delete add a message with a different user as other user?
        Not sure if this is a useful test as there isn't a way that another user could do that?"""
        with self.client as c:

            other_user = User.signup(username='other_user',
                          email='other@other.com',
                          password="otherother",
                          image_url=None)
            db.session.commit()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post("/messages/new", data={"text": "Hello","user_id":f"{other_user.id}"}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

    def test_deleting_other_user_message(self):
        with self.client as c:
            other_user = User.signup(username='other_user',
                          email='other@other.com',
                          password="otherother",
                          image_url=None)
            db.session.commit()
            msg = Message(text="other_user")
            other_user.messages.append(msg)
            db.session.commit()
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{msg.id}/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(len(other_user.messages),1)

    def test_message_like(self):
        """Can user like and unlike message?"""
        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            msg = Message(text="test")
            self.testuser.messages.append(msg)
            db.session.commit()

            # user likes message
            resp = c.post(f'/messages/{msg.id}/like')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(len(self.testuser.likes),1)

            # user unlikes message
            resp = c.post(f'/messages/{msg.id}/like')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(len(self.testuser.likes),0)
    
    def test_message_like_logout(self):
        """Can message be like when user is logged out?"""
        with self.client as c:

            msg = Message(text="test")
            self.testuser.messages.append(msg)
            db.session.commit()

            resp = c.post(f'/messages/{msg.id}/like',follow_redirects=True)

            self.assertEqual(resp.status_code,200)
            self.assertEqual(len(self.testuser.likes),0)
            self.assertIn("Sign up",resp.text)           