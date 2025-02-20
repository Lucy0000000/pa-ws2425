import datetime
import os

import numpy as np

import project.functions as fn

def main():
    import h5py  # ✅ Import innerhalb der Funktion erlaubt
    import numpy as np  # Falls numpy nicht oben importiert ist

    # Define variables
    processed_data = {}  # Speichert gefilterte und verarbeitete Daten
    df_data = {}  # Speichert Daten wie Zeit
    filter_sizes = (3, 5, 7)  # Definiere verschiedene Filtergrößen

    brewing = "brewing_0002"
    tank_id = "B004"
    measured_quantities = ("level", "temperature", "timestamp")

    file_path = "project/data/data_GdD_Datensatz_WS2425.h5"
    tank_path = f"{brewing}/{tank_id}"

    raw_data = {}

    # Step 1: Open the HDF5 file and read data
    with h5py.File(file_path, "r") as file:
        print("Main groups:", list(file.keys()))

        if brewing in file:
            print(f"Available subgroups in {brewing}:", list(file[brewing].keys()))
            if tank_id in file[brewing]:
                print(f"✅ Tank {tank_id} exists!")
                tank_group = file[brewing][tank_id]
                print("Available datasets in tank group:", list(tank_group.keys()))
            else:
                print(f"⚠️ Tank {tank_id} not found!")
        else:
            print(f"⚠️ Group {brewing} not found!")

    # Step 2: Read measurement data
    for quantity in measured_quantities:
        data_path = f"{tank_path}/{quantity}"
        print(f"📥 Reading {quantity} from {data_path}...")
        raw_data[quantity] = fn.read_data(file_path, data_path)

        # Debugging-Ausgabe
        print(f"🔍 Debug: {quantity} -> type: {type(raw_data[quantity])}, value: {raw_data[quantity][:5]}")

    print("Final verification of the read data:", {k: v.shape for k, v in raw_data.items()})

    # Step 3: Check if all required arrays exist
    for key in measured_quantities:
        if raw_data[key] is None:
            raise ValueError(f"❌ Error: raw_data['{key}'] is None. Cannot process!")

    # Step 4: Check and align data lengths
    lengths = {key: len(value) for key, value in raw_data.items()}
    print("Lengths before processing:", lengths)

    # Shorten arrays to smallest length
    min_length = min(lengths.values())
    print(f"Shortening all arrays to {min_length} elements.")
    for key in measured_quantities:
        raw_data[key] = raw_data[key][:min_length]

    new_lengths = {key: len(value) for key, value in raw_data.items()}
    print("Final lengths after shortening:", new_lengths)

    if len(set(new_lengths.values())) > 1:
        raise ValueError(f"❌ Error: Arrays do not have the same length after processing! {new_lengths}")

    # Step 5: Convert timestamps
    df_data["time"] = fn.process_time_data(raw_data["timestamp"])
    print(f"🕒 First 5 processed timestamps: {df_data['time'][:5]}")

    # 🛠 **Fix: Check if `time` is sorted & contains unique values**
    if not np.all(np.diff(df_data["time"]) > 0):
        print("⚠️ Warning: `time` is not strictly increasing. Sorting...")
        sorted_indices = np.argsort(df_data["time"])
        df_data["time"] = df_data["time"][sorted_indices]
        for key in ["level", "temperature"]:
            raw_data[key] = raw_data[key][sorted_indices]

    # Step 6: Handle NaN values in level and temperature
    for key in ["level", "temperature"]:
        print(f"🔄 Checking NaN values in {key}...")

        # **Fix: Prüfen, ob NaN-Werte vorhanden sind**
        if np.isnan(raw_data[key]).sum() == 0:
            print(f"✅ No NaN values in {key}. Skipping interpolation.")
        else:
            print(f"🔄 Interpolating NaN values in {key}...")
            raw_data[key] = fn.interpolate_nan_data(df_data["time"], raw_data[key])
            
            # **Fix: Überprüfen, ob Interpolation funktioniert hat**
            if raw_data[key] is None or np.isnan(raw_data[key]).sum() > 0:
                raise ValueError(f"❌ Error: Interpolation failed for '{key}'! Check input data!")

            print(f"✅ {key} successfully interpolated!")

    # Step 7: Apply filtering
    for filter_size in filter_sizes:
        print(f"📊 Applying moving average filter of size {filter_size}...")

        # Filter temperature data
        processed_data[f"temperature_k_{filter_size}"] = fn.filter_data(raw_data["temperature"], filter_size)

        # Process and filter level data
        filtered_level = fn.remove_negatives(raw_data["level"])
        if filtered_level is None:
            raise ValueError("❌ Error: remove_negatives returned None!")

        interpolated_level = fn.interpolate_nan_data(df_data["time"], filtered_level)
        if interpolated_level is None:
            raise ValueError("❌ Error: interpolate_nan_data returned None!")

        processed_data[f"level_k_{filter_size}"] = fn.filter_data(interpolated_level, filter_size)

    print("✅ All data successfully filtered and processed!")
    print("Final processed data:", {k: v.shape for k, v in processed_data.items()})


if __name__ == "__main__":
    main()
