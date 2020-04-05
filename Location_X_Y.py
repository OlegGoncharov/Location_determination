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
from pykalman import KalmanFilter
import time

d = 1.12 # Расстояние между антеннами



logging_file = "log.txt"
rtlsUtil = RtlsUtil(logging_file, RtlsUtilLoggingLevel.ALL)

devices = [
    {"com_port": "COM73", "baud_rate": 460800, "name": "CC26x2 Master"},
    {"com_port": "COM97", "baud_rate": 460800, "name": "CC26x2 Passive"},
    {"com_port": "COM99", "baud_rate": 460800, "name": "CC26x2 Passive"}
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



end_loop_read = 200



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

tempX_list = list()
tempY_list = list()
angle_arr_1 = list()
angle_arr_2 = list()

ind_coinc = 0
measurements_list = []

# матрица перехода и наблюдения для Калмановской фильтрации
transition_matrix = [[1, 1, 0, 0],
                     [0, 1, 0, 0],
                     [0, 0, 1, 1],
                     [0, 0, 0, 1]]

observation_matrix = [[1, 0, 0, 0],
                      [0, 0, 1, 0]]






plt.ion()

img = plt.imread("85282_1.jpg")
fig, ax = plt.subplots()
ax.imshow(img, extent=[-1.75,1.75, -1.391/2,1.391/2])

plt.show()
plt.xlabel('X, м')
plt.ylabel('Y, м')
plt.xlim(-5,5)
plt.ylim(-3,3)
plt.plot(d/2-d/5, -1*1.391/2, marker='o', markersize=5, color="blue", label='Антенна 1')
plt.plot(-d/2-d/5, -1*1.391/2, marker='o', markersize=5, color="blue", label='Антенна 2')
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
                angle_arr_1.append(float(data['payload'].angle))
            elif data['identifier'] == new_x[1]:
                i_2 = i_2 + 1
                angle_arr_2.append(float(data['payload'].angle))
            if i_1==i_2:  
                try:
                    ind_coinc = ind_coinc +1
                    tempX_1 = math.sin((angle_arr_1[i_1-1]+angle_arr_2[i_2-1])*math.pi/180)
                    tempX_2 = math.sin((angle_arr_1[i_1-1]-angle_arr_2[i_2-1])*math.pi/180)
                    tempX = tempX_1/tempX_2*d/2
                    tempX_list.append(tempX)
                    tempY = cot(angle_arr_1[i_1-1]*math.pi/180)*(tempX+d/2)
                    tempY_list.append(tempY)
                    measurements_list.append([tempX,tempY])
                    if ind_coinc % 5 == 0:
                        measurements  = np.asarray(measurements_list)
                        measurements_list.clear()


                        # нефильтрованное положение брелка
                        plt.plot(measurements[:, 0], -1.391/2 - abs(measurements[:, 1]), marker='o', markersize=3, color="red")
                        plt.xlim(-5,5)
                        plt.ylim(-5,5)
                        plt.show()
                        initial_state_mean = [measurements[0, 0],
                                              0,
                                              measurements[0, 1],
                                              0]
                        transition_matrix = [[1, 1, 0, 0],
                                             [0, 1, 0, 0],
                                             [0, 0, 1, 1],
                                             [0, 0, 0, 1]]

                        observation_matrix = [[1, 0, 0, 0],
                                              [0, 0, 1, 0]]

                        kf1 = KalmanFilter(transition_matrices = transition_matrix,
                              observation_matrices = observation_matrix,
                              initial_state_mean = initial_state_mean)

                        kf1 = kf1.em(measurements, n_iter=10)


                        (smoothed_state_means, smoothed_state_covariances) = kf1.smooth(measurements)






                        




                        
                        plt.pause(10*1/460800)
                        
                except:
                    continue

    except queue.Empty:
        continue
with open('your_file_X.txt', 'w') as f:
    for item in tempX_list:
        f.write("%s\n" % item)
 
with open('your_file_Y.txt', 'w') as f:
    for item in tempY_list:
        f.write("%s\n" % item)

        
rtlsUtil.aoa_stop()
if rtlsUtil.ble_connected:
    rtlsUtil.ble_disconnect()
    print("Master Disconnected")

rtlsUtil.done()
print("Done")
