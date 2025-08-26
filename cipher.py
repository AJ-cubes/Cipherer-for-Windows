import json
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

import cv2
from PIL import Image
import numpy as np
import soundfile as sf

items = json.load(open(f"unicode-chars.json", "r"))["items"]


def cipher(text, num):
    return ''.join(["" + items[(items.index(text[i]) + num) % len(items)] for i in range(len(text))])


def decipher(text, num):
    return ''.join(["" + items[(items.index(text[i]) - num) % len(items)] for i in range(len(text))])


def generate_indices(shape, key):
    np.random.seed(key)
    indices = np.arange(np.prod(shape))
    np.random.shuffle(indices)
    return indices


def shuffle_pixels(image_data, indices):
    return image_data.flatten()[indices].reshape(image_data.shape)


def unshuffle_pixels(image_data, indices):
    unshuffled_data = np.zeros_like(image_data.flatten())
    unshuffled_data[indices] = image_data.flatten()
    return unshuffled_data.reshape(image_data.shape)


def encrypt_image(image_path, key):
    image = Image.open(image_path)
    image_data = np.array(image)

    indices = generate_indices(image_data.shape, key)
    encrypted_image_data = shuffle_pixels(image_data, indices)

    encrypted_image = Image.fromarray(encrypted_image_data)
    return encrypted_image


def decrypt_image(image_path, key):
    encrypted_image = Image.open(image_path)
    encrypted_data = np.array(encrypted_image)

    indices = generate_indices(encrypted_data.shape, key)
    decrypted_image_data = unshuffle_pixels(encrypted_data, indices)

    decrypted_image = Image.fromarray(decrypted_image_data)
    return decrypted_image


def generate_block_indices(h, w, block_size, key):
    np.random.seed(key)
    indices = np.arange((h // block_size) * (w // block_size))
    np.random.shuffle(indices)
    return indices


def shuffle_blocks(image_data, indices, block_size):
    h, w, c = image_data.shape
    num_blocks_w = w // block_size

    shuffled_image = np.zeros_like(image_data)
    for i, idx in enumerate(indices):
        src_row = (i // num_blocks_w) * block_size
        src_col = (i % num_blocks_w) * block_size
        dest_row = (idx // num_blocks_w) * block_size
        dest_col = (idx % num_blocks_w) * block_size

        shuffled_image[dest_row:dest_row + block_size, dest_col:dest_col + block_size, :] = \
            image_data[src_row:src_row + block_size, src_col:src_col + block_size, :]

    return shuffled_image


def process_frame(frame, indices, inverse_indices, block_size, mode='encrypt'):
    if mode == 'encrypt':
        return shuffle_blocks(frame, indices, block_size)
    elif mode == 'decrypt':
        return shuffle_blocks(frame, inverse_indices, block_size)


def encrypt_decrypt_video(input_path, key, block_size, mode='encrypt'):
    cap = cv2.VideoCapture(input_path)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    indices = generate_block_indices(h, w, block_size, key)
    inverse_indices = np.argsort(indices)

    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

    cap.release()

    cpu_count = multiprocessing.cpu_count()
    with ThreadPoolExecutor(max_workers=cpu_count) as executor:
        processed_frames = list(
            executor.map(lambda f: process_frame(f, indices, inverse_indices, block_size, mode), frames))

    return processed_frames


def generate_sound_indices(length, key):
    np.random.seed(key)
    indices = np.arange(length)
    np.random.shuffle(indices)
    return indices


def shuffle_samples(audio_data, indices):
    return audio_data[indices]


def process_audio(audio_data, indices, inverse_indices, mode='encrypt'):
    if mode == 'encrypt':
        return shuffle_samples(audio_data, indices)
    elif mode == 'decrypt':
        return shuffle_samples(audio_data, inverse_indices)


def encrypt_decrypt_audio(input_path, key, mode='encrypt'):
    audio_data, sample_rate = sf.read(input_path)
    length = audio_data.shape[0]

    indices = generate_sound_indices(length, key)
    inverse_indices = np.argsort(indices)

    cpu_count = multiprocessing.cpu_count()
    with ThreadPoolExecutor(max_workers=cpu_count) as executor:
        processed_audio = list(executor.map(lambda f: process_audio(f, indices, inverse_indices, mode), [audio_data]))

    return processed_audio[0], sample_rate


password_type = ""
