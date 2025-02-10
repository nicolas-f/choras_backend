import os
import unittest

from app import create_app, db


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        """
        This method runs once before any test in this class.
        It sets up the application context and creates the necessary database tables.
        """
        self.app, _ = create_app(settings_module=os.environ.get("APP_TEST_SETTINGS_MODULE"))
        self.db = db
        with self.app.app_context():
            self.db.create_all()

    def tearDown(self):
        """
        This method runs once after all tests in this class have been executed.
        It removes the database session and drops the database tables.
        """
        with self.app.app_context():
            self.db.session.remove()
            self.db.drop_all()
