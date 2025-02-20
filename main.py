import datetime
import os

import numpy as np

import project.functions as fn


def main():
    import h5py  # ✅ Import innerhalb der Funktion erlaubt

    brewing = "brewing_0002"
    tank_id = "B004"
    measured_quantities = ("level", "temperature", "timestamp")

    file_path = "project/data/data_GdD_Datensatz_WS2425.h5"
    tank_path = f"{brewing}/{tank_id}"  
    raw_data = {}

    # Öffne die HDF5-Datei
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

    # 📥 Daten einlesen
    for quantity in measured_quantities:
        data_path = f"{tank_path}/{quantity}"
        print(f"🔍 Reading {quantity} from {data_path}...")  # Debug
        raw_data[quantity] = fn.read_data(file_path, data_path)  

        if raw_data[quantity] is None:
            print(f"⚠️ Warning: No data found for {quantity}!")

    print("Final verification of the read data:", raw_data)

    # ❗ Fehlerbehandlung für fehlende Daten
    if not all(q in raw_data and raw_data[q] is not None for q in measured_quantities):
        raise ValueError("❌ Error: At least one measurement value is missing!")

    # 📏 Überprüfung der Längen
    lengths = {key: len(value) if value is not None else 0 for key, value in raw_data.items()}
    print("Lengths of the arrays before verification:", lengths)

    # ⏳ Kürzen auf die kleinste Länge
    min_length = min(lengths.values())
    print(f"Shortening all arrays to the smallest length: {min_length}")

    for key in measured_quantities:
        raw_data[key] = raw_data[key][:min_length]

    # 📏 Erneute Überprüfung der Längen
    new_lengths = {key: len(value) for key, value in raw_data.items()}
    print("Final array lengths after shortening:", new_lengths)

    if len(set(new_lengths.values())) > 1:
        raise ValueError(f"❌ Error: Arrays do not have the same length after processing! {new_lengths}")

    # 🔢 Negativwerte entfernen
    for key in ["level", "temperature"]:
        if np.any(raw_data[key] < 0):
            print(f"⚠️ Negative values detected in {key}, removing...")
            raw_data[key] = fn.remove_negatives(raw_data[key])

    # 🔄 Interpolation von NaN-Werten
    for key in ["level", "temperature"]:
        if np.isnan(raw_data[key]).sum() > 0:
            print(f"🔄 Interpolating NaN values in {key}...")
            raw_data[key] = fn.interpolate_nan_data(raw_data["timestamp"], raw_data[key])

    print("✅ All NaN values interpolated successfully!")

    # ⏳ Zeitdaten umwandeln
    raw_data["timestamp"] = fn.process_time_data(raw_data["timestamp"])

    # 🛠 Debug-Ausgabe der ersten Timestamps
    print("First 5 processed timestamps:", raw_data["timestamp"][:5])

    print("✅ All data successfully loaded and verified!")

if __name__ == "__main__":
    main()