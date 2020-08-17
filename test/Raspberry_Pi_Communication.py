# built-ins
import socket
import json
import multiprocessing
import select
import time
import os
from subprocess import call

# project modules
from TPM_Utility import Instructions
import Raspberry_Pi_Setup_Control

with open('/home/pi/Desktop/TPM/Raspberry_Pi_settings.json', 'r') as read_file:
    settings = json.load(read_file)

# processes
record_process = None
screen_pipe, at_screen = multiprocessing.Pipe()


def Func1(*args):
    conn.send("0".encode())
    print("Func1")


def Func2(*args):
    print("Func2")


def test_func(instruction_pipe, *args):
    active = False
    record_dict = {}
    trial_start_time = None
    print('init')

    instruction_pipe.send(Instructions.Ready)

    while True:
        # Check for new instructions
        if instruction_pipe.poll():
            command = instruction_pipe.recv()
            if command is Instructions.Start_Trial:
                active = True
                record_dict = {}
                trial_start_time = time.perf_counter()
            elif command is Instructions.End_Trial:
                active = False
                instruction_pipe.send(Instructions.Sending_Records)
                print('SENDING ' + str(len(record_dict)) + ' LINES.')
                instruction_pipe.send(record_dict)
            elif command is Instructions.Stop_Experiment:
                break
            else:
                raise ValueError(f'Unknown command received: {command}')

        if not active:
            continue

        now = time.perf_counter()
        record_dict[now] = now - trial_start_time

        print('im active')

    print('im closed')


def init_screen(*args):
    global record_process
    record_process = multiprocessing.Process(target=Raspberry_Pi_Setup_Control.experiment_loop,
                                             args=(at_screen, settings),
                                             kwargs={'simulation': settings['simulation'],
                                                     'target_fps': settings['target_fps'],
                                                     'show_fps': settings['show_fps']})
    record_process.daemon = True
    record_process.start()


def start_trial(*args):
    screen_pipe.send(Instructions.Start_Trial)


def end_trial(*args):
    screen_pipe.send(Instructions.End_Trial)


def shutdown_screen(*args):
    global record_process
    screen_pipe.send(Instructions.Stop_Experiment)
    print('recorder told to stop')
    record_process.join()
    record_process = None


def get_settings(key=None, *args):
    print(key)
    print(settings.keys())
    if key:
        try:
            conn.send('{}: {}'.format(key, settings[key]).encode())
        except KeyError:
            conn.send("Unknown setting requested.".encode())
    else:
        conn.send(str(settings).encode())


def set_setting(key, value, *args):
    settings[key] = value
    with open('/home/pi/Desktop/TPM/Raspberry_Pi_settings.json', 'w') as write_file:
        json.dump(settings, write_file)
    conn.send('{}: {}'.format(key, settings[key]).encode())


def end(with_poweroff=False, *args):
    if record_process:
        screen_pipe.send(Instructions.Stop_Experiment)
        record_process.join()
    conn.send("shutdown".encode())
    server_socket.close()
    if with_poweroff:
        call("sudo shutdown --poweroff now", shell=True)
    else:
        quit()


def shutdown(*args):
    end(with_poweroff=True)


options = {"test1": Func1,
           "test2": Func2,
           'end': end,
           'shutdown': shutdown,
           'get_settings': get_settings,
           'set_setting': set_setting,
           '1': init_screen,
           '2': start_trial,
           '3': end_trial,
           '4': shutdown_screen,
           }

if __name__ == '__main__':
    try:
        os.nice(-20)
    except AttributeError:
        # not available on Windows
        pass

    # Create a Server Socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', 6666))

    while True:
        print("Raspberry Pi listening on socket 6666")
        server_socket.listen(1)     # wait for a client to connect
        conn, client = server_socket.accept()
        print(conn, client)

        # Receive data from client and decide which function to call
        while True:
            # external communications
            try:    # check if select fails
                ready_to_read, ready_to_write, in_error = \
                    select.select([conn], [conn], [], 1)
                if len(ready_to_read) > 0:
                    dataFromClient = conn.recv(256)
                    try:
                        message = dataFromClient.decode().split(' ')
                        if len(message) > 1:
                            options[message[0]](*message[1:])
                        else:
                            options[message[0]]()
                    except KeyError as error:
                        conn.send("KeyError occured. Function invalid.".encode())
                    except TypeError as error:
                        conn.send("TypeError occured. Probably wrong count or type of argument.".encode())
            except select.error as error:
                conn.close()
                print(f'Select Error: {error}')
                break
            except socket.error as error:
                conn.close()
                print(f'Socket Error: {error}')
                break

            # internal communications
            if screen_pipe.poll():
                message = screen_pipe.recv()
                if message is Instructions.Ready:
                    print('screen is ready')
                elif message is Instructions.Sending_Records:
                    print('receiving records')
                    received_dict = screen_pipe.recv()
                    print('RECEIVED ' + str(len(received_dict)) + ' LINES.')
                elif message is Instructions.Trial_Aborted:
                    print('trial aborted')
                else:
                    raise ValueError(f'Unknown message received: {message}')
