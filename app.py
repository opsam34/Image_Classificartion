from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
import os
from DeepImageSearch import Index, LoadData, SearchImage
from PIL import Image
import hashlib

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_image_hash(image_path):
    """Generate a hash for an image to check if it's a duplicate."""
    hash_sha256 = hashlib.sha256()
    with open(image_path, 'rb') as f:
        while chunk := f.read(8192):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_folder():
    if 'folder' not in request.files:
        return "No folder part"
    
    folder_files = request.files.getlist('folder')
    if not folder_files:
        return "No file selected"
    
    image_paths = []
    for file in folder_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            image_paths.append(file_path)

    image_list = LoadData().from_folder([UPLOAD_FOLDER])
    Index(image_list).Start()

    output_images = {}
    saved_image_hashes = set()

    for image_path in image_paths:
        si = SearchImage().get_similar_images(image_path="car.jpg", number_of_images=4)

        for i, (key, img_path) in enumerate(si.items()):
            img_hash = get_image_hash(img_path)
            if img_hash not in saved_image_hashes:
                output_image_path = os.path.join(OUTPUT_FOLDER, f"{os.path.basename(image_path)}_similar_{i + 1}.jpg")
                img = Image.open(img_path)
                img.save(output_image_path)
                saved_image_hashes.add(img_hash)

                similarity = 'N/A'  

                output_images[image_path] = {
                    "image_path": os.path.basename(output_image_path),
                    "similarity": similarity  
                }

    return render_template('results.html', output_images=output_images)


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
