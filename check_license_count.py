import sys
import json
import os

def check_license_count(json_file, threshold):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        total_count = 0  
        licenses = {}  
        # Extract license information from the 'license_detections'
        for detection in data.get('license_detections', []):
            license_expression = detection['license_expression']
            detection_count = detection['detection_count']
            licenses[license_expression] = detection_count
            total_count += detection_count  

        print(f"Detected licenses: {licenses}") 
        print(f"Total number of detected licenses: {total_count}")

        if total_count >= threshold:
            print(f"License detection meets the threshold ({threshold}). Test passed!")
            sys.exit(0)  # Exit with success
        else:
            print(f"License detection is below the threshold ({threshold}). Test failed.")
            sys.exit(1)  # Exit with failure

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_license_count.py <path_to_json_file> [threshold]")
        sys.exit(1)

    json_file = sys.argv[1]

    # Use an environment variable for threshold if available, or default to 3
    threshold = int(os.getenv('LICENSE_THRESHOLD', 3))

    # If a threshold is provided as an argument, override the default
    if len(sys.argv) > 2:
        try:
            threshold = int(sys.argv[2])
        except ValueError:
            print("Threshold must be an integer.")
            sys.exit(1)

    check_license_count(json_file, threshold)
