from django.shortcuts import render, redirect
from django.http import JsonResponse
import random
import time
from agora_token_builder import RtcTokenBuilder
from .models import RoomMember, Detection, Etudiant
import json
from django.views.decorators.csrf import csrf_exempt
import cv2
import numpy as np
from keras.models import load_model
from keras.utils import img_to_array
from django.http import StreamingHttpResponse
from django.views.decorators import gzip
from django.utils import timezone
import mysql.connector
from datetime import datetime
from .forms import DetectionForm
import asyncio
import pyvirtualcam
from itertools import groupby
#from agora import AgoraRTCClient
# Se connecter à la base de données MySQL
#mydb = mysql.connector.connect(
 # host="localhost",
  #user="root",
  #password="",
  #database="detection_emotion_db",)
# Créer la table pour stocker les données de détection d'émotion
#mycursor = mydb.cursor()
#mycursor.execute("CREATE TABLE IF NOT EXISTS detections (id INT AUTO_INCREMENT PRIMARY KEY, emotion VARCHAR(255), detection_time DATETIME)")

# Create your views here.
def first(request):
    return render(request, 'base/first.html')

def home(request):
    return render(request, 'Teacher/base/home.html')

def homes(request):
    return render(request, 'Student/base/homes.html')

def lobby(request):
    return render(request, 'Teacher/base/lobby.html')

def room_t(request):
      detections = Detection.objects.all()
      data = [{'emotion': d.emotion, 'detection_time': d.detection_time} for d in detections]
      context = {'data': data}
    
      return render(request, 'Teacher/base/room.html',context)
def room_s(request):
    return render(request, 'Student/base/room.html')
def recommendation_s(request):
    latest_detection = Detection.objects.latest('detection_time')
    detections = Detection.objects.filter(etudiant=latest_detection.etudiant).order_by('-detection_time')
    data = [{'emotion': d.emotion, 'detection_time': d.detection_time, 'etudiant': d.etudiant.nom} for d in detections]
    latest_etudiant = latest_detection.etudiant.nom if detections.exists() else None
    context = {'data': data, 'latest_etudiant': latest_etudiant}
    return render(request, 'Student/recommendation/recommendation.html',context)
def recommendation_spositive(request):
    latest_detection = Detection.objects.latest('detection_time')
    detections = Detection.objects.filter(etudiant=latest_detection.etudiant).order_by('-detection_time')
    data = [{'emotion': d.emotion, 'detection_time': d.detection_time, 'etudiant': d.etudiant.nom} for d in detections]
    latest_etudiant = latest_detection.etudiant.nom if detections.exists() else None
    context = {'data': data, 'latest_etudiant': latest_etudiant}
    return render(request, 'Student/recommendation/positive_recommendation.html',context)
def recommendation_t(request):

    return render(request, 'Teacher/recommendation/recommendation.html')
def recommendation_tpositive(request):

    return render(request, 'Teacher/recommendation/positive_recommendation.html')
#Dashboarding: Teacher
def dashboard_t(request):
    detections = Detection.objects.all()
    data = [{'emotion': d.emotion, 'detection_time': d.detection_time,'etudiant':d.etudiant.nom} for d in detections]
   
    etudiants = detections.order_by().values_list('etudiant__nom', flat=True).distinct()
    context = {'data': data,'etudiants': etudiants}
    return render(request, 'Teacher/dashboard/dashboard.html', context)

#Dashboarding: Student
def dashboard_s(request):
    latest_detection = Detection.objects.latest('detection_time')
    detections = Detection.objects.filter(etudiant=latest_detection.etudiant).order_by('-detection_time')
    data = [{'emotion': d.emotion, 'detection_time': d.detection_time, 'etudiant': d.etudiant.nom} for d in detections]
    latest_etudiant = latest_detection.etudiant.nom if detections.exists() else None
    context = {'data': data, 'latest_etudiant': latest_etudiant}
    return render(request, 'Student/dashboard/dashboard.html', context)

async def getToken(request):
    appId = "72bfab75cd3b4b1b87aab06996d2daed"
    appCertificate = "c64c362a21c742fbb613ba61118128e2"
    channelName = request.GET.get('channel')
    uid = random.randint(1, 230)
    expirationTimeInSeconds = 3600
    currentTimeStamp = int(time.time())
    privilegeExpiredTs = currentTimeStamp + expirationTimeInSeconds
    role = 1

    token = RtcTokenBuilder.buildTokenWithUid(appId, appCertificate, channelName, uid, role, privilegeExpiredTs)
    await asyncio.sleep(0.01)
    return JsonResponse({'token': token, 'uid': uid}, safe=False)


@csrf_exempt
def createMember(request):
    data = json.loads(request.body)
    member, created = RoomMember.objects.get_or_create(
        name=data['name'],
        uid=data['UID'],
        room_name=data['room_name']
    )
   
    global detection
    detection=True

    return JsonResponse({'name':data['name']}, safe=False)


def getMember(request):
    uid = request.GET.get('UID')
    room_name = request.GET.get('room_name')

    member = RoomMember.objects.get(
        uid=uid,
        room_name=room_name,
    )
    name = member.name

    return JsonResponse({'name':member.name}, safe=False)
detection=True
@csrf_exempt
def deleteMember(request):
    data = json.loads(request.body)
    member = RoomMember.objects.get(
        name=data['name'],
        uid=data['UID'],
        room_name=data['room_name']
    )
    member.delete()
    global detection
    detection=False
    return JsonResponse('Member deleted', safe=False)

def student(request):
    return render(request, 'Student/base/student.html')
 # Load the emotion detection model
classifier =load_model(r'C:\Users\aya\Desktop\Emotion_Detection\model.h5')

    # Initialize the emotion labels and the MySQL database connection
emotion_labels = ['Angry','Disgust','Fear','Happy','Neutral', 'Sad', 'Surprise']

# Create a cascade classifier for detecting faces
face_classifier = cv2.CascadeClassifier(r'C:\Users\aya\Desktop\Emotion_Detection\haarcascade_frontalface_default.xml')
width=640
height=480
def emotion_detection(request):
    with pyvirtualcam.Camera(width, height, 20) as cam:
        cap = cv2.VideoCapture(0)
        gray = None
        member_list = list(RoomMember.objects.exclude(name='Mr Ali').values_list('name', flat=True))
        while detection:
            success, frame = cap.read()
            if not success:
                break
            else:
                labels = []
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_classifier.detectMultiScale(gray)
                for (x, y, w, h) in faces:
                    roi_gray = gray[y:y + h, x:x + w]
                    roi_gray = cv2.resize(roi_gray, (48, 48), interpolation=cv2.INTER_AREA)
                    if np.sum([roi_gray]) != 0:
                        roi = roi_gray.astype('float') / 255.0
                        roi = np.array(roi)
                        roi = np.expand_dims(roi, axis=0)
                        prediction = classifier.predict(roi)[0]
                        label = emotion_labels[prediction.argmax()]
                        label_position = (x, y)
                        for member_name in member_list:
                            etudiant, created = Etudiant.objects.get_or_create(nom=member_name)
                            etudiant.etat = 'present(e)'
                            etudiant.save()
                            detection_data = Detection.objects.create(etudiant=etudiant, emotion=label, detection_time=timezone.now())
                            detection_data.save()
                            member_list = list(RoomMember.objects.exclude(name='Mr Ali').values_list('name', flat=True))
                    else:
                        cv2.putText(frame, 'No Faces', (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
            cam.send(frame)
    return render(request, 'Student/base/room.html')
