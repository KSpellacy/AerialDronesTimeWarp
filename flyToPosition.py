import keyboard
from codrone_edu.drone import *

drone = Drone()
drone.pair()


running = True
positionData = []


def stop_program():
    """Sets the 'running' variable too False to exit the loop."""
    global running
    running = False
    print("Ctrl+u pressed. Stopping the program.")


# Register the hotkey, linking it to the `stop_program` function
keyboard.add_hotkey("ctrl+u", stop_program)


print("Program is running. Press Ctrl+u to stop.")
# capture position data of drone and store it in a .txt file


def getAltitudeData(positionDataList):
    altitude = drone.get_altitude_data()
    positionDataList.extend(altitude)


while running:
    print("Hold the drone in the position you want to capture and hit enter")
    if keyboard.is_pressed("enter"):
        getAltitudeData(positionData)
        time.sleep(0.2)

        