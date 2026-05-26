import gc
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


DEFAULT_TOKENIZER_NAME = "Z-Image-Turbo-tokenizer/tokenizer"


def _tokenizer_names():
    text_encoder_root = Path(folder_paths.models_dir) / "text_encoders"
    names = []
    if text_encoder_root.exists():
        for config in text_encoder_root.rglob("tokenizer_config.json"):
            names.append(config.parent.relative_to(text_encoder_root).as_posix())
    return sorted(set(names)) or [DEFAULT_TOKENIZER_NAME]


def _resolve_tokenizer_path(tokenizer_name):
    text_encoder_root = Path(folder_paths.models_dir) / "text_encoders"
    candidate = text_encoder_root / tokenizer_name

    if (candidate / "tokenizer_config.json").is_file():
        return str(candidate)

    raise FileNotFoundError(
        "Could not find the Z-Image tokenizer folder. Place tokenizer files at:\n"
        f"{Path('models') / 'text_encoders' / DEFAULT_TOKENIZER_NAME}\n\n"
        f"Selected tokenizer_name: {tokenizer_name}\n"
        f"Checked: {candidate}"
    )


def _unload_all_pipelines():
    """캐시된 모든 파이프라인을 VRAM에서 해제합니다."""
    global _PIPELINE_CACHE

    for key in list(_PIPELINE_CACHE.keys()):
        pipe = _PIPELINE_CACHE.pop(key)
        # 내부 모델들을 CPU로 이동 (None 설정 없이)
        try:
            for attr in ['dit', 'text_encoder', 'model']:
                obj = getattr(pipe, attr, None)
                if obj is not None and hasattr(obj, 'to'):
                    obj.to('cpu')
        except Exception:
            pass
        # 파이프라인 객체 참조 해제
        del pipe

    # VRAM 정리
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    gc.collect()
    print("[ggf-ltp-zimage] VRAM 해제 완료")


class L2PZImagePipelineLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_name": (folder_paths.get_filename_list("diffusion_models"),),
                "text_encoder_name": (folder_paths.get_filename_list("text_encoders"),),
                "tokenizer_name": (_tokenizer_names(),),
                "device": (["cuda", "cpu"],),
                "dtype": (["bf16", "fp32"],),
            }
        }

    RETURN_TYPES = ("L2P_ZIMAGE_PIPELINE",)
    RETURN_NAMES = ("pipeline",)
    FUNCTION = "load"
    CATEGORY = "L2P/Z-Image"

    def load(self, model_name, text_encoder_name, tokenizer_name, device, dtype):
        from diffsynth.pipelines.z_image_L2P import ZImagePipeline, ModelConfig

        model_path = folder_paths.get_full_path_or_raise("diffusion_models", model_name)
        text_encoder_path = folder_paths.get_full_path_or_raise("text_encoders", text_encoder_name)
        resolved_tokenizer_path = _resolve_tokenizer_path(tokenizer_name)
        torch_dtype = torch.bfloat16 if dtype == "bf16" else torch.float32
        key = (model_path, text_encoder_path, resolved_tokenizer_path, device, str(torch_dtype))

        if key not in _PIPELINE_CACHE:
            print("[ggf-ltp-zimage] 모델 로딩 중...")
            pipe = ZImagePipeline.from_pretrained(
                torch_dtype=torch_dtype,
                device=device,
                model_configs=[
                    ModelConfig(path=model_path),
                    ModelConfig(path=text_encoder_path),
                ],
                tokenizer_config=ModelConfig(path=resolved_tokenizer_path),
            )
            pipe.offload_text_encoder = True
            _PIPELINE_CACHE[key] = pipe
            print("[ggf-ltp-zimage] 모델 로딩 완료")

        return (_PIPELINE_CACHE[key],)


class L2PZImageGenerate:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pipeline": ("L2P_ZIMAGE_PIPELINE",),
                "prompt": ("STRING", {"multiline": True, "dynamic_prompts": True}),
                "negative_prompt": ("STRING", {"multiline": True, "dynamic_prompts": True, "default": ""}),
                "width": ("INT", {"default": 1024, "min": 256, "max": 4096, "step": 128}),
                "height": ("INT", {"default": 1024, "min": 256, "max": 4096, "step": 128}),
                "steps": ("INT", {"default": 30, "min": 1, "max": 100, "step": 1}),
                "cfg_scale": ("FLOAT", {"default": 2.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647, "control_after_generate": True}),
                "randomize_seed": ("BOOLEAN", {"default": True}),
                "unload_after_generate": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "L2P/Z-Image"

    def generate(self, pipeline, prompt, negative_prompt, width, height, steps, cfg_scale, seed, randomize_seed, unload_after_generate):
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
        result = (torch.from_numpy(array)[None,],)

        # 이미지 변환 완료 후 언로드 (pipeline 참조가 더 이상 필요 없는 시점)
        if unload_after_generate:
            _unload_all_pipelines()

        return result


class L2PZImageUnload:
    """
    이 노드를 실행하면 ggf-ltp 모델을 VRAM에서 즉시 해제합니다.
    Flux, Z-Image Turbo 등 다른 모델로 전환하기 전에 사용하세요.
    빈 워크플로우에 단독으로 놓고 실행해도 됩니다.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "unload"
    CATEGORY = "L2P/Z-Image"

    def unload(self):
        _unload_all_pipelines()
        return {}


NODE_CLASS_MAPPINGS = {
    "L2PZImagePipelineLoader": L2PZImagePipelineLoader,
    "L2PZImageGenerate": L2PZImageGenerate,
    "L2PZImageUnload": L2PZImageUnload,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "L2PZImagePipelineLoader": "L2P Z-Image Pipeline Loader",
    "L2PZImageGenerate": "L2P Z-Image Generate",
    "L2PZImageUnload": "L2P Z-Image Unload (Free VRAM)",
}
