import queue
import json
import pandas as pd
import matplotlib.pyplot as plt
import math
import scipy.io as sio
import numpy as np
from rtls_util import RtlsUtil, RtlsUtilLoggingLevel, RtlsUtilException
from itertools import groupby
from sympy import *
from PIL import Image




d = 1.47 # Расстояние между антеннами



logging_file = "log.txt"
rtlsUtil = RtlsUtil(logging_file, RtlsUtilLoggingLevel.ALL)

devices = [
    {"com_port": "COM73", "baud_rate": 460800, "name": "CC26x2 Master"},
    {"com_port": "COM48", "baud_rate": 460800, "name": "CC26x2 Passive"},
    {"com_port": "COM102", "baud_rate": 460800, "name": "CC26x2 Passive"}
]
## Setup devices
master_node, passive_nodes, all_nodes = rtlsUtil.set_devices(devices)
rtlsUtil.reset_devices()
print("Devices Reset")
try:
    scan_results = rtlsUtil.scan(15)
except:
    print("Slave не обнаружен. Запустите программу снова")
    exit()
rtlsUtil.ble_connect(scan_results[0], 100)
print("Connection Success")    



end_loop_read = 3000



aoa_params = {
                "aoa_run_mode": "AOA_MODE_ANGLE",  ## AOA_MODE_ANGLE, AOA_MODE_PAIR_ANGLES, AOA_MODE_RAW
                "aoa_cc2640r2": {
                "aoa_cte_scan_ovs": 4,
                "aoa_cte_offset": 4,
                "aoa_cte_length": 20,
                "aoa_sampling_control": int('0x00', 16),
            },
                "aoa_cc26x2": {
                "aoa_slot_durations": 1,
                "aoa_sample_rate": 1,
                "aoa_sample_size": 1,
                "aoa_sampling_control": int('0x10', 16),
                ## bit 0   - 0x00 - default filtering, 0x01 - RAW_RF no filtering,
                ## bit 4,5 - default: 0x10 - ONLY_ANT_1, optional: 0x20 - ONLY_ANT_2
                "aoa_sampling_enable": 1,
                "aoa_pattern_len": 2,
                "aoa_ant_pattern": [0, 1]
    }
}
try:
    rtlsUtil.aoa_set_params(aoa_params)
except:
    print("Не удалось установить параметры конфигурации. Запустите снова")
    exit()
print("AOA Paramas Set")

rtlsUtil.aoa_start(cte_length=20, cte_interval=1)
print("AOA Started")

def deleterep(l):
    n = []
    for i in l:
        if i not in n:
            n.append(i)
    return n

i2 = 0
arr_data_identify = []
while i2<60:
    try:
        data = rtlsUtil.aoa_results_queue.get(block=True, timeout=0.5)
        arr_data_identify.append(data['identifier'])
        i2 = i2+1
    except queue.Empty:
        i2 = i2+1
        continue
    
new_x = deleterep(arr_data_identify)

arr_data_identify.clear()
arr_data_identify.append('E0')

i = 0
i_1 = 0
i_2 = 0

channel1_list = list()
channel2_list = list()

angle_arr_1 = list()
angle_arr_2 = list()

rssi_arr_2 = list()
rssi_arr_1 = list()

R_list = list()
ind_R_list = list()
ind_coinc = 0

plt.ion()

img = plt.imread("85282_1.jpg")
fig, ax = plt.subplots()
ax.imshow(img, extent=[-1.391/2,1.391/2,-1.75,1.75])

plt.show()
plt.xlabel('Y, м')
plt.ylabel('X, м')
plt.xlim(-5,5)
plt.ylim(-3,3)
plt.plot(-1*1.391/2, d/2-d/5, marker='o', markersize=5, color="blue", label='Антенна 1')
plt.plot(-1*1.391/2, -d/2-d/5, marker='o', markersize=5, color="blue", label='Антенна 2')
while i<=end_loop_read:
    try:
        i = i + 1
        data = rtlsUtil.aoa_results_queue.get(block=True, timeout=0.5)
        arr_data_identify.append(data['identifier'])
        if (i==end_loop_read-1) and data['identifier'] == new_x[0]:
            break
        if (arr_data_identify[i] == arr_data_identify[i-1]):
            continue
        else:
            if data['identifier'] == new_x[0]:
                i_1 = i_1 + 1
                angle_arr_1.append(data['payload'].angle)
                rssi_arr_1.append(data['payload'].rssi)
                channel1_list.append(data['payload'].channel)
            elif data['identifier'] == new_x[1]:
                i_2 = i_2 + 1
                angle_arr_2.append(data['payload'].angle)
                rssi_arr_2.append(data['payload'].rssi)
                channel2_list.append(data['payload'].channel)
            if i_1==i_2:
                ind_coinc = ind_coinc +1
                try:
                    tempX_1 = math.sin((angle_arr_1[i_1-1]+angle_arr_2[i_2-1])*math.pi/180)
                    tempX_2 = math.sin((angle_arr_1[i_1-1]-angle_arr_2[i_2-1])*math.pi/180)
                    tempX = tempX_1/tempX_2*d/2        
                    tempY = cot(angle_arr_1[i_1-1]*math.pi/180)*(tempX+d/2)
                    plt.plot(-1*1.391/2 - abs(tempY), tempX, marker='o', markersize=3, color="red")
                    plt.xlim(-5,5)
                    plt.ylim(-3,3)
                    plt.show()
                    plt.pause(2*1/460800)
                except:
                    continue

    except queue.Empty:
        continue

sio.savemat('Ant1_two_antennas.mat', {'alpha1':angle_arr_1, 'rssi_1':rssi_arr_1, 'channel1':channel1_list})
sio.savemat('Ant2_two_antennas.mat', {'alpha2':angle_arr_2, 'rssi_2':rssi_arr_2, 'channel2':channel2_list})
rtlsUtil.aoa_stop()
if rtlsUtil.ble_connected:
    rtlsUtil.ble_disconnect()
    print("Master Disconnected")

rtlsUtil.done()
print("Done")
