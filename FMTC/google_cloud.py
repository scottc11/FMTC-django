from builtins import str as text
import logging
from django.contrib.auth import settings
from django.utils import timezone
from gcloud import datastore, storage
from gcloud.exceptions import GCloudError
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger('probex.google_cloud')
__all__ = ['PROJECT_ID', 'DEFAULT_JOBQUEUE_NAME', 'DEFAULT_ZONE', 'DEFAULT_BUCKET_NAME', 'DEFAULT_JOB_BUCKET_NAME',
           'TEAM', 'machine_types', 'default_bucket', 'default_job_bucket', 'http_compute', 'gce_service',
           'update_datastore', 'upload_to_storage', 'create_datastore', 'get_from_storage']


# Default values for Google Cloud
PROJECT_ID = 'cyclica-ligandexpress-46'
API_VERSION = 'v1'
DEFAULT_ZONE = 'us-central1-c'
DEFAULT_JOBQUEUE_NAME = 'Ligand_Express'
DEFAULT_JOB_BUCKET_NAME = "ligexprj"
DEFAULT_BUCKET_NAME = "ligex"
TEAM = 'science'

machine_types = {
    1: "n1-standard-1",
    2: "n1-highcpu-2",
    4: "n1-highcpu-4",
    8: "n1-highcpu-8",
    16: "n1-highcpu-16",
    32: "n1-highcpu-32"
}

# Create service credentials for Google Cloud
scopes = ['https://www.googleapis.com/auth/compute',
          'https://www.googleapis.com/auth/datastore',
          'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/devstorage.read_write'
          ]

# This try except is needed to allow CI testing to pass - it does not properly set the
# variables because there are not appropriate service credentials
try:
    service_credentials = ServiceAccountCredentials.from_json_keyfile_dict(settings.GOOGLE_CREDENTIALS, scopes=scopes)
    http_compute = service_credentials.authorize(Http())

    # Create clients for gcloud compatible Google Cloud Services
    gce_service = build('compute', API_VERSION, http=http_compute)
    datastore_client = datastore.Client(credentials=service_credentials, project=PROJECT_ID)
    storage_client = storage.Client(credentials=service_credentials, project=PROJECT_ID)
    default_bucket = storage_client.get_bucket(DEFAULT_BUCKET_NAME)
    default_job_bucket = storage_client.get_bucket(DEFAULT_JOB_BUCKET_NAME)
except ValueError:
    import mock
    service_credentials = object()
    http_compute = object()
    gce_service = object()
    datastore_client = object()
    storage_client = object()
    default_bucket = mock.Mock()
    mockblob = mock.MagicMock()
    mockblob.name = 'foo-0.16.0.whl'
    default_bucket.list_blobs = mock.MagicMock(return_value=[mockblob], name=['foo-bar.whl'])
    default_job_bucket = mock.MagicMock()


def update_datastore(job_num, status):
    """
    Update the status of the Google Datastore entry for the job number.
    :param job_num: int
    :param status: str
    """
    query = datastore_client.query(kind="Job")
    query.add_filter("job_num", "=", job_num)
    results = list(query.fetch())
    if len(results) == 0:
        raise Exception("Datastore entry not found.")
    entity = results[0]

    with datastore_client.transaction():
        entity['date'] = timezone.localtime(timezone.now())
        entity['status'] = text(status)
        datastore_client.put(entity)


def remove_datastore(job_num):
    """
    Delete a job from the datastore.
    :param job_num: int
    """
    query = datastore_client.query(kind="Job")
    query.add_filter("job_num", "=", job_num)
    results = list(query.fetch())
    if len(results) == 0:
        raise Exception("Datastore entry not found.")
    entity = results[0]

    with datastore_client.transaction():
        datastore_client.delete(entity.key())


def upload_to_storage(obj, bucket_name, blob_path, filename=False, string=False, stream=False):
    """
    Upload to Google Cloud Storage to given bucket name and blob path.
    :param obj: str or filestream, object you want to upload can be a filename, string or filestream
    :param bucket_name: str
    :param blob_path: str
    :param filename: bool
    :param string: bool
    :param stream: bool
    """
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_path)
    try:
        if filename:
            blob.upload_from_filename(obj)
        elif string:
            blob.upload_from_string(obj)
        elif stream:
            blob.upload_from_file(obj)
        else:
            raise Exception("You must indicate type of object: filename, string or stream.")
    except GCloudError as err:
        logger.exception(err)
        raise err


def create_datastore(job):
    """
    Create a Google Datastore entry and return the Key formatted for pipeline
    :param job: Job instance
    :return: str, Datastore key formatted for pipeline
    """
    with datastore_client.transaction():
        parent_key = datastore_client.key('Job Queue', DEFAULT_JOBQUEUE_NAME)
        key = datastore_client.key('Job', parent=parent_key)
        newjob = datastore.Entity(key=key)
        newjob['date'] = job.created
        newjob['email'] = job.approver.email
        newjob['job_num'] = job.absolute_num
        newjob['files.filename'] = job.structure.name
        newjob['status'] = text(job.status)
        newjob['error'] = False
        datastore_client.put(newjob)
    key = "Key" + str(newjob.key.flat_path)
    return key


def get_from_storage(bucket_name, blob_path, filename=None, string=False, stream=None):
    """
    Download file from Google Storage.
    :param bucket_name: str, Bucket where the file is in
    :param blob_path: str, path of file in Google Storage after bucket
    :param filename: str
    :param string: bool
    :param stream: file object
    return: str, if string return blob as string
    """
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_path)
    if blob:
        if filename:
            blob.download_to_filename(filename)
        elif string:
            data = blob.download_as_string()
            return data
        elif stream:
            blob.download_to_file(stream)
        else:
            raise ValueError("You must indicate type of object: filename, string or stream.")
    else:
        raise ValueError("That blob does not exist.")


def wipe_storage_folder(prefix, bucket_name=DEFAULT_JOB_BUCKET_NAME):
    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    bucket.delete_blobs(list(blobs))
