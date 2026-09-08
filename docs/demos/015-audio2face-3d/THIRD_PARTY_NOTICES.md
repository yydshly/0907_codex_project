# Sources and third-party notices

This is an independent research demonstration, not an official NVIDIA product or endorsement.

## NVIDIA Audio2Face-3D v2.3 Mark

Licensed by NVIDIA Corporation under the NVIDIA Open Model License.

- Model: https://huggingface.co/nvidia/Audio2Face-3D-v2.3-Mark
- Revision: 5451728e07378df93b04523279e134a9993ae71b
- Agreement: https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/
- Local agreement copy: [NVIDIA Open Model License](licenses/NVIDIA-Open-Model-License.txt)

The original ONNX model and PCA resources are downloaded separately into ignored vendor storage. Browser motion assets contain per-clip compressed reconstructions of outputs produced by that model. They are not independently trained models. The demo does not redistribute the ONNX weight file. Original model copyright and license remain applicable to included model-derived resources.

## NVIDIA Maya-ACE / Mark mesh

Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.

- Source: https://github.com/NVIDIA/Maya-ACE
- Commit: f0dc13670952c495450dab1655c94e9056c9d7d9
- File: sample_project/maya_geom/mark_geom_v2_topo1.ma
- [MIT License](licenses/Maya-ACE-MIT.txt)

Vertex and topology files were extracted from the official Maya ASCII scene. Coordinate ordering is retained; polygons were triangulated for browser rendering. Lighting, colors, camera and playback are supplied by this independent demo.

## NVIDIA SDK and training framework

Input/output conventions were checked against NVIDIA's SDK and training framework. This project uses a separately written ONNX Runtime adapter, not a compiled SDK build.

- [SDK MIT license](licenses/Audio2Face-SDK-MIT.txt)
- [Training framework Apache-2.0 license](licenses/Training-Framework-Apache-2.0.txt)

## Three.js

Copyright 2010-2025 Three.js Authors. [MIT license](licenses/Threejs-MIT.txt).

The local bundle, including OrbitControls, is reused from this workspace's existing Three.js demonstration. Its embedded copyright notice is preserved.

## Original Mark sample audio and data

The two Chinese scripts were written for this demonstration. Audio was synthesized locally using the Windows Microsoft Huihui Desktop voice. No user voice recordings, NVIDIA training dataset, Audio2Emotion weights, or third-party speech recordings are included. Uploaded audio is only processed on the user's local machine and is excluded from the static showcase.


## Published fictional portrait demonstration

The 8020 screen recording and three-clip montage show an original AI-generated fictional adult character. The reference portrait was created with the ImageGen tool; it is not a photograph of an uploaded user or an identified real person.

- Body motion: LTX-Video 13B 0.9.8 distilled through the official Hugging Face Space; generated clips downloaded for reuse. Source: https://github.com/Lightricks/LTX-Video .
- Voice in this recording: Edge TTS `zh-TW-HsiaoChenNeural`, via https://github.com/rany2/edge-tts . These are synthetic readings of the project's own short scripts, not cloned user recordings. This recorded sample does not use MiniMax TTS.
- Lip synchronization: MuseTalk 1.5, https://github.com/TMElyralab/MuseTalk , commit 0a89dec45a0192b824e3cf4daf96c239440c5ed8. [MuseTalk MIT code license](licenses/MuseTalk-MIT.txt). Model/auxiliary weights retain their separate terms and are not distributed here.
- Local preprocessing: facexlib RetinaFace, FAN and ParseNet; project-written tracking, mask and timing adaptation; OpenCV/FFmpeg compositing and encoding.

This is a playback demonstration of generated media, not real-time dialogue generation. Browser frames were captured while operating the actual local page; original clip audio was aligned to observed media-clock events. The capture method and timing are described in `media/recording-report.json` on the published site.

The newer local workflow also uses MiniMax conversation/TTS and Hailuo video generation; these are API services, not included weight files. Public assets do not include private conversation records, user-uploaded images, API credentials, or Camila assets/renders. Camila remains a local evaluation asset; no permission to redistribute it is implied.


## Restored public effect comparisons

The expanded static guide also includes the fictional AI character Ruoan, generated during this project. Its local facial sample uses LivePortrait; its natural half-body sample uses MiniMax Hailuo. Both comparison clips use the same MiniMax-generated voice audio and local MuseTalk lip synchronization. They are selected demonstration outputs, not user-uploaded portraits or chat history. The 8020 static player additionally includes the original generated motion, earlier mouth-treatment result and matching idle clips to preserve the four comparison modes. Camila remains unavailable on the public site; its explanatory text is retained.
