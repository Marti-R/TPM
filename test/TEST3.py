# built-ins
import socket
import json
import multiprocessing
import select
import time
import os

# project modules
import TPM_Utility as util
import Raspberry_Pi_pygame

with open('/home/pi/Desktop/TPM/Raspberry_Pi_settings.json', 'r') as read_file:
    settings = json.load(read_file)
recorder_line = multiprocessing.Array('f', 3)

# processes
record_process = None
screen_pipe, at_screen = multiprocessing.Pipe()


def Func1(*args):
    con.send("0".encode())
    print("Func1")


def Func2(*args):
    print("Func2")


def test_func(instruction_pipe, *args):
    active = False
    record_dict = {}
    trial_start_time = None
    print('init')

    instruction_pipe.send(util.Instructions.Ready)

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
                instruction_pipe.send(util.Instructions.Sending_Records)
                print('SENDING ' + str(len(record_dict)) + ' LINES.')
                instruction_pipe.send(record_dict)
            elif command is util.Instructions.Stop_Experiment:
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
    record_process = multiprocessing.Process(target=Raspberry_Pi_pygame.experiment_loop,
                                             args=(at_screen, settings, True))
    record_process.daemon = True
    record_process.start()


def start_trial(*args):
    screen_pipe.send(util.Instructions.Start_Trial)


def end_trial(*args):
    screen_pipe.send(util.Instructions.End_Trial)


def shutdown_screen(*args):
    global record_process
    screen_pipe.send(util.Instructions.Stop_Experiment)
    print('recorder told to stop')
    record_process.join()
    record_process = None


def get_settings(key=None, *args):
    print(key)
    print(settings.keys())
    if key:
        try:
            con.send('{}: {}'.format(key, settings[key]).encode())
        except KeyError:
            con.send("Unknown setting requested.".encode())
    else:
        con.send(str(settings).encode())


def set_setting(key, value, *args):
    settings[key] = value
    with open('/home/pi/Desktop/TPM/Raspberry_Pi_settings.json', 'w') as write_file:
        json.dump(settings, write_file)
    con.send('{}: {}'.format(key, settings[key]).encode())


def Stop(*args):
    if record_process:
        screen_pipe.send(util.Instructions.Stop_Experiment)
    con.send("shutdown".encode())
    server_socket.close()
    quit()


options = {"test1": Func1,
           "test2": Func2,
           "quit": Stop,
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

    # Create a Server Socket and wait for a client to connect
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except AttributeError:
        # not available on Windows
        pass
    server_socket.bind(('', 6666))
    print("UDPServer Waiting for client on port 6666")
    server_socket.listen(1)
    con, client = server_socket.accept()
    print(con, client)

    # Recive data from client and decide which function to call
    while True:
        # check for external communications
        ready = select.select([con], [], [], 1)
        if ready[0]:
            dataFromClient = con.recv(256)
            try:
                message = dataFromClient.decode().split(' ')
                print(message)
                if len(message) > 1:
                    options[message[0]](*message[1:])
                else:
                    options[message[0]]()
            except KeyError as error:
                con.send("KeyError occured. Function invalid.".encode())
            except TypeError as error:
                print(error)
                con.send("TypeError occured. Probably wrong count or type of argument.".encode())

        print('still alive')
        # check internal communications
        if screen_pipe.poll():
            message = screen_pipe.recv()
            if message is util.Instructions.Ready:
                print('screen is ready')
            elif message is util.Instructions.Sending_Records:
                print('receiving records')
                received_dict = screen_pipe.recv()
                print('RECEIVED ' + str(len(received_dict)) + ' LINES.')
            elif message is util.Instructions.Trial_Aborted:
                print('trial aborted')
            else:
                raise ValueError(f'Unknown message received: {message}')
