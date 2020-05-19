from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import numpy as np
from PIL import Image, ImageDraw
from .east_nms import nms
import tensorflow as tf
import os
import pandas as pd

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class East_Predictor:
    def __init__(self, model_path, max_image_size=768):
        self.sess, self.out = self.__load_model(model_path)
        self.max_image_size = max_image_size

    def __load_model(self, model_path):
        graph = tf.Graph()
        with graph.as_default():
            with tf.gfile.FastGFile(os.path.join(project_dir, model_path), 'rb') as fs:
                graph_def = tf.GraphDef()
                graph_def.ParseFromString(fs.read())
                tf.import_graph_def(graph_def, name='')
                out = graph.get_tensor_by_name('east_detect/concat:0')
        sess = tf.Session(graph=graph)
        return sess, out

    def __sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def resize_image(self, image):
        """限制图片最大为max_image_size, 超出则等比例缩小。并将图片长宽微调为32的倍数。"""
        w, h = image.size
        if w >= h:
            nw = min(self.max_image_size, w)
            h = int(h * nw / w)
            w = nw
        else:
            nh = min(self.max_image_size, h)
            w = int(w * nh / h)
            h = nh
        w = max(w - (w % 32), 1)
        h = max(h - (h % 32), 1)
        return w, h

    def predict(self, image_path, pixel_threshold=0.9):
        image = Image.open(image_path).convert('RGB')
        width, height = image.size

        # d_wight, d_height = self.resize_image(image)
        d_wight, d_height = self.max_image_size, self.max_image_size
        scale_ratio_w = width / d_wight
        scale_ratio_h = height / d_height

        # 预处理成模型输入
        image = image.resize((d_wight, d_height), Image.ANTIALIAS)
        image = np.array(image) / 127.5 - 1.0
        x = np.expand_dims(image, axis=0)

        feed_dict = {
            'input_img:0': x
        }
        y = self.sess.run(self.out, feed_dict=feed_dict)
        # 对预测结果进行还原
        y = np.squeeze(y, axis=0)
        y[:, :, :3] = self.__sigmoid(y[:, :, :3])
        cond = np.greater_equal(y[:, :, 0], pixel_threshold)
        activation_pixels = np.where(cond)
        quad_scores, quad_after_nms = nms(y, activation_pixels)

        text_rects = []
        for score, geo in zip(quad_scores, quad_after_nms):
            if np.amin(score) > 0:
                rescaled_geo = geo * [scale_ratio_w, scale_ratio_h]
                # rescaled_geo_list = np.reshape(rescaled_geo, (8,)).tolist()
                # text_rects.append(rescaled_geo_list)

                reorder_geo = reorder_vertexes(rescaled_geo)
                rescaled_geo_list = np.reshape(reorder_geo, (8,)).tolist()
                text_rects.append(rescaled_geo_list)

        return text_rects

def reorder_vertexes(xy_list, epsilon=1e-4):
    """对文本框的四角的坐标点进行排序"""
    reorder_xy_list = np.zeros_like(xy_list)
    ordered = np.argsort(xy_list, axis=0)
    xmin1_index = ordered[0, 0]
    xmin2_index = ordered[1, 0]
    if xy_list[xmin1_index, 0] == xy_list[xmin2_index, 0]:
        if xy_list[xmin1_index, 1] <= xy_list[xmin2_index, 1]:
            reorder_xy_list[0] = xy_list[xmin1_index]
            first_v = xmin1_index
        else:
            reorder_xy_list[0] = xy_list[xmin2_index]
            first_v = xmin2_index
    else:
        reorder_xy_list[0] = xy_list[xmin1_index]
        first_v = xmin1_index
    others = list(range(4))
    others.remove(first_v)
    k = np.zeros((len(others),))
    for index, i in zip(others, range(len(others))):
        k[i] = (xy_list[index, 1] - xy_list[first_v, 1]) \
               / (xy_list[index, 0] - xy_list[first_v, 0] + epsilon)
    k_mid = np.argsort(k)[1]
    third_v = others[k_mid]
    reorder_xy_list[2] = xy_list[third_v]
    others.remove(third_v)
    b_mid = xy_list[first_v, 1] - k[k_mid] * xy_list[first_v, 0]
    second_v, fourth_v = 0, 0
    for index, i in zip(others, range(len(others))):
        delta_y = xy_list[index, 1] - (k[k_mid] * xy_list[index, 0] + b_mid)
        if delta_y > 0:
            second_v = index
        else:
            fourth_v = index
    reorder_xy_list[1] = xy_list[second_v]
    reorder_xy_list[3] = xy_list[fourth_v]
    k13 = k[k_mid]
    k24 = (xy_list[second_v, 1] - xy_list[fourth_v, 1]) / (
            xy_list[second_v, 0] - xy_list[fourth_v, 0] + epsilon)
    if k13 < k24:
        tmp_x, tmp_y = reorder_xy_list[3, 0], reorder_xy_list[3, 1]
        for i in range(2, -1, -1):
            reorder_xy_list[i + 1] = reorder_xy_list[i]
        reorder_xy_list[0, 0], reorder_xy_list[0, 1] = tmp_x, tmp_y
    return reorder_xy_list

def map_rects(rects, **kwargs):
    """rects由list, 参照标准结构，映射为dict"""
    sorted_rects = sorted(rects, key=lambda rect: rect[1])
    rect_dict = dict()
    for ind, rect in enumerate(sorted_rects):
        rect_dict[str(ind)] = rect
    return rect_dict

def dump(image_path, text_rects, output_path):
    img = Image.open(image_path).convert('RGB')
    draw = ImageDraw.Draw(img)
    for rect in text_rects:
        rect = [int(np.round(e)) for e in rect]
        draw.line((rect[0], rect[1], rect[2], rect[3]), fill=(0, 255, 0), width=3)
        draw.line((rect[2], rect[3], rect[4], rect[5]), fill=(0, 255, 0), width=3)
        draw.line((rect[4], rect[5], rect[6], rect[7]), fill=(0, 255, 0), width=3)
        draw.line((rect[6], rect[7], rect[0], rect[1]), fill=(0, 255, 0), width=3)
    img.save(output_path)

# model_path = 'models/east_epoch2-loss0.0473.pb'
# model_path = 'models/east_epoch7-loss0.0792.pb'
model_path = 'models/east_epoch3-loss0.0714.pb'
# model_path = 'models/east_epoch6-loss0.2760.pb'
max_image_size = 768
east = East_Predictor(model_path, max_image_size)

@csrf_exempt
def east_image(request):
    savepath = ''
    if request.POST:
        savepath = request.POST['savepath']
    elif request.GET:
        savepath = request.GET['savepath']

    text_rects = east.predict(savepath)
    rect_dict = map_rects(text_rects)
    image_name = os.path.basename(savepath)
    key, ext = os.path.splitext(image_name)
    output_path = os.path.join("static/tmpfiles/", key+'.jpg')
    dump(savepath, text_rects, output_path)

    return JsonResponse(data={'key': key,
                              'output_path': output_path,
                              'rect_dict': json.dumps(rect_dict, ensure_ascii=False)})