# built-ins
import time
from collections import deque
import math
import random as rdm
import os
import sys

# externals
import pygame

# project modules
import TPM_Utility as util


class MarkerLayer:
    def __init__(self, parent, marker_distribution, marker_height,
                 image_location, mirrored=True):
        assert isinstance(parent, pygame.Surface), \
            'Parent must be a Pygame surface.'
        assert isinstance(marker_distribution, tuple) and len(marker_distribution) == 3 and \
               all(i > 0 for i in marker_distribution), \
            'The marker distribution must be a int-tuple of length 3 (left of screen, on screen, right of screen).'
        assert isinstance(marker_height, int) and marker_height > 0, \
            'The marker height must be an integer above 0.'
        assert isinstance(image_location, list) and len(image_location) > 0 and \
               all(isinstance(location, str) for location in image_location), \
            'The image location must be a list of strings, which show the possible images for the markers.'
        assert isinstance(mirrored, bool), \
            'The mirrored flag must be a boolean deciding whether the markers are mirrored at the middle of the screen.'

        self.parent = parent
        self.size = parent.get_size()
        self.surface = pygame.Surface(self.size)

        self.rectangle = self.surface.get_rect()
        self.background_color = (0, 0, 0)
        self.surface.fill(self.background_color)
        self.marker_height = marker_height
        self.image_location = image_location
        self.mirrored = mirrored
        self.markers = deque(maxlen=sum(marker_distribution))

        _surf = [None] * sum(marker_distribution)
        _rect = [None] * sum(marker_distribution)

        for i in range(sum(marker_distribution)):
            loaded_image = pygame.image.load(image_location[rdm.randint(0, len(image_location) - 1)])
            zoom_factor = marker_height / loaded_image.get_height()
            if self.mirrored:
                _surf[i] = [pygame.transform.rotozoom(loaded_image, 0, zoom_factor),
                            pygame.transform.flip(pygame.transform.rotozoom(loaded_image, 180, zoom_factor),
                                                  True, False)]
            else:
                _surf[i] = pygame.transform.rotozoom(loaded_image, 0, zoom_factor)

        self.location_pointer = _surf[marker_distribution[0]][0].get_width() / 2
        self.space = parent.get_width() / marker_distribution[1]
        self.left_spawn = -(marker_distribution[0] * self.space)
        self.right_spawn = parent.get_width() + marker_distribution[2] * self.space

        for i in range(sum(marker_distribution)):
            if self.mirrored:
                _rect[i] = [_surf[i][0].get_rect(), _surf[i][1].get_rect()]
                _rect[i][0].center = [(-marker_distribution[0] + i) * self.space
                                      + self.location_pointer, parent.get_height() * 1 / 4]
                _rect[i][1].center = [(-marker_distribution[0] + i) * self.space
                                      + self.location_pointer, parent.get_height() * 3 / 4]
            else:
                _rect[i] = _surf[i][0].get_rect()
                _rect[i].center = [(-marker_distribution[0] + i) * self.space
                                   + self.location_pointer, parent.get_height() * 2 / 4]

            wobble_x_abs = int(self.space / 3)
            wobble_x_random = rdm.randint(-wobble_x_abs, wobble_x_abs)

            if self.mirrored:
                wobble_y_abs = int(parent.get_height() / 4 - _rect[i][0].height / 2)
                wobble_y_random = rdm.randint(-wobble_y_abs, wobble_y_abs)
                _rect[i] = [_rect[i][0].move(wobble_x_random, wobble_y_random),
                            _rect[i][1].move(wobble_x_random, -wobble_y_random)]
                self.markers.append([[_surf[i][0], _rect[i][0]], [_surf[i][1], _rect[i][1]]])

            else:
                wobble_y_abs = int((parent.get_width() / 2))
                wobble_y_random = rdm.randint(-wobble_y_abs, wobble_y_abs)
                _rect[i] = _rect[i].move(wobble_x_random, wobble_y_random)
                self.markers.append([_surf[i], _rect[i]])
        print("init")
        self.move(0)

    def move(self, delta):
        self.surface.fill(self.background_color)
        self.location_pointer += delta

        if self.location_pointer < 0 or self.location_pointer > self.space:
            if self.location_pointer < 0:
                spawn = self.right_spawn
            else:
                spawn = self.left_spawn

            loaded_image = pygame.image.load(self.image_location[rdm.randint(0, len(self.image_location) - 1)])
            zoom_factor = self.marker_height / loaded_image.get_height()
            if self.mirrored:
                _surf = [pygame.transform.rotozoom(loaded_image, 0, zoom_factor),
                         pygame.transform.flip(pygame.transform.rotozoom(loaded_image, 180, zoom_factor),
                                               True, False)]

                _rect = [_surf[0].get_rect(),
                         _surf[1].get_rect()]
                _rect[0].center = [spawn, self.parent.get_height() * 1 / 4]
                _rect[1].center = [spawn, self.parent.get_height() * 3 / 4]
                wobble_y_abs = int(self.parent.get_height() / 4 - _rect[0].height / 2)
                wobble_y_random = rdm.randint(-wobble_y_abs, wobble_y_abs)
            else:
                _surf = pygame.transform.rotozoom(loaded_image, 0, zoom_factor)
                _rect = _surf.get_rect()
                _rect.center = [spawn, self.parent.get_height() * 2 / 4]
                wobble_y_abs = int(self.parent.get_height() / 2)
                wobble_y_random = rdm.randint(-wobble_y_abs, wobble_y_abs)

            wobble_x_abs = int(self.space / 3)
            wobble_x_random = rdm.randint(-wobble_x_abs, wobble_x_abs)

            if self.mirrored:
                _rect = (_rect[0].move(wobble_x_random, wobble_y_random),
                         _rect[1].move(wobble_x_random, -wobble_y_random))
                new_marker = [[_surf[0], _rect[0]], [_surf[1], _rect[1]]]
            else:
                _rect = _rect.move(wobble_x_random, wobble_y_random)
                new_marker = [_surf, _rect]

            if self.location_pointer < 0:
                self.markers.append(new_marker)
                print("append right")
            else:
                self.markers.appendleft(new_marker)
                print("append left")

            self.location_pointer = self.location_pointer % self.space

        for i in range(0, len(self.markers)):
            if self.mirrored:
                self.markers[i][0][1] = self.markers[i][0][1].move(delta, 0)
                self.markers[i][1][1] = self.markers[i][1][1].move(delta, 0)
                self.surface.blit(*self.markers[i][0])
                self.surface.blit(*self.markers[i][1])
            else:
                self.markers[i][1] = self.markers[i][1].move(delta, 0)
                self.surface.blit(*self.markers[i])

    def blit_to_parent(self):
        self.parent.blit(self.surface, self.rectangle)


def experiment_loop(instruction_pipe, settings, simulation=False):
    try:
        os.nice(-20)
    except AttributeError:
        # not available on Windows
        pass

    pygame.init()
    # clock = pygame.time.Clock()

    reward_length = 5

    show_fps = True
    target_fps = 60

    black = (0, 0, 0)  # Background-color (black)
    warning_color = (255, 0, 0)  # Warning-color for failed trials (red)
    starting_color = (0, 255, 0)  # Starting-color to mark beginning of a new trial (green)

    ahead_buffer = 2  # Buffered objects in front of the mouse
    onscreen_objects = 4  # Objects currently on-screen
    behind_buffer = 2  # Buffered objects behind the mouse

    # Load settings
    acceleration_cutoff = settings["acceleration_cutoff"]
    reward_abort = settings["reward_abort"]
    tube_out = settings["tube_out"]
    disk_out = settings["disk_out"]
    if settings["main_screen_direction_left"]:
        screen_direction = -1
    else:
        screen_direction = 1

    marker_height = settings["marker_height"]
    speed_multiplier = settings["speed_multiplier"]
    p_cm_ratio = settings["p_cm_ratio"]

    wheel_diameter = settings["wheel_diameter"]
    tube_distance = settings["tube_distance"]
    wheel_circumference = math.pi * wheel_diameter

    marker_locations = [f'/home/pi/Desktop/TPM/markers/{file}' for file in os.listdir('/home/pi/Desktop/TPM/markers') if
                        file.endswith('.gif')]

    font = pygame.font.SysFont('Comic Sans MS', 30)

    SCREEN = pygame.display.set_mode((settings['screen_pixel_width'], settings['screen_pixel_height']),
                                     pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)

    SCREEN_SIZE = SCREEN.get_size()

    # Create Screen objects
    experiment_screen = MarkerLayer(SCREEN, (ahead_buffer, onscreen_objects, behind_buffer),
                                    marker_height, marker_locations)

    print('test')

    # Prepare visual output (if needed)
    if simulation:
        visual_output = [[None, None], [None, None]]
        visual_output[0][0] = pygame.transform.rotozoom(pygame.image.load("/home/pi/Desktop/TPM/simulation/Tube.gif"),
                                                        0, 0.25)
        visual_output[0][1] = pygame.transform.rotozoom(pygame.image.load("/home/pi/Desktop/TPM/simulation/Disk.gif"),
                                                        0, 0.25)
        visual_output[1][0] = visual_output[0][0].get_rect()
        visual_output[1][0].center = [200, 50]
        visual_output[1][1] = visual_output[0][1].get_rect()
        visual_output[1][1].center = [1000, 50]

    # Else import and prepare the Raspberry Pi communication with the ADC and the PWM pins
    else:
        # Prepare the PWM-pin to be written on
        import pigpio
        pi = pigpio.pi()
        pi.hardware_PWM(tube_out, 500, 100000)
        pi.hardware_PWM(disk_out, 500, 100000)
        print("PiGPIO PWM initialized.")

        # Prepare the i2c communication
        import board
        import busio
        i2c = busio.I2C(board.SCL, board.SDA)
        print("I2C initialized.")

        # Prepare the ADC-object
        import adafruit_ads1x15.ads1115 as ADS
        from adafruit_ads1x15.analog_in import AnalogIn
        ads = ADS.ADS1115(i2c)
        ads.gain = 2 / 3
        print("ADC initialized.")

        # Prepare position channel to be read
        position_channel = AnalogIn(ads, ADS.P0)
        velocity_channel = AnalogIn(ads, ADS.P1)
        print("Channels initialized.")

    print('test')

    disk_state = 0
    disk_names = ["Blocked", "Visual", "Smell", "Opened"]

# Writing the disk-movement
    if simulation:
        visual_output[0][1] = pygame.transform.rotozoom(pygame.image.load("/home/pi/Desktop/TPM/simulation/Disk.gif"),
                                                        -90 + disk_state * -90, 0.25)
        visual_output[1][1] = visual_output[0][1].get_rect()
        visual_output[1][1].center = [1000, 50]
    else:
        pi.hardware_PWM(disk_out, 500, int(disk_state * 0.25 * 500000) + 100000)

    record_dict = {}
    print('test')

    trial_start_time = time.perf_counter()
    start_time = time.perf_counter()
    print('test')

    if show_fps:
        start_time = trial_start_time
        x = 0.5
        counter = 0
        text_surface = pygame.Surface((100, 100))

    if simulation:
        position_volt = 0
        virtual_speed = 0
        last_frame = trial_start_time

    else:
        position_volt = position_channel.voltage

    absolute_position = 0
    tube_position = 0
    old_position_volt = position_volt
    old_delta_position_volt = 0

    active = False
    tube_contact = False
    print('init')

    instruction_pipe.send(util.Instructions.Ready)

    # Trial-phase loop
    while True:
        # Check for new instructions
        if instruction_pipe.poll():
            command = instruction_pipe.recv()
            if command is util.Instructions.Start_Trial:
                active = True
                record_dict = {}
                trial_start_time = time.perf_counter()
            elif command is util.Instructions.End_Trial:
                active = False
                tube_position = 0
                instruction_pipe.send(util.Instructions.Sending_Records)
                print('SENDING ' + str(len(record_dict)) + ' LINES.')
                instruction_pipe.send(record_dict)
            elif command is util.Instructions.Stop_Experiment:

                break
            else:
                raise ValueError(f'Unknown command received: {command}')

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            # Virtual input
            if simulation and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    virtual_speed += 0.1
                elif event.button == 5:
                    virtual_speed -= 0.1

        # Filling screen and showing starting signal
        if time.time() < trial_start_time + 1.2:
            if int((time.time() - trial_start_time) / 0.2) % 2 != 0:
                SCREEN.fill(starting_color)
            else:
                SCREEN.fill(black)
        else:
            SCREEN.fill(black)

        # clock.tick(target_fps)

        timestamp_volt = time.perf_counter() - trial_start_time

        if simulation:
            if virtual_speed < -2.5:
                virtual_speed = -2.5
            elif virtual_speed > 2.5:
                virtual_speed = 2.5

            position_volt += virtual_speed * (1. / target_fps)

            if position_volt < 0:
                position_volt = 5
            if position_volt > 5:
                position_volt = 0

        else:
            position_volt = position_channel.voltage

        delta_position_volt = position_volt - old_position_volt
        old_position_volt = position_volt
        delta2_position_volt = delta_position_volt - old_delta_position_volt

        if abs(delta2_position_volt) > acceleration_cutoff:
            continue

        delta_position_real = delta_position_volt / 5.033 * wheel_circumference

        if active and abs(speed_multiplier * p_cm_ratio * delta_position_real) > 1:
            tube_position += speed_multiplier * delta_position_real

        if tube_contact:
            if tube_position < reward_abort * tube_distance:
                tube_position = 0

                tube_contact = False
                active = False

                instruction_pipe.send(util.Instructions.Trial_Aborted)
                continue

            elif tube_position > tube_distance:
                tube_position = tube_distance

            if not simulation:
                pi.hardware_PWM(tube_out, 500, int(500000) + 100000)

        else:
            if tube_position < 0:
                tube_position = 0

            elif tube_position > 0.95 * tube_distance:
                tube_position = tube_distance
                tube_contact = True

            if not simulation:
                pi.hardware_PWM(tube_out, 500, int(tube_position / tube_distance * 500000) + 100000)

        absolute_position += delta_position_real

        # Moving the markers
        shift = screen_direction * speed_multiplier * p_cm_ratio * delta_position_real
        experiment_screen.move(shift)
        experiment_screen.blit_to_parent()

        timestamp_shift = time.perf_counter() - trial_start_time

        record_dict[timestamp_volt] = {
            'position_volt': position_volt,
            'timestamp_shift': timestamp_shift,
            'position_cm': absolute_position
        }

        if simulation:
            if tube_contact:
                visual_output[1][0].center = [200 + 20 * tube_distance, 50]
            else:
                visual_output[1][0].center = [200 + 20 * tube_position, 50]
            SCREEN.blit(visual_output[0][0], visual_output[1][0])
            SCREEN.blit(visual_output[0][1], visual_output[1][1])

            if tube_contact:
                phase = 'Reward'
            elif active:
                phase = 'Trial'
            else:
                phase = 'Inactive'

            text = [f"Phase: {phase}",
                    f"Screen speed: {speed_multiplier * delta_position_real / (timestamp_volt - last_frame)}",
                    f"Volt position [in V]: {position_volt}",
                    f"Volt delta [in V]: {delta_position_volt}",
                    f"Virtual position [in cm]: {tube_position}",
                    f"Current disk state: {disk_names[disk_state]}"]

            last_frame = timestamp_volt

            for i, l in enumerate(text):
                render = font.render(l, 0, (255, 255, 255))
                SCREEN.blit(render, (SCREEN_SIZE[0] - render.get_size()[0], 0 + font.get_linesize() * i))

        if show_fps:
            counter += 1
            if (time.perf_counter() - start_time) > x:
                my_font = pygame.font.SysFont('Comic Sans MS', 30)
                text_surface = my_font.render(f'FPS: {int(counter / (time.perf_counter() - start_time))}',
                                              False, (255, 255, 255))
                start_time = time.perf_counter()
                counter = 0
            SCREEN.blit(text_surface, (0, 0))

        pygame.display.flip()

    pygame.display.quit()
    pygame.quit()
    print('im closed')
