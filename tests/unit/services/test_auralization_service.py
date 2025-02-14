import unittest

from app.models.AudioFile import AudioFile
from app.services import auralization_service
from tests.unit import BaseTestCase


class UsersUnitTests(BaseTestCase):
    def setUp(self):
        """
        Set up method to initialize variables and preconditions.
        """
        super().setUp()

    def test_insert_initial_audio_files(self):
        """
        Test that initial audio_files are correctly inserted into the database.
        """
        # When
        with self.app.app_context():
            # Call the function to insert initial audio_files
            auralization_service.insert_initial_audios_examples()

            # Fetch audio_files from the database
            audio_files = auralization_service.get_all_audio_files()

        # Then
        # Ensure that audio_files are inserted correctly
        self.assertTrue(len(audio_files) > 0)


if __name__ == "__main__":
    unittest.main()
