import os
import PySpin
import sys
from opto import Opto

import numpy as np

from Python3.CounterAndTimer import print_device_info, setup_counter_and_timer, configure_digital_io, reset_trigger

saved_image_path = 'saved_images/'
NUM_IMAGES = 2  # number of images to grab


def configure_exposure_and_trigger(nodemap,exposure_time):
    """
    This function configures the camera to set a manual exposure value and enables
    camera to be triggered by the PWM signal.

    :param nodemap: Device nodemap.
    :type nodemap: INodeMap
    :return: True if successful, False otherwise.
    :rtype: bool
    """

    print('\nConfiguring Exposure and Trigger')

    try:
        result = True

        # Turn off auto exposure
        node_exposure_auto = PySpin.CEnumerationPtr(nodemap.GetNode('ExposureAuto'))
        if not PySpin.IsAvailable(node_exposure_auto) or not PySpin.IsWritable(node_exposure_auto):
            print('\nUnable to set Exposure Auto (enumeration retrieval). Aborting...\n')
            return False

        entry_exposure_auto_off = node_exposure_auto.GetEntryByName('Off')
        if not PySpin.IsAvailable(entry_exposure_auto_off) or not PySpin.IsReadable(entry_exposure_auto_off):
            print('\nUnable to set Exposure Auto (entry retrieval). Aborting...\n')
            return False

        exposure_auto_off = entry_exposure_auto_off.GetValue()

        node_exposure_auto.SetIntValue(exposure_auto_off)

        # Set Exposure Time to less than 1/50th of a second (5000 us is used as an example)
        node_exposure_time = PySpin.CFloatPtr(nodemap.GetNode('ExposureTime'))
        if not PySpin.IsAvailable(node_exposure_time) or not PySpin.IsWritable(node_exposure_time):
            print('\nUnable to set Exposure Time (float retrieval). Aborting...\n')
            return False

        node_exposure_time.SetValue(exposure_time)

        # Ensure trigger mode is off
        #
        # *** NOTES ***
        # The trigger must be disabled in order to configure
        node_trigger_mode = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerMode'))
        if not PySpin.IsAvailable(node_trigger_mode) or not PySpin.IsWritable(node_trigger_mode):
            print('\nUnable to disable trigger mode (node retrieval). Aborting...\n')
            return False

        entry_trigger_mode_off = node_trigger_mode.GetEntryByName('Off')
        if not PySpin.IsAvailable(entry_trigger_mode_off) or not PySpin.IsReadable(entry_trigger_mode_off):
            print('\nUnable to disable trigger mode (enum entry retrieval). Aborting...\n')
            return False

        node_trigger_mode.SetIntValue(entry_trigger_mode_off.GetValue())

        # Set Trigger Source to Counter 0 Start
        node_trigger_source = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerSource'))
        if not PySpin.IsAvailable(node_trigger_source) or not PySpin.IsWritable(node_trigger_source):
            print('\nUnable to set trigger source (enumeration retrieval). Aborting...\n')
            return False

        entry_trigger_source_counter_0_start = node_trigger_source.GetEntryByName('Counter0Start')
        if not PySpin.IsAvailable(entry_trigger_source_counter_0_start)\
                or not PySpin.IsReadable(entry_trigger_source_counter_0_start):
            print('\nUnable to set trigger mode (enum entry retrieval). Aborting...\n')
            return False

        node_trigger_source.SetIntValue(entry_trigger_source_counter_0_start.GetValue())

        # Set Trigger Overlap to Readout
        node_trigger_overlap = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerOverlap'))
        if not PySpin.IsAvailable(node_trigger_overlap) or not PySpin.IsWritable(node_trigger_overlap):
            print('\nUnable to set Trigger Overlap (enumeration retrieval). Aborting...\n')
            return False

        entry_trigger_overlap_ro = node_trigger_overlap.GetEntryByName('ReadOut')
        if not PySpin.IsAvailable(entry_trigger_overlap_ro) or not PySpin.IsReadable(entry_trigger_overlap_ro):
            print('\nUnable to set Trigger Overlap (entry retrieval). Aborting...\n')
            return False

        trigger_overlap_ro = entry_trigger_overlap_ro.GetValue()

        node_trigger_overlap.SetIntValue(trigger_overlap_ro)

        # Turn trigger mode on
        entry_trigger_mode_on = node_trigger_mode.GetEntryByName('On')
        if not PySpin.IsAvailable(entry_trigger_mode_on) or not PySpin.IsReadable(entry_trigger_mode_on):
            print('\nUnable to enable trigger mode (enum entry retrieval). Aborting...\n')
            return False

        node_trigger_mode.SetIntValue(entry_trigger_mode_on.GetValue())

    except PySpin.SpinnakerException as ex:
        print('Error: {}'.format(ex))
        return False

    return result

def acquire_images(cam, nodemap, nodemap_tldevice):
    """
    This function acquires and saves 10 images from a device; please see
    Acquisition example for more in-depth comments on acquiring images.

    :param cam: Camera to acquire images from.
    :param nodemap: Device nodemap.
    :param nodemap_tldevice: Transport layer device nodemap.
    :type cam: CameraPtr
    :type nodemap: INodeMap
    :type nodemap_tldevice: INodeMap
    :return: True if successful, False otherwise.
    :rtype: bool
    """

    print('\n*** IMAGE ACQUISITION ***\n')
    try:
        result = True

        # Set acquisition mode to continuous
        node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
        if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
            print('Unable to set acquisition mode to continuous (enumeration retrieval). Aborting...\n')
            return False

        entry_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
        if not PySpin.IsAvailable(entry_acquisition_mode_continuous)\
                or not PySpin.IsReadable(entry_acquisition_mode_continuous):
            print('Unable to set acquisition mode to continuous (enum entry retrieval). Aborting...\n')
            return False

        acquisition_mode_continuous = entry_acquisition_mode_continuous.GetValue()

        node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

        print('Acquisition mode set to continuous...')

        #  Begin acquiring images
        cam.BeginAcquisition()

        print('Acquiring images...')

        #  Retrieve device serial number for filename
        device_serial_number = ''
        node_device_serial_number = PySpin.CStringPtr(nodemap_tldevice.GetNode('DeviceSerialNumber'))
        if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
            device_serial_number = node_device_serial_number.GetValue()
            print('Device serial number retrieved as {}...'.format(device_serial_number))

        print('')

        # Retrieve, convert, and save images
        for i in range(NUM_IMAGES):
            try:

                #  Retrieve next received image and ensure image completion
                image_result = cam.GetNextImage(1000)

                if image_result.IsIncomplete():
                    print('Image incomplete with image status {} ...'.format(image_result.GetImageStatus()))

                else:

                    #  Print image information; height and width recorded in pixels
                    width = image_result.GetWidth()
                    height = image_result.GetHeight()
                    print('Grabbed image {}, width = {}, height = {}'.format(i, width, height))

                    #  Convert image to mono 8
                    image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)

                    # Create a unique filename
                    if device_serial_number:
                        filename = 'CounterAndTimer-{}-{}.jpg'.format(device_serial_number, i)
                    else:  # if serial number is empty
                        filename = 'CounterAndTimer-{}.jpg'.format(i)

                    #  Save image
                    image_converted.Save(filename)
                    print('Image saved at {}'.format(filename))

                    #  Release image
                    image_result.Release()
                    print('')

            except PySpin.SpinnakerException as ex:
                print('Error: {}'.format(ex))
                return False

        #  End acquisition
        cam.EndAcquisition()

    except PySpin.SpinnakerException as ex:
        print('Error: {}'.format(ex))
        return False

    return result

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

def run_single_camera(cam, exposure_time):
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
        result &= configure_exposure_and_trigger(nodemap, exposure_time)
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

def camera_pipeline(cam_list,exposure_time):

    for i, cam in enumerate(cam_list):

        print('Running example for camera {}...'.format(i))

        run_single_camera(cam,exposure_time)

        print('Camera {} example complete... \n'.format(i))

    return cam

if __name__ == '__main__':
    min_etl_current = -250
    max_etl_current = 250
    current_step = 50
    exposure_time = 4000

    current_list = np.arange(min_etl_current, max_etl_current+1 , current_step).tolist()

    print('Current list steps: ',current_list)
    print('Steps in total: ',len(current_list))

    system, cam_list = config_camera()

    for current in current_list:
        print("Current current level: ", current)
        cam = camera_pipeline(cam_list,exposure_time)
        del cam
    
    release_cam(cam_list,system)
