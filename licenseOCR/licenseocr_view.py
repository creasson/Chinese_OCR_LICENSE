from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import tensorflow as tf
import json
from PIL import Image
import cv2
import numpy as np
import re
import os
from .BusinessLicense import BusinessLicense

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_dict(dict_file):
    chars = []
    with open(dict_file, encoding='utf-8', mode='r') as fs:
        while True:
            line = fs.readline()
            if not line:
                break
            items = line.strip().split('\t')
            if len(items) < 2:
                continue
            elif re.search('\s', items[0]) is not None:
                continue
            chars.append(items[0])
    chars.append('blank')

    char_to_id = {v: i for i, v in enumerate(chars)}
    id_to_char = {i: v for i, v in enumerate(chars)}
    return char_to_id, id_to_char

class Dense_Predictor:
    def __init__(self, model_path, dict_file, image_shape=(640, 32)):
        self.sess, self.out = self.__load_model(model_path)
        self.char_to_id, self.id_to_char = load_dict(dict_file)
        self.num_classes = len(self.id_to_char)
        self.image_shape = image_shape

    def __load_model(self, model_path):
        graph = tf.Graph()
        with graph.as_default():
            with tf.gfile.FastGFile(model_path, 'rb') as fs:
                graph_def = tf.GraphDef()
                graph_def.ParseFromString(fs.read())
                tf.import_graph_def(graph_def, name='')
                out = graph.get_tensor_by_name('out/truediv:0')
        sess = tf.Session(graph=graph)
        return sess, out

    def __decode_single_line(self, pred_text):
        char_list = []
        for i in range(len(pred_text)):
            if pred_text[i] != self.num_classes - 1 and (
                    (pred_text[i] != pred_text[i - 1]) or (i > 1 and pred_text[i] == pred_text[i - 2])):
                char_list.append(self.id_to_char[pred_text[i]])
        return u''.join(char_list)

    def predict(self, image_path, show=True):
        image = Image.open(image_path)
        image = image.resize(self.image_shape, Image.ANTIALIAS)
        image = image.convert('L')
        image = np.array(image) / 127.5 - 1.0
        image = np.expand_dims(image, axis=2)
        X = np.expand_dims(image, axis=0)
        feed_dict = {
            'the_input:0': X
        }
        probs = self.sess.run(self.out, feed_dict=feed_dict)
        y_pred = probs.argmax(axis=2)[0]
        line_text = self.__decode_single_line(y_pred)

        if show:
            print(line_text)
            img = image * 127.5 + 127.5
            img = cv2.cvtColor(np.asarray(img, dtype=np.uint8), cv2.COLOR_RGB2BGR)
            cv2.imshow('', img)
            cv2.waitKey(-1)
        return line_text

    def process(self, imgs):
        maxlen = max([img.shape[1] for img in imgs])
        pad_imgs = []
        for img in imgs:
            pad_img = np.zeros(shape=(32, maxlen, 1))
            pad_img[:, :img.shape[1], :] = img
            pad_imgs.append(pad_img)
        return pad_imgs

    def predict_rects(self, image_path, rect_dict):
        image = Image.open(image_path).convert('RGB')
        chimg_list = []
        index_list = []

        for index, cnt in rect_dict.items():
            index_list.append(index)
            rect = np.reshape(np.asarray(cnt[0:8], np.float32), (4, 2))
            min_rect = cv2.minAreaRect(rect)
            box = cv2.boxPoints(min_rect)
            box = np.int0(np.round(box))
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            region = [min(xs), min(ys), max(xs), max(ys)]
            chimg = image.crop(region)
            w, h = chimg.size

            # 如果右下点【2】的纵坐标 + 右上点【3】的纵坐标 的均值 小于 左上点【0】 的纵坐标
            # 或者右下点【2】的纵坐标 + 右上点【3】的纵坐标 的均值 大于 左下点【1】 的纵坐标
            # 则该四边形倾斜度较大，考虑将文字区域外的像素点置为纯白色。
            if rect[2, 1] + rect[3, 1] > 2 * rect[1, 1] or rect[2, 1] + rect[3, 1] < 2 * rect[0, 1]:
                rect[:, 0] = rect[:, 0] - region[0]
                rect[:, 1] = rect[:, 1] - region[1]
                pim = chimg.load()
                for i in range(w):
                    # 对每一个i值，给出上下两条边框线之外的j的所有值。
                    if rect[3, 0] - rect[0, 0] != 0:
                        min_j = int(rect[0, 1] + (i - rect[0, 0]) * (rect[3, 1] - rect[0, 1]) / (rect[3, 0] - rect[0, 0]))
                        for j in range(0, min_j):
                            pim[i, j] = (255, 255, 255)
                    if rect[2, 0] - rect[1, 0] != 0:
                        max_j = int(np.ceil(rect[1, 1] + (i - rect[1, 0]) * (rect[2, 1] - rect[1, 1]) / (rect[2, 0] - rect[1, 0])))
                        for j in range(max_j, h):
                            pim[i, j] = (255, 255, 255)

                # rotate_angle = min_rect[-1]
                # if rotate_angle > 45:
                #     rotate_angle = -90 + rotate_angle
                # elif rotate_angle < -45:
                #     rotate_angle = 90 + rotate_angle
                # # 旋转会降低图片的清晰度, 所以尽量避免旋转
                # # chimg = chimg.rotate(rotate_angle)
                # # 为避免旋转后超出部分被填充为黑色, 这里使用alpha图层
                # chimg = chimg.convert('RGBA')
                # rot = chimg.rotate(rotate_angle, expand=1)
                # fff = Image.new('RGBA', rot.size, (255,) * 4)
                # chimg = Image.composite(rot, fff, rot)
                # w, h = chimg.size

            chimg = chimg.resize((int(w * 32 / h), 32), Image.ANTIALIAS)
            chimg = chimg.convert('L')
            chimg = np.array(chimg) / 127.5 - 1.0
            chimg = np.expand_dims(chimg, axis=2)
            chimg_list.append(chimg)

        if len(chimg_list) == 0:
            return dict()
        pad_chimg_list = self.process(chimg_list)
        feed_dict = {
            'the_input:0': np.asarray(pad_chimg_list)
        }
        line_texts = []
        probs = self.sess.run(self.out, feed_dict=feed_dict)
        for y_pred in probs.argmax(axis=2):
            line_text = self.__decode_single_line(y_pred)
            line_texts.append(line_text)

        result = []
        for index, cnt in rect_dict.items():
            result.append({
                'text': line_texts[int(index)],
                'box': cnt[0:8]
            })
        bs = BusinessLicense(result)
        composed_texts = []
        for key, value in bs.res.items():
            composed_texts.append('{} : {}'.format(key, value))
        return '\n'.join(composed_texts)

model_path = os.path.join(project_dir, 'models/dense_epoch2-acc0.7935.pb')
dict_file_path = os.path.join(project_dir, 'dictionary/chars_dict.txt')
image_shape = (640, 32)
dense = Dense_Predictor(model_path, dict_file_path, image_shape)

@csrf_exempt
def http_ocr_image(request):
    savepath = ''
    text_rects = ''
    if request.POST:
        savepath = request.POST['savepath']
        text_rects = request.POST['rect_dict']
    elif request.GET:
        savepath = request.GET['savepath']
        text_rects = request.GET['rect_dict']

    text_rects = json.loads(text_rects)
    formarted_text = dense.predict_rects(savepath, text_rects)
    return JsonResponse(data={'ocr_texts': formarted_text})