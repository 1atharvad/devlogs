---
title: "Facial Expression Detection: K-Fold Cross-Validation"
description: "Implementing k-fold cross-validation for the FER-2023 training pipeline — custom fold directory generation, deficit filling for imbalanced classes, and fixed validation across folds."
pubDate: "Aug 15 2024"
primaryTag: "AI"
tags: ["Python", "TensorFlow", "Keras", "Deep Learning"]
---

The [base training pipeline](/devlogs/fed-model-training) uses a fixed FER-2023 train/validation split — the same images always end up in training, the same in validation. That works for a single run, but it means the accuracy numbers depend on that particular split. If a model happens to train on easy examples and validate on hard ones, the metrics look worse than they are. The reverse gives false confidence.

K-fold cross-validation rotates which portion of the training data is used for each run, giving a more reliable picture of how the model actually generalizes.

## How the Folds Are Generated

Keras's `ImageDataGenerator` doesn't support k-fold natively — it works from a directory, not from an in-memory index. The solution is to materialize each fold as its own directory. Before each training run, `load_data` creates `images/train-{fold}/` by copying the relevant subset of files from `images/train/`:

```python
def load_data(self, dataset_name, start, end):
    dir_path = ['images', dataset_name]
    dest_dir_path = ['images', f'{dataset_name}-{self.fold}']

    if os.path.exists(os.path.join(*dest_dir_path)):
        shutil.rmtree(os.path.join(*dest_dir_path))
    os.makedirs(os.path.join(*dest_dir_path))
    ...
```

The fold is a window into the per-class file list: images `[start, end)` go into the fold directory. Each class is processed independently so the fold composition mirrors the class distribution in the full dataset.

## Handling Class Imbalance

FER-2023 classes aren't balanced — some emotions have more training images than others. A naive window approach would produce folds of unequal size across classes, since the window `[start, end)` hits the boundary of a smaller class before a larger one.

The deficit fill handles this: after copying the window, if a class didn't produce enough files to fill the target fold size, the shortfall is filled by randomly sampling from the images *outside* the current window:

```python
deficit = min(file_count, end - start) - (count - start + 1)

for file_index in random.sample(
    list(set(np.arange(0, file_count)) - set(np.arange(start, end))), deficit
):
    img_path = os.path.join(*dir_path, file_list[file_index])
    shutil.copy(img_path, os.path.join(*dest_dir_path))
```

This keeps each fold approximately the same total size regardless of per-class imbalance, without duplicating the same images into the validation window.

## Fixed Validation Set

The validation set never rotates. Each fold trains on a different `train-{fold}` directory but always validates against the fixed `images/validation/` split from FER-2023. This keeps the validation signal consistent across folds — the accuracy numbers are comparable because they're measured against the same examples every time.

## Config-Driven Folds

The number of folds is a field in `model-details.json`:

```json
{
    "k-fold": 5
}
```

With `k-fold: 1` the pipeline runs a single pass — the standard training mode. Setting it to 5, as used for model `0.1.3`, runs five iterations. The fold size is derived from the largest class in the training set, so `get_fold_sizes()` scans the directory rather than hardcoding a number:

```python
def get_fold_sizes(self):
    img_count = {}
    for folder in os.listdir(os.path.join('images', 'train')):
        img_count[folder] = len(os.listdir(os.path.join('images', 'train', folder)))
    return max(img_count.values())
```

The fold window boundaries are calculated from this max — `fold_size = get_fold_sizes() / k_fold` — so the split adapts automatically if the dataset changes.

The [prediction system](/devlogs/fed-prediction-system) built on top of these trained models is covered next.
