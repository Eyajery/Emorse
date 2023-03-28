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
#from agora import AgoraRTCClient

# Se connecter à la base de données MySQL
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="detection_emotion_db",
)
# Créer la table pour stocker les données de détection d'émotion
mycursor = mydb.cursor()
mycursor.execute("CREATE TABLE IF NOT EXISTS detections (id INT AUTO_INCREMENT PRIMARY KEY, emotion VARCHAR(255), detection_time DATETIME)")

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
    return render(request, 'Teacher/base/room.html')
def room_s(request):
    return render(request, 'Student/base/room.html')

#Dashboarding: Teacher
def dashboard_t(request):
    detections = Detection.objects.all()
    data = [{'emotion': d.emotion, 'detection_time': d.detection_time} for d in detections]
    context = {'data': data}
    return render(request, 'Teacher/dashboard/dashboard.html', context)

#Dashboarding: Student
def dashboard_s(request):
    detections = Detection.objects.all()
    data = [{'emotion': d.emotion, 'detection_time': d.detection_time} for d in detections]
    context = {'data': data}
    return render(request, 'Student/dashboard/dashboard.html', context)

def getToken(request):
    appId = "72bfab75cd3b4b1b87aab06996d2daed"
    appCertificate = "c64c362a21c742fbb613ba61118128e2"
    channelName = request.GET.get('channel')
    uid = random.randint(1, 230)
    expirationTimeInSeconds = 3600
    currentTimeStamp = int(time.time())
    privilegeExpiredTs = currentTimeStamp + expirationTimeInSeconds
    role = 1

    token = RtcTokenBuilder.buildTokenWithUid(appId, appCertificate, channelName, uid, role, privilegeExpiredTs)

    return JsonResponse({'token': token, 'uid': uid}, safe=False)


@csrf_exempt
def createMember(request):
    data = json.loads(request.body)
    member, created = RoomMember.objects.get_or_create(
        name=data['name'],
        uid=data['UID'],
        room_name=data['room_name']
    )

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

@csrf_exempt
def deleteMember(request):
    data = json.loads(request.body)
    member = RoomMember.objects.get(
        name=data['name'],
        uid=data['UID'],
        room_name=data['room_name']
    )
    member.delete()
    return JsonResponse('Member deleted', safe=False)

def student(request):
    return render(request, 'Student/base/student.html')
 # Load the emotion detection model
classifier =load_model(r'C:\Users\aya\Desktop\Emotion_Detection\model.h5')

    # Initialize the emotion labels and the MySQL database connection
emotion_labels = ['Angry','Disgust','Fear','Happy','Neutral', 'Sad', 'Surprise']

# Create a cascade classifier for detecting faces
face_classifier = cv2.CascadeClassifier(r'C:\Users\aya\Desktop\Emotion_Detection\haarcascade_frontalface_default.xml')


# Function to generate frames from the video stream
def gen_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            labels = []
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_classifier.detectMultiScale(gray)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                roi_gray = gray[y:y + h, x:x + w]
                roi_gray = cv2.resize(roi_gray, (48, 48), interpolation=cv2.INTER_AREA)
                if np.sum([roi_gray]) != 0:
                    roi = roi_gray.astype('float') / 255.0
                    roi = np.array(roi)
                    roi = np.expand_dims(roi, axis=0)
                    prediction = classifier.predict(roi)[0]
                    label = emotion_labels[prediction.argmax()]
                    label_position = (x, y)
                    cv2.putText(frame, label, label_position, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    Detection.objects.create(emotion=label, detection_time=timezone.now())
                    # Sauvegarder les données de détection d'émotion dans la base de données
                    sql = "INSERT INTO detections (emotion, detection_time) VALUES (%s, %s)"
                    val = (label, datetime.now())
                    mycursor.execute(sql, val)
                    mydb.commit()
                else:
                    cv2.putText(frame, 'No Faces', (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Decorator to compress the video stream
@gzip.gzip_page
def emotion_detection(request):
    try:
        return StreamingHttpResponse(gen_frames(), content_type="multipart/x-mixed-replace;boundary=frame")
    except Exception as e:
        print(e)

  





            