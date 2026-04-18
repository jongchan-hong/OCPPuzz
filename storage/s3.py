from parser_modules.s3_upload_config_dto import S3UploadConfigDTO


def get_s3_config():
    access_key = input("Write your s3 access key >>")
    if not access_key:
        print("s3 access key is missing")
        exit()
    secret_key = input("Write your s3 secret key >>")
    if not secret_key:
        print("s3 secret key is missing")
        exit()
    bucket_name = input("Write your s3 bucket name >>")
    if not bucket_name:
        print("s3 bucket name is missing")
        exit()
    region = input("Write your s3 region >>")
    if not region:
        print("s3 region is missing")
        exit()
    return S3UploadConfigDTO (
        access_key=access_key,
        secret_key=secret_key,
        bucket_name=bucket_name,
        region=region,
    )