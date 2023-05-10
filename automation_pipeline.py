import os
import PySpin
import sys
from opto import Opto

import numpy as np

from Python3.CounterAndTimer import print_device_info, setup_counter_and_timer, configure_digital_io, configure_exposure_and_trigger, acquire_images, reset_trigger

saved_image_path = 'saved_images/'


def config_camera():
     # Retrieve singleton reference to system object
    system = PySpin.System.GetInstance()

    # Get current library version
    version = system.GetLibraryVersion()
    print('Library version: {}.{}.{}.{}'.format(version.major, version.minor, version.type, version.build))

    # Retrieve list of cameras from the system
    cam_list = system.GetCameras()

    num_cameras = cam_list.GetSize()

    print('Number of cameras detected: {}'.format(num_cameras))

    # Finish if there are no cameras
    if num_cameras == 0:

        # Clear camera list before releasing system
        cam_list.Clear()

        # Release system instance
        system.ReleaseInstance()

        print('Not enough cameras!')
        input('Done! Press Enter to exit...')

        return False

    return system, cam_list

def release_cam(cam_list,system):

    # Release reference to camera
    # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
    # cleaned up when going out of scope.
    # The usage of del is preferred to assigning the variable to None.

    # Clear camera list before releasing system
    cam_list.Clear()

    # Release system instance
    system.ReleaseInstance()

    input('Done! Press Enter to exit...')

def run_single_camera(cam):
    """
    This function acts as the body of the example; please see the NodeMapInfo example
    for more in-depth comments on setting up cameras.

    :param cam: Camera to run on.
    :type cam: CameraPtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True

        # Retrieve TL device nodemap and print device information
        nodemap_tldevice = cam.GetTLDeviceNodeMap()

        result &= print_device_info(nodemap_tldevice)

        # Initialize camera
        cam.Init()

        # Retrieve GenICam nodemap
        nodemap = cam.GetNodeMap()

        # Configure Counter and Timer setup
        result &= setup_counter_and_timer(nodemap)
        if not result:
            return result

        # Configure DigitalIO (GPIO output)
        result &= configure_digital_io(nodemap)
        if not result:
            return result

        # Configure Exposure and Trigger
        result &= configure_exposure_and_trigger(nodemap)
        if not result:
            return result

        # Acquire images
        result &= acquire_images(cam, nodemap, nodemap_tldevice)

        # Reset trigger
        result &= reset_trigger(nodemap)

        # Deinitialize camera
        cam.DeInit()

    except PySpin.SpinnakerException as ex:
        print('Error: {}'.format(ex))
        result = False

    return result

def camera_pipeline(cam_list):

    for i, cam in enumerate(cam_list):

        print('Running example for camera {}...'.format(i))

        run_single_camera(cam)

        print('Camera {} example complete... \n'.format(i))

    return cam

if __name__ == '__main__':
    min_etl_current = -250
    max_etl_current = 250
    current_step = 50

    current_list = np.arange(min_etl_current, max_etl_current+1 , current_step).tolist()

    print('Current list steps: ',current_list)
    print('Steps in total: ',len(current_list))

    system, cam_list = config_camera()

    for current in current_list:
        print("Current current level: ", current)
        cam = camera_pipeline(cam_list)
        del cam
    
    release_cam(cam_list,system)
