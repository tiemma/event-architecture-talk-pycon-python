import datetime
import time
from termcolor import colored
from flask import g, request, Flask
from redis import StrictRedis
from rfc3339 import rfc3339
from server_timing import Timing
from uuid import uuid4
from os import mkdir, path, rename
from json import loads, decoder, dumps
from requests import post


app = Flask(__name__)
t = Timing(app, force_debug=True)
user_data = {}
redisClient = StrictRedis(host="localhost", port=6379)
redisClient.pubsub()


@app.before_request
def start_timer():
    g.start = time.time()


@app.after_request
def log_request(response):
    if request.path == "/favicon.ico":
        return response
    elif request.path.startswith("/static"):
        return response

    now = time.time()
    duration = round(now - g.start, 2)
    dt = datetime.datetime.fromtimestamp(now)
    timestamp = rfc3339(dt, utc=True)

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    host = request.host.split(":", 1)[0]
    args = dict(request.args)

    log_params = [
        ("method", request.method, "blue"),
        ("path", request.path, "blue"),
        ("status", response.status_code, "yellow"),
        ("duration", duration, "green"),
        ("time", timestamp, "magenta"),
        ("ip", ip, "red"),
        ("host", host, "red"),
        ("params", args, "blue"),
        ("headers", "\n{}".format(request.headers), "cyan")
    ]

    request_id = request.headers.get("X-Request-ID")
    if request_id:
        log_params.append(("request_id", request_id, "yellow"))

    parts = []
    for name, value, color in log_params:
        part = colored("{}={}".format(name, value), color)
        parts.append(part)
    line = " ".join(parts)
    app.logger.info(line)

    return response


def create_folders(data):
    curr_path = "./static/{}".format(uuid4())
    new_path = "./static/{}".format(uuid4())
    if "user" in curr_path:
        new_path += "-user"
    elif "folder" in curr_path:
        new_path += "-folder"
    try:
        data = loads(data)
        curr_path = "./static/{}".format(data["path"])
    except decoder.JSONDecodeError as e:
        app.logger.error("Error occurred: {error} ON DATA {data}".format(error=e, data=data))

    status = "CREATED_FOLDER"
    message = "The folder was created successfully"
    resp = {"path": curr_path, "new_path": new_path}

    if path.exists(curr_path):
        status = "MOVED_FOLDER"
        message = "The folder {path} already exists, moved to {new_path}".format(path=curr_path, new_path=new_path)
        rename(curr_path, new_path)
    else:
        mkdir(curr_path)
        del resp["new_path"]

    return {
        "data": resp,
        "method": request.method,
        "status": status,
        "message": message
    }


def publish(event, data):
    try:

        app.logger.info("REDIS  - Publishing event {} with {}".format(event, data))
        redisClient.publish(event, data)
        app.logger.info("Done publishing event successfully")

    except Exception as e:
        print("!!!!!!!!!! EXCEPTION !!!!!!!!!")
        print(str(e))


@app.route("/write", methods=["POST"])
@t.timer(name="write-without-events")
def create_user_folders():
    resp = create_folders(request.data)
    post("http://localhost:3000/{}".format(resp["status"]), data=resp["data"])
    return resp


@app.route("/events/write", methods=["POST"])
@t.timer(name="write-with-events")
def create_folders_with_events():
    data = loads(request.data)
    data["path"] = "{}-user".format(data["path"])
    resp = create_folders(dumps(data))
    publish(resp["status"], dumps(resp))
    return resp


@app.route("/events/write.user.pattern", methods=["POST"])
@t.timer(name="write-with-user-events-pattern")
def create_folders_with_user_events():
    data = loads(request.data)
    data["path"] = "{}-user".format(data["path"])
    resp = create_folders(dumps(data))
    publish("user.{}".format(resp["status"]), dumps(resp))
    return resp


@app.route("/events/write.folder.pattern", methods=["POST"])
@t.timer(name="write-with-folder-events-pattern")
def create_folders_with_folder_events():
    data = loads(request.data)
    data["path"] = "{}-folder".format(data["path"])
    resp = create_folders(dumps(data))
    publish("folder.{}".format(resp["status"]), dumps(resp))
    return resp


if __name__ == "__main__":
    app.run(debug=True)

