from flask import Flask, request, jsonify
import boto3
import re
import io
from PIL import Image
import time
from waitress import serve

app = Flask(__name__)

# Aadhaar pattern (12 digits or 4-4-4 group format)
AADHAAR_REGEX = r'\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b'

# AWS Textract client
textract = boto3.client(
    'textract',
    region_name='us-east-1',  # Change this if needed
    aws_access_key_id='AKIAYOISDC7MZZPA3G5G',
    aws_secret_access_key='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'
)

def extract_aadhaar_from_image(image_bytes):
    try:
        # Call AWS Textract to detect document text
        response = textract.detect_document_text(Document={'Bytes': image_bytes})

        # Extracting all text from the response blocks
        extracted_text = " ".join(
            [item["Text"] for item in response["Blocks"] if item["BlockType"] == "WORD"]
        )

        print("[*] Extracted Text:", extracted_text)  # Debugging print for the extracted text

        # Using regex to find Aadhaar numbers in the extracted text
        aadhaar_numbers = re.findall(AADHAAR_REGEX, extracted_text)
        
        # Return the Aadhaar numbers without spaces
        return [n.replace(" ", "") for n in aadhaar_numbers]

    except Exception as e:
        print(f"[!] Error during Textract extraction: {e}")
        raise

@app.route('/extract_aadhaar', methods=['POST'])
def extract_aadhaar():
    print('[*] Received request')

    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded."}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "Empty file uploaded."}), 400

    try:
        image_bytes = image_file.read()

        print('[*] Sending to AWS Textract...')
        start_time = time.time()
        aadhaar_numbers = extract_aadhaar_from_image(image_bytes)
        elapsed = time.time() - start_time
        print(f'[*] AWS Textract processing time: {elapsed:.2f}s')

        print('[*] Aadhaar Numbers:', aadhaar_numbers)

        if not aadhaar_numbers:
            return jsonify({"message": "No Aadhaar number found."}), 404

        return jsonify({"aadhaar_numbers": aadhaar_numbers}), 200

    except Exception as e:
        print('[!] Error:', str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting server on http://127.0.0.1:5000")
    serve(app, host='127.0.0.1', port=5000)
