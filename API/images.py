import falcon
import os
import uuid
import mimetypes
import classify
import blobcrop
import imagehash
import img_util
import ratiohash
import ocr


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
        # ext = mimetypes.guess_extension(req.content_type)
        # filename = '{uuid}{ext}'.format(uuid=uuid.uuid4(), ext=ext)
        filename = req.params['name']
        print('Retrieving image: "' + filename + '"')
        image_path = os.path.join(self.storage_path, filename)

        with open(image_path, 'wb') as image_file:
            while True:
                chunk = req.stream.read(4096)
                if not chunk:
                    break

                image_file.write(chunk)

        images = [image_path]

        img_list = blobcrop.crop_to_blob(image_path)
        basename, ext = filename.rsplit('.', 1)
        for i, img in enumerate(img_list):
            sub_img_path = basename + '-' + str(i + 1) + "." + ext
            sub_img_path = os.path.join(self.storage_path, sub_img_path)
            img.save(sub_img_path)
            images.append(sub_img_path)

        resp.body = '{ "subimages": ['

        for img in images:
            print(img)

            is_bar = classify.classify(self.bar_net, self.bar_trans, [img], labels_file=self.bar_label)
            print(is_bar[1][0], is_bar[1][1])
            print(is_bar[2][0], is_bar[2][1])

            is_pure = classify.classify(self.pure_net, self.pure_trans, [img], labels_file=self.pure_label)
            print(is_pure[1][0], is_pure[1][1])
            print(is_pure[2][0], is_pure[2][1])

            phash = str(imagehash.phash(img_util.open_if(img)))

            rhash = 'NA'
            if float(is_bar[1][1]) > 99 and is_bar[1][0] == 'bar':
                rhash = ratiohash.get_hash(img)

            text = ''
            if not (float(is_pure[1][1]) > 50 and is_pure[1][0] == 'pure'):
                text = ocr.ocr(img)

            resp.body += '{' \
                         '"location": "' + img + '",' + \
                         '"' + str(is_bar[1][0]) + '": "' + str(is_bar[1][1]) + '",' + \
                         '"' + str(is_bar[2][0]) + '": "' + str(is_bar[2][1]) + '",' + \
                         '"' + str(is_pure[1][0]) + '": "' + str(is_pure[1][1]) + '",' + \
                         '"' + str(is_pure[2][0]) + '": "' + str(is_pure[2][1]) + '",' + \
                         '"phash": "' + phash + '",' + \
                         '"rhash": "' + rhash + '",' + \
                         '"text": "' + text + '"' + \
                         '},'

        resp.body = resp.body[:-1] + ']}'

        resp.status = falcon.HTTP_201
        resp.location = '/images/' + filename


class Item(object):
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def on_get(self, req, resp, name):
        resp.content_type = mimetypes.guess_type(name)[0]
        image_path = os.path.join(self.storage_path, name)
        resp.stream = open(image_path, 'rb')
        resp.stream_len = os.path.getsize(image_path)
