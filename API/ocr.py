"""This module wraps around pytesser. It allows simple usage of the OCR,
and provides a function to compare images base on the ocr results."""

from PIL import Image
from pytesser.pytesser import *
import cv2
import numpy as np
import img_util
import textwrap


def ocr(img, limit=3):
    """Extracts words longer than specified from the image and returns them as
    a single string.
    
    Parameters
    ----------
    img
        Path to the image of which the words should be extracted.
        Alternativly PIL Image object.
    limit : int, optional
        Specifies the minimum length of the words to be considered.
        
    Returns
    -------
    str
        Extracted words of the image, sperated by a space.
    """
    # load image as grayscale
    img = img_util.to_cv2(img)
    # get resize factor
    height, width = img.shape[:2]
    factor = float(800) / height
    # resize image
    img = cv2.resize(img, None, fx=factor, fy=factor,
                     interpolation=cv2.INTER_CUBIC)
    # convert image to PIL image    
    img = Image.fromarray(img)
    text = image_to_string(img)
    text = text.split()
    text = [t for t in text if len(t) >= int(limit)]
    text = " ".join(text)
    return text


def distance(s1, s2, min_words=10, max_wordlength=3):
    """Compares two strings that each contain words seperated by a space,
    and returns the distance that the two strings have.
    
    Parameters
    ----------
    s1 : str
        Contains words of image 1, sperated by a space.
    s2 : str
        Contains words of image 2, sperated by a space.
    min_words : int, optional
        The minumum number of n-grams in each string required
    max_wordlength : int, optional
        The n in n-grams. 3 is highly recommended. 
    
    Returns
    -------
    float
        The distance between both input strings.      
    """
    
    if s1 == 'NA' or s2 == 'NA':
        return 10000.0
    
    # split strings to lists on whitespaces
    s1 = set(s1.split())
    s2 = set(s2.split())
    
    # split word into trigrams
    u1 = set()
    for x in s1:
        for tri in textwrap.wrap(x, max_wordlength):
            if len(tri) > 2:
                u1.add(tri) 
    u2 = set()
    for x in s2:
        for tri in textwrap.wrap(x, max_wordlength):
            if len(tri) > 2:
                u2.add(tri)
    
    # skip short sets
    if len(u1) < min_words or len(u2) < min_words:
        return 10000.0
    # similarity is the number of same unique elements
    length = len(set.intersection(u1, u2))
    if length == 0:
        return np.inf
    sd = len(set.symmetric_difference(u1, u2))
    return np.float(sd) / length