---
title: "Facial Expression Detection: FastAPI, Gradio, and HuggingFace Deployment"
description: "Wrapping the expression classifier in a Gradio demo mounted on FastAPI, deploying to HuggingFace Spaces, and solving cold start latency with a Selenium heartbeat."
pubDate: "Aug 25 2024"
primaryTag: "AI"
tags: ["Python", "FastAPI", "Gradio", "HuggingFace", "Docker"]
---

The [prediction pipeline](/devlogs/fed-prediction-system) works locally. Making it accessible required a browser-based demo without asking users to run code. The initial version used Streamlit, but the project moved to FastAPI with Gradio mounted at the root — giving a REST backend alongside the demo UI in a single process.

## Gradio Interface

The UI is built with `gr.Blocks()` with a `gr.Interface` inside it wrapping the prediction function:

```python
with gr.Blocks() as demo:
    image_input = gr.Image(label='Input Image')
    image_box = gr.Interface(
        api.predict_on_image,
        image_input,
        gr.Image(label='Output Image'),
        title="Facial Emotion Detection (FED) demo",
        description=description,
        allow_flagging='never'
    )
    example_files = [os.path.join("demo-files", img_file) for img_file in os.listdir("demo-files") if img_file != '.DS_Store']
    examples = gr.Examples(example_files, image_input)

app = gr.mount_gradio_app(app, demo, path='/')
```

The output is `gr.Image` — not a label distribution, but the annotated image returned by `api.predict_on_image` with bounding boxes and expression labels drawn directly on it. The same `draw_rect` function used by the local prediction modes produces the output. Demo images ship with the repo so the interface is usable without uploading a test image.

## HuggingFace Spaces Deployment

HuggingFace Spaces runs the app in a Docker container. Getting the environment right was the bulk of the deployment work.

The main issue was OpenCV. The `opencv-python` PyPI package bundles its own display libraries that fail headlessly in containers. The fix: declare OpenCV's system-level dependencies in the `Dockerfile` directly rather than in `packages.txt`. Once that was separated from the Python dependencies, the build was stable.

The environment also required explicit version pins for TensorFlow and Python in the Dockerfile — floating constraints silently drift as dependencies update. With pins in place, the container environment is reproducible and matches the environment the model was trained in.

## Cold Start Latency

HuggingFace Spaces goes inactive after a period of no traffic. The first request after an idle period hits a cold start — the container has to spin back up before serving.

The fix was a Selenium headless Firefox browser running on a schedule, periodically loading the Space to keep the process alive:

```python
def headless_browser():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')

    try:
        HUGGING_FACE_API_URL = config('HUGGING_FACE_API_URL')
        browser = webdriver.Firefox(options=options)
        browser.get(HUGGING_FACE_API_URL)
    except Exception as e:
        print(f"[Error] Headless browser failed: {e}")
```

The URL is read from config rather than hardcoded. Not a clean solution — it generates artificial traffic — but it keeps the app responsive on first load without any changes to the HuggingFace infrastructure.
