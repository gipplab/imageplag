"""This module contains shared image utility functions shared in this
package."""

from PIL import Image
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


def absdiff10k(i, j):
    """Calculates the absolute difference between two values. Difference is 
    set to zero, if one value is the maximum value of 10000.001
    
    Parameters
    ----------
    i : int
        Smaller value, the value that is divided by later on.
    j : int
        Larger value.
        
    Returns
    -------
    float
        abs(i-j) / float(i), or 0.0 for maximum value cases.
    """
    if i >= 10000.001 or j >= 10000.001:
        return 0.0
    else:
        return abs(i - j) / float(i)


def eval_distances(data, threshold=1.0, cutoff=10):
    """Evaluates the largest relative gap in a distribution to get suspicious
    outliers.
    
    Parameters
    ----------
    data : List
        The distribution to evaluate.
    threshold : float, optional
        A threshold to weight the largest relative gap in the distribution.
    cutoff : int, optional
        The number of possible plagiarism cases. If there are more matches, it
        is considered not plagiarism. (e.g. for a common logo)
    
    Returns
    -------
    int, float
        (x, y), x as the position where the largest gap occurs,
                y in [0,1) as the normalized level of suspicion.
    """
    data = np.array(data)
    data = data.astype(float)
    # remove capped values
    data[data == np.inf] = 10000.0
    # avoid div by 0 problems
    data += 0.001
    data.sort()
    median = np.median(data)
    # avoid outliers with a large distance
    data[data > median] = median
    # get weighted distances between neighbours
    dist = [absdiff10k(i, j) for i, j in zip(data[:-1], data[1:])]
    # position of the cutoff point outliers - non-outliers
    amax = np.argmax(dist)
    # maximal relative distance is key to determine plagiarism
    dmax = dist[amax]
    # normalize score between 0 and 1
    score = (dmax / threshold)
    score /= 1 + score
    # if there are many suspicous findings, it is probably not plagiarism
    if amax > cutoff:
        return len(data), 0.0
    # return the number of supicious matches, level of suspicion
    return amax + 1, score
