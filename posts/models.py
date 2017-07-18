
from django.conf import settings
from django.db import models
from FMTC.storage import GoogleCloudStorage
from datetime import datetime


def format_storage_path(instance, filename):
    date = datetime.now()
    date = datetime.isoformat(date).split('T')[0]
    return '{0}/{1}'.format(date, filename)


# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=250)
    sub_title = models.CharField(max_length=500)
    pub_date = models.DateTimeField()
    image = models.ImageField(upload_to=format_storage_path, storage=GoogleCloudStorage())
    thumbnail = models.ImageField(upload_to=format_storage_path, storage=GoogleCloudStorage())
    body = models.TextField()
    github = models.URLField(max_length=250, default='https://github.com/scottc11')

    def __str__(self):
        return self.title

    def pub_date_pretty(self):
        return self.pub_date.strftime('%b %e %Y')

    def summary(self):
        return self.body[:100]







# structure = models.FileField(blank=True, default="", upload_to=get_path, storage=GoogleCloudStorage(), validators=[file_size])
