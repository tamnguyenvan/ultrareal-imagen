import requests

# Replace this with your actual Modal endpoint URL after deployment
# e.g., run `modal serve main.py` or `modal deploy main.py` to get the URL
MODAL_ENDPOINT = "https://rembgai-production--ultrareal-imagen-ultrarealimagen-infer.modal.run"
# Or if testing locally via modal serve, it might be something else

def test_inference():
    # Base prompt focusing on a highly realistic AI-generated human model in a studio
    prompt = "A typical fast food restaurant dining area during lunch, empty trays on tables, soda fountain, customers eating, bright overhead lighting, realistic plastic surfaces, smartphone photograph, everyday scene."
    
    # Recommended positive magic string for Qwen-Image
    positive_magic = ", Ultra HD, 4K, cinematic composition."
    
    full_prompt = prompt + positive_magic
    
    print(f"Sending prompt: {full_prompt}")
    
    # Payload configuration matching the endpoint's form data
    data = {
        "prompt": full_prompt,
        "seed": 42,
        "randomize_seed": False, # Fixed seed for deterministic testing
        "guidance_scale": 4.0,
        "steps": 40,
        "width": 1584,
        "height": 1056, # 3:2 aspect ratio
    }
    
    try:
        print("Waiting for response from Modal...")
        response = requests.post(MODAL_ENDPOINT, data=data, timeout=600)
        response.raise_for_status()
        
        # Save output image
        output_filename = "test_output.png"
        with open(output_filename, "wb") as f:
            f.write(response.content)
            
        print(f"Successfully generated image and saved to {output_filename}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error during inference request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")

if __name__ == "__main__":
    if "YOUR_WORKSPACE_NAME" in MODAL_ENDPOINT:
        print("Please replace the MODAL_ENDPOINT variable in this script with your actual deployed Modal endpoint URL.")
    else:
        test_inference()
