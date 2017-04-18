import falcon
import images
import classify
import os

# Settings
storage_path = '/home/christopher/Desktop/FalconTest'
bar_classifier = 'DNN_bar_no_bar'
pure_classifier = 'DNN_pure_no_pure'
use_gpu = False


# Startup
api = application = falcon.API()

image_collection = images.Collection(storage_path, bar_classifier, pure_classifier, use_gpu)
print("storage_path: " + storage_path)
image = images.Item(storage_path)

api.add_route('/images', image_collection)
api.add_route('/images/{name}', image)
print("server ready")
