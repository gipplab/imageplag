import pandas as pd
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
import database
import json


class Collection(object):
    def __init__(self, database_path, storage_path, bar_classifier, pure_classifier, use_gpu):

        self.storage_path = storage_path
        self.db_handler = database.DBHandler(database_path)

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

        # Load database
        print("Loading Database..")

        print("  ..done!")

    def on_get(self, req, resp):
        if "id" not in req.params:
            resp.body = '{"Status": "Alive"}'
            resp.status = falcon.HTTP_200
        else:
            print ('=' * 50)
            print('Received analyse request for id', req.params['id'])
            sub_df = self.db_handler.df[self.db_handler.df['parent'] == req.params['id']]
            cmp_df = self.db_handler.df[self.db_handler.df['parent'] != req.params['id']]

            resp.body = '{ ' + \
                        '"analyse": "True",' + \
                        '"store": "False",' + \
                        '"id": "' + str(req.params['id']) + '",' + \
                        '"subimages": ['

            for index, row in sub_df.iterrows():
                name = row['id']
                parent = row['parent']
                phash = row['phash']
                rhash = row['rhash']
                text = row['text']
                bool_bar = row['is_bar'] == 1
                bool_pure = row['is_pure'] == 1

                if "phash_thresh" in req.params:
                    df = self.db_handler.eval_phash(phash, cmp_df, float(req.params["phash_thresh"]))
                else:
                    df = self.db_handler.eval_phash(phash, cmp_df)
                matches_phash = '['
                for index, row in df.iterrows():
                    matches_phash += '{' \
                                     '"id": "' + str(row.id) + '",' + \
                                     '"parent": "' + str(row.parent) + '",' + \
                                     '"score": "' + str(row.score) + '"' + \
                                     '},'
                if matches_phash[-1] == ',':
                    matches_phash = matches_phash[:-1]
                matches_phash += ']'

                matches_rhash = '[]'
                if bool_bar:
                    if "rhash_thresh" in req.params:
                        df = self.db_handler.eval_rhash(rhash, cmp_df, float(req.params["rhash_thresh"]))
                    else:
                        df = self.db_handler.eval_rhash(rhash, cmp_df)
                    matches_rhash = '['
                    for index, row in df.iterrows():
                        matches_rhash += '{' \
                                         '"id": "' + str(row.id) + '",' + \
                                         '"parent": "' + str(row.parent) + '",' + \
                                         '"score": "' + str(row.score) + '"' + \
                                         '},'
                    if matches_rhash[-1] == ',':
                        matches_rhash = matches_rhash[:-1]
                    matches_rhash += ']'

                matches_text = '[]'
                if not bool_pure:
                    if "text_thresh" in req.params:
                        df = self.db_handler.eval_text(text, cmp_df, float(req.params["text_thresh"]))
                    else:
                        df = self.db_handler.eval_text(text, cmp_df)
                    matches_text = '['
                    for index, row in df.iterrows():
                        matches_text += '{' \
                                        '"id": "' + str(row.id) + '",' + \
                                        '"parent": "' + str(row.parent) + '",' + \
                                        '"score": "' + str(row.score) + '"' + \
                                        '},'
                    if matches_text[-1] == ',':
                        matches_text = matches_text[:-1]
                    matches_text += ']'

                resp.body += '{'
                resp.body += '"id": "' + str(name) + '",'
                resp.body += '"parent": "' + str(parent) + '",'
                resp.body += '"is_pure": "' + str(bool_pure) + '",'
                resp.body += '"is_bar": "' + str(bool_bar) + '",'
                resp.body += '"matches_phash": ' + matches_phash + ','
                resp.body += '"matches_rhash": ' + matches_rhash + ','
                resp.body += '"matches_text": ' + matches_text
                resp.body += '},'

            resp.body = resp.body[:-1] + ']}'

    def on_post(self, req, resp):
        # ext = mimetypes.guess_extension(req.content_type)
        # filename = '{uuid}{ext}'.format(uuid=uuid.uuid4(), ext=ext)
        filename = req.params['id']
        # Analyse here is not recommended - if image is submitted twice, the first copy will distort the results.
        analyse = False  # (req.params['analyse'] == 'true')
        store = (req.params['store'] == 'true')

        print ('=' * 50)
        print('Retrieving image: "' + filename + '"')
        base_path = self.storage_path
        if not store:
            base_path = '/tmp'

        image_path = os.path.join(base_path, filename)

        print('Analyse: ' + str(analyse))
        print('Store: ' + str(store))

        with open(image_path, 'wb') as image_file:
            while True:
                chunk = req.stream.read(4096)
                if not chunk:
                    break

                image_file.write(chunk)

        images = [image_path]

        img_list = blobcrop.crop_to_blob(image_path)
        for i, img in enumerate(img_list):
            sub_img_path = filename + '-' + str(i + 1)
            sub_img_path = os.path.join(base_path, sub_img_path)
            img.save(sub_img_path, format='JPEG')
            images.append(sub_img_path)

        resp.body = '{ ' + \
                    '"analyse": "' + str(analyse) + '",' + \
                    '"store": "' + str(store) + '",' + \
                    '"id": "' + str(filename) + '",' + \
                    '"subimages": ['

        for img in images:
            print ('-' * 50)
            print(img)

            is_bar = classify.classify(self.bar_net, self.bar_trans, [img], labels_file=self.bar_label)
            print(is_bar[1][0], is_bar[1][1])
            print(is_bar[2][0], is_bar[2][1])

            is_pure = classify.classify(self.pure_net, self.pure_trans, [img], labels_file=self.pure_label)
            print(is_pure[1][0], is_pure[1][1])
            print(is_pure[2][0], is_pure[2][1])

            phash = str(imagehash.phash(img_util.open_if(img)))

            rhash = 'NA'
            bool_bar = 0
            if float(is_bar[1][1]) > 99 and is_bar[1][0] == 'bar':
                rhash = ratiohash.get_hash(img)
                bool_bar = 1

            text = ''
            bool_pure = 1
            if not (float(is_pure[1][1]) > 50 and is_pure[1][0] == 'pure'):
                text = ocr.ocr(img)
                bool_pure = 0

            id = os.path.split(img)[-1]
            res = ''
            if store:
                res = self.db_handler.add_entry(id, filename, phash, rhash, text, bool_bar, bool_pure)

            matches_phash = '[]'
            matches_rhash = '[]'
            matches_text = '[]'
            if analyse:
                df = self.db_handler.eval_phash(phash)
                matches_phash = '['
                for index, row in df.iterrows():
                    matches_phash += '{' \
                                     '"id": "' + str(row.id) + '",' + \
                                     '"score": "' + str(row.score) + '"' + \
                                     '},'
                if matches_phash[-1] == ',':
                    matches_phash = matches_phash[:-1]
                matches_phash += ']'

                matches_rhash = '[]'
                if bool_bar:
                    df = self.db_handler.eval_rhash(rhash)
                    matches_rhash = '['
                    for index, row in df.iterrows():
                        matches_rhash += '{' \
                                         '"id": "' + str(row.id) + '",' + \
                                         '"score": "' + str(row.score) + '"' + \
                                         '},'
                    if matches_rhash[-1] == ',':
                        matches_rhash = matches_rhash[:-1]
                    matches_rhash += ']'

                matches_text = '[]'
                if not bool_pure:
                    df = self.db_handler.eval_text(text)
                    matches_text = '['
                    for index, row in df.iterrows():
                        matches_text += '{' \
                                        '"id": "' + str(row.id) + '",' + \
                                        '"score": "' + str(row.score) + '"' + \
                                        '},'
                    if matches_text[-1] == ',':
                        matches_text = matches_text[:-1]
                    matches_text += ']'

            resp.body += '{'
            if analyse:
                resp.body += '"matches_phash": ' + matches_phash + ','
                resp.body += '"matches_rhash": ' + matches_rhash + ','
                resp.body += '"matches_text": ' + matches_text + ','
            if store:
                resp.body += '"db_response": "' + res + '",'
            resp.body += '"id": "' + id + '",' + \
                         '"location": "' + img + '",' + \
                         '"' + str(is_bar[1][0]) + '": "' + str(is_bar[1][1]) + '",' + \
                         '"' + str(is_bar[2][0]) + '": "' + str(is_bar[2][1]) + '",' + \
                         '"' + str(is_pure[1][0]) + '": "' + str(is_pure[1][1]) + '",' + \
                         '"' + str(is_pure[2][0]) + '": "' + str(is_pure[2][1]) + '",' + \
                         '"phash": "' + phash + '",' + \
                         '"rhash": "' + rhash + '",' + \
                         '"text": ' + json.dumps(text) + '' + \
                         '},'

        resp.body = resp.body[:-1] + ']}'

        resp.status = falcon.HTTP_201
        resp.location = '/images/' + filename

        self.db_handler.reload_db()


class Item(object):
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def on_get(self, req, resp, id):
        resp.content_type = mimetypes.guess_type(id)[0]
        image_path = os.path.join(self.storage_path, id)
        resp.stream = open(image_path, 'rb')
        resp.stream_len = os.path.getsize(image_path)
