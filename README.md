# GetGoingFast ComfyUI L2P Z-Image

ComfyUI custom nodes and starter workflows for running **L2P Z-Image 6B pixel-space** generation in ComfyUI.

Built for people who want to get moving fast: [getgoingfast.pro](https://getgoingfast.pro)

## What This Is

This adds two ComfyUI nodes:

- `L2P Z-Image Pipeline Loader`
- `L2P Z-Image Generate`

It wraps the public L2P Z-Image pipeline so ComfyUI can run the **no-VAE pixel-space 6B model** directly and output a normal `IMAGE` tensor for preview/save nodes.

## Included

- `__init__.py` custom node entrypoint
- `diffsynth/` runtime files adapted from the public L2P Z-Image HF Space
- `requirements.txt`
- `workflows/z_image_l2p_no_vae_from_hidream.json`

## Install

From your ComfyUI `custom_nodes` directory:

```powershell
cd D:\comfyUI\ComfyUI\custom_nodes
git clone https://github.com/gjnave/getgoingfast-comfyui-l2p-zimage.git
cd getgoingfast-comfyui-l2p-zimage
D:\comfyUI\ComfyUI\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Restart ComfyUI after installing.

## Models

Put these files in your ComfyUI models folder:

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
          tokenizer_config.json
          vocab.json
```

Useful upstream links:

- L2P weights: <https://huggingface.co/zhen-nan/L2P>
- Z-Image tokenizer/text encoder source: <https://huggingface.co/Tongyi-MAI/Z-Image-Turbo>
- Comfy split Z-Image assets: <https://huggingface.co/Comfy-Org/z_image_turbo>

The tested local checkpoint name was:

```text
Z-image-6b-no-VAE.safetensors
```

If your file name differs, select it manually in the loader node.

## Workflow

Copy or open:

```text
workflows/z_image_l2p_no_vae_from_hidream.json
```

If Comfy marks the tokenizer widget red, select your local tokenizer folder in the `L2P Z-Image Pipeline Loader` node.

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

- L2P project: <https://github.com/TencentYoutuResearch/T2I-L2P>
- L2P weights: <https://huggingface.co/zhen-nan/L2P>
- Reference HF Space: <https://huggingface.co/spaces/multimodalart/z-image-6b-pixel-space>
- Packaged for fast ComfyUI use by [GetGoingFast](https://getgoingfast.pro)

## License

Apache-2.0. See `LICENSE` and `NOTICE`.
