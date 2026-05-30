---
title: "Three Models, One Face: Finding What Actually Works on MPS"
description: "Why the first output looked right and felt wrong — and how evaluating Wav2Lip, SadTalker, and LivePortrait in sequence led to splitting the problem in two."
pubDate: "May 20 2026"
primaryTag: "AI"
tags: ["Python", "Computer Vision", "Automation"]
---

The first Wav2Lip output looked correct. The mouth was moving, the sync was tight, every metric I'd set out to hit was green. Then I watched it for five more seconds and understood why it was unusable: the mouth was moving and absolutely nothing else was. No head tilt. No eye movement. A frozen face with one animated region. It read as wrong in a way that was worse than no animation at all.

That output set the direction for everything that followed.

## The Hardware Ceiling Came First

Before I evaluated any model for quality, I hit the hardware problem. Running these pipelines on CPU — standard Mac setup — a single 90-second output took close to three hours. That number makes quality evaluation irrelevant. You can't iterate on parameters you can't test.

The fix was MPS — Apple's Metal Performance Shaders, which exposes the GPU on Apple Silicon to PyTorch. Moving tensors to the MPS device instead of CPU dropped execution time from three hours to around 30 minutes. Still slow, but testable. The 30-minute number became the constraint everything else was evaluated inside.

That constraint mattered more than I expected. Most of the newer, more capable models in this space are written for CUDA. MPS support is limited or absent. That eliminated a large part of the option space before I evaluated a single output.

## Wav2Lip: Right Problem, Wrong Scope

Wav2Lip does exactly what it's designed to do: move the mouth in sync with audio. The sync quality is good. The problem is that the model's scope ends at the mouth — it has no concept of the rest of the face. Real faces don't work that way. The head tilts, the eyes blink, the jaw movement ripples into the cheeks. Wav2Lip strips all of that context out and you feel its absence immediately.

The uncanny valley problem with Wav2Lip isn't a flaw. It's the correct implementation of a narrow spec.

## SadTalker: Better Motion, Wrong Hardware

SadTalker adds head pose and eye motion alongside lip sync. The output is immediately more natural — the face moves like something that's actually sitting somewhere and talking. The improvement is real.

Two problems. First: SadTalker synthesizes motion from training data rather than transferring it. The movement is statistically plausible but not grounded in the specific audio — you can feel the disconnect across a full clip even when individual frames look fine. Second: SadTalker requires CUDA. On MPS it falls back to CPU, which brings the three-hour problem back. That ended the evaluation.

## LivePortrait: The Different Approach

LivePortrait doesn't generate motion — it transfers it. You give it a short driving video and it applies that motion pattern onto a static source face. The head tilts in the driving clip become head tilts on your face. The eye blinks transfer. The micro-movements transfer. Because the motion came from a real person, it feels like a real person.

MPS support is solid. Execution time with pre-extracted keypoints (`.pkl` format, so the driving video isn't reprocessed each run) is 3–5 minutes.

## Splitting the Problem

Every model I'd looked at tried to solve motion and lip sync together. The quality ceiling for that approach was SadTalker — hardware-constrained and motion that didn't belong to the audio.

The decision that changed the architecture: treat them as independent problems. LivePortrait handles motion transfer. Wav2Lip handles lip sync on top of the LivePortrait output. Each model solves the part it's actually good at.

The result isn't perfect. But it's better than either model alone, and it runs on MPS in under 6 minutes without GFPGAN enhancement.

The full architecture — timing breakdown, driving video selection, GFPGAN post-pass — is in [Building a Talking Head That Actually Looks Human](/articles/building-a-talking-head-that-actually-looks-human).
