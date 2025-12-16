# Final Project — ECEN Course

My individual repo for the final project.

## Project Overview
Main documentation:  
[Project Overview Wiki](https://github.com/cu-ecen-aeld/final-project-dylanzflores/wiki/Project-Overview)

## Description
This project translates text captured from a USB camera and displays the translated text on a 1.51-inch OLED display.  
Language selection is done interactively using a rotary encoder wired through GPIO pins.  
Google Cloud Vision API is used for OCR, and Google Cloud Translate API for translations.  

## Requirements / Libraries
To run this project on a Raspberry Pi, install the following Python packages:

```bash
pip install opencv-python
pip install google-cloud-storage
pip install google-cloud-vision
pip install google-cloud-translate
pip install Pillow
pip install RPi.GPIO
