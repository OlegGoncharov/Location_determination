from pykalman import KalmanFilter
import numpy as np
import matplotlib.pyplot as plt
import time

file1 = open("your_file_X.txt","r+")
stroka1 = file1.read().splitlines()

s1 = list()
for line in stroka1:
    s1.append(float(line))

file2 = open("your_file_Y.txt","r+")
stroka2 = file2.read().splitlines()

s2 = list()
for line in stroka2:
    s2.append(float(line))

measurements = np.column_stack((s1,s2))

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


kf2 = KalmanFilter(transition_matrices = transition_matrix,
                  observation_matrices = observation_matrix,
                  initial_state_mean = initial_state_mean,
                  observation_covariance = 80*kf1.observation_covariance,
                  em_vars=['transition_covariance', 'initial_state_covariance'])

kf2 = kf2.em(measurements, n_iter=5)
(smoothed_state_means, smoothed_state_covariances)  = kf2.smooth(measurements)

plt.figure(1)
plt.xlabel("time, step")
plt.ylabel("X, м")
times = range(measurements.shape[0])
plt.plot(times, measurements[:, 0], 'bo',
         times, smoothed_state_means[:, 0], 'b--')


plt.figure(2)
plt.xlabel("time, step")
plt.ylabel("Y, м")
times = range(measurements.shape[0])
plt.plot(times, measurements[:, 1], 'ro',
         times, smoothed_state_means[:, 2], 'r--',)
plt.show()

print("СКО до фильтрации координата X = " + str(np.std(measurements[:, 1])))
print("СКО после фильтрации координата X = " + str(np.std(smoothed_state_means[:, 2])))

print("СКО до фильтрации координата Y = " + str(np.std(measurements[:, 0])))
print("СКО после фильтрации координата Y = " + str(np.std(smoothed_state_means[:, 0])))


