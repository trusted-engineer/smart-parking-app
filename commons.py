import cv2
import requests
import tensorflow as tf
import numpy as np
import time

#from PIL import Image

model_path = 'static/model/modelv2.tflite'

interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Load the labels into a list
"""classes = ['???'] * model.model_spec.config.num_classes
label_map = model.model_spec.config.label_map
for label_id, label_name in label_map.as_dict().items():
  classes[label_id-1] = label_name"""

classes = ['car', 'truck']

# Define a list of colors for visualization
COLORS = np.random.randint(0, 255, size=(len(classes), 3), dtype=np.uint8)

def preprocess_image(image_path, input_size):
  """Preprocess the input image to feed to the TFLite model"""
  #img = tf.io.read_file(image_path)
  #img = tf.io.decode_image(img, channels=3)
  urldict = {
      "torrington": "http://67.43.220.114:80/jpg/image.jpg?$timestamp",
      "montreal": "http://70.81.224.78:80/webcapture.jpg?command=snap&channel=1$timestamp?",
      "iga": "http://111.64.36.153:50001/cgi-bin/camera?resolution=640&amp;quality=1&amp;Language=0&amp;$timestamp",
      "asahi": "http://124.155.121.218:3000/webcapture.jpg?command=snap&channel=1?$timestamp",
      "kwangmyong": "http://121.125.133.92:8000/webcapture.jpg?command=snap&channel=1?$timestamp",
      "mobile": "http://170.249.152.2:8080/cgi-bin/viewer/video.jpg?r=$timestamp",
      "meridian": "http://67.61.139.162:8080/jpg/image.jpg?overview=0&resolution=1280x720&videoframeskipmode=empty&timestamp=$timestamp&Axis-Orig-Sw=true"
  }
  url = "http://124.155.121.218:3000/webcapture.jpg?command=snap&channel=1?1655585957"
  if image_path in urldict:
      url = urldict[image_path]
  url = url.replace("$timestamp", str(int(time.time())))
  img = tf.image.decode_jpeg(
        requests.get(url).content, channels=3, name="jpeg_reader")
  img = tf.image.convert_image_dtype(img, tf.uint8)
  original_image = img
  resized_img = tf.image.resize(img, input_size)
  resized_img = resized_img[tf.newaxis, :]
  resized_img = tf.cast(resized_img, dtype=tf.uint8)
  return resized_img, original_image


def detect_objects(image, threshold):
  """Returns a list of detection results, each a dictionary of object info."""

  signature_fn = interpreter.get_signature_runner()

  # Feed the input image to the model
  output = signature_fn(images=image)

  # Get all outputs from the model
  count = int(np.squeeze(output['output_0']))
  scores = np.squeeze(output['output_1'])
  classes = np.squeeze(output['output_2'])
  boxes = np.squeeze(output['output_3'])

  results = []
  for i in range(count):
    if scores[i] >= threshold:
      result = {
        'bounding_box': boxes[i],
        'class_id': classes[i],
        'score': scores[i]
      }
      results.append(result)
  return results


def run_odt_and_draw_results(image_path, threshold=0.5):
  """Run object detection on the input image and draw the detection results"""
  # Load the input shape required by the model
  _, input_height, input_width, _ = interpreter.get_input_details()[0]['shape']

  # Load the input image and preprocess it
  preprocessed_image, original_image = preprocess_image(
      image_path,
      (input_height, input_width)
    )

  # Run object detection on the input image
  results = detect_objects(preprocessed_image, threshold=threshold)

  # Plot the detection results on the input image
  original_image_np = original_image.numpy().astype(np.uint8)
  for obj in results:
    # Convert the object bounding box from relative coordinates to absolute
    # coordinates based on the original image resolution
    ymin, xmin, ymax, xmax = obj['bounding_box']
    xmin = int(xmin * original_image_np.shape[1])
    xmax = int(xmax * original_image_np.shape[1])
    ymin = int(ymin * original_image_np.shape[0])
    ymax = int(ymax * original_image_np.shape[0])

    # Find the class index of the current object
    class_id = int(obj['class_id'])

    # Draw the bounding box and label on the image
    color = [int(c) for c in COLORS[class_id]]
    cv2.rectangle(original_image_np, (xmin, ymin), (xmax, ymax), color, 2)
    # Make adjustments to make the label visible for all objects
    y = ymin - 15 if ymin - 15 > 15 else ymin + 15
    label = "{}: {:.0f}%".format(classes[class_id], obj['score'] * 100)
    cv2.putText(original_image_np, label, (xmin, y),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

  # Return the final image
  original_float64 = original_image_np.astype(np.uint8)
  return original_float64, len(results)