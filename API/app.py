import falcon
import images


# Settings
storage_path = '/imageplag/images'
bar_classifier = 'DNN_bar_no_bar'
pure_classifier = 'DNN_pure_no_pure'
database_path = 'database.sqlite'
use_gpu = False


# Startup
api = application = falcon.API()

print("prepare data models")
image_collection = images.Collection(database_path, storage_path, bar_classifier, pure_classifier, use_gpu)

print("storage_path: " + storage_path)
image = images.Item(storage_path)

print("database_path: " + database_path)

api.add_route('/images', image_collection)
api.add_route('/images/{id}', image)

print("server ready")
