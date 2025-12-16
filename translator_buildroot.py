# ------------------------------------------------------
# TRANSLATION + OLED DISPLAY SCRIPT + ROTARY MENU
# ------------------------------------------------------

import cv2
from google.cloud import storage
from google.cloud import vision
from google.cloud import translate_v2 as translate
import pandas as pd
import os
import time
import sys
import logging
import timeit

# ⭐ ADD OLED LIBRARY PATH ⭐
sys.path.append('/home/dylan/Senior_Design/lib')

from PIL import Image, ImageDraw, ImageFont
from waveshare_OLED import OLED_1in51

# ------------------------------------------------------
# Start timer
# ------------------------------------------------------
start = timeit.default_timer()

# ------------------------------------------------------
# Google Cloud Setup
# ------------------------------------------------------
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/dylan/Senior_Design/sdtesting-381922-e0eaf737e0c8.json'
storage_client = storage.Client()
translate_client = translate.Client()
vision_client = vision.ImageAnnotatorClient()

# ------------------------------------------------------
# OLED Initialize
# ------------------------------------------------------
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "pic")

disp = OLED_1in51.OLED_1in51()
disp.Init()
disp.clear()

# ------------------------------------------------------
# Helper display function
# ------------------------------------------------------
def disp_OLED(text, x_offset):
    image1 = Image.new('1', (disp.width, disp.height), "WHITE")
    draw = ImageDraw.Draw(image1)
    font1 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 14)

    # Border
    draw.line([(0,1),(127,2)], fill=0)
    draw.line([(0,1),(0,63)], fill=0)
    draw.line([(0,63),(127,63)], fill=0)
    draw.line([(127,1),(127,63)], fill=0)

    draw.text((x_offset, 20), text, font=font1, fill=0)
    disp.ShowImage(disp.getbuffer(image1))

# ------------------------------------------------------
# LANGUAGE SELECTION MENU (ROTARY ENCODER)
# ------------------------------------------------------

LANG_OPTIONS = [
    ("Afrikaans", "af"),
    ("Arabic", "ar"),
    ("Chinese", "zh"),
    ("Czech", "cs"),
    ("Danish", "da"),
    ("Dutch", "nl"),
    ("English", "en"),
    ("Finnish", "fi"),
    ("French", "fr"),
    ("German", "de"),
    ("Greek", "el"),
    ("Hebrew", "he"),
    ("Hindi", "hi"),
    ("Hungarian", "hu"),
    ("Italian", "it"),
    ("Japanese", "ja"),
    ("Korean", "ko"),
    ("Norwegian", "no"),
    ("Polish", "pl"),
    ("Portuguese", "pt"),
    ("Romanian", "ro"),
    ("Russian", "ru"),
    ("Spanish", "es"),
    ("Swedish", "sv"),
    ("Thai", "th"),
    ("Turkish", "tr"),
    ("Ukrainian", "uk"),
    ("Vietnamese", "vi")
]


current_lang = 0

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

# Rotary encoder pins (YOUR WIRING)
CLK = 17
DT  = 18
SW  = 22

GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW,  GPIO.IN, pull_up_down=GPIO.PUD_UP)

def show_language_option(idx):
    disp_OLED("  Select : " + LANG_OPTIONS[idx][0], 0)

# Show first option
show_language_option(current_lang)

# ---- ROTARY MENU LOOP ----
last_state = GPIO.input(CLK)
select_done = False

while not select_done:
    clk_state = GPIO.input(CLK)
    dt_state  = GPIO.input(DT)

    # Detect rotation
    if clk_state != last_state:
        if dt_state != clk_state:
            current_lang = (current_lang + 1) % len(LANG_OPTIONS)
        else:
            current_lang = (current_lang - 1) % len(LANG_OPTIONS)

        show_language_option(current_lang)
        time.sleep(0.15)

    last_state = clk_state

    # Detect button press
    if GPIO.input(SW) == 0:
        time.sleep(0.2)   # debounce
        select_done = True

# Final selection
target_lang = LANG_OPTIONS[current_lang][1]
disp_OLED("Chosen: " + LANG_OPTIONS[current_lang][0], 5)
time.sleep(1.5)
disp.clear()

print("Language selected:", LANG_OPTIONS[current_lang])

# ------------------------------------------------------
# Capture image from camera
# ------------------------------------------------------
cam = cv2.VideoCapture(0)
ret, frame = cam.read()
cam.release()

if not ret:
    print("Camera failed to capture image.")
    sys.exit()

cv2.imwrite('/home/dylan/Senior_Design/img.jpg', frame)
print("Image captured.\n")

# ------------------------------------------------------
# Upload to Google Cloud bucket
# ------------------------------------------------------
bucket = storage_client.bucket('imageprocessing')
blob = bucket.blob('img.jpg')
blob.upload_from_filename('/home/dylan/Senior_Design/img.jpg')
print("Image uploaded to bucket.\n")

# ------------------------------------------------------
# OCR with Google Vision
# ------------------------------------------------------
image_uri = vision.Image(
    source=vision.ImageSource(image_uri='gs://imageprocessing/img.jpg')
)
response = vision_client.text_detection(image=image_uri)
texts = response.text_annotations

if not texts:
    detected_text = None
else:
    detected_text = texts[0].description.strip()

print("OCR Result:", detected_text, "\n")

# ------------------------------------------------------
# No text found
# ------------------------------------------------------
if not detected_text:
    disp_OLED("No text found", 10)
    time.sleep(3)
    disp.clear()
    GPIO.cleanup()
    sys.exit()

# ------------------------------------------------------
# Translate text
# ------------------------------------------------------
translated = translate_client.translate(
    detected_text,
    target_language=target_lang
)["translatedText"]

print("Translated text:", translated, "\n")

stop = timeit.default_timer()
print("Total time:", stop - start, "seconds\n")

# ------------------------------------------------------
# Display translation on OLED
# ------------------------------------------------------
if len(translated) < 20:
    disp_OLED(translated, 7)
    time.sleep(5)

else:
    print("Scrolling on OLED...")
    for x in range(0, -(len(translated)*7), -5):
        disp_OLED(translated, x)
        time.sleep(0.1)

disp.clear()
GPIO.cleanup()
