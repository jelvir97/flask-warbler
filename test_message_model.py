"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_message_creation(self):       
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        msg = Message(text='This is a test message.',
                      user_id=u.id)
        db.session.add(msg)
        db.session.commit()

        self.assertIsInstance(msg, Message)
        self.assertIn(msg,u.messages)
        self.assertEquals(len(u.messages),1)

    def test_message_like(self):
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        msg = Message(text='This is a test message.',
                      user_id=u.id)
        db.session.add(msg)
        db.session.commit()

        # user likes message
        u.likes.append(msg)
        db.session.commit()

        self.assertEquals(len(u.likes),1)
        self.assertIn(msg,u.likes)

        # user unlikes message
        u.likes.remove(msg)
        db.session.commit()

        self.assertEquals(len(u.likes),0)
        self.assertNotIn(msg,u.likes)