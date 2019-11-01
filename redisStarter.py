import redis
import time
import traceback
from json import dumps

def WorkCheck():
    try:

        # HERE SOME INITIAL WORK IS DONE THAT SCRIPTS 1 & 2 NEED TO WAIT FOR
        # IDs SERIAL PORTS
        # SAVE TO db

        r = redis.StrictRedis(host='localhost', port=6379)                # Connect to local Redis instance

        p = r.pubsub()                                                    # See https://github.com/andymccurdy/redis-py/#publish--subscribe

        print("Starting main scripts...")

        data = {"curr_path": "./static/e8bc2dd3-a3b3-4cb4-98e8-64c13fe33b03"}
        r.publish('MOVED_FOLDER', dumps(data))                                # PUBLISH START message on startScripts channel

        print("Done")

    except Exception as e:
        print("!!!!!!!!!! EXCEPTION !!!!!!!!!")
        print(str(e))
        print(traceback.format_exc())

WorkCheck()