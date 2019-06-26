import os
import random

import cv2 as cv
import numpy as np
from torch.utils.data import Dataset

from config import im_size, num_classes, color_map
from utils import to_categorical

train_images_folder = 'data/instance-level_human_parsing/Training/Images'
train_categories_folder = 'data/instance-level_human_parsing/Training/Category_ids'
valid_images_folder = 'data/instance-level_human_parsing/Validation/Images'
valid_categories_folder = 'data/instance-level_human_parsing/Validation/Category_ids'


def get_category(categories_folder, name):
    filename = os.path.join(categories_folder, name + '.png')
    semantic = cv.imread(filename, 0)
    return semantic


def to_bgr(y_pred):
    ret = np.zeros((im_size, im_size, 3), np.float32)
    for r in range(320):
        for c in range(320):
            color_id = y_pred[r, c]
            # print("color_id: " + str(color_id))
            ret[r, c, :] = color_map[color_id]
    ret = ret.astype(np.uint8)
    return ret


def random_choice(image_size):
    height, width = image_size
    crop_height, crop_width = 320, 320
    x = random.randint(0, max(0, width - crop_width))
    y = random.randint(0, max(0, height - crop_height))
    return x, y


def safe_crop(mat, x, y):
    crop_height, crop_width = 320, 320
    if len(mat.shape) == 2:
        ret = np.zeros((crop_height, crop_width), np.float32)
    else:
        ret = np.zeros((crop_height, crop_width, 3), np.float32)
    crop = mat[y:y + crop_height, x:x + crop_width]
    h, w = crop.shape[:2]
    ret[0:h, 0:w] = crop
    return ret


class LIPDataset(Dataset):
    def __init__(self, split):
        self.usage = split

        if split == 'train':
            id_file = 'data/instance-level_human_parsing/Training/train_id.txt'
            self.images_folder = train_images_folder
            self.categories_folder = train_categories_folder
        else:
            id_file = 'data/instance-level_human_parsing/Validation/val_id.txt'
            self.images_folder = valid_images_folder
            self.categories_folder = valid_categories_folder

        with open(id_file, 'r') as f:
            self.names = f.read().splitlines()

        np.random.shuffle(self.names)

    def __getitem__(self, i):
        name = self.names[i]
        filename = os.path.join(self.images_folder, name + '.jpg')
        image = cv.imread(filename)
        image_size = image.shape[:2]
        category = get_category(self.categories_folder, name)

        x, y = random_choice(image_size)
        image = safe_crop(image, x, y)
        category = safe_crop(category, x, y)

        if np.random.random_sample() > 0.5:
            image = np.fliplr(image)
            category = np.fliplr(category)

        x = image / 255.
        y = category
        y = to_categorical(y, num_classes)

        return x, y

    def __len__(self):
        return len(self.names)


def gen_names():
    num_fgs = 431
    num_bgs = 43100
    num_bgs_per_fg = 100

    names = []
    bcount = 0
    for fcount in range(num_fgs):
        for i in range(num_bgs_per_fg):
            names.append(str(fcount) + '_' + str(bcount) + '.png')
            bcount += 1

    valid_names = random.sample(names, num_valid)
    train_names = [n for n in names if n not in valid_names]

    with open('valid_names.txt', 'w') as file:
        file.write('\n'.join(valid_names))

    with open('train_names.txt', 'w') as file:
        file.write('\n'.join(train_names))


if __name__ == "__main__":
    gen_names()