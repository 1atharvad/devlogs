---
title: "Facial Expression Detection: Image, Video, and Webcam Prediction"
description: "Running facial expression inference across three input modes — static images, video files, and live webcam — using OpenCV for face detection and the full preprocessing pipeline from bounding box to model input."
pubDate: "Aug 15 2024"
primaryTag: "AI"
tags: ["Python", "OpenCV", "TensorFlow", "Keras"]
---

With the [model trained](/devlogs/fed-model-training), the prediction system exposes three input modes from a single entry point: a static image file, a video file processed frame by frame, or a live webcam feed. All three run through the same face detection and classification pipeline.

## Face Detection

Every mode converts the input to grayscale first. The Haar cascade classifier (`haarcascade_frontalface_default.xml`) runs on the grayscale image and returns bounding box coordinates for each detected face.

```python
grayScaledImg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
face_co_ordinates = self.trained_face_data.detectMultiScale(grayScaledImg, 1.15)
```

The `detectMultiScale` scale factor differs between modes. Static images use `1.15` — more sensitive, slower, but there's no frame budget to worry about. Video and webcam use `1.3` with `minNeighbors=5` — less sensitive, faster, and the higher neighbor threshold filters out false positives that would flicker distractingly across frames.

The Haar cascade is a deliberate tradeoff. Alternatives like MTCNN or RetinaFace handle pose variation and partial occlusion better, but at higher latency — too slow for per-frame webcam processing on the target hardware. For frontal faces under reasonable lighting, the Haar cascade is fast enough and accurate enough.

## Preprocessing Pipeline

Once the bounding box is found, the face region goes through a fixed preprocessing pipeline before the model sees it:

```python
def get_prediction_on_frame(self, grayImg, co_ordinates):
    x, y, w, h = co_ordinates
    cropped_face = grayImg[y:y+h, x:x+w]
    roi = cv2.resize(cropped_face, (self.capture_size, self.capture_size))
    return self.model.predict_emotion(roi[np.newaxis, :, :, np.newaxis])
```

The face region is cropped directly from the grayscale image — not from the color frame. Grayscale is the consistent format throughout because the model was trained on grayscale 96×96 images; running detection and cropping on the same grayscale array avoids any conversion at inference time.

After cropping, the region is resized to `capture_size` × `capture_size` (96×96). The final line — `roi[np.newaxis, :, :, np.newaxis]` — reshapes the 2D array from `(96, 96)` to `(1, 96, 96, 1)`, adding a batch dimension and a channel dimension. That's the shape Keras expects: batch size 1, height, width, channels 1. Without this expansion the model call fails with a shape mismatch.

## Three Prediction Modes

All modes share the same detection and preprocessing loop — the only structural difference is the input source:

```
python predict_expression img photo.jpg
python predict_expression video clip.mp4
python predict_expression webcam
```

**Image mode** reads a single file, runs detection once, and displays the annotated result. `waitKey(0)` holds the window open until the user closes it.

**Video mode** opens the file with `VideoCapture(video_file)` and loops until `video.read()` returns no more frames. `waitKey(1)` gives a 1ms pause per iteration — enough for the display to update without blocking the loop.

**Webcam mode** is almost identical to video mode — `VideoCapture(0)` instead of a file path, and the loop runs indefinitely until the user exits. Multiple faces in the same frame each get their own bounding box and label independently.

## Rendering Output

Detection and inference run on the grayscale image, but the output is drawn back onto the original color frame — so the user sees the bounding box overlaid on the actual face as it appears, not a grayscale copy:

```python
def draw_rect(self, prediction, img_frame, co_ordinates):
    x, y, w, h = co_ordinates
    text_size, _ = cv2.getTextSize(prediction, self.font, 1, 2)
    cv2.rectangle(img_frame, (x, y - 30 - text_size[1]), (x + text_size[0], y - 10), (180, 184, 176), -1)
    cv2.putText(img_frame, prediction, (x, y - 20), self.font, 1, (69, 74, 24), 2)
    cv2.rectangle(img_frame, (x, y), (x + w, y + h), (106, 118, 252), 4)
```

The label background is sized dynamically using `cv2.getTextSize` — it fits the width of the predicted class name rather than a fixed rectangle. This matters because the seven class names have different lengths ("Disgust" vs "Fear"). The background is drawn above the face box, the text is rendered over it, and the bounding box is drawn in blue-purple with thickness 4.

## Model Loading

The prediction system reads `model-details.json` from the versioned model directory — the same config file written during training — to get `class-list` and `picture-size` before loading the model:

```python
def get_model_details(self, version):
    model_dir = Path(base_dir, 'models', f'model-{version}')
    with open(f'{model_dir}/model-details.json', 'r') as json_file:
        model_details = json.load(json_file)

    self.emotions_list = model_details['class-list']
    self.capture_size = model_details['picture-size']
    self.model = FacialExpressionModel(f'models/model-{version}/model.h5', self.emotions_list)
```

This means `class-list` and `picture-size` at inference always match whatever was used during training — there's no separate constant to keep in sync. The `model-details.json` is the bridge between the training pipeline and the prediction system.

`make_predict_function()` is called after loading to pre-compile the prediction graph. Without it, the first `model.predict()` call triggers a compilation step mid-inference, producing a latency spike on the first frame. Moving that cost to initialization keeps the first prediction fast.

`predict_emotion` maps the model output to a label:

```python
def predict_emotion(self, img):
    predict_values = self.loaded_model.predict(img, verbose=False)
    return self.emotions_list[np.argmax(predict_values)]
```

The softmax output is a distribution over all 7 classes. `argmax` picks the highest-confidence one and returns the corresponding string from `emotions_list`. The version is hardcoded to `0.1.1` — across five training runs it tied for the best validation accuracy (64.66%) and had the lowest loss, so it was written directly into the prediction code.

Wrapping this in a deployable web interface — Gradio mounted on FastAPI and hosted on HuggingFace Spaces — is covered in the [next entry](/devlogs/fed-api-gradio).
