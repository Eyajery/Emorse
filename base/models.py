from django.db import models

# Create your models here.

class RoomMember(models.Model):
    name = models.CharField(max_length=200)
    uid = models.CharField(max_length=1000)
    room_name = models.CharField(max_length=200)
    insession = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name}, {self.uid},{self.room_name},{self.insession}'
class Etudiant(models.Model):
    nom = models.CharField(max_length=100)
    etat=models.CharField(max_length=100,default='absent(e)')
   


    class Meta:
        verbose_name_plural = 'etudiant'

    def __str__(self):
        return f'{self.nom},{self.etat}'



class Detection(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE,default=None)
    emotion = models.CharField(max_length=255)
    detection_time = models.DateTimeField(auto_now_add=True)
   
    class Meta:
        verbose_name_plural = 'Detection'

    def __str__(self):
        return f'{self.emotion}, {self.detection_time},{self.etudiant}'
    
    
