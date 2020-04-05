from pykalman import KalmanFilter
import numpy as np
import matplotlib.pyplot as plt
import time

measurements = np.asarray([(-0.19619056024494633,-0.19619056024494633),(-0.19619056024494633,-0.19619056024494633),(-0.1608465328235466,-0.1608465328235466),(-0.1608465328235466,-0.1608465328235466),(-0.2526928515046333,-0.2526928515046333)])
print(measurements)
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

print(kf1)
(smoothed_state_means, smoothed_state_covariances) = kf1.smooth(measurements)
print("initial_state_mean = " + str(smoothed_state_means))
plt.figure(1)
times = range(measurements.shape[0])
plt.plot(times, measurements[:, 0], 'bo',
         times, measurements[:, 1], 'ro',
         times, smoothed_state_means[:, 0], 'b--',
         times, smoothed_state_means[:, 2], 'r--',)
plt.show()
