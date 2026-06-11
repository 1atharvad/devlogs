---
title: "Facial Expression Detection: CNN Architecture and Training Pipeline"
description: "Designing a 5-block convolutional network to classify 7 facial expressions, training on FER-2023 with data augmentation and k-fold cross-validation, and managing versioned model artifacts."
pubDate: "Aug 04 2024"
primaryTag: "AI"
tags: ["Python", "TensorFlow", "Keras", "Deep Learning"]
---

The task is a 7-class classification problem: given a 96×96 grayscale face image, output one of Angry, Disgust, Fear, Happy, Neutral, Sad, or Surprise. The dataset is FER-2023, split into `images/train/` and `images/validation/` directories with one subdirectory per emotion class.

The design constraint throughout was deployment: the model needed to be lightweight enough for real-time inference on HuggingFace Spaces, not just accurate on a benchmark.

## CNN Architecture

The model is built around five convolutional blocks with a progressively widening filter count: 16 → 32 → 64 → 128 → 256. Each block follows the same pattern:

```
Conv2D → BatchNorm → Conv2D → BatchNorm → ReLU → MaxPool → Dropout(0.3)
```

Two convolutions per block before pooling lets the network build richer representations within the same spatial resolution before downsampling. BatchNorm after each convolution stabilizes training. Dropout at 0.3 per block is the primary regularization mechanism, with L2 weight regularization on every convolution kernel throughout.

The classification head uses `GlobalAveragePooling2D` rather than `Flatten` — it averages each feature map to a single value, reducing the parameter count going into the dense layers significantly:

```python
model.add(layers.GlobalAveragePooling2D())
model.add(layers.Dense(16, kernel_regularizer=regularizers.l2(l2=self.l2_strength)))
model.add(layers.BatchNormalization())
model.add(layers.Dropout(0.2))
model.add(layers.Dense(self.output_size, activation='softmax', kernel_regularizer=regularizers.l2(l2=self.l2_strength)))
```

The `Dense(16)` bottleneck before the output layer forces compact representations. The architecture is wrapped in a `ModelArchitecture` class parameterized by `picture_size`, `output_size`, and `l2_strength`.

## Model Versioning via JSON Config

Every training run is version-managed. When training starts, `get_model_details()` prompts for a version number, creates `models/model-{version}/`, and writes a `model-details.json` with all hyperparameters:

```json
{
    "batch-size": 100,
    "class-list": ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Sad", "Surprise"],
    "epoch": 60,
    "k-fold": 1,
    "l2-strength": 0.001,
    "learning-rate": 0.001,
    "picture-size": 96,
    "version": "0.1.1"
}
```

If the version directory already exists, the script asks whether to retrain and loads the existing config if yes. The `model-details.json` is the single source of truth for every hyperparameter — the training code reads from it rather than hardcoding values.

After training, `model.h5` and an accuracy/loss plot are saved to the same directory. The full training history is auditable alongside the weights.

## Data Loading and Augmentation

Training data loads through `ImageDataGenerator` with on-the-fly augmentation:

```python
train_set = ImageDataGenerator(
    rescale=1./255,
    rotation_range=10,
    horizontal_flip=True,
    width_shift_range=0.1,
    height_shift_range=0.1,
    zoom_range=0.1,
).flow_from_directory(...)
```

Augmentation is applied only to the training set; validation loads with rescaling only. Images are loaded as grayscale at 96×96. A fixed random seed via `utils.set_random_seed(self.seed)` makes runs reproducible.

## Training

The model compiles with Adam at `lr=0.001` and categorical crossentropy. A `ReduceLROnPlateau` callback monitors validation loss and drops the learning rate by 80% (factor 0.2) if it doesn't improve for 3 consecutive epochs — letting the model train aggressively early and fine-tune as it converges.

Early stopping was tried and rejected. The problem was that it triggered before the model had stabilized — validation loss was still noisy in the mid-training range, and stopping there produced underfitting rather than solving overfitting. `ReduceLROnPlateau` handled the same concern more gracefully: instead of halting, it reduces the step size and lets the model continue refining. The result was a more stable convergence over the full 60 epochs.

Training runs for 60 epochs at batch size 100. After each run, the weights save to `model.h5` and accuracy/loss curves are saved as a PNG alongside the model.

The k-fold training setup — which runs this pipeline across multiple data splits for more reliable accuracy estimates — is covered in the [next entry](/devlogs/fed-kfold).
