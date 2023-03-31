from django.contrib import admin

# Register your models here.

from .models import RoomMember, Detection, Etudiant,Savemember


admin.site.register(RoomMember)
admin.site.register(Detection)
admin.site.register(Etudiant)
admin.site.register(Savemember)