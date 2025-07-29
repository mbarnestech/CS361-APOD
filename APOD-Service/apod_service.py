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
load_dotenv()

socket_number = os.getenv("PORT_APOD")
api_key = os.getenv("APOD_API_KEY")


def set_up_server(socket_number):
    context = zmq.Context()
    socket = context.socket(zmq.REP)  # REP is the reply socket
    socket.bind(f"tcp://*:{socket_number}")
    print(f"APOD microservice listening on tcp://*:{socket_number}...")
    return socket


def get_data(api_key, date):
    """
    based on / adapted from helper get_data function here: the nasa helper file: https://github.com/nasa/apod-api/blob/master/apod_parser/apod_object_parser.py
    """
    url = f'https://api.nasa.gov/planetary/apod?api_key={api_key}'
    if date:
        url = url + f"&date={date}"
    raw_response = requests.get(url).text
    response = json.loads(raw_response)
    return response


def get_apod_dict(response):
    apod_dict = {
        "date": response["date"],
        "explanation": response["explanation"],
        "title": response["title"],
        "url": response.get("hdurl") or response.get("url") or "No URL",
    }
    return apod_dict


def show_image(url, media_type):
    if media_type == "image":
        # next three lines of code adapted from https://www.geeksforgeeks.org/python/how-to-open-an-image-from-the-url-in-pil/#
        suffix = get_match(r"\.{1}\w{3,4}$", url)
        apod_file = f"./apod{suffix}"
        urllib.request.urlretrieve(url, apod_file)
        img = Image.open(apod_file)
        img.show()
        time.sleep(1)
        os.remove(apod_file)
        return "Image Shown"
    else:
        return "Image Not Shown"


def get_match(regex_expression, string):
    substring = ""
    substringMatch = re.search(regex_expression, string)
    if substringMatch:
        substring = substringMatch.group()
    return substring


def parse_message(message, api_key):
    messageString = message.decode()
    # make sure message is meant for this service
    if messageString[0] != "4":
        return False, None, None

    # get whether to show picture (default is yes)
    show = "text" not in messageString

    # get date (default is today)
    date = get_match(r"\d{4}-\d{2}-\d{2}", messageString[1:])

    # get information from apod
    response = get_data(api_key, date)
    apod_dict = get_apod_dict(response)

    # show image if not instructed not to
    if show:
        result = show_image(apod_dict["url"], response["media_type"])
        return True, apod_dict, result

    # return
    return True, apod_dict, "Image Not Requested"


if __name__ == "__main__":
    socket = set_up_server(socket_number)
    dateRegex = r"\d{4}-\d{2}-\d{2}"

    while True:
        # get and parse message
        message = socket.recv()
        is_success, apod_dict, image_status = parse_message(message, api_key)
        if is_success:
            socket.send_pyobj({"status": "success", "apod_dict": apod_dict, "image_status": image_status})
        else:
            socket.send_pyobj({"status": "invalid request"})
