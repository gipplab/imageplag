import falcon
import os
import uuid
import mimetypes
import classify


class Collection(object):
    def __init__(self, storage_path, bar_classifier, pure_classifier, use_gpu):

        self.storage_path = storage_path

        # Load classifiers
        print("Loading Bar Chart Classifier..")
        self.bar_net = classify.get_net(os.path.join(bar_classifier, 'snap.caffemodel'),
                                   os.path.join(bar_classifier, 'deploy.prototxt'),
                                   use_gpu=use_gpu)
        self.bar_trans = classify.get_transformer(os.path.join(bar_classifier, 'deploy.prototxt'),
                                             os.path.join(bar_classifier, 'mean.binaryproto'))
        self.bar_label = os.path.join(bar_classifier, 'labels.txt')
        print("  ..done!")

        print("Loading Pure Image Classifier..")
        self.pure_net = classify.get_net(os.path.join(pure_classifier, 'snap.caffemodel'),
                                    os.path.join(pure_classifier, 'deploy.prototxt'),
                                    use_gpu=use_gpu)
        self.pure_trans = classify.get_transformer(os.path.join(pure_classifier, 'deploy.prototxt'),
                                              os.path.join(pure_classifier, 'mean.binaryproto'))
        self.pure_label = os.path.join(pure_classifier, 'labels.txt')
        print("  ..done!")

    def on_get(self, req, resp):
        resp.body = '{"Status": "Alive"}'
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp):
        #ext = mimetypes.guess_extension(req.content_type)
        #filename = '{uuid}{ext}'.format(uuid=uuid.uuid4(), ext=ext)
        filename = req.params['name']
        print('Retrieving image: "' + filename + '"')
        image_path = os.path.join(self.storage_path, filename)

        with open(image_path, 'wb') as image_file:
            while True:
                chunk = req.stream.read(4096)
                if not chunk:
                    break

                image_file.write(chunk)

        print(image_path)

        is_bar = classify.classify(self.bar_net, self.bar_trans, [image_path], labels_file=self.bar_label)
        print(is_bar[1][0], is_bar[1][1])
        print(is_bar[2][0], is_bar[2][1])

        is_pure = classify.classify(self.pure_net, self.pure_trans, [image_path], labels_file=self.pure_label)
        print(is_pure[1][0], is_pure[1][1])
        print(is_pure[2][0], is_pure[2][1])

        resp.status = falcon.HTTP_201
        resp.location = '/images/' + filename
        resp.body = '{' \
                    '"location": "' + image_path + '",' + \
                    '"' + str(is_bar[1][0]) + '": "' + str(is_bar[1][1]) + '",' + \
                    '"' + str(is_bar[2][0]) + '": "' + str(is_bar[2][1]) + '",' + \
                    '"' + str(is_pure[1][0]) + '": "' + str(is_pure[1][1]) + '",' + \
                    '"' + str(is_pure[2][0]) + '": "' + str(is_pure[2][1]) + '"' +\
                    '}'


class Item(object):
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def on_get(self, req, resp, name):
        resp.content_type = mimetypes.guess_type(name)[0]
        image_path = os.path.join(self.storage_path, name)
        resp.stream = open(image_path, 'rb')
        resp.stream_len = os.path.getsize(image_path)