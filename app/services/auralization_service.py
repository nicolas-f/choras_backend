from typing import Optional, List, Tuple
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from sqlalchemy import asc
from pathlib import Path
import numpy as np
import soundfile as sf
import logging
import json
import gc
import os

from flask_smorest import abort
from celery import shared_task

from config import AuralizationParametersConfig as AuralizationParameters
from config import DefaultConfig
from config import app_dir

from app.types import Status
from app.models.AudioFile import AudioFile
from app.models.Auralization import Auralization
from app.models.Export import Export
from app.models.Simulation import Simulation
from app.services.export_service import ExportHelper
from app.db import db

# Create Logger for this module
logger = logging.getLogger(__name__)


def get_auralization_by_id(auralization_id: int) -> Optional[Auralization]:
    auralization: Optional[Auralization] = Auralization.query.filter_by(id=auralization_id).first()
    return auralization if auralization else Auralization(status=Status.Uncreated)


def get_auralization_by_simulation_audiofile_ids(simulation_id: int, audiofile_id: int) -> Optional[Auralization]:
    auralization: Optional[Auralization] = Auralization.query.filter_by(
        simulationId=simulation_id, audioFileId=audiofile_id
    ).first()
    return auralization if auralization else Auralization(status=Status.Uncreated)


def get_auralization_wav_path(auralization_id: int) -> Optional[Path]:
    auralization: Optional[Auralization] = get_auralization_by_id(auralization_id)
    if auralization is None:
        abort(404, message="No auralization found with this id.")

    elif auralization.status != Status.Completed:
        abort(400, message="Auralization is not completed yet.")

    else:
        try:
            wav_file_path = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, auralization.wavFileName)
            return Path(wav_file_path)
        except Exception as e:
            abort(400, message=f"Error while getting the wav file path: {e}")
            return None

def get_impulse_response_wav_path(simulation_id: int) -> Optional[Path]:
    simulation: Optional[Simulation] = Simulation.query.filter_by(id=simulation_id).first()
    if simulation is None:
        abort(404, message="No simulation found with this id.")
    elif simulation.status != Status.Completed:
        abort(400, message="Simulation is not completed yet.")
    else:
        try:
            wav_file_path = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, f"{simulation.export.name.replace('.xlsx', '.wav')}")
            return Path(wav_file_path)
        except Exception as e:
            abort(400, message=f"Error while getting the impulse response wav file path: {e}")
            return None

def get_impulse_response_plot(simulation_id: int) -> Optional[dict]:
    simulation: Optional[Simulation] = Simulation.query.filter_by(id=simulation_id).first()
    if simulation is None:
        abort(404, message="No simulation found with this id.")
    elif simulation.status != Status.Completed:
        abort(400, message="Simulation is not completed yet.")
    else:
        try:
            xlsx_file_path = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, simulation.export.name)
            exportHelper = ExportHelper()
            plot_data = exportHelper.extract_from_xlsx_to_dict(xlsx_file_path, {"impulse response": [f"{AuralizationParameters.visualization_fs}Hz"]})
            return {"impulseResponse": plot_data["impulse response"][f"{AuralizationParameters.visualization_fs}Hz"], "fs": AuralizationParameters.visualization_fs, "simulationId": simulation.id}
        except Exception as e:
            abort(400, message=f"Error while getting the impulse response plot: {e}")
            return None

def create_new_auralization(simulation_id: int, audiofile_id: int) -> Optional[Auralization]:
    auralization: Optional[Auralization] = get_auralization_by_simulation_audiofile_ids(simulation_id, audiofile_id)
    if auralization.status == Status.Uncreated or auralization.status == Status.Error:
        try:
            auralization = Auralization(simulationId=simulation_id, audioFileId=audiofile_id)
            auralization.status = Status.Created

            db.session.add(auralization)
            db.session.commit()

            logger.info(f"Start running auralization task for auralization id: {auralization.id}")
            run_auralization.delay(auralization.id)
            logger.info(f"Auralization task for auralization id: {auralization.id} is running")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating auralization: {e}")
            abort(400, "Error creating auralization")

    return auralization


@shared_task
def run_auralization(auralizationId: int) -> None:
    try:
        auralization: Auralization = get_auralization_by_id(auralizationId)
        auralization.status = Status.InProgress
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating auralization status to InProgress: {e}")
        abort(400, "Error updating auralization status to InProgress")

    try:
        input_audio_file: AudioFile = auralization.audioFile
        signal_file_name = os.path.join(input_audio_file.path, input_audio_file.name)

        simulation: Simulation = auralization.simulation
        export: Export = simulation.export
        pressure_file_name = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, export.name.replace(".xlsx", "_pressure.csv"))

        auralization.wavFileName = export.name.replace(".xlsx", f"_{input_audio_file.name}.wav")
        wav_output_file_name = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, auralization.wavFileName)

        logger.debug("signal_file_name: %s", signal_file_name)
        logger.debug("pressure_file_name: %s", pressure_file_name)
        logger.debug("wav_output_file_name: %s", wav_output_file_name)

        _, _ = auralization_calculation(signal_file_name, pressure_file_name, wav_output_file_name)

        auralization.status = Status.Completed

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        auralization.status = Status.Error
        db.session.commit()
        logger.error(f"Error running this auralization {auralization.id}: {e}")
        abort(400, "Error running this auralization")


def auralization_calculation(
    signal_file_name: Optional[str], pressure_file_name: str, wav_output_file_name: Optional[str] = None
) -> Tuple[List[int], int]:
    # Load the signal and pressure data
    try:
        
        if signal_file_name is not None:
            # Extract data and sampling rate from file
            data_signal, fs = sf.read(signal_file_name)  # this returns "data_signal", which is the
            # audiodata (one_dimentional array) of the anechoic signal. It returns also the
            # "fs" sample frequency of the signal
        else:
            data_signal, fs = None, AuralizationParameters.visualization_fs

        data_pressure = np.loadtxt(
            pressure_file_name, skiprows=1, usecols=range(1, 6), delimiter=','
        )  # this returns the pressure data
        center_freq = np.loadtxt(
            pressure_file_name, usecols=range(1, 6), delimiter=',', dtype=str, max_rows=1
        )  # this returns the center frequencies of the bands with the suffix "Hz"

        center_freq = np.array([np.int32(f[:-2]) for f in center_freq])  # remove "Hz" suffix from the center frequency
        nBands = len(center_freq)  # number of bands
        p_rec_off_deriv_band = (
            data_pressure.transpose().copy()
        )  # energy decay curve in terms of pressure differentiated

        del data_pressure  # Delete the data to free up memory
        gc.collect()  # Force garbage collection

    except Exception as e:
        logger.error(f'Error loading files: {e}')
        return None, None

    # Auralization Calculation
    try:
        # RESAMPLING PRESSURE ENVELOPE
        num_samples = int(p_rec_off_deriv_band.shape[1] * fs / AuralizationParameters.original_fs)
        p_rec_off_deriv_band_resampled = np.zeros((p_rec_off_deriv_band.shape[0], num_samples))
        for i in range(p_rec_off_deriv_band.shape[0]):
            p_rec_off_deriv_band_resampled[i, :] = resample_poly(
                p_rec_off_deriv_band[i, :], up=int(fs), down=int(AuralizationParameters.original_fs)
            )

        # Clip negative values to zero
        p_rec_off_deriv_band_resampled = np.clip(p_rec_off_deriv_band_resampled, a_min=0, a_max=None)

        # SQUARE-ROOT of ENVELOPE
        # From the envelope of the impulse response, we need to get the impulse response
        square_root = np.sqrt(p_rec_off_deriv_band_resampled)  # this gives the impulse response at each frequency

        # FOURTH ATTEMPT of noise creation
        np.random.seed(AuralizationParameters.random_seed)
        noise = np.random.rand(1, p_rec_off_deriv_band_resampled.shape[1]) * 2 * (np.sqrt(3)) - (
            np.sqrt(3)
        )  # random noise vector with unifrom distribution and with numbers between -1 and 1
        noise = sum(noise)  # this line of code is used for passing from a row vector to a column vector

        # BUTTER FILTER
        Nyquist_freq = int(fs / 2)
        filter_order = AuralizationParameters.filter_order  # number of biquad sections of the desired system
        nth_octave = AuralizationParameters.nth_octave  # e.g., 3 for third-octave
        filter_tot = []
        for fc in center_freq:
            # Calculate low and high cutoff frequencies for each band
            lowcut = fc / (2 ** (1 / (2 * nth_octave)))
            highcut = fc * (2 ** (1 / (2 * nth_octave)))

            # Normalize the cutoff frequencies by the Nyquist frequency
            low = lowcut / Nyquist_freq
            high = highcut / Nyquist_freq

            # Design Butterworth bandpass filter
            butter_band = butter(
                filter_order, [low, high], btype='band', output='sos'
            )  # butter_band contains the second-order sections representation of the Butterworth filter

            # Append filter coefficients to filter tot
            filter_tot.append(butter_band)

        # TIME DOMAIN OF THE FILTERED RANDOM NOISE: for each band the sosfilt creates
        # a time domain convolution of the noise with the filter
        filt_noise_band = [
            sosfilt(band, noise) for band in filter_tot
        ]  # this is in the time domain because the sosfilt gives the time domain

        # Make the filt_noise_band list into an array
        filt_noise_band = np.array(filt_noise_band)

        # Padding the square-root to the same length as the filtered random noise
        pad_length = filt_noise_band.shape[1] - p_rec_off_deriv_band_resampled.shape[1]
        square_root_padded = np.pad(square_root, ((0, 0), (0, pad_length)), mode='constant')

        # Multiplication of SQUARE-ROOT of envelope with filtered random noise (FILTERED)
        imp_filt_band = []
        for fi in range(nBands):
            imp_filt = square_root_padded[fi, :] * filt_noise_band[fi, :]
            imp_filt_band.append(imp_filt)

        # ALL FREQUENCY IMPULSE RESPONSE WITHOUT DIRECT SOUND
        # Sum of the bands in the time domain
        imp_tot = [sum(imp_filt_band[i][j] for i in range(len(imp_filt_band))) for j in range(len(imp_filt_band[0]))]
        imp_tot = np.array(imp_tot, dtype=float)
        
        if data_signal is not None:
            # CONVOLUTION FOR AURALIZATION
            # Create impulse*signal response
            sh_conv = np.convolve(imp_tot, data_signal)  # convolution of the impulse response with the anechoic signal
            sh_conv = sh_conv / max(abs(sh_conv))  # normalized to the maximum value of the convolved signal
            sh_conv_normalized = normalize_to_int16(sh_conv)  # normalize the floating-point data to the range of int16
            # t_conv = np.arange(0, (len(sh_conv)) / fs, 1 / fs)  # Time vector of the convolved signal

            if wav_output_file_name is not None:
                # Create a file wav for auralization
                wavfile.write(wav_output_file_name, fs, sh_conv_normalized)
                return None, None  # in 16 bit format
        
        else:
            imp_tot = imp_tot / max(abs(imp_tot))
            imp_tot_normalized = normalize_to_int16(imp_tot)
            
            if wav_output_file_name is not None:
                # Create a file wav for impulse response
                wavfile.write(wav_output_file_name, fs, imp_tot_normalized)
            return (imp_tot_normalized.tolist(), fs) # fs = 44100 Hz if no signal file is provided

    except Exception as e:
        logger.error(f'Error during auralization calculation: {e}')
        return None, None


def normalize_to_int16(sh_conv: np.ndarray) -> np.ndarray:
    return np.int16(sh_conv / np.max(np.abs(sh_conv)) * 32767)


def get_all_audio_files():
    return AudioFile.query.order_by(asc(AudioFile.id)).all()


def insert_initial_audios_examples():
    audio_files = get_all_audio_files()
    if len(audio_files):
        return
    logger.info("Inserting initial audio example files")
    with open(os.path.join(app_dir, "models", "data", "audio_files.json")) as json_audio_files:
        initial_audio_files = json.load(json_audio_files)
        try:
            new_audio_files = []
            for audio_file in initial_audio_files:
                new_audio_files.append(AudioFile(name=audio_file["name"], description=audio_file["description"]))

            db.session.add_all(new_audio_files)
            db.session.commit()

        except Exception as ex:
            db.session.rollback()
            logger.error(f"Can not insert initial audio files! Error: {ex}")
            abort(400, f"Can not insert initial audio files! Error: {ex}")

    return {"message": "Initial audio files added successfully!"}
