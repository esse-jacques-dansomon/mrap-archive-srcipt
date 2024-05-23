import os
import time
import base64
import requests
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Load environment variables from .env file
load_dotenv()

# Configuration
WATCHED_DIR = os.getenv('WATCHED_DIR')
API_URL = os.getenv('API_URL')
LAABS_AUTH = os.getenv('LAABS_AUTH')
ARCHIVAL_PROFILE_REFERENCE = os.getenv('ARCHIVAL_PROFILE_REFERENCE')
SERVICE_LEVEL_REFERENCE = os.getenv('SERVICE_LEVEL_REFERENCE')
RETENTION_RULE_CODE = os.getenv('RETENTION_RULE_CODE')
DESCRIPTION_CLASS = os.getenv('DESCRIPTION_CLASS')
FULL_TEXT_INDEXATION = os.getenv('FULL_TEXT_INDEXATION', 'none')
DESCRIPTION_LEVEL = os.getenv('DESCRIPTION_LEVEL')


class Watcher(FileSystemEventHandler):
    def __init__(self):
        self.pending_files = []

    def on_created(self, event):
        if event.is_directory:
            print(f"New directory detected: {event.src_path}")
            self.process_new_directory(event.src_path)
        else:
            print(f"New file detected: {event.src_path}")
            self.process_file(event.src_path)

    def process_new_directory(self, dir_path):
        """Process all files in a new directory."""
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                self.process_file(file_path)

    def process_file(self, file_path):
        """Process an individual file."""
        if os.path.isfile(file_path) and not file_path.endswith('~'):
            encoded_content = self.encode_file_to_base64(file_path)
            self.add_file_to_pending(file_path, encoded_content)
        else:
            print(f"Ignored file (not valid or temporary): {file_path}")

    @staticmethod
    def encode_file_to_base64(file_path):
        """Encode file content to base64."""
        with open(file_path, 'rb') as file:
            encoded_string = base64.b64encode(file.read()).decode('utf-8')
        return encoded_string

    def add_file_to_pending(self, file_path, encoded_content):
        """Add file data to pending list."""
        file_name = os.path.basename(file_path)
        mimetype = self.get_mimetype(file_path)
        file_data = {
            "handler": encoded_content,
            "size": str(os.path.getsize(file_path)),
            "fileName": file_name,
            "mimetype": mimetype
        }
        self.pending_files.append(file_data)
        self.send_pending_files()

    def send_pending_files(self):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'service',
            'Cookie': 'LAABS-AUTH=' + LAABS_AUTH
        }
        """Send pending files to API."""
        if len(self.pending_files) > 0:
            data = self.create_api_data()
            response = requests.post(API_URL, json=data, headers=headers)
            if response.status_code == 200:
                print(f"Data sent successfully. {response}")
                self.pending_files = []
            else:
                print(f"Error {response} sending data.")

    def create_api_data(self):
        """Create data for API request."""
        archive_name = os.path.basename(WATCHED_DIR)
        data = {
            "archive": {
                "digitalResources": self.pending_files,
                "archiveName": archive_name,
                "archivalProfileReference": ARCHIVAL_PROFILE_REFERENCE,
                "serviceLevelReference": SERVICE_LEVEL_REFERENCE,
                "retentionRuleCode": RETENTION_RULE_CODE,
                "retentionStartDate": "2018-01-01",
                "retentionDuration": "P10Y",
                "finalDisposition": "preservation",
                "disposalDate": "2028-01-01",
                "retentionRuleStatus": None,
                "accessRuleCode": "AR039",
                "accessRuleDuration": "P25Y",
                "accessRuleStartDate": "2007-01-01",
                "accessRuleComDate": "2032-01-01",
                "classificationRuleCode": None,
                "classificationRuleDuration": None,
                "classificationRuleStartDate": None,
                "classificationEndDate": None,
                "classificationLevel": None,
                "classificationOwner": None,
                "userOrgRegNumbers": None,
                "depositDate": "2024-02-15T10:53:59.000Z",
                "lastCheckDate": None,
                "lastDeliveryDate": None,
                "lastModificationDate": None,
                "status": "preserved",
                "description": {
                    "title": [
                        archive_name
                    ],
                    "keyword": [
                        {
                            "keywordType": "corpname",
                            "keywordContent": "API"
                        }
                    ],
                    "language": [
                        "fra"
                    ],
                    "sentDate": "2000-12-23",
                    "documentType": "Facture",
                    "descriptionLevel": "Item",
                    "filePlanPosition": [
                        "2020/Janvier"
                    ]

                },
                "fullTextIndexation": "none",
                "descriptionClass": "seda2",
                "fileplanLevel": "item",
                "processingStatus": None,
                "parentArchiveId": None

            },
            "zipContainer": False
        }
        return data

    @staticmethod
    def get_mimetype(file_path):
        """Determine the MIME type of a file."""
        import mimetypes
        mimetype, _ = mimetypes.guess_type(file_path)
        return mimetype if mimetype else "application/octet-stream"


if __name__ == "__main__":
    event_handler = Watcher()
    observer = Observer()
    observer.schedule(event_handler, WATCHED_DIR, recursive=True)

    print(f"Watching directory: {WATCHED_DIR}")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
