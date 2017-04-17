"""This module will calculate ratios on bar charts and generate hashes of it.
"""

import cv2
import textwrap as tw
import numpy as np
import img_util


def to_hash(bars):
    """Converts a list to a hash, each 3 digits represent one bar height.
    
    Parameters
    ----------
    bars : a list of integer
        Bar heights from bar chart as a list.
        
    Returns
    -------
    str
        A string containing bar height information in hex
    """
    # normalize and hex with leading zeros, 10^(-3) precision
    h = ''.join([format(int(round(x / float(max(bars))  * 1000)), 'x').zfill(3) for x in bars])
    return h


def clean(img, limit=0.004):   
    """Removes small spots in a black and white image.
    
    Parameters
    ----------
    img : cv2 black and white image
        The black and white image to clean.
    limit : float, optional
        The minimum area under which a spot is removed in ratio to image area.
        
    Returns
    -------
    cv2 black and white image
        The input image without spots.
    """
    # get shape of the image
    height, width = img.shape[:2]
    # recalulate limit to absolute value
    limit *= height * width
    # get countours of the images
    contours, hierarchy = cv2.findContours(img.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # remove small contours
    for cnt in contours:
        if cv2.contourArea(cnt) < limit:
            cv2.drawContours(img, [cnt], -1, (255, 255, 255), -1)
    return img


def floodfill(img, color=0):
    """Floodfills an image from the point (0, 0).
    
    Parameters
    ----------
    img : cv2 black and white image
        The image to fill.
    color : int, optional
        The color with which the image should be filled.
        
    Returns
    -------
    cv2 black and white image
        The filled image.
    """
    height, width = img.shape[:2]
    mask = np.zeros((height+2, width+2), np.uint8) 
    img_filled = img.copy()
    cv2.floodFill(img_filled, mask, (0,0), color)
    return img_filled


def remove_rectangle(bw_img, thresh=0.9, margin=10):
    """Checks if largest contour is a rectangle. If so, it will crop the image
    top and right side with a margin on that rectangle, that the rectangle
    will become an L-shape.
    
    Parameters
    ----------
    bw_img : cv2 black and white image
        The black and white image to check.
    thresh : float, optional
        The minium ratio of contour area to rectangle area. Used to determine,
        if largest contour is a rectangle or not.
    margin : int
        The margin with which the top and right side should be cut.
        
    Returns
    -------
    cv2 black and white image
        The input image, possibly cropped to outer rectangle top and right
        side.
    """
    # get shape of the image
    height, width = bw_img.shape[:2]
    # floodfill from point (0, 0)
    img_filled = floodfill(bw_img)
    # get clean shape
    img_filled = bw_img - img_filled
    # invert image, shapes must be white
    img_filled = 255-img_filled
    # get contours
    contours, hierarchy = cv2.findContours(img_filled.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # check if there are contours
    if len(contours) == 0:
        return bw_img
    # get areas of countours
    areas = [cv2.contourArea(cnt) for cnt in contours]
    # get countour with the largest area
    x,y,w,h = cv2.boundingRect(contours[np.argmax(areas)])
    # get ratio of countour area to rectange area
    ratio = max(areas) / float(w*h)
    # check if ratio indicates a square
    if ratio > 0.9:
        # if so, crop image from top and right side
        mask = np.ones(bw_img.shape, np.uint8)*255
        mask[y+margin:height, 0:x+w-margin] = bw_img[y+margin:height, 0:x+w-margin]
        bw_img = mask
    return bw_img


def extract_bars(img, bar_min_width=0.01, bar_min_height=0.01, gap_size=0.01):
    """Extracts bar heights of a preprocesed bar chart with black filled bars.

    Parameters
    ----------
    img : cv2 black and white image
        A preprocessed bar chart with black filled bars.
    bar_min_width : float
        The minimum with of a single bar in ratio to image with.
    bar_min_height : float
        The minimum height of a single bar in ratio to image height.
    gap_size : float
        The number of pixel to consider in the neigbourhood for a bar in ratio
        to image width.

    Returns
    -------
    list
        A list of integer containing the bar heights in the image from left
        to right.
    """
    # get image dimensions
    height, width = img.shape[:2]
    # conert ratios to absolute values
    bar_min_width = bar_min_width * width
    bar_min_height = bar_min_height * height
    gap_size = int(gap_size * width)
    # scan from bottom up to determine x-axis
    bars = []
    for x in range(0, width):
        start = height-1
        while start >= 0 and img[start, x] == 255:
            start -= 1
        end = start
        while end >= 0 and img[end, x] == 0:
            end -= 1
        bars.append(start - end)
  
    # collect sets that may turn to bars
    # each set has (elements, life)
    result = []
    cache = []
    for b in bars:
        # check if bar height belongs to a set on the left
        for c in reversed(cache):
            if b in c[0] or b+1 in c[0] or b-1 in c[0]:
                # if b belongs to a set, fit it there
                c[0].append(b)
                # increas life of that set
                c[1] += 2
                if c[1] > gap_size:
                    c[1] = gap_size
                break
        else:
            # create new set with new inital life
            s = [[b], 2]
            cache.append(s)
        # decrease life of every cached set
        for c in cache:
            c[1] -= 1
        # get a list with all large dead sets
        dead = [np.mean(c[0]) for c in cache if c[1] <= 0 and len(c[0]) >= bar_min_width]
        result += dead
        # remove dead sets
        cache = [c for c in cache if c[1] > 0]
    # check if there are live large sets leftover
    rest = [np.mean(c[0]) for c in cache if len(c[0]) >= bar_min_width]
    result += rest
    result = [r for r in result if r >= bar_min_width]
    return result                   


def get_hash(img):
    """"Takes an barchart and returns its ratio hash.
    
    Parameters
    ----------
    img
        Path to the image containing the barchart. May be surrounded by a
        rectangle. Higher quality images yield better results.
        Alternativly PIL Image object.
        
    Returns
    -------
    str
        A single string containing information about the bar ratios as hex.
        Each three characters represent one bar height in hex.
        Read from left to right, same as in the original image.
    """
    # load image as grayscale
    gray_img = img_util.to_cv2(img)
    # thresholding to bw image
    bw_img = cv2.threshold(gray_img, 200, 255, cv2.THRESH_BINARY)[1]
    # give image a white border
    bw_img = cv2.copyMakeBorder(bw_img, top=20, bottom=20, left=20, right=20, borderType=cv2.BORDER_CONSTANT, value=255)
    # remove spots
    bw_img = clean(bw_img)
    # check if plot has a rectangluar border, if so, remove it
    bw_img = remove_rectangle(bw_img)
    # floodfill image to prepare extraction of bars
    bw_img = bw_img - floodfill(bw_img)
    # extract bars
    bars = extract_bars(bw_img)
    # calculate hash
    return to_hash(bars)


def distance(hash1, hash2):
    """Takes two ratio hashes and returns the distance between them.
    
    Parameters
    ----------
    hash1 : str
        First hash in three digits hex representation.
    hash2 : str
        Second hash in three digits hex representation.
        
    Returns
    -------
    int
        The distance between the barcharts that the hashes represent
    """
    # if one of the hashes has less than 4 bars, return max distance
    if len(hash1) < 12 or len(hash2) < 12:
        return 10000
    # if the two hashes have different length, return max distance
    while len(hash1) < len(hash2):
        return 10000
    while len(hash2) < len(hash1):
        return 10000
    # split string in chunks of 3
    hash1 = tw.wrap(hash1, 3)
    hash2 = tw.wrap(hash2, 3)
    # convert hash from hex to base 10
    hash1 = [int(x, base=16) for x in hash1]
    hash2 = [int(x, base=16) for x in hash2]
    # sort bar heights
    list.sort(hash1)
    list.sort(hash2)
    # get distance as mean of absolute errors
    distance = sum([abs(x-y) for x, y in zip(hash1, hash2)])
    return distance