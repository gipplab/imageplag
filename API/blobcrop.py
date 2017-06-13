import cv2
import numpy as np
from PIL import Image
import img_util


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


def pad(img, padding=10):
    """Adds a white border to the image.

    Parameters
    ----------
    img : cv2 image
        The image to pad
    padding : int
        The size of the padding
    
    Returns
    -------
    cv2 image
        The padded image
    """ 
    
    height, width = img.shape[:2]
    mask = np.ones((height + 2*padding, width + 2*padding), np.uint8) * 255
    mask[padding:height+padding, padding:width+padding] = img
    return mask


def fix_border(bw_img, margin=5):
    """Checks if largest contour is a rectangle and if it will cover > 90%
    width and > 90% height of the image.
    
    Parameters
    ----------
    bw_img : cv2 black and white image
        The black and white image to check.
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
    # if largest contour is smaller than 90% of the image, it is not
    # considered to be a border
    if w < 0.9*width or h < 0.9*height:
        return bw_img
    # get ratio of countour area to rectange area
    ratio = max(areas) / float(w*h)
    # check if ratio indicates a square
    if ratio > 0.9:
        # if so, crop image from top and right side
        mask = np.ones(bw_img.shape, np.uint8)*255
        mask[y+margin:y+h-margin, x+margin:x+w-margin] =\
            bw_img[y+margin:y+h-margin, x+margin:x+w-margin]
        bw_img = mask
    return bw_img
    
    
def subimage(img, rect):
    """Crops an image to a bounding rectangle.

    Parameters
    ----------
    img : cv2 image
        The image that should be cropped.
    rect : cv2 bounding rectangle
        The rectangle the image should be cropped to.
        
    Returns
    -------
    cv2 image
        The input image cropped to the specified bounding rectangle.
    """
    
    x, y, w, h = rect
    return img[y:y+h, x:x+w]
    

def crop_to_blob(img, min_blob_size=0.1):
    """Converts an image to a number of subimages. Each subimage contains one
    blob (spot of connected pixels).
    
    Parameters
    ----------
    img : {PIL Image Object, str}
        The image or path to the image that should be decomposed into
        subimages.
    min_blob_size :
        The minimum size of the subimages in ratio to the original image.
        
    Returns
    -------
    list
        A list of PIL Image objects that contain blobs.
    """
    
    # read image as grayscale
    img = img_util.to_cv2(img)
    # get shape of the image
    height, width = img.shape[:2]
    # ensure the image has a white border
    img = pad(img)
    # adaptive thresholding
    img_bw = cv2.adaptiveThreshold(img.copy(), 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # dilate the working image
    kernel = np.ones((2, 2), np.uint8)
    img_bw = 255 - img_bw
    img_bw = cv2.dilate(img_bw, kernel, iterations = 1)
    img_bw = 255 - img_bw
    # preprocess the border of the image
    img_bw = fix_border(img_bw)
    # floodfill the image
    img_filled = floodfill(img_bw)
    # fill inner blob areas
    img_bw = img_bw - img_filled
    # invert image
    img_bw = 255 - img_bw
    # find contours
    contours, hierarchy = cv2.findContours(img_bw, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    # convert contours to bounding rectangles
    rects = [cv2.boundingRect(cnt) for cnt in contours]
    # get only contours with large bounding rectangles
    # > 10% of orignal image height and width
    # > 10 by 10 pixels
    rects = [rect for rect in rects if\
        rect[2] > min_blob_size*width and \
        rect[3] > min_blob_size*height and \
        rect[2] > 10 and \
        rect[3] > 10]
    # extract subimages from original image
    img_list = [subimage(img, rect) for rect in rects]
    #display(img_list)
    # convert image to PIL image
    img_list = [Image.fromarray(i) for i in img_list]
    return img_list


def display(images): 
    """Debug function. Takes a list of cv2 images and displays them.
    
    Parameters
    ----------
    images : list
        List of images that will be displayed.
    """
    
    for img in images:
        cv2.imshow('image', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()