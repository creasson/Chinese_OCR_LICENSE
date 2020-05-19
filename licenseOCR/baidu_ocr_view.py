from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .baidu_ocr import BaiduOCR
import os
from PIL import Image, ImageDraw

ocr = BaiduOCR(apiKey='hhkcKD0CTP40VD6vxW92FOPt',
               secretKey='gx59LaFgRwMu0g31rilZeG4VnkCIFM9H'
               )

@csrf_exempt
def ocr_image(request):
    savepath = ''
    if request.POST:
        savepath = request.POST['savepath']
    elif request.GET:
        savepath = request.GET['savepath']
    with open(savepath, 'rb') as fs:
        image = fs.read()
        ocr_res = ocr.accurate(image)
        ocr_texts = []
        img = Image.open(savepath)
        draw = ImageDraw.Draw(img)
        for item in ocr_res['words_result']:
            ocr_texts.append(item['words'])

            loc = item['location']
            rect = [
                loc['left'], loc['top'],   # 左上
                loc['left'] + loc['width'], loc['top'],     # 右上
                loc['left'] + loc['width'], loc['top'] + loc['height'],     # 右下
                loc['left'], loc['top'] + loc['height']     # 左下
            ]
            rect = [int(e) for e in rect]
            draw.line((rect[0], rect[1], rect[2], rect[3]), fill=(0, 255, 0), width=3)
            draw.line((rect[2], rect[3], rect[4], rect[5]), fill=(0, 255, 0), width=3)
            draw.line((rect[4], rect[5], rect[6], rect[7]), fill=(0, 255, 0), width=3)
            draw.line((rect[6], rect[7], rect[0], rect[1]), fill=(0, 255, 0), width=3)

        imgname = os.path.split(savepath)[-1]
        output_path = os.path.join("static/tmpfiles/", imgname)
        img.save(output_path)

    return JsonResponse(data={'output_path': output_path,
                              'ocr_texts': '\n'.join(ocr_texts)
                              })
