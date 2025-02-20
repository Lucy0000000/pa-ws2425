import datetime
import os

import numpy as np

import project.functions as fn



def main():
    import h5py
    import numpy as np

    # Define variables
    processed_data = {}
    df_data = {}
    filter_sizes = (3, 5, 7)

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

        print(f"🔍 Debug: {quantity} -> type: {type(raw_data[quantity])}, value: {raw_data[quantity][:5]}")

    print("Final verification of the read data:", {k: v.shape for k, v in raw_data.items()})

    # Step 3: Check if all required arrays exist
    for key in measured_quantities:
        if raw_data[key] is None:
            raise ValueError(f"❌ Error: raw_data['{key}'] is None. Cannot process!")

    # Step 4: Check and align data lengths
    lengths = {key: len(value) for key, value in raw_data.items()}
    print("Lengths before processing:", lengths)

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

    # Step 6: Handle NaN values in level and temperature
    for key in ["level", "temperature"]:
        print(f"🔄 Checking NaN values in {key}...")

        if np.isnan(raw_data[key]).sum() == 0:
            print(f"✅ No NaN values in {key}. Skipping interpolation.")
        else:
            print(f"🔄 Interpolating NaN values in {key}...")
            raw_data[key] = fn.interpolate_nan_data(df_data["time"], raw_data[key])

            if raw_data[key] is None or np.isnan(raw_data[key]).sum() > 0:
                raise ValueError(f"❌ Error: Interpolation failed for '{key}'! Check input data!")

            print(f"✅ {key} successfully interpolated!")

    # Step 7: Load metadata from HDF5 file
    P_heater = fn.read_metadata(file_path, tank_path, "power_heater") or 0
    eta_heater = fn.read_metadata(file_path, tank_path, "efficiency_heater") or 1
    k_tank = fn.read_metadata(file_path, tank_path, "heat_transfer_coeff_tank")
    area_tank = fn.read_metadata(file_path, tank_path, "surface_area_tank")
    T_env = fn.read_metadata(file_path, brewing, "T_env")
    mass_tank = fn.read_metadata(file_path, tank_path, "mass_tank")
    specific_heat_capacity_tank = fn.read_metadata(file_path, tank_path, "specific_heat_capacity_tank")

    specific_heat_capacity = 4184
    tank_footprint = 2.5
    density = 1000

    # Compute initial internal energy E_0
    E_0 = fn.calc_enthalpy(mass_tank, specific_heat_capacity_tank, T_env)

    for filter_size in filter_sizes:
        print(f"📊 Processing filter size {filter_size}...")

        # Filter temperature data
        processed_data[f"temperature_k_{filter_size}"] = fn.filter_data(raw_data["temperature"], filter_size)

        # Process and filter level data
        filtered_level = fn.remove_negatives(raw_data["level"])
        interpolated_level = fn.interpolate_nan_data(df_data["time"], filtered_level)
        processed_data[f"level_k_{filter_size}"] = fn.filter_data(interpolated_level, filter_size)

        # Calculate mass
        processed_data[f"mass_k_{filter_size}"] = fn.calc_mass(
            processed_data[f"level_k_{filter_size}"], tank_footprint, density
        )

        min_length = min(
            processed_data[f"mass_k_{filter_size}"].shape[0],
            raw_data["temperature"].shape[0],
            len(df_data["time"])
        )
        processed_data[f"mass_k_{filter_size}"] = processed_data[f"mass_k_{filter_size}"][:min_length]
        raw_data["temperature"] = raw_data["temperature"][:min_length]
        df_data["time"] = df_data["time"][:min_length]

        inner_energy = []

        for i in range(min_length):
            Q_zu = fn.calc_heater_heat_flux(P_heater, eta_heater)
            Q_ab = fn.calc_convective_heat_flow(k_tank, area_tank, raw_data["temperature"][i], T_env)
            H_zu = fn.calc_enthalpy(processed_data[f"mass_k_{filter_size}"][i], specific_heat_capacity, raw_data["temperature"][i])
            E_t = Q_zu - Q_ab + H_zu + E_0
            inner_energy.append(E_t)

        df_data[f"inner_energy_k_{filter_size}"] = np.array(inner_energy)
        print(f"✅ Internal energy calculated for filter size {filter_size}")

    print("✅ All data successfully processed!")

    # 📌 Aufgabe 5: Daten archivieren (HDF5-Speicherung)
    h5_path = "project/data/data_GdD_plot_WS2425.h5"
    group_path = "processed_data"

    metadata = {
        "legend_title": "Internal Energy Analysis",
        "x_label": "Time (s)",
        "x_unit": "s",
        "y_label": "Internal Energy (J)",
        "y_unit": "J",
    }

    fn.store_plot_data(df_data, h5_path, group_path, metadata)
    print(f"✅ Processed data successfully saved to {h5_path}")

    # 📌 Aufgabe 5: Daten archivieren (HDF5-Speicherung)
    h5_path = "project/data/data_GdD_plot_WS2425.h5"  # Define the HDF5 file path
    group_path = "processed_data"  # Define the group where data will be stored

    # Define metadata
    metadata = {
        "legend_title": "Internal Energy Analysis",
        "x_label": "Time (s)",
        "x_unit": "s",
        "y_label": "Internal Energy (J)",
        "y_unit": "J",
    }

    # Store processed data in HDF5 file
    fn.store_plot_data(df_data, h5_path, group_path, metadata)
    print(f"✅ Processed data successfully saved to {h5_path}")

    # 📌 Test: Read stored data to verify
    df_loaded, metadata_loaded = fn.read_plot_data(h5_path, group_path)
    print("✅ Loaded data preview:")
    print(df_loaded.head())  # Show first few rows of stored data
    print("✅ Loaded metadata:")
    print(metadata_loaded)  # Show stored metadata
     # 📌 Aufgabe 5d: Daten archivieren (HDF5-Speicherung)
    h5_path = "project/data/data_GdD_plot_WS2425.h5"  # Path to the HDF5 file
    group_path = "processed_data"  # Group where data will be stored in HDF5

    # Define metadata dictionary
    metadata = {
        "legend_title": "Internal Energy Analysis",
        "x_label": "Time (s)",
        "x_unit": "s",
        "y_label": "Internal Energy (J)",
        "y_unit": "J",
    }

    # ✅ Store processed data in HDF5 file
    fn.store_plot_data(df_data, h5_path, group_path, metadata)
    print(f"✅ Processed data successfully saved to {h5_path}")
 
    df_loaded, metadata_loaded = fn.read_plot_data(h5_path, group_path)

    # Generate plot using stored metadata
    fig = fn.plot_data(df_loaded, metadata_loaded)

    # Define destination path
    destination_path = "./plotid/GdD_WS2425_<Matrikelnummer>_plot.png"

    # Publish the plot
    fn.publish_plot(fig, h5_path, destination_path)
if __name__ == "__main__":
    main()