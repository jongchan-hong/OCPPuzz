from dataclasses import dataclass
from typing import Optional

@dataclass
class S3UploadConfigDTO:
    access_key: str
    secret_key: str
    bucket_name: str
    s3_prefix: str = "uploads"
    region: str = "us-east-2"
    public: bool = True