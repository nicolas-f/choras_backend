"""Test the pyroomacoustics simulation backend.
"""
import pytest
import numpy as np
import numpy.testing as npt
import os
import json
import simulation_backend.pyroomacoustics_interface as pra_interface
import tempfile
from pathlib import Path


def default_input_data():
    """Load the example input data."""
    with open("tests/pyroomacoustics/test_input_pyroomacoustics.json", 'r') as f:
        data = json.load(f)

    return data


@pytest.fixture
def input_data():
    """Fixture to load the example input data."""
    return default_input_data()


@pytest.fixture
def create_temporary_input_file():
    """Fixture to create a temporary input JSON file which can be reused to
    write results to."""
    input_tmp = default_input_data()
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname) / "temp_input.json"
        with open(tmp_path, 'w') as f:
            json.dump(input_tmp, f)
        yield str(tmp_path)

    return str(tmp_path)


def test_create_tmp_file(create_temporary_input_file):
    """Test the creation of a temporary input file.
    """
    tempfile_path = create_temporary_input_file
    assert os.path.exists(tempfile_path)


def test_get_receiver(input_data):
    """Test the get_receiver function."""
    receiver = pra_interface.get_receiver_positions(input_data)

    assert receiver is not None
    npt.assert_array_equal(receiver, np.array([[1.0, 1.0, 1.5]]))


def test_get_source_positions(input_data):
    """Test the get_source_positions function."""
    sources = pra_interface.get_source_positions(input_data)

    assert sources is not None
    npt.assert_array_equal(sources, np.array([2.0, 2.0, 1.5]))


def test_export_rir_to_input(create_temporary_input_file):
    """Test the export_rir_to_input function."""
    tmpfile = create_temporary_input_file
    rir = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5], dtype=float)
    pra_interface.export_rir_to_input(tmpfile, rir)

    with open(tmpfile, 'r') as f:
        data = json.load(f)

    npt.assert_array_equal(
        data['results'][0]['responses'][0]['receiverResults'], rir)
