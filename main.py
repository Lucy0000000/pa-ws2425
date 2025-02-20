import datetime
import os

import numpy as np

import project.functions as fn


def main():
    """Main function to read, verify, and process HDF5 data."""
    import h5py  # ✅ Import inside the function
    
    # Define file path and dataset structure
    brewing = "brewing_0002"
    tank_id = "B004"
    measured_quantities = ("level", "temperature", "timestamp")

    file_path = "project/data/data_GdD_Datensatz_WS2425.h5"
    tank_path = f"{brewing}/{tank_id}"  

    raw_data = {}

    # Open the HDF5 file and check structure
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
                return
        else:
            print(f"⚠️ Group {brewing} not found!")
            return

    # Read measurement data from the file
    for quantity in measured_quantities:
        data_path = f"{tank_path}/{quantity}"  
        raw_data[quantity] = fn.read_data(file_path, data_path)  
        print(f"Debug: {quantity} -> {raw_data[quantity]}")  

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
    print("Lengths of the arrays after shortening:", new_lengths)

    # If there is still a mismatch after shortening → detailed error message
    if len(set(new_lengths.values())) > 1:
        raise ValueError(f"❌ Error: Arrays have different lengths after shortening! {new_lengths}")

    # Convert timestamps if stored in nanoseconds
    print("First timestamp converted:", datetime.datetime.utcfromtimestamp(raw_data["timestamp"][0] / 1e9))

    # Check for NaN values in the data
    for key in raw_data:
        print(f"{np.isnan(raw_data[key]).sum()} NaN values in {key}")

    print("✅ All data successfully loaded and verified!")


if __name__ == "__main__":
    main()