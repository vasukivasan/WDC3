from azure.storage.blob import BlobServiceClient
import os


class AzureSession():
    def __init__(self):
        pass

    def download_blob_to_file(self, filePath, fileName):

        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=fileName)

        print("Started downloading")
        with open(file=filePath, mode="wb") as sample_blob:
            download_stream = blob_client.download_blob()
            sample_blob.write(download_stream.readall())
        print("Download Complete")

    def uploadToBlobStorage(self,file_path, fileName):
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=fileName)
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data)
            print(f"Uploaded {fileName}.")