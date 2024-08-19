"""This module contains the main application logic for processing and displaying radar data."""
from threading import Thread
from modules.utils import Utils
from modules.radar import Radar
#from modules.gui import GUI
#from modules.heatmap import HEATMAP
import numpy as np
import csv
import datetime


radarConfig = input("Radar Config Auswahl mit entsprechender Nummer \nBest Range: 1 \nBest Range Resolution: 2 \nBest Velocity_Resolution: 3\n")

# CSV Sachen
aufzeichnung = input("Sollen die die Daten aufgezeichnet werden? Y/N ")
if(aufzeichnung == "Y" or aufzeichnung == "y" or aufzeichnung == "Yes" or aufzeichnung == "yes" or aufzeichnung == "" ):
    csv_datei = input("Bitte geben Sie einen Namen für die CSV-Datei ein (z. B. messungen): ")
    fieldnames = ['Zeitstempel', 'Objekt', 'Entfernung', 'Geschwindigkeit', 'SNR', 'noise']
    csv_datei = csv_datei + "_RadarConf_" + radarConfig + ".csv"

# Neue CSV-Datei mit den fieldnames erstellen
    with open(csv_datei, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)

# Point Cloud GUI
POINT_CLOUD_GUI = 0
# Heatmap GUI
HEATMAP_GUI = 0

# Initialize classes
Utils = Utils()
Radar = Radar()
#GUI = GUI()
#HEATMAP = HEATMAP()

RADAR_CLI_PORT, RADAR_DATA_PORT, RADAR_CONFIG_FILE_PATH, DATA_STORAGE_FILE_PATH, DATA_STORAGE_FILE_NAME, IMAGE_STORAGE_FILE_PATH = Utils.get_radar_env()

#Radar Config Auswahl
RADAR_CONFIG_PREFIX_PATH="radar_config"

if radarConfig == "1":
    RADAR_CONFIG_FILE_NAME="Demo_Visualizer_Best_Range.cfg"
elif radarConfig == "2":
    RADAR_CONFIG_FILE_NAME="Demo_Visualizer_Best_Range_Res.cfg"
elif radarConfig == "3":
    RADAR_CONFIG_FILE_NAME="Demo_Visualizer_Best_Velocity_Res.cfg"
RADAR_CONFIG_FILE_PATH = RADAR_CONFIG_PREFIX_PATH + "/" + RADAR_CONFIG_FILE_NAME
print(RADAR_CONFIG_FILE_PATH)

cli_serial, data_serial = Radar.start(
    RADAR_CLI_PORT, RADAR_DATA_PORT, RADAR_CONFIG_FILE_PATH)

#RADAR_POSITION_X, RADAR_POSITION_Y, RADAR_POSITION_Z, GRID_SIZE = Utils.get_gui_env()


def sliding_window(frameNum, queue, snr):

    queue.append(snr)

    # Check if the window buffer is full
    if len(queue) >= frameNum:
        # Clear the window buffer for the next window
        queue = queue[1:]  # Remove the oldest data point

    return queue


def trigger_check(sta, lta, status):
    if not sta or not lta:
        return status

    staMean = sum(sta)/len(sta)
    ltaMean = sum(lta)/len(lta)

    if staMean/ltaMean > 1.35:
        status = True
    elif staMean/ltaMean < 1.1:
        status = False

    # print(f'''status: {status}, STA/LTA: {staMean/ltaMean}, staMean:{staMean}, ltaMean:{ltaMean}''')
    return status


def radar_thread_function():
    """radar_thread_function"""
    sta = []
    lta = []
    status = False
    prev_status = False  # 
    counter = 0
    pre_trigger_data = []

    while True:
        data_ok, _, detection_obj = Radar.read_and_parse_radar_data(data_serial)
        avg_pt = Radar.find_average_point(data_ok, detection_obj)
        
        if data_ok:
            pre_trigger_data.append(avg_pt)
            if len(pre_trigger_data) > 10:
                pre_trigger_data.pop(0)

            ## Print mal sachen
            print("objekt Anzahl",detection_obj['numObj']) 
            print("Entfernungen",detection_obj['range'])
            ##Print ende
            if(aufzeichnung == "Y" or aufzeichnung == "y" or aufzeichnung == "Yes" or aufzeichnung == "yes" or aufzeichnung == "" ):
            # Aktuellen Zeitstempel abrufen
                zeitstempel = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            # Neue Zeile zur CSV-Datei hinzufügen
                with open(csv_datei, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([zeitstempel, detection_obj['numObj'], detection_obj['range'], detection_obj['doppler'], detection_obj['snr'], detection_obj['noise'] ])


radar_thread_function()
