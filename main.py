import datetime
import os

import numpy as np

import project.functions as fn


def main():
    import h5py  

    brewing = "brewing_0002"
    tank_id = "B004"
    measured_quantities = ("level", "temperature", "timestamp")

    file_path = "project/data/data_GdD_Datensatz_WS2425.h5"
    tank_path = f"{brewing}/{tank_id}"  

    raw_data = {}

    # Open the HDF5 file
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

    # Read measurement data from the file
    for quantity in measured_quantities:
        data_path = f"{tank_path}/{quantity}"  
        raw_data[quantity] = fn.read_data(file_path, data_path)  
        print(f"🔵 Reading {quantity} from {data_path}...")

    print("Final verification of the read data:", raw_data)

    # Check if all required arrays exist
    if not all(q in raw_data for q in measured_quantities):
        raise ValueError("❌ Error: At least one measurement value is missing!")

    # Check if all arrays have the same length
    lengths = {key: len(value) for key, value in raw_data.items()}
    print("Lengths of the arrays before verification:", lengths)

    # If lengths are different → shorten all arrays
    min_length = min(lengths.values())
    print(f"Shortening all arrays to the smallest length: {min_length}")

    for key in measured_quantities:
        raw_data[key] = raw_data[key][:min_length]

    # Check again after shortening
    new_lengths = {key: len(value) for key, value in raw_data.items()}
    print("Final array lengths after shortening:", new_lengths)

    if len(set(new_lengths.values())) > 1:
        raise ValueError(f"❌ Error: Arrays do not have the same length after processing! {new_lengths}")

    # Convert timestamps if stored in nanoseconds
    raw_data["timestamp"] = fn.process_time_data(raw_data["timestamp"])
    print(f"First 5 processed timestamps: {raw_data['timestamp'][:5]}")

    # Interpolate NaN values
    for key in ["level", "temperature"]:
        print(f"🔵 Interpolating NaN values in {key}...")
        raw_data[key] = fn.interpolate_nan_data(raw_data["timestamp"], raw_data[key])

    print("✅ All NaN values interpolated successfully!")

    # Filter data using moving average (SMA)
    window_size = 5  # Example: Use a window of 5 data points
    for key in ["level", "temperature"]:
        print(f"🟢 Applying moving average filter to {key}...")
        raw_data[key] = fn.filter_data(raw_data[key], window_size)
    
    print("✅ All data successfully filtered!")

    # Check for NaN values in the data
    for key in raw_data:
        print(f"{np.isnan(raw_data[key]).sum()} NaN values in {key}")

    print("✅ All data successfully loaded and verified!")

if __name__ == "__main__":
    main()