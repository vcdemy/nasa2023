import skimage
import time
from glob import glob
import numpy as np
import cv2
from pydub import AudioSegment
import gradio as gr

piano_notes = ['A2', 'B2', 'C3', 'D3', 'E3', 'F3', 'G3',
               'A3', 'B3', 'C4', 'D4', 'E4', 'F4', 'G4',
               'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5',
               'A5', 'B5', 'C6', 'D6', 'E6', 'F6', 'G6']

piano_sounds = []

for i in range(len(piano_notes)):
    piano_sounds.append(AudioSegment.from_file(f'notes\\{piano_notes[i]}.wav'))

sounds = []

for i in range(14):
    sounds.append(AudioSegment.from_mp3(f'background\\{i}.mp3'))

# drums = []
# drums.append(AudioSegment.from_mp3('background\drum01.mp3'))
# drums.append(AudioSegment.from_mp3('background\drum02.mp3'))

def adjust(notes, exclude):
    temp = []
    for i in notes:
        for j in exclude:
            if j in piano_notes[i]:
                temp.append(i)
    for i in temp:
        notes.remove(i)


def generate(background, notes, wait_time=500):
    notes.sort()
    pos = 0
    for i in notes:
        background = background.overlay(piano_sounds[i], position=pos)
        pos += wait_time
    background = background[:pos+1500]
    background.fade_out(1000)
    return background
    

def process(image):
    width = image.shape[1]
    height = image.shape[0]
    cw = width // 7
    ch = height // 4

    channel = 0

    features = []

    for i in range(4):
        for j in range(7):
            data = image[i*ch:(i+1)*ch-1, j*cw:(j+1)*cw-1, channel]
            features.append(data.mean())

    for i in range(1, 7):
        rr, cc = skimage.draw.line(0, i*cw-1, height-1, i*cw-1)
        image[rr, cc] = 255

    for j in range(1, 4):
        rr, cc = skimage.draw.line(j*ch-1, 0, j*ch-1, width-1)
        image[rr, cc] = 255

    for i in range(4):
        for j in range(7):
            cv2.putText(image, piano_notes[i*7+j], (j*cw+cw//2-20, i*ch+ch//2+10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1, cv2.LINE_AA)

    # 使用enumerate()函数获取每个元素的索引和值，并将它们存储在一个列表中
    indexed_list = list(enumerate(features))

    # 使用sorted()函数根据值对索引列表进行排序（从大到小）
    sorted_list = sorted(indexed_list, key=lambda x: x[1], reverse=True)

    indices = [index for index, _ in sorted_list[:8]]
    adjust(indices, ['B', 'D'])

    # 風鈴背景音樂
    bgm = int(abs((image.std()-20)/2.5))%14
    # drums[0].play()
    # background.play()
    song = generate(sounds[bgm], indices, 500)
    # song.export('test.wav', format='wav')

    return song


def process_user_video(input_video):
    # Open the video file
    cap = cv2.VideoCapture(input_video)

    # Get the frames per second (fps) of the video
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Initialize lists to store corresponding timestamps
    timestamps = []

    scene_change = []
    audios = []

    # Define the sampling interval in seconds (0.5 seconds)
    sampling_interval = 0.5

    # Initialize variables for tracking time
    current_time = 0.0
    last_timestamp = 0.0
    
    old_frame = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Update the current time
        current_time += 1.0 / fps

        if current_time - last_timestamp >= sampling_interval:
            if not old_frame:
                difference = frame
            else:
                difference = frame - old_frame
            if difference.mean() > 10:
                scene_change.append(current_time)
                audios.append(process(frame))
            timestamps.append(current_time)
            last_timestamp = current_time

    # Initialize the pydub audio segment
    combined_audio = AudioSegment.empty()

    for audio in audios:
        combined_audio += audio

    # Export the generated audio as a file
    output_audio = "output_audio.wav"
    combined_audio.export(output_audio, format="wav")

    return output_audio  # Provide the generated audio file as the output


gr.Interface(process_user_video, 'video', 'audio').launch()

