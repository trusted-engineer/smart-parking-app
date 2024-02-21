# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python38_render_template]
# [START gae_python3_render_template]
import datetime

from flask import Flask, render_template, jsonify, request
from commons import run_odt_and_draw_results
import base64
from PIL import Image
from io import BytesIO

app = Flask(__name__)


@app.route('/')
def root():
    # For the sake of example, use static information to inflate the template.
    # This will be replaced with real information in later steps.
    dummy_times = [datetime.datetime(2018, 1, 1, 10, 0, 0),
                   datetime.datetime(2018, 1, 2, 10, 30, 0),
                   datetime.datetime(2018, 1, 3, 11, 0, 0),
                   ]

    return render_template('index.html', times=dummy_times)

@app.route('/processing', methods=['GET'])
def process():
    args = request.args.to_dict()
    name = args.get("name")
    data, cars = run_odt_and_draw_results(name, threshold=0.3)
    #data = base64.encodebytes(data)
    #data = base64.b64encode(data).decode("utf-8")  
    pil_img = Image.fromarray(data)
    buff = BytesIO()
    pil_img.save(buff, format="JPEG")
    new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8") 

    #return jsonify({
    #            'msg': 'success',
    #            'img': data
    #       })
    #return f'<img src="data:image/jpg;base64,{data}">'
    return render_template('result.html', data=new_image_string, num=cars, name=name)

"""@app.route('/processing', methods=['GET'])
def process():
    args = request.args.to_dict()
    name = "Default"
    image_string = ''
    if 'name' in args:
        name = args.get("name")
    return render_template('result.html', data=image_string, num='16', name=name)"""


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python3_render_template]
# [END gae_python38_render_template]
