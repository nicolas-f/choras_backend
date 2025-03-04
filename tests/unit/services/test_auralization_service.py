import unittest

from app.models.Auralization import Auralization
from app.models.Simulation import Simulation
from app.models.Export import Export
from app.services import auralization_service
from app.types import Status
from tests.unit import BaseTestCase
from werkzeug.exceptions import HTTPException

from pathlib import Path
from config import DefaultConfig, AuralizationParametersConfig
import shutil


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

    def test_update_audios_examples(self):
        with self.app.app_context():
            auralization_service.update_audios_examples()
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

    def test_get_auralization_by_simulation_audiofile_ids(self):
        """
        Test that auralization is correctly retrieved by simulation_id and audio_file_id combination.
        """
        with self.app.app_context():
            arulization: Auralization = Auralization(simulationId=1, audioFileId=1, wavFileName="test.wav")
            self.db.session.add(arulization)
            self.db.session.commit()
            simulation_id = arulization.simulationId
            audio_file_id = arulization.audioFileId

            arulization_db = auralization_service.get_auralization_by_simulation_audiofile_ids(
                simulation_id, audio_file_id
            )
            self.assertEqual(arulization_db.status, Status.Created)

            self.db.session.delete(arulization)
            self.db.session.commit()
            arulization_db = auralization_service.get_auralization_by_simulation_audiofile_ids(
                simulation_id, audio_file_id
            )

            self.assertEqual(arulization_db.status, Status.Uncreated)

    def test_get_auralization_wav_path(self):
        """
        Test that auralization wav path is correctly retrieved.
        """
        with self.app.app_context():
            arulization: Auralization = Auralization(
                simulationId=1, audioFileId=1, status=Status.Completed, wavFileName="test.wav"
            )
            self.db.session.add(arulization)
            self.db.session.commit()
            araulization_id = arulization.id

            wav_path = auralization_service.get_auralization_wav_path(araulization_id)
            self.assertEqual(wav_path.name, "test.wav")

            self.db.session.delete(arulization)
            self.db.session.commit()
            self.assertRaises(
                HTTPException, auralization_service.get_auralization_wav_path, araulization_id
            )  # test that abort correctly raises exception

    def test_get_impulse_response_plot(self):
        """
        Test that impulse response plot is correctly retrieved.
        """
        with self.app.app_context():
            simulation: Simulation = Simulation(name="test", solverSettings={}, modelId=1, status=Status.Completed)
            self.db.session.add(simulation)
            self.db.session.commit()
            simulation_id = simulation.id

            export: Export = Export(name="test.xlsx", simulationId=simulation_id)
            self.db.session.add(export)
            self.db.session.commit()

            test_file_path = Path('tests', 'unit', 'services', 'data', 'test.xlsx')
            temp_destination = Path(DefaultConfig.UPLOAD_FOLDER_NAME)
            temp_destination.mkdir(parents=True, exist_ok=True)
            temp_file_path = Path(shutil.copy(test_file_path, temp_destination))

            impulse_response_plot = auralization_service.get_impulse_response_plot(simulation_id=simulation_id)

            self.assertTrue(len(impulse_response_plot['impulseResponse']) > 0)
            self.assertEqual(impulse_response_plot['fs'], AuralizationParametersConfig.visualization_fs)
            self.assertEqual(impulse_response_plot['simulationId'], simulation_id)

            # test for file deletion
            temp_file_path.unlink()
            self.assertRaises(HTTPException, auralization_service.get_impulse_response_plot, simulation_id)

            # test for in-progress
            simulation.status = Status.InProgress
            self.db.session.commit()
            self.assertRaises(HTTPException, auralization_service.get_impulse_response_plot, simulation_id)

            # test for non-exising simulation
            self.db.session.delete(export)
            self.db.session.delete(simulation)
            self.db.session.commit()
            self.assertRaises(HTTPException, auralization_service.get_impulse_response_plot, simulation_id)

    # TODO: testing procedure for: create_new_auralization -> run_auralization -> auralization_calculation
    def test_create_new_auralization(
        self,
    ):
        pass


if __name__ == "__main__":
    unittest.main()
