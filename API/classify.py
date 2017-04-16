"""Module based upon 
https://github.com/NVIDIA/DIGITS/blob/master/examples/classification/example.py"""

import os

from google.protobuf import text_format
import numpy as np
import PIL.Image
import scipy.misc

os.environ['GLOG_minloglevel'] = '2'  # Suppress most caffe output
import caffe  # noqa
from caffe.proto import caffe_pb2  # noqa


def get_net(caffemodel, deploy_file, use_gpu=False):
    """Returns an instance of caffe.Net
    
    Parameters
    ----------
    caffemodel : str
        Path to a .caffemodel file.
    deploy_file : str
        Path to a .prototxt file.
    use_gpu : bool, optional
        If True, use the GPU for inference.
        
    Returns
    -------
    caffe.Net
        The caffemodel net.
    """
    
    if use_gpu:
        caffe.set_mode_gpu()
    else:
        caffe.set_mode_cpu()

    # load a new model
    return caffe.Net(deploy_file, caffemodel, caffe.TEST)


def get_transformer(deploy_file, mean_file=None):
    """Returns an instance of caffe.io.Transformer
    
    Parameters
    ----------
    deploy_file : str
        path to a .prototxt file.
    mean_file : str, optional
        path to a .binaryproto file.
        
    Returns
    -------
    caffe.io.Transformer
        The caffemodel transformer.
    """
    
    network = caffe_pb2.NetParameter()
    with open(deploy_file) as infile:
        text_format.Merge(infile.read(), network)

    if network.input_shape:
        dims = network.input_shape[0].dim
    else:
        dims = network.input_dim[:4]

    t = caffe.io.Transformer(inputs={'data': dims})
    t.set_transpose('data', (2, 0, 1))  # transpose to (channels, height, width)

    # color images
    if dims[1] == 3:
        # channel swap
        t.set_channel_swap('data', (2, 1, 0))

    if mean_file:
        # set mean pixel
        with open(mean_file, 'rb') as infile:
            blob = caffe_pb2.BlobProto()
            blob.MergeFromString(infile.read())
            if blob.HasField('shape'):
                blob_dims = blob.shape
                assert len(blob_dims) == 4, 'Shape should have 4 dimensions - shape is "%s"' % blob.shape
            elif blob.HasField('num') and blob.HasField('channels') and \
                    blob.HasField('height') and blob.HasField('width'):
                blob_dims = (blob.num, blob.channels, blob.height, blob.width)
            else:
                raise ValueError('blob does not provide shape or 4d dimensions')
            pixel = np.reshape(blob.data, blob_dims[1:]).mean(1).mean(1)
            t.set_mean('data', pixel)

    return t


def load_image(path, height, width, mode='RGB'):
    """
    Load an image from disk.
    
    Parameters
    ----------
    path : str
        Path to an image on disk.
    width : int
        Resize dimension.        
    height : int
        Resize dimension.
    mode : str, optional
        The PIL mode that the image should be converted to. (RGB for color or L
        for grayscale)
        
    Returns
    -------
    np.ndarray
        (channels x width x height)
    """
    
    image = PIL.Image.open(path)
    image = image.convert(mode)
    image = np.array(image)
    # squash
    image = scipy.misc.imresize(image, (height, width), 'bilinear')
    return image


def forward_pass(images, net, transformer, batch_size=None):
    """
    Returns scores for each image as an np.ndarray (nImages x nClasses)
    
    Parameters
    ----------
    images : List
        A list of np.ndarrays.
    net : caffe.Net
        A caffe.Net.
    transformer : caffe.io.Transformer
        A caffe.io.Transformer.
    batch_size : int, optional
        How many images can be processed at once.
        (a high value may result in out-of-memory errors)
        
    Returns
    -------
    np.ndarray
        Scores for each image. (nImages x nClasses)
    """
    
    if batch_size is None:
        batch_size = 1

    caffe_images = []
    for image in images:
        if image.ndim == 2:
            caffe_images.append(image[:, :, np.newaxis])
        else:
            caffe_images.append(image)

    dims = transformer.inputs['data'][1:]

    scores = None
    for chunk in [caffe_images[x:x + batch_size] for x in xrange(0, len(caffe_images), batch_size)]:
        new_shape = (len(chunk),) + tuple(dims)
        if net.blobs['data'].data.shape != new_shape:
            net.blobs['data'].reshape(*new_shape)
        for index, image in enumerate(chunk):
            image_data = transformer.preprocess('data', image)
            net.blobs['data'].data[index] = image_data
        output = net.forward()[net.outputs[-1]]
        if scores is None:
            scores = np.copy(output)
        else:
            scores = np.vstack((scores, output))

    return scores


def read_labels(labels_file):
    """
    Returns a list of strings
    
    Parameters
    ----------
    labels_file : str
        Path to a .txt file
    """
    
    if not labels_file:
        print('No labels file provided for interpretation.')
        return None

    labels = []
    with open(labels_file) as infile:
        for line in infile:
            label = line.strip()
            if label:
                labels.append(label)
    assert len(labels), 'No labels found'
    return labels


def classify(net, transformer, image_files, labels_file=None, batch_size=None):
    """
    Classify some images against a Caffe model and returns the results
    
    Parameters
    ----------
    net : caffe.Net
        A caffe.Net.
    transformer : caffe.io.Transformer
        A caffe.io.Transformer.
    image_files : List
        List of paths to images.
    labels_file : str, optional
        Path to a .txt file.
    batch_size : int, optional
        How many images can be processed at once.
        (a high value may result in out-of-memory errors)
        
    Returns
    -------
    List
        A list of classification results.
    """
    
    # Load the model and images
    _, channels, height, width = transformer.inputs['data']
    if channels == 3:
        mode = 'RGB'
    elif channels == 1:
        mode = 'L'
    else:
        raise ValueError('Invalid number for channels: %s' % channels)
    images = [load_image(image_file, height, width, mode) for image_file in image_files]
    labels = read_labels(labels_file)

    # Classify the image
    scores = forward_pass(images, net, transformer, batch_size=batch_size)

    # Process the results
    indices = (-scores).argsort()[:, :5]  # take top 5 results
    classifications = []
    for image_index, index_list in enumerate(indices):
        result = []
        for i in index_list:
            # 'i' is a category in labels and also an index into scores
            if labels is None:
                label = 'Class #%s' % i
            else:
                label = labels[i]
            result.append((label, round(100.0 * scores[image_index, i], 4)))
        classifications.append(result)

    results = []
    for index, classification in enumerate(classifications):
        result = [image_files[index]]
        for label, confidence in classification:
            result.append((label, confidence))
        results.append(result)
    return result        
        