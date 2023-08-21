"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_repr(self):
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        db.session.add(u)
        db.session.commit()

        self.assertEqual(u.__repr__(),f'<User #{u.id}: testuser, test@test.com>')

    def test_user_follow(self):
        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        u1.following.append(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertTrue(u2.is_followed_by(u1))

        u1.following.remove(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u2.is_followed_by(u1))


    def test_user_creation(self):
        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        self.assertIsInstance(u1, User)

        
        # self.assertNotIsInstance(u2, User)
        with self.assertRaises(IntegrityError):
            u2 = User(
            email="test2@test.com",
            username="testuser2"
            )
            db.session.add(u2)
            db.session.commit()
        
    def test_user_authentication(self):
        u = User.signup(
            email="besttest@test.com",
            username="besttestuser",
            password="HASHED_PASSWORD",
            image_url=None
        )       
        db.session.commit()

        self.assertIsInstance(User.authenticate(username='besttestuser',
                                                password='HASHED_PASSWORD'),
                              User)
        
        # testing w/ invalid username
        self.assertNotIsInstance(User.authenticate(
            username='wrongtestuser',
            password='HASHED_PASSWORD'
        ), User)

        # testing w/ invalid password
        self.assertNotIsInstance(User.authenticate(
            username='besttestuser',
            password='wrong_password'
        ), User)
