# external imports
import os
import zmq
import requests
import json
from dotenv import load_dotenv
import urllib.request
import time
from PIL import Image
import re

def get_env_variables():
    load_dotenv()
    socket_number = os.getenv("SOCKET_NUMBER")
    api_key = os.getenv("APOD_API_KEY")
    return socket_number, api_key

def set_up_server(socket_number):
    context = zmq.Context()
    socket = context.socket(zmq.REP) # REP is the reply socket
    socket.bind(f"tcp://*:{socket_number}")
    return socket


def get_data(api_key, date):
    """
    based on / adapted from helper get_data function here: the nasa helper file: https://github.com/nasa/apod-api/blob/master/apod_parser/apod_object_parser.py
    """
    url = f'https://api.nasa.gov/planetary/apod?api_key={api_key}'
    if date:
        url = url + f"date={date}"
    raw_response = requests.get(f'https://api.nasa.gov/planetary/apod?api_key={api_key}').text
    response = json.loads(raw_response)
    return response

def get_apod_dict(response):
    apod_dict = {
        "date": response["date"],
        "explanation": response["explanation"],
        "title": response["title"],
        "url": response["url"],
    }
    return apod_dict

def show_image(url, media_type):
    if media_type == "image":
        # next three lines of code adapted from https://www.geeksforgeeks.org/python/how-to-open-an-image-from-the-url-in-pil/#
        urllib.request.urlretrieve(url, "./apod.jpg")
        img = Image.open("./apod.jpg")
        img.show()
        time.sleep(5)
        os.remove("./apod.jpg")
        return "image shown"
    else:
        return "incorrect media type; image not shown"


if __name__ == "__main__":
    socket_number, api_key = get_env_variables()
    socket = set_up_server(socket_number)
    dateRegex = r"\d{4}-\d{2}-\d{2}"

    while True:
        # get and parse message
        message = socket.recv()
        messageString = message.decode()
        if messageString[0] != "3":
            socket.send_pyobj({"status": "invalid request"})
            continue
        show = "show" in messageString
        dateMatch = re.search(dateRegex, messageString[1:])
        date = ""
        if dateMatch:
            date = dateMatch.group()
        

        response = get_data(api_key, date)
        apod_dict = get_apod_dict(response)

        if show:
            result = show_image(apod_dict["url"], response["media_type"])
        
        socket.send_pyobj({"status": "success", "apod_dict": apod_dict})

        

        
