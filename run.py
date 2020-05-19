import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.system('python manage.py runserver 0.0.0.0:8999')