import datetime
import os

import numpy as np

import project.functions as fn


def main():
    import h5py  # ✅ Import innerhalb der Funktion erlaubt

    df_data = {}

    brewing = "brewing_0002"
    tank_id = "B004"
    measured_quantities = ("level", "temperature", "timestamp")

    file_path = "project/data/data_GdD_Datensatz_WS2425.h5"
    tank_path = f"{brewing}/{tank_id}"  

    raw_data = {}

    # Öffne die HDF5-Datei
    with h5py.File(file_path, "r") as file:  
        print("Hauptgruppen:", list(file.keys()))  

        if brewing in file:
            print(f"Verfügbare Untergruppen in {brewing}:", list(file[brewing].keys()))
            if tank_id in file[brewing]:
                print(f"✅ Tank {tank_id} ist vorhanden!")  
                tank_group = file[brewing][tank_id]  
                print("Verfügbare Datensätze in tank_group:", list(tank_group.keys()))

                datasets = list(tank_group.keys())  
            else:
                print(f"⚠️ Tank {tank_id} wurde nicht gefunden!")
        else:
            print(f"⚠️ Gruppe {brewing} wurde nicht gefunden!")

    # Messdaten aus der Datei lesen
    for quantity in measured_quantities:
        data_path = f"{tank_path}/{quantity}"  
        raw_data[quantity] = fn.read_data(file_path, data_path)  
        print(f"Debug: {quantity} -> {raw_data[quantity]}")  

    print("Finale Überprüfung der ausgelesenen Daten:", raw_data)

    # Prüfe, ob alle Arrays die gleiche Länge haben
    lengths = {key: len(value) for key, value in raw_data.items()}
    print("Längen der Arrays:", lengths)
    
    if len(set(lengths.values())) > 1:
        raise ValueError("❌ Fehler: Die gelesenen Arrays haben unterschiedliche Längen!")

    # Falls Timestamps in Nanosekunden gespeichert sind, umrechnen
    print("Erster Timestamp umgerechnet:", datetime.datetime.utcfromtimestamp(raw_data["timestamp"][0] / 1e9))

    # Prüfe auf NaN-Werte in den Daten
    for key in raw_data:
        print(f"{np.isnan(raw_data[key]).sum()} NaN-Werte in {key}")

    print("✅ Alle Daten erfolgreich geladen und geprüft!")


if __name__ == "__main__":
    main()
