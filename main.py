from flask import Flask
from flask import render_template, send_from_directory, url_for, redirect

from flask_uploads import UploadSet, IMAGES, configure_uploads

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired

from wtforms import FileField, SubmitField

import os
import cv2


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some secret string'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# The code above will limit the maximum allowed payload to 16 megabytes.
# If a larger file is transmitted,
# Flask will raise a RequestEntityTooLarge exception.
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

app.config['UPLOADED_PHOTOS_DEST'] = UPLOAD_FOLDER
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)

app.config['LASTIMGPATH_FILENAME'] = 'last_image_path.txt'


class UploadForm(FlaskForm):
    # name = StringField('name', validators=[DataRequired()])
    photo = FileField(
        validators=[
            FileAllowed(ALLOWED_EXTENSIONS, 'Only images are allowed'),
            FileRequired('File should not be empty')
        ]
    )
    submit = SubmitField('Upload')


class RotateForm(FlaskForm):
    rotate_left = SubmitField('Rotate left')
    rotate_right = SubmitField('Rotate right')


def get_last_image_path():
    filepath = os.path.join(
        app.static_folder,
        app.config['LASTIMGPATH_FILENAME']
    )
    if not os.path.isfile(filepath):
        return None

    with open(filepath, 'r') as f:
        image_path = f.readline()

    return image_path


def set_last_image_path(image_path):
    filepath = os.path.join(
        app.static_folder,
        app.config['LASTIMGPATH_FILENAME']
    )
    with open(filepath, 'w') as f:
        f.write(image_path)


def rotate_image(img_filepath, rotate_right):
    rotatecode = (cv2.ROTATE_90_CLOCKWISE
                  if rotate_right
                  else cv2.ROTATE_90_COUNTERCLOCKWISE
                  )
    image = cv2.rotate(cv2.imread(img_filepath), rotatecode)

    cv2.imwrite(img_filepath, image)


@app.route('/', methods=['GET', 'POST'])
def index():
    upload_form = UploadForm()
    rotate_form = RotateForm()
    # print('validate_on_submit', form.validate_on_submit())

    if upload_form.validate_on_submit():
        print('validate_on_submit')
        # fileName = secure_filename(form.photo.file.filename)
        filename = upload_form.photo.data
        filename = photos.save(upload_form.photo.data)

        set_last_image_path(
            os.path.join(app.config['UPLOADED_PHOTOS_DEST'], filename)
        )

        return redirect(url_for('index'))

    if rotate_form.is_submitted():
        # if rotate_form.validate_on_submit():
        if rotate_form.rotate_left.data:
            rotate_image(get_last_image_path(), False)
        if rotate_form.rotate_right.data:
            rotate_image(get_last_image_path(), True)

        return redirect(url_for('index'))

    return render_template('index.html',
                           upload_form=upload_form,
                           rotate_form=rotate_form,
                           img_path=get_last_image_path())


@app.route('/uploads/<filename>')
def get_file(filename):
    print('filename:', filename)
    return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'], filename)


app.run(debug=True)
