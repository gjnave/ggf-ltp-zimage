import random
import sys
from pathlib import Path

import numpy as np
import torch

import folder_paths


NODE_DIR = Path(__file__).resolve().parent
if str(NODE_DIR) not in sys.path:
    sys.path.insert(0, str(NODE_DIR))


_PIPELINE_CACHE = {}


TOKENIZER_DIR = "Z-Image-Turbo-tokenizer/tokenizer"


def _resolve_tokenizer_path():
    candidates = [
        Path(folder_paths.models_dir) / "text_encoders" / TOKENIZER_DIR,
    ]

    for candidate in candidates:
        if (candidate / "tokenizer_config.json").is_file():
            return str(candidate)

    checked = "\n".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(
        "Could not find the Z-Image tokenizer folder. Place tokenizer files at:\n"
        f"{Path('models') / 'text_encoders' / TOKENIZER_DIR}\n\n"
        f"Checked:\n{checked}"
    )


class L2PZImagePipelineLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_name": (folder_paths.get_filename_list("diffusion_models"),),
                "text_encoder_name": (folder_paths.get_filename_list("text_encoders"),),
                "device": (["cuda", "cpu"],),
                "dtype": (["bf16", "fp32"],),
            }
        }

    RETURN_TYPES = ("L2P_ZIMAGE_PIPELINE",)
    RETURN_NAMES = ("pipeline",)
    FUNCTION = "load"
    CATEGORY = "L2P/Z-Image"

    def load(self, model_name, text_encoder_name, device, dtype):
        from diffsynth.pipelines.z_image_L2P import ZImagePipeline, ModelConfig

        model_path = folder_paths.get_full_path_or_raise("diffusion_models", model_name)
        text_encoder_path = folder_paths.get_full_path_or_raise("text_encoders", text_encoder_name)
        resolved_tokenizer_path = _resolve_tokenizer_path()
        torch_dtype = torch.bfloat16 if dtype == "bf16" else torch.float32
        key = (model_path, text_encoder_path, resolved_tokenizer_path, device, str(torch_dtype))
        if key not in _PIPELINE_CACHE:
            pipe = ZImagePipeline.from_pretrained(
                torch_dtype=torch_dtype,
                device=device,
                model_configs=[
                    ModelConfig(path=model_path),
                    ModelConfig(path=text_encoder_path),
                ],
                tokenizer_config=ModelConfig(path=resolved_tokenizer_path),
            )
            # This pipeline supports manual text-encoder offload; keeping it enabled
            # reduces peak VRAM for the 6B pixel-space checkpoint.
            pipe.offload_text_encoder = True
            _PIPELINE_CACHE[key] = pipe
        return (_PIPELINE_CACHE[key],)


class L2PZImageGenerate:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pipeline": ("L2P_ZIMAGE_PIPELINE",),
                "prompt": ("STRING", {"multiline": True, "dynamic_prompts": True}),
                "negative_prompt": ("STRING", {"multiline": True, "dynamic_prompts": True, "default": ""}),
                "width": ("INT", {"default": 1024, "min": 256, "max": 4096, "step": 16}),
                "height": ("INT", {"default": 1024, "min": 256, "max": 4096, "step": 16}),
                "steps": ("INT", {"default": 30, "min": 1, "max": 100, "step": 1}),
                "cfg_scale": ("FLOAT", {"default": 2.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647, "control_after_generate": True}),
                "randomize_seed": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "L2P/Z-Image"

    def generate(self, pipeline, prompt, negative_prompt, width, height, steps, cfg_scale, seed, randomize_seed):
        if randomize_seed:
            seed = random.randint(0, 2**31 - 1)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        image = pipeline(
            prompt=prompt.strip(),
            negative_prompt=negative_prompt or "",
            cfg_scale=float(cfg_scale),
            height=int(height),
            width=int(width),
            seed=int(seed),
            rand_device=pipeline.device,
            num_inference_steps=int(steps),
        )
        image = image.convert("RGB")
        array = np.asarray(image).astype(np.float32) / 255.0
        return (torch.from_numpy(array)[None,],)


NODE_CLASS_MAPPINGS = {
    "L2PZImagePipelineLoader": L2PZImagePipelineLoader,
    "L2PZImageGenerate": L2PZImageGenerate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "L2PZImagePipelineLoader": "L2P Z-Image Pipeline Loader",
    "L2PZImageGenerate": "L2P Z-Image Generate",
}
