import logging
import os
import tempfile
from django.core.exceptions import SuspiciousFileOperation
from django.core.files import File
from django.core.files.storage import Storage
from django.conf import settings
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from gcloud.exceptions import GCloudError
from probex.google_cloud import TEAM, default_job_bucket

logger = logging.getLogger('probex.storage')


# pylint: disable=abstract-method
@deconstructible()
class GoogleCloudStorage(Storage):
    """
    Custom file storage backend to Google Cloud Storage.
    """

    def __init__(self):
        self.bucket = default_job_bucket
        self.storage_location = TEAM

    def _open(self, name, mode='rb'):
        filename = self.storage_location + name
        if self.storage_location in name:
            filename = name
        if self.exists(name):
            blob = self.bucket.get_blob(filename)
            temp_file = tempfile.TemporaryFile()
            blob.download_to_file(temp_file)
            return File(temp_file)

    def _save(self, name, content):
        filename = self.storage_location + name
        if self.storage_location in name:
            filename = name
        blob = self.bucket.blob(filename)
        # upload file to storage
        if settings.TEST_LOCK_ON:
            return filename
        try:
            blob.upload_from_file(content, size=content.size)
        except GCloudError as err:
            logger.exception(err)
        return filename

    def delete(self, name):
        filename = self.storage_location + name
        if self.storage_location in name:
            filename = name
        if self.exists(name):
            blob = self.bucket.get_blob(filename)
            blob.delete()

    def url(self, name):
        filename = self.storage_location + name
        if self.storage_location in name:
            filename = name
        if self.exists(name):
            url = self.bucket.get_blob(filename).public_url
        else:
            url = "File does not exist."
        return url

    def exists(self, name):
        filename = self.storage_location + name
        if self.storage_location in name:
            filename = name
        exists = self.bucket.blob(filename).exists()
        return exists

    def get_available_name(self, name, max_length=None):
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        datetime = timezone.localtime(timezone.now())
        date_string = datetime.strftime("%Y-%m-%d-%T")
        while self.exists(name) or (max_length and len(name) > max_length):
            name = os.path.join(dir_name, "%s_%s%s" % (file_root, date_string, file_ext))
            if max_length is None:
                continue
            truncation = len(name) - max_length
            if truncation > 0:
                file_root = file_root[:truncation]
                if not file_root:
                    raise SuspiciousFileOperation(
                        'Storage can not find an available filename for "%s". '
                        'Please make sure that the corresponding file field '
                        'allows sufficient "max_length".' % name
                    )
                name = os.path.join(dir_name, "%s_%s%s" % (file_root, date_string, file_ext))
        return name

    def size(self, name):
        filename = self.storage_location + name
        if self.storage_location in name:
            filename = name
        if self.exists(name):
            blob = self.bucket.get_blob(filename)
            return blob.size
