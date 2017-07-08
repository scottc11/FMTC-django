from django.db import models

# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=250)
    sub_title = models.CharField(max_length=500)
    pub_date = models.DateTimeField()
    image = models.ImageField(upload_to='static/media/')
    thumbnail = models.ImageField(upload_to='static/media/')
    body = models.TextField()
    github = models.URLField(max_length=250, default='https://github.com/scottc11')

    def __str__(self):
        return self.title

    def pub_date_pretty(self):
        return self.pub_date.strftime('%b %e %Y')

    def summary(self):
        return self.body[:100]
