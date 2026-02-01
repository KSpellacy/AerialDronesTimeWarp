from codrone_edu.drone import *
import time

drone = Drone()
drone.pair()

dataset = "color_data"
colors = ["green", "purple", "red", "lightblue", "blue", "yellow", "black", "white"]
samples = 500

for label in colors:
    input(f"Press Enter to calibrate {label}...")
    data = []

    print("0% ", end="")
    for j in range(samples):
        color_data = drone.get_color_data()[0:9]
        data.append(color_data)

        time.sleep(0.005)
        if j % 10 == 0:
            print("-", end="")
    print(" 100%")

    drone.new_color_data(label, data, dataset)

print("Done calibrating.")
drone.close()


