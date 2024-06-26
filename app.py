import os
import time
import base64
import shutil
import requests
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Load environment variables from .env file
load_dotenv()

# Configuration
WATCHED_DIR = os.getenv('WATCHED_DIR')
WATCHED_DIRS = os.getenv('WATCHED_DIRS').split(',')
TEMP_DIR = os.getenv('TEMP_DIR')
API_URL = os.getenv('API_URL')
LAABS_AUTH = os.getenv('LAABS_AUTH')
ARCHIVAL_PROFILE_REFERENCE = os.getenv('ARCHIVAL_PROFILE_REFERENCE')
SERVICE_LEVEL_REFERENCE = os.getenv('SERVICE_LEVEL_REFERENCE')
RETENTION_RULE_CODE = os.getenv('RETENTION_RULE_CODE')
DESCRIPTION_CLASS = os.getenv('DESCRIPTION_CLASS')
FULL_TEXT_INDEXATION = os.getenv('FULL_TEXT_INDEXATION', 'none')
DESCRIPTION_LEVEL = os.getenv('DESCRIPTION_LEVEL')


def wait_for_file_availability(file_path, retries=5, delay=1):
    """Wait for a file to become available if it is in use."""
    for i in range(retries):
        try:
            with open(file_path, 'rb') as file:
                file.read()
            return  # File is available
        except IOError:
            print(f"File {file_path} is in use, retrying ({i + 1}/{retries})...")
            time.sleep(delay)
    raise IOError(f"File {file_path} is still in use after {retries} retries.")


def copy_to_temp(file_path):
    """Copy file to temporary directory and return new file path."""
    try:
        temp_file_path = os.path.join(TEMP_DIR, os.path.basename(file_path))
        wait_for_file_availability(file_path)
        shutil.copy2(file_path, temp_file_path)
        return temp_file_path
    except Exception as e:
        print(f"Error copying file to temp directory: {e}")


def get_custom_file_name(file_path):
    """Generate custom file name based on directory and file name."""
    try:
        directory = os.path.basename(os.path.dirname(file_path))
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        return f"{file_name}"
    except Exception as e:
        print(f"Error generating custom file name: {e}")
        return os.path.basename(file_path)


def clean_temp_dir():
    """Clean the temporary directory by removing all files."""
    try:
        for file_name in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, file_name)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    except Exception as e:
        print(f"Error cleaning temp directory: {e}")


class Watcher(FileSystemEventHandler):
    def __init__(self):
        self.pending_files = []

    def on_created(self, event):
        try:
            if event.is_directory:
                print(f"New directory detected: {event.src_path}")
                self.process_new_directory(event.src_path)
            else:
                print(f"New file detected: {event.src_path}")
                self.process_file(event.src_path)
        except Exception as e:
            print(f"Error processing created event: {e}")

    def process_new_directory(self, dir_path):
        """Process all files in a new directory."""
        try:
            for root, _, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    self.process_file(file_path)
        except Exception as e:
            print(f"Error processing new directory: {e}")

    def process_file(self, file_path):
        """Process an individual file."""
        try:
            if os.path.isfile(file_path) and not file_path.endswith('~'):
                temp_file_path = copy_to_temp(file_path)
                encoded_content = self.encode_file_to_base64(temp_file_path)
                self.add_file_to_pending(temp_file_path, encoded_content)
            else:
                print(f"Ignored file (not valid or temporary): {file_path}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    @staticmethod
    def encode_file_to_base64(file_path):
        """Encode file content to base64."""
        try:
            with open(file_path, 'rb') as file:
                encoded_string = base64.b64encode(file.read()).decode('utf-8')
            return encoded_string
        except Exception as e:
            print(f"Error encoding file to base64: {e}")

    def add_file_to_pending(self, file_path, encoded_content):
        """Add file data to pending list."""
        try:
            print(f"file : {file_path}")
            # file_name = os.path.basename(file_path)
            file_name = get_custom_file_name(file_path)
            mimetype = self.get_mimetype(file_path)
            print(f"file_name {file_name}")
            file_data = {
                "handler": encoded_content,
                "size": str(os.path.getsize(file_path)),
                "fileName": file_name,
                "mimetype": mimetype
            }
            self.pending_files.append(file_data)
            self.send_pending_files(file_name)
        except Exception as e:
            print(f"Error adding file to pending list: {e}")

    def send_pending_files(self, file_name):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'service',
            'Cookie': 'LAABS-AUTH=' + LAABS_AUTH
        }
        """Send pending files to API."""
        if len(self.pending_files) > 0:
            try:
                data = self.create_api_data(file_name)
                response = requests.post(API_URL, json=data, headers=headers)
                if response.status_code == 200:
                    print(f"Data sent successfully. {response}")
                    self.pending_files = []
                    clean_temp_dir()
                else:
                    print(f"Error {response.status_code} sending data: {response.text}")
            except Exception as e:
                print(f"Exception while sending data to API: {e}")

    def create_api_data(self, file_name):
        """Create data for API request."""
        try:
            archive_name = file_name
            data = {
                "archive": {
                    "digitalResources": self.pending_files,
                    "archiveName": archive_name,
                    "archivalProfileReference": ARCHIVAL_PROFILE_REFERENCE,
                    "serviceLevelReference": SERVICE_LEVEL_REFERENCE,
                    # "retentionRuleCode": RETENTION_RULE_CODE,
                    # "retentionStartDate": "2018-01-01",
                    # "retentionDuration": "P10Y",
                    "finalDisposition": "preservation",
                    # "disposalDate": "2028-01-01",
                    "retentionRuleStatus": None,
                    # "accessRuleCode": "AR039",
                    # "accessRuleDuration": "P25Y",
                    # "accessRuleStartDate": "2007-01-01",
                    # "accessRuleComDate": "2032-01-01",
                    "classificationRuleCode": None,
                    "classificationRuleDuration": None,
                    "classificationRuleStartDate": None,
                    "classificationEndDate": None,
                    "classificationLevel": None,
                    "classificationOwner": None,
                    "userOrgRegNumbers": None,
                    # "depositDate": "2024-02-15T10:53:59.000Z",
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
                        "descriptionLevel": DESCRIPTION_LEVEL,
                        "filePlanPosition": [
                            "2020/Janvier"
                        ]
                    },
                    "fullTextIndexation": FULL_TEXT_INDEXATION,
                    "descriptionClass": DESCRIPTION_CLASS,
                    "fileplanLevel": "item",
                    "processingStatus": None,
                    "parentArchiveId": None
                },
                "zipContainer": False
            }
            return data
        except Exception as e:
            print(f"Error creating API data: {e}")

    @staticmethod
    def get_mimetype(file_path):
        """Determine the MIME type of a file."""
        try:
            import mimetypes
            mimetype, _ = mimetypes.guess_type(file_path)
            return mimetype if mimetype else "application/octet-stream"
        except Exception as e:
            print(f"Error getting mimetype for file {file_path}: {e}")


if __name__ == "__main__":
    try:
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)

        event_handler = Watcher()
        observers = []

        for directory in WATCHED_DIRS:
            observer = Observer()
            observer.schedule(event_handler, directory, recursive=True)
            observers.append(observer)
            print(f"Watching directory: {directory}")

        for observer in observers:
            observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            for observer in observers:
                observer.stop()
        for observer in observers:
            observer.join()
    except Exception as e:
        print(f"Error starting the watcher: {e}")
