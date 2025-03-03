import unittest

from app.models.AudioFile import AudioFile
from app.models.Auralization import Auralization
from app.services import auralization_service
from app.types import Status
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
        with self.app.app_context():
            auralization_service.insert_initial_audios_examples()
            audio_files = auralization_service.get_all_audio_files()

        self.assertTrue(len(audio_files) > 0)

    def test_get_auralization_by_id(self):
        """
        Test that auralization is correctly retrieved by araulization_id.
        """
        with self.app.app_context():
            arulization: Auralization = Auralization(simulationId=1, audioFileId=1, wavFileName="test.wav")
            self.db.session.add(arulization)
            self.db.session.commit()
            araulization_id = arulization.id

            arulization_db = auralization_service.get_auralization_by_id(araulization_id)
            self.assertEqual(arulization_db.status, Status.Created)

            self.db.session.delete(arulization)
            self.db.session.commit()
            arulization_db = auralization_service.get_auralization_by_id(araulization_id)

            self.assertEqual(arulization_db.status, Status.Uncreated)


if __name__ == "__main__":
    unittest.main()
