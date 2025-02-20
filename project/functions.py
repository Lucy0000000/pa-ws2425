from typing import Any

import h5py as h5
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
from numpy.typing import NDArray
import pandas as pd
from plotid.publish import publish
from plotid.tagplot import tagplot


def read_metadata(file: str, path: str, attr_key: str) -> Any | None:

  try:
        with h5.File(file, "r") as hdf_file:  # Open the HDF5 file in read mode
            group_or_dataset = hdf_file[path]  # Access the specified group or dataset
            metadata = group_or_dataset.attrs[attr_key]  # Retrieve the metadata attribute
            return metadata
  except KeyError:
    print(f"⚠️ Warning: Metadata '{attr_key}' not found in path '{path}'!")  
    return None  # Return None if the metadata or path does not exist




def read_data(file: str, path: str) -> np.ndarray | None:
    """Liest die Daten aus einer HDF5-Datei und gibt sie als NumPy-Array zurück."""
    try:
        with h5.File(file, "r") as hdf_file:
            dataset = hdf_file[path]  # Zugriff auf den Dataset
            return np.array(dataset)  # Konvertiere die Daten in ein NumPy-Array
    except KeyError:
        print(f"⚠️ Warning: Dataset '{path}' nicht gefunden!")
        return None





def check_equal_length(*arrays: NDArray) -> bool:
    """
    Überprüft, ob alle übergebenen Arrays die gleiche Länge haben.

    :param arrays: Beliebig viele NumPy-Arrays
    :return: True, wenn alle Arrays gleich lang sind, sonst False
    """
    return len(set(map(len, arrays))) == 1


def process_time_data(data: NDArray) -> NDArray:
    """
    Converts timestamps from milliseconds to seconds and normalizes them to start at zero.

    :param data: Array of timestamps in milliseconds.
    :return: Array of timestamps in seconds, starting from zero.
    """
    data_sec = data / 1000  # Convert milliseconds to seconds
    return data_sec - data_sec[0]  # Normalize by subtracting the first value

def remove_negatives(array: NDArray) -> NDArray:
    """Removes all negative values from the given array."""
    return array[array >= 0]



def linear_interpolation(
    time: NDArray, start_time: float, end_time: float, start_y: float, end_y: float
) -> NDArray:
    pass


def interpolate_nan_data(time: NDArray, y_data: NDArray) -> NDArray:
    pass


def filter_data(data: NDArray, window_size: int) -> NDArray:
    """Filter data using a moving average approach.

    Args:
        data (NDArray): Data to be filtered
        window_size (int): Window size of the filter

    Returns:
        NDArray: Filtered data
    """
    output = []
    pad_width = window_size // 2
    padded_data = np.pad(array=data, pad_width=pad_width, mode="edge")
    for i in range(pad_width, padded_data.size - pad_width):
        # Implementieren Sie hier den SMA!
        sma = []
        output.append(sma)
    return np.array(output)


def calc_heater_heat_flux(P_heater: float, eta_heater: float) -> float:
    pass


def calc_convective_heat_flow(
    k_tank: float, area_tank: float, t_total: float, t_env: float
) -> float:
    pass


def calc_mass(level_data: NDArray, tank_footprint: float, density: float) -> NDArray:
    pass


def calc_enthalpy(
    mass: float, specific_heat_capacity: float, temperature: float
) -> float:
    pass


def store_plot_data(
    data: dict[str, NDArray], file_path: str, group_path: str, metadata: dict[str, Any]
) -> None:
    pass


def read_plot_data(
    file_path: str, group_path: str
) -> tuple[pd.DataFrame, dict[str, Any]]:
    pass


def plot_data(data: pd.DataFrame, formats: dict[str, str]) -> Figure:
    pass


def publish_plot(
    fig: Figure, source_paths: str | list[str], destination_path: str
) -> None:
    pass


if __name__ == "__main__":
    pass
