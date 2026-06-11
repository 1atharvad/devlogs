---
title: "Facial Expression Detection: Streamlit, Gradio, and HuggingFace Deployment"
description: "Wrapping the expression classifier in a Streamlit app with embedded Gradio components, deploying to HuggingFace Spaces, and solving cold start latency with a Selenium heartbeat."
pubDate: "Aug 25 2024"
primaryTag: "AI"
tags: ["Python", "Streamlit", "Gradio", "HuggingFace", "Docker"]
---

The [prediction pipeline](/devlogs/fed-prediction-system) works locally. Making it accessible required a browser-based demo that doesn't ask users to run code. The deployment stack is Streamlit for app structure and Gradio for the interactive UI components — both hosted on HuggingFace Spaces.

The combination came out of a hackathon context where Streamlit was a sponsor. Prior experience with both tools made the integration a natural fit: Streamlit handles layout and app scaffolding; Gradio's component model handles the image input and output display without having to write custom HTML.

## Gradio Inside Streamlit

Gradio's `gr.Interface` wraps the prediction function and is embedded within the Streamlit app. The interface accepts an uploaded image and outputs a label distribution over all 7 expression classes ranked by confidence — not just the top prediction. Showing the full distribution makes it easier to see when the model is uncertain between two similar expressions, like Fear and Surprise.

Five demo images ship with the repo covering several of the expression classes, so the interface is usable without a test image on hand.

## HuggingFace Spaces Deployment

HuggingFace Spaces runs the app in a Docker container. Getting the environment right was the bulk of the deployment work.

The main issue was OpenCV. The `opencv-python` PyPI package bundles its own display libraries that fail headlessly in containers. The fix: declare OpenCV's system-level dependencies in the `Dockerfile` directly rather than in `packages.txt`. Once that was separated from the Python dependencies, the build was stable.

The environment also required explicit version pins for TensorFlow and Python in the Dockerfile — floating constraints silently drift over time as dependencies update. With pins in place, the container environment is reproducible and matches the environment the model was trained in.

## Cold Start Latency

Streamlit on HuggingFace Spaces goes inactive after a period of no traffic. The first request after an idle period hits a cold start — the Streamlit process has to spin back up before serving, which produces a noticeable delay for whoever triggers it.

The fix was a Selenium headless browser running on a schedule, periodically loading the Space URL to keep the app alive. Not a clean solution — it's artificial traffic generating real load — but it works: cold starts don't reach users. For a demo that needs to feel responsive on first interaction, it was the right call.
