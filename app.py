import os
import shutil
import json
from flask import Flask, render_template, request, redirect
from main import process_video  # don't forget to support timecodes inside process_video!
from generate_report import generate_report

# folders for storing files
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
RESULT_JSON = os.path.join(RESULT_FOLDER, 'results.json')

# create folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# clear upload folder before start
def clear_upload_folder():
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

clear_upload_folder()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        if file:
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
            return redirect(request.url)

    files = os.listdir(app.config["UPLOAD_FOLDER"])
    return render_template("index.html", files=files)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file", 400

        file = request.files['file']
        if file.filename == '':
            return "No file selected", 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # get timecodes
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")

        try:
            start_time = float(start_time) if start_time else None
            end_time = float(end_time) if end_time else None
        except ValueError:
            return "Invalid time values", 400

        # validate duration
        if start_time is not None and end_time is not None:
            if end_time - start_time < 1.0:
                return '''
                <script>
                    alert("Minimum interval length is 1 second.");
                    window.history.back();
                </script>
                '''

        # process the video
        process_video(filepath, start_time=start_time, end_time=end_time)

        # load results
        if os.path.exists(RESULT_JSON):
            with open(RESULT_JSON, 'r', encoding='utf-8') as f:
                results = json.load(f)
        else:
            results = {}

        return render_template('upload.html', results=results)

    # GET request
    if os.path.exists(RESULT_JSON):
        with open(RESULT_JSON, 'r', encoding='utf-8') as f:
            results = json.load(f)
    else:
        results = {}

    return render_template('upload.html', results=results)

generate_report()

if __name__ == '__main__':
    app.run(debug=True)
