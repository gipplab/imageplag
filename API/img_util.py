"""This module contains shared image utility functions shared in this
package."""

import Image
import numpy as np
import cv2


def to_cv2(img):
    """Converts path or PIL Image object to cv2 image
    
    Parameters
    ----------
    img
        Path to image, or PIL Image object.
    
    Returns
    -------
    cv2 image
        The coverted and loaded image.
    """
    if isinstance(img, Image.Image):
        cv2_img = np.array(img)
        if len(cv2_img.shape) == 3 or len(cv2_img.shape) == 4:
            # convert from Image to gray image
            return cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
        else:
            # if image is already grayscale
            return cv2_img
    else:
        # load to gray cv2 image
        return cv2.imread(img, 0)


def fix_size(img):
    """Function that will resize any image smaller than 10 by 10 pixels to
    the default size of 10 by 10 pixels.

    Parameters
    ----------
    img
        Any PIL Image of any size, or path to that image.

    Returns
    -------
    PIL Image
        The original input image with a minimum height and minimum width of
        10 pixels each.
    """
    img = open_if(img)
    width, height = img.size
    if width < 10:
        img = img.resize((10, height), Image.ANTIALIAS)
    width, height = img.size
    if height < 10:
        img = img.resize((width, 10), Image.ANTIALIAS)
    return img


def open_if(img):
    """Conditinally opens a PIL Image. Makes sure that a PIL Image is returned.

    Parameters
    ----------
    img
        Path to an image, or Image object.

    Returns
    -------
    PIL Image
        The object from input, or the opend image.
    """
    if isinstance(img, Image.Image):
        return img
    else:
        return Image.open(img)