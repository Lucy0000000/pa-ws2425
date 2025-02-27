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
    """Performs linear interpolation for a given time range."""
    slope = (end_y - start_y) / (end_time - start_time)  
    return start_y + slope * (time - start_time)  



def interpolate_nan_data(time: NDArray, y_data: NDArray) -> NDArray:
    """Interpolates NaN values in y_data based on time using linear interpolation."""
    
    # Falls es keine NaN-Werte gibt, gib einfach das Original-Array zurück
    if np.isnan(y_data).sum() == 0:
        print("✅ No NaN values detected. Returning original data.")
        return y_data  

    # Falls ALLE Werte NaN sind, kann nicht interpoliert werden → Fehler ausgeben
    nan_mask = np.isnan(y_data)
    if nan_mask.all():
        raise ValueError("❌ Error: All values in y_data are NaN! Cannot interpolate.")

    # Lineare Interpolation
    return np.interp(time, time[~nan_mask], y_data[~nan_mask])


def filter_data(data: NDArray, window_size: int) -> NDArray:
    """Filter data using a moving average approach (SMA).

    Args:
        data (NDArray): Data to be filtered
        window_size (int): Window size of the filter

    Returns:
        NDArray: Filtered data
    """
    output = []
    pad_width = window_size // 2
    padded_data = np.pad(array=data, pad_width=pad_width, mode="edge")  # Padding to handle edges

    for i in range(pad_width, padded_data.size - pad_width):
        sma = np.mean(padded_data[i - pad_width : i + pad_width + 1])  # Compute SMA
        output.append(sma)

    return np.array(output)



def calc_heater_heat_flux(P_heater: float, eta_heater: float) -> float:
    """Calculates the heat flux provided by the heater.

    Args:
        P_heater (float): Electrical power input to the heater (W)
        eta_heater (float): Efficiency of the heater (0 to 1)

    Returns:
        float: Heat flux delivered to the system (W)
    """
    return P_heater * eta_heater



def calc_convective_heat_flow(k_tank: float, area_tank: float, t_total: float, t_env: float) -> float:
    """
    

    :param k_tank:(k)
    :param area_tank:  (A_s)
    :param t_total:  (T)
    :param t_env: (T_env)
    :return: (Q_ab)
    """
    return k_tank * area_tank * (t_total - t_env)



def calc_mass(level_data: NDArray, tank_footprint: float, density: float) -> NDArray:
    print(f"🔍 Debugging calc_mass: level_data[:5]={level_data[:5] if level_data is not None else 'None'}, "
          f"tank_footprint={tank_footprint}, density={density}")

    if level_data is None or tank_footprint is None or density is None:
        print("❌ Error: One or more inputs to calc_mass() are None!")
        return None

    return level_data * tank_footprint * density


def calc_enthalpy(mass: float, specific_heat_capacity: float, temperature: float) -> float:
    if mass is None or specific_heat_capacity is None or temperature is None:
        raise ValueError("❌ Error: One or more input values for calc_enthalpy() are None!")

    if np.isscalar(mass) and np.isnan(mass):
        raise ValueError("❌ Error: Mass is NaN!")
    if np.isscalar(temperature) and np.isnan(temperature):
        raise ValueError("❌ Error: Temperature is NaN!")

    print(f"🔍 Debug: mass = {mass[:5] if isinstance(mass, np.ndarray) else mass}, "
          f"temp = {temperature[:5] if isinstance(temperature, np.ndarray) else temperature}")

    return mass * specific_heat_capacity * temperature







def store_plot_data(
    data: dict[str, np.ndarray], file_path: str, group_path: str, metadata: dict[str, Any]
) -> None:
    """Saves processed data and metadata into an HDF5 file."""
    
    # Convert dictionary to Pandas DataFrame
    df = pd.DataFrame(data)
    
    # Open or create HDF5 file and store data
    with pd.HDFStore(file_path, mode="a") as store:
        store.put(group_path, df, format="table", data_columns=True)

        # Store metadata as attributes
        with h5.File(file_path, "a") as hdf_file:
            group = hdf_file.require_group(group_path)
            for key, value in metadata.items():
                group.attrs[key] = value
    
    print(f"✅ Data successfully stored in {file_path} under '{group_path}'")


def read_plot_data(
    file_path: str, group_path: str
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Reads data and metadata from an HDF5 file."""

    # Load DataFrame from HDF5 file
    with pd.HDFStore(file_path, mode="r") as store:
        df = store[group_path]

    # Load metadata
    metadata = {}
    with h5.File(file_path, "r") as hdf_file:
        if group_path in hdf_file:
            group = hdf_file[group_path]
            metadata = {key: group.attrs[key] for key in group.attrs.keys()}

    print(f"✅ Data successfully loaded from {file_path} under '{group_path}'")
    return df, metadata


def plot_data(data: pd.DataFrame, formats: dict[str, str]) -> Figure:
    """Generates a plot for internal energy over time with different filter sizes."""
    
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot all available internal energy columns
    for column in data.columns:
        if "inner_energy" in column:
            ax.plot(data["time"], data[column], label=column.replace("_", " ").title())

    # Format the plot
    ax.set_xlabel(formats.get("x_label", "Time (s)"))
    ax.set_ylabel(formats.get("y_label", "Internal Energy (J)"))
    ax.set_title(formats.get("legend_title", "Internal Energy Analysis"))
    ax.legend()
    ax.grid(True)

    print("✅ Plot successfully created!")
    return fig

def publish_plot(fig: Figure, source_paths: str | list[str], destination_path: str) -> None:
    """Saves and publishes a plot."""

    # Ensure the destination directory exists
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    # Save the figure
    fig.savefig(destination_path, dpi=300, bbox_inches="tight")
    print(f"✅ Plot successfully saved to {destination_path}")

    # Publish the plot using the given paths
    publish(fig, source_paths, destination_path)
    print("✅ Plot successfully published!")


if __name__ == "__main__":
    pass
