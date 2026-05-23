# ggf-ltp-zimage

ComfyUI custom nodes and starter workflows for running **L2P Z-Image 6B pixel-space** generation in ComfyUI.

Built for people who want to get moving fast: [getgoingfast.pro](https://getgoingfast.pro)

<img src="./assets/nt.png>

## What This Is

This adds two ComfyUI nodes:

- `L2P Z-Image Pipeline Loader`
- `L2P Z-Image Generate`

It wraps the public L2P Z-Image pipeline so ComfyUI can run the **no-VAE pixel-space 6B model** directly and output a normal `IMAGE` tensor for preview/save nodes.

## Included

- `__init__.py` custom node entrypoint
- `diffsynth/` runtime files adapted from the public L2P Z-Image HF Space
- `requirements.txt`
- `workflows/ggf_l2p_zimage_6b_no_vae.json`

## Install

From your ComfyUI `custom_nodes` directory:

```powershell
cd <ComfyUI>\custom_nodes
git clone https://github.com/gjnave/ggf-ltp-zimage.git
cd ggf-ltp-zimage
<ComfyUI>\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Restart ComfyUI after installing.

## Required Models

This repo does not include model weights. Put these required files in your ComfyUI models folder:

```text
ComfyUI/
  models/
    diffusion_models/
      Z-image-6b-no-VAE.safetensors
    text_encoders/
      qwen_3_4b.safetensors
      Z-Image-Turbo-tokenizer/
        tokenizer/
          merges.txt
          tokenizer.json
          tokenizer_config.json
          vocab.json
```

The default workflow expects these exact local names:

```text
Z-image-6b-no-VAE.safetensors
qwen_3_4b.safetensors
Z-Image-Turbo-tokenizer/tokenizer
```

If your file or folder names differ, select the correct entries in the `L2P Z-Image Pipeline Loader` node.

## Download Required Models

Set `COMFY_ROOT` to your ComfyUI folder, then run the commands below in PowerShell.
Replace the placeholder path with the folder that contains your `main.py`.

```powershell
$COMFY_ROOT = "<path-to-your-ComfyUI>"
$HF = "$COMFY_ROOT\venv\Scripts\hf.exe"
```

Install this custom node first, because its `requirements.txt` installs the Hugging Face `hf` download CLI:

```powershell
cd $COMFY_ROOT\custom_nodes
git clone https://github.com/gjnave/ggf-ltp-zimage.git
cd ggf-ltp-zimage
$COMFY_ROOT\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Download the L2P Z-Image 6B no-VAE model:

- Source page: <https://huggingface.co/zhen-nan/L2P>
- Direct file page: <https://huggingface.co/zhen-nan/L2P/blob/main/model-1k-merge.safetensors>
- Local file expected by the workflow: `models/diffusion_models/Z-image-6b-no-VAE.safetensors`

Manual download: download `model-1k-merge.safetensors`, put it in `ComfyUI/models/diffusion_models`, and rename it to `Z-image-6b-no-VAE.safetensors`.

```powershell
& $HF download zhen-nan/L2P model-1k-merge.safetensors --local-dir "$COMFY_ROOT\models\diffusion_models"
Move-Item -Force "$COMFY_ROOT\models\diffusion_models\model-1k-merge.safetensors" "$COMFY_ROOT\models\diffusion_models\Z-image-6b-no-VAE.safetensors"
```

Download the Qwen 3 4B text encoder:

- Source page: <https://huggingface.co/Comfy-Org/z_image_turbo/tree/main/split_files/text_encoders>
- Direct file page: <https://huggingface.co/Comfy-Org/z_image_turbo/blob/main/split_files/text_encoders/qwen_3_4b.safetensors>
- Local file expected by the workflow: `models/text_encoders/qwen_3_4b.safetensors`

Manual download: download `qwen_3_4b.safetensors` and put it directly in `ComfyUI/models/text_encoders`.

```powershell
& $HF download Comfy-Org/z_image_turbo split_files/text_encoders/qwen_3_4b.safetensors --local-dir "$COMFY_ROOT\models\text_encoders"
Move-Item -Force "$COMFY_ROOT\models\text_encoders\split_files\text_encoders\qwen_3_4b.safetensors" "$COMFY_ROOT\models\text_encoders\qwen_3_4b.safetensors"
Remove-Item -Recurse -Force "$COMFY_ROOT\models\text_encoders\split_files"
```

Download the Z-Image tokenizer:

- Source page: <https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/tree/main/tokenizer>
- Direct file pages:
  - <https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/blob/main/tokenizer/merges.txt>
  - <https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/blob/main/tokenizer/tokenizer.json>
  - <https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/blob/main/tokenizer/tokenizer_config.json>
  - <https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/blob/main/tokenizer/vocab.json>
- Local folder expected by the workflow: `models/text_encoders/Z-Image-Turbo-tokenizer/tokenizer`

Manual download: download all four tokenizer files and put them in `ComfyUI/models/text_encoders/Z-Image-Turbo-tokenizer/tokenizer`.

```powershell
& $HF download Tongyi-MAI/Z-Image-Turbo tokenizer/merges.txt tokenizer/tokenizer.json tokenizer/tokenizer_config.json tokenizer/vocab.json --local-dir "$COMFY_ROOT\models\text_encoders\Z-Image-Turbo-tokenizer"
```

After downloading, restart ComfyUI. The loader dropdowns should show:

```text
model_name: Z-image-6b-no-VAE.safetensors
text_encoder_name: qwen_3_4b.safetensors
tokenizer_name: Z-Image-Turbo-tokenizer/tokenizer
```

## Workflow

Copy or open:

```text
workflows/ggf_l2p_zimage_6b_no_vae.json
```

The `tokenizer_name` dropdown is populated by scanning:

```text
ComfyUI/models/text_encoders
```

It shows tokenizer folders as relative names, for example:

```text
Z-Image-Turbo-tokenizer/tokenizer
```

It should not show machine-specific absolute drive paths.

## Smoke Test

After restart, create this tiny test:

- prompt: `a tiny red cube on a plain white background`
- size: `256 x 256`
- steps: `1`
- cfg: `1.0`

On the original development machine this generated successfully through the ComfyUI API.

## Notes

- This is a lightweight Comfy wrapper around the L2P Z-Image runtime, not a native KSampler graph.
- The model is large. First run can take a while because the 6B model and Qwen text encoder need to load.
- Some unrelated custom-node import warnings in your Comfy log do not necessarily affect this node.

## Credits

- Tencent Youtu Research L2P project
- zhen-nan L2P model release
- multimodalart L2P Z-Image reference Space
- Packaged for fast ComfyUI use by [GetGoingFast](https://getgoingfast.pro)

## License

Apache-2.0. See `LICENSE` and `NOTICE`.
