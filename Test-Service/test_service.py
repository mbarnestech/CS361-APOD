from dotenv import load_dotenv
import os
import zmq

def get_env_variables():
    load_dotenv()
    socket_number = os.getenv("SOCKET_NUMBER")
    return socket_number

def set_up_client(socket_number):
    context = zmq.Context()
    print("Client attempting to connect to server...")
    socket = context.socket(zmq.REQ) # REQ is the request socket
    socket.connect(f"tcp://localhost:{socket_number}")
    return socket

if __name__ == "__main__":
    socket_number = get_env_variables()
    socket = set_up_client(socket_number)

    while True:
        # wait so I can time sending of message
        message = input("What message should I send? ")
        # send message
        socket.send_string(message)
        # wait for receipt of message from server
        waiting = True
        while waiting:
            pyobj = socket.recv_pyobj()
            if pyobj["status"] != "success":
                print(pyobj["status"])
                waiting = False
                continue
            print(pyobj["apod_dict"])
            waiting = False

