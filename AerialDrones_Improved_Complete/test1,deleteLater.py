from codrone_edu.drone import Drone  # Import the Drone CLASS

drone = Drone()  # Create a drone OBJECT
drone.pair()     # Connect to the drone

drone.takeoff()      # Correct: takeoff() not take_off()
drone.set_pitch(30)
drone.move(3)
drone.hover(2)
drone.land()

drone.close()        # Close connection when done