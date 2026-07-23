import modal
import random
import io

from fastapi import Form, Response

# -----------------------
# Modal setup
# -----------------------

app = modal.App("ultrareal-imagen")

image = (
    modal.Image.debian_slim()
    .apt_install("git", "libgl1", "libglib2.0-0")
    .pip_install(
        "torch==2.13.0",
        "torchvision==0.28.0",
        "git+https://github.com/huggingface/diffusers.git@973a077c6a4e7e7a7ea61a84bedd29ac24fb609a",
        "transformers==5.14.1",
        "accelerate==1.14.0",
        "peft==0.18.0",
        "Pillow==12.3.0",
        "numpy",
        "fastapi[standard]",
        "python-multipart"
    )
    .run_commands(
        "python -c \"from huggingface_hub import snapshot_download; import os; os.environ['HF_TOKEN']=''; snapshot_download('Qwen/Qwen-Image')\"",
        "python -c \"from huggingface_hub import hf_hub_download; import os; os.environ['HF_TOKEN']=''; hf_hub_download('Danrisi/Qwen-image_SamsungCam_UltraReal', 'Samsung.safetensors')\""
    )
)

with image.imports():
    import numpy as np
    import torch
    from PIL import Image
    from diffusers import DiffusionPipeline

# -----------------------
# Model class (persistent container)
# -----------------------

@app.cls(
    image=image,
    gpu="A100-80GB",
    timeout=3600,
    scaledown_window=60,
    startup_timeout=3600,
)
@modal.concurrent(max_inputs=10)
class UltraRealImagen:
    @modal.enter()
    def initialize(self):
        print("Initializing UltraRealImagen...")
        dtype = torch.bfloat16

        self.pipe = DiffusionPipeline.from_pretrained(
            "Qwen/Qwen-Image",
            torch_dtype=dtype
        ).to("cuda")
        self.pipe.load_lora_weights("Danrisi/Qwen-image_SamsungCam_UltraReal", weight_name="Samsung.safetensors")
        print("Initialization complete.")

    @modal.fastapi_endpoint(method="POST")
    async def infer(
        self,
        prompt: str = Form(...),
        seed: int = Form(42),
        randomize_seed: bool = Form(True),
        guidance_scale: float = Form(4.0),
        steps: int = Form(40),
        height: int = Form(None),
        width: int = Form(None),
    ):
        MAX_SEED = np.iinfo(np.int32).max

        if randomize_seed:
            seed = random.randint(0, MAX_SEED)

        generator = torch.Generator("cuda").manual_seed(seed)

        result = self.pipe(
            prompt=prompt,
            negative_prompt=" ",
            height=height,
            width=width,
            num_inference_steps=steps,
            generator=generator,
            true_cfg_scale=guidance_scale,
        ).images

        # Convert result image to binary output
        buffer = io.BytesIO()
        result[0].save(buffer, format="PNG")
        
        return Response(
            content=buffer.getvalue(),
            media_type="image/png"
        )