import os
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import hashlib

@csrf_exempt
def upload(request):
    if request.method == "POST":
        myFile = request.FILES.get("myfile", None)
        if not myFile:
            return HttpResponse("no files for upload!")

        tmppath = os.path.join("static/uploadFiles/", myFile.name)
        destination = open(tmppath, 'wb')
        myhash = hashlib.md5()
        for chunk in myFile.chunks():
            destination.write(chunk)
            myhash.update(chunk)
        destination.close()
        cmd5 = myhash.hexdigest()
        savepath = os.path.join("static/uploadFiles/", cmd5 + '.jpg')

        try:
            image = Image.open(tmppath).convert('RGB')
            image.save(savepath)
        except:
            savepath = ''

        return JsonResponse(data={'savepath': savepath})