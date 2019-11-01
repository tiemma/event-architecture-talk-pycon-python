import redis
import time
import traceback


def RedisCheck():
    try:
        r = redis.StrictRedis(host='localhost', port=6379)                          # Connect to local Redis instance

        p = r.pubsub()                                                              # See https://github.com/andymccurdy/redis-py/#publish--subscribe
        p.subscribe('MOVED_FOLDER')                                                 # Subscribe to startScripts channel
        PAUSE = True

        while PAUSE:                                                                # Will stay in loop until START message received
            print("Waiting For redisStarter...")
            message = p.get_message()                                               # Checks for message
            if message:
                command = message['data']                                           # Get data from message
                print(command)
                if command == b'START':                                             # Checks for START message
                    PAUSE = False                                                   # Breaks loop

            time.sleep(1)

        print("Permission to start...")

    except Exception as e:
        print("!!!!!!!!!! EXCEPTION !!!!!!!!!")
        print(str(e))
        print(traceback.format_exc())


RedisCheck()