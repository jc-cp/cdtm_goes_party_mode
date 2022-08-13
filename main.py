import os
import sys
import RPi.GPIO as GPIO
import time
import pygame
from os import listdir
from os.path import isfile, join
import array
import threading
import logging
sys.path.append('/usr/local/lib/python3.9/site-packages')
from ola.ClientWrapper import ClientWrapper
# import ray
import multiprocessing
import random


# @ray.remote
class DMX(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.start()
        logging.info("dmx")
        self.universe = 1
        self.wrapper = None
        self.loop_count = 0
        self.TICK_INTERVAL = 100  # in ms

    def run(self):
        while True:
            print('Creating Wrapper')
            def DmxSent(state):
                if not state.Succeeded():
                    wrapper.Stop()

            def SendDMXFrame():
                # schdule a function call in 100ms
                # we do this first in case the frame computation takes a long time.
                wrapper.AddEvent(TICK_INTERVAL, SendDMXFrame)

                # compute frame here
                rgb = [random.randint(1, 255), random.randint(1, 255), random.randint(1, 255)]
                data = array.array('B', rgb)
                global loop_count
                data.append(loop_count % 255)
                loop_count += 1

                # send
                wrapper.Client().SendDmx(universe, data, DmxSent)

            wrapper = ClientWrapper()
            wrapper.AddEvent(TICK_INTERVAL, SendDMXFrame)
            wrapper.Run()
            print('A')

def DMX_process():
    logging.info("dmx")
    def DmxSent(state):
        if not state.Succeeded():
            wrapper.Stop()

    def SendDMXFrame():
        # schdule a function call in 100ms
        # we do this first in case the frame computation takes a long time.
        wrapper.AddEvent(TICK_INTERVAL, SendDMXFrame)

        # compute frame here
        rgb = [random.randint(1,255), random.randint(1,255), random.randint(1,255)]
        data = array.array('B', rgb)
        global loop_count
        data.append(loop_count % 255)
        loop_count += 1

        # send
        wrapper.Client().SendDmx(universe, data, DmxSent)

    print('Creating Wrapper')
    wrapper = ClientWrapper()
    wrapper.AddEvent(TICK_INTERVAL, SendDMXFrame)
    wrapper.Run()


def play_starting_music():
    print("Music Loading...")
    pygame.mixer.music.load("music_lib/starting_music/music_starting_jaq.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue
    time.sleep(0.05)
    pygame.mixer.music.load("music_lib/starting_music/Okay_lets_go.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue


# @ray.remote
class PLAY_AUX(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.start()
        self.button_state = 1

    def run(self):
        counter = 0
        try:
            for song in song_list:
                # print(button_state)
                pygame.mixer.music.load("music_lib/" + str(song))
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    if GPIO.input(11) == GPIO.HIGH and self.button_state == 1:
                        while counter < 9000000:
                            counter += 1
                            print(counter)
                            if GPIO.input(11) == GPIO.LOW and counter <= 50000:
                                print("Next song.")
                                time.sleep(0.25)
                                break
                            elif GPIO.input(11) == GPIO.LOW and counter >= 50000:
                                print("Button was long pushed, music stopped.")
                                self.button_state = 3
                                break
                            else:
                                continue
                        break
                    else:
                        continue
                counter = 0

                if self.button_state == 3:
                    break

        except FileNotFoundError:
            print("No songs available.")
            sys.exit(1)

        finally:
            button_answer.value = 100
            print("Final arg.")
            return


def play_aux(button_state):
    counter = 0
    try:
        for song in song_list:
            # print(button_state)
            pygame.mixer.music.load("music_lib/" + str(song))
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if GPIO.input(11) == GPIO.HIGH and button_state == 1:
                    while counter < 9000000:
                        counter += 1
                        print(counter)
                        if GPIO.input(11) == GPIO.LOW and counter <= 50000:
                            print("Next song.")
                            time.sleep(0.25)
                            break
                        elif GPIO.input(11) == GPIO.LOW and counter >= 50000:
                            print("Button was long pushed, music stopped.")
                            button_state = 3
                            break
                        else:
                            continue
                    break
                else:
                    continue
            counter = 0

            if button_state == 3:
                break

    except FileNotFoundError:
        print("No songs available.")
        sys.exit(1)

    finally:
        # button_answer.value = 100
        print("Final arg.")
        return


def main():
    try:
        print("Waiting for button...")
        time.sleep(1.5)
        while True:
            if GPIO.input(11) == GPIO.HIGH and button_state.value == 0:
                # Button + LED
                print("Button was pushed!")
                # button_state.value = 1
                GPIO.output(13, GPIO.HIGH)

                # Loading music
                play_starting_music()


                # TODO: insert threads here
                logging.info("Main    : before running threads")

                PLAY_AUX()
                DMX()
                #threading.Thread(target=play_aux(button_state.value), args=(1,), daemon=True).start()
                #threading.Thread(target=DMX_process(), args=(2,), daemon=True).start()

                # button_answer = ray.get([play_aux.remote(), DMX_process.remote()])
                # button_answer = play_aux(button_state)
                #x = multiprocessing.Process(target=play_aux(button_state.value))
                #x.start()
                #multiprocessing.Process(target=DMX_process).start()
                #x.join()

                time.sleep(1)
                while True:
                    if button_answer.value == 100:
                        print("button answer", button_answer.value)
                        break
                break
    finally:
        print("Shutting down main.py!")
        GPIO.cleanup()
        sys.exit(0)


if __name__ == "__main__":
    ###### GPIO Vars ######
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)     # to use Raspberry Pi board pin numbers
    GPIO.setup(11, GPIO.IN)
    GPIO.setup(13, GPIO.OUT)
    GPIO.output(13, GPIO.LOW)    # Output set to low per default as the led should be out

    ###### Music Vars ######
    pygame.mixer.init(44100, -16, 1, 1024)

    ####### Button ######
    # global button_state
    #button_state= 0  # =0 when not pressed
    #global button_answer
    #button_answer= 0  # for ending code

    ###### Threading Vars ######
    format = "%(asctime)s: %(message)s"
    #ray.init()

    ###### DMX Vars ######
    universe = 1
    wrapper = None
    loop_count = 0
    TICK_INTERVAL = 100  # in ms

    ###### Generic Vars ######
    cwd = os.getcwd()
    music_path = join(cwd + "/Desktop/party_mode/music_lib/")
    song_list = [f for f in listdir(music_path) if isfile(join(music_path, f))]

    ###### Logging + Start ######
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    # logging.info("Main    : before creating threads")
    logging.info("Main    : before running at all.")

    manager = multiprocessing.Manager()
    button_answer = manager.Value('i', 0)
    button_state = manager.Value('i', 0)

    main()

    logging.info("Main    : wait for the thread to finish")
    # logging.info("Main    : all done")
