import boto3
import botocore
import os
from tqdm import tqdm

# Configure client to access public AWS S3 bucket without credentials
s3 = boto3.client('s3', config=botocore.config.Config(signature_version=botocore.UNSIGNED))

bucket_name = 'amazon-last-mile-challenges'
prefix = 'almrrc2021/'  # Path to the 2021 challenge data
output_dir = './data'

os.makedirs(output_dir, exist_ok=True)

print("Fetching file list from S3 bucket...")
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
contents = response.get('Contents', [])

# Filter out directory placeholders
files_to_download = [obj for obj in contents if not obj['Key'].endswith('/')]

print(f"Found {len(files_to_download)} files to check/download.")

for obj in files_to_download:
    file_key = obj['Key']
    file_size = obj['Size']
    
    # Create matching folder paths locally
    local_file_path = os.path.join(output_dir, os.path.relpath(file_key, prefix))
    
    # Check if file exists and matches the size on S3
    if os.path.exists(local_file_path) and os.path.getsize(local_file_path) == file_size:
        print(f"Skipping (already downloaded): {os.path.basename(file_key)}")
        continue

    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
    
    # Set up the individual file progress bar
    file_name = os.path.basename(file_key)
    with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Downloading {file_name}") as pbar:
        s3.download_file(
            Bucket=bucket_name, 
            Key=file_key, 
            Filename=local_file_path,
            Callback=pbar.update  # Feeds download progress directly into the progress bar
        )

print("\nAll downloads completed successfully!")
