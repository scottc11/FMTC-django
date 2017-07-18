import os
import tempfile

from django.conf import settings
from django.utils.deconstruct import deconstructible
from django.core.files.storage import Storage
from google.cloud import storage


@deconstructible()
class GoogleCloudStorage(Storage):
    def __init__(self, option=None):
        self.storage_client = storage.Client(project=settings.GOOGLE_APPLICATION_CREDENTIALS['project_id'])
        self.bucket = self.storage_client.get_bucket(settings.CLOUD_STORAGE_BUCKET)
        self.storage_location = settings.MEDIA_PREFIX

    def _open(self, name, mode='rb'):
        print('------------------')
        print('in open')
        filepath = self.storage_location + name # ex. 'media/filename.png'
        if self.storage_location in name:
            filepath = name
        if self.exists(name):
            blob = self.bucket.get_blob(filepath)
            temp_file = tempfile.TemporaryFile()
            blob.download_to_file(temp_file)
            return File(temp_file)

    def _save(self, name, file_obj):
        filepath = self.storage_location + name
        blob = self.bucket.blob(filepath)
        try:
            blob.upload_from_file(file_obj, size=file_obj.size)
        except GCloudError as err:
            print(err)
        return filepath

    def delete(self, name):
        filename = self.storage_location + name
        if self.storage_location in name:
            filename = name
        if self.exists(name):
            blob = self.bucket.get_blob(filename)
            blob.delete()

    def exists(self, name):
        filename = self.storage_location + name
        if self.storage_location in name:
            filename = name
        exists = self.bucket.blob(filename).exists()
        return exists

    def url(self, name):
        filename = self.storage_location + name
        if self.storage_location in name:
            filename = name
        if self.exists(name):
            url = self.bucket.get_blob(filename).public_url
        else:
            url = "File does not exist."
        return url
