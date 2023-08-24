"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User
from sqlalchemy.exc import NoResultFound,IntegrityError
from psycopg2.errors import UniqueViolation

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
        db.session.rollback()
        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser1 = User.signup(username="testuser1",
                                    email="test1@test.com",
                                    password="testuser1",
                                    image_url=None)
        
        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)

        db.session.commit()

    def test_user_signup(self):
        """Test User Signup"""

        with self.client as c:
            
            resp = c.post("/signup", data={"username": "testuser3",
                                           "password":"testuser3",
                                           "email":"test3@test.com",
                                           "image_url":None})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            users = User.query.all()
            self.assertEqual(len(users),3)
            self.assertEqual(users[2].username,"testuser3")

    def test_user_signup_duplicate(self):
        """Test user sign up if username is taken"""

        with self.client as c:
            
            resp = c.post("/signup", data={"username": "testuser2",
                                           "password":"testuser3",
                                           "email":"test3@test.com",
                                           "image_url":None},
                                           follow_redirects=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Username already taken",resp.text)

    def test_user_follow(self):
        """Test user follow/unfollow"""
        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY]= self.testuser1.id 
            # test follow
            resp = c.post(f'/users/follow/{self.testuser2.id}')

            self.assertEqual(resp.status_code,302)
            self.assertEqual(len(self.testuser1.following),1)
            self.assertEqual(len(self.testuser2.followers),1)
            
            #  test unfollow
            resp = c.post(f'/users/stop-following/{self.testuser2.id}')

            self.assertEqual(resp.status_code,302)
            self.assertEqual(len(self.testuser1.following),0)
            self.assertEqual(len(self.testuser2.followers),0)

    def test_user_delete(self):
        """Test user deletion from db"""
        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id
            
            resp = c.post('/users/delete',follow_redirects=True)

            self.assertEqual(resp.status_code,200)

            users = User.query.all()
            self.assertEqual(len(users),1)
            self.assertIn('Sign up',resp.text)
            self.assertEqual(users[0].username,"testuser2")

    def test_user_follower_page(self):
        """Test if user can view follower/following page"""
        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            # following page
            resp1 = c.get(f'/users/{self.testuser2.id}/following')
            self.assertEqual(resp1.status_code,200)
            self.assertIn(self.testuser2.username,resp1.text)

            # followers page

            resp2 = c.get(f'/users/{self.testuser2.id}/followers')
            self.assertEqual(resp2.status_code,200)
            self.assertIn(self.testuser2.username,resp2.text)