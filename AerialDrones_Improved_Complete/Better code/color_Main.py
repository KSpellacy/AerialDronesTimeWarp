
from codrone_edu.drone import *

# drone = Drone()
# drone.pair()


def play(da_drone: Drone):
    da_drone.set_drone_LED(255, 255, 255, 150)  # white

    try:
        da_drone.load_color_data("color_data")  # newer name
    except AttributeError:
        da_drone.load_classifier("color_data")

    while True:
        color_data = da_drone.get_color_data()
        color = da_drone.predict_colors(color_data)

        if color[0] == "red":
            da_drone.set_drone_LED(255, 0, 0, 150)

        elif color[0] == "lightblue":
            da_drone.set_drone_LED(0, 0, 255, 150)

        elif color[0] == "green":
            da_drone.set_drone_LED(0, 128, 0, 150)
        elif color[0] == "purple":
            da_drone.set_drone_LED(0, 0, 255, 150)
        elif color[0] == "blue":
            da_drone.set_drone_LED(0, 0, 255, 150)
        elif color[0] == "yellow":
            da_drone.set_drone_LED(0, 255, 0, 150)
        elif color[0] == "black":
            da_drone.set_drone_LED(0, 0, 255, 150)
        elif color[0] == "white":
            da_drone.set_drone_LED(0, 0, 255, 150)
        elif color[0] == "_":
            da_drone.set_drone_LED(0, 0, 255, 150)  # blue