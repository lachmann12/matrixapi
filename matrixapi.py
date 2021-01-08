import datetime
import time
import tornado.escape
import tornado.ioloop
import tornado.web
import os
import io
import string
import random
import requests
import hashlib
import base64
import hmac
import uuid
from dateutil import parser
import threading
import re
import h5py as h5
import urllib.request
import sys
import pandas as pd
import numpy as np

base_name = os.environ['BASE_NAME']
matrix_url = os.environ['MATRIX_URL']
token = os.environ['TOKEN']

print("matrix: "+matrix_url)
urllib.request.urlretrieve(matrix_url, 'matrix.h5')
print("matrix loaded")

class ListRowID(tornado.web.RequestHandler):
    def post(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        f = h5.File("matrix.h5")
        ids = list(f["meta"]["rowid"])
        response = { 'index': [x.decode("UTF-8") for x in ids]}
        self.write(response)
    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        f = h5.File("matrix.h5")
        ids = list(f["meta"]["rowid"])
        response = { 'index': [x.decode("UTF-8") for x in ids]}
        self.write(response)

class ListColID(tornado.web.RequestHandler):
    def post(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        f = h5.File("matrix.h5")
        ids = list(f["meta"]["colid"])
        response = { 'columns': [x.decode("UTF-8") for x in ids]}
        self.write(response)
    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        f = h5.File("matrix.h5")
        ids = list(f["meta"]["colid"])
        response = { 'columns': [x.decode("UTF-8") for x in ids]}
        self.write(response)

class GetSlice(tornado.web.RequestHandler):
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        f = h5.File("matrix.h5")
        colids = [x.decode("UTF-8") for x in list(f["meta"]["colid"])]
        rowids = [x.decode("UTF-8") for x in list(f["meta"]["rowid"])]
        data["index"] = list(set(data["index"]).intersection(set(rowids)))
        data["columns"] = list(set(data["columns"]).intersection(set(colids)))
        row_idx = np.array(sorted([rowids.index(x) for x in data["index"]]))
        col_idx = np.array(sorted([colids.index(x) for x in data["columns"]]))
        if len(row_idx) > 0 and len(col_idx) > 0:
            values = pd.DataFrame(f["data"]["matrix"][:, col_idx][row_idx, :])
            values.index = np.array(rowids)[row_idx]
            values.columns = np.array(colids)[col_idx]
            response = values.to_json(orient="split")
        else:
            response = { 'error': 'no matching colids or rowids'}
        f.close()
        self.write(response)

class GetCol(tornado.web.RequestHandler):
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        f = h5.File("matrix.h5")
        colids = [x.decode("UTF-8") for x in list(f["meta"]["colid"])]
        rowids = [x.decode("UTF-8") for x in list(f["meta"]["rowid"])]
        if data["id"] in colids:
            values = list(f["data"]["matrix"][:, colids.index(data["id"])])
            response = { 'index': rowids, 'columns': data["id"], 'values': [float(x) for x in values]}
        else:
            response = { 'error': data["id"]+' not in colids'}
        f.close()
        self.write(response)
class GetRow(tornado.web.RequestHandler):
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        f = h5.File("matrix.h5")
        colids = [x.decode("UTF-8") for x in list(f["meta"]["colid"])]
        rowids = [x.decode("UTF-8") for x in list(f["meta"]["rowid"])]
        if data["id"] in rowids:
            values = list(f["data"]["matrix"][:, colids.index(data["id"])])
            response = { 'index': data["id"], 'columns': colids, 'values': [float(x) for x in values]}
        else:
            response = { 'error': data["id"]+' not in rowids'}
        f.close()
        self.write(response)

class VersionHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        response = { 'version': '1',
                     'last_build':  datetime.date.today().isoformat() }
        self.write(response)
    def post(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        response = { 'version': '1',
                     'last_build':  datetime.date.today().isoformat() }
        self.write(response)

application = tornado.web.Application([
    (r"/"+base_name+"/version", VersionHandler),
    (r"/"+base_name+"/colid", ListColID),
    (r"/"+base_name+"/rowid", ListRowID),
    (r"/"+base_name+"/row", GetRow),
    (r"/"+base_name+"/col", GetCol),
    (r"/"+base_name+"/slice", GetSlice)
])


if __name__ == "__main__":
    application.listen(5000)
tornado.ioloop.IOLoop.instance().start()