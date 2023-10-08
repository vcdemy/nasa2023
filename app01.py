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
    song.export('test.wav', format='wav')

    return image, (44100, np.array(song.get_array_of_samples()))


gr.Interface(process, 'image', ['image', 'audio'], title="Soudify", description="Select an image and click submit!").launch()

