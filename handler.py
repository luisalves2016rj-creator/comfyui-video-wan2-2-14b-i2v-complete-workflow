import runpod
import json
import os
import asyncio
from comfyui_wrapper import ComfyUIWrapper

wrapper = ComfyUIWrapper()

def get_loras_dir():
    # Helper to find where ComfyUI stores LoRAs dynamically in the container
    for path in ["/workspace/ComfyUI/models/loras", "/comfyui/models/loras", "./models/loras", "/workspace/models/loras"]:
        if os.path.exists(os.path.dirname(path)):
            return path
    return "./models/loras"

async def handler(job):
    try:
        input_data = job.get("input", {})
        
        print(f"Received job payload: {json.dumps(input_data, indent=2)}")
        
        container_loras_dir = get_loras_dir()
        os.makedirs(container_loras_dir, exist_ok=True)
        print(f"[LoRA Setup] Container LoRAs directory resolved to: {container_loras_dir}")
        
        # 1. Check if persistent network volume is mounted and auto-link existing LoRAs
        use_volume = os.path.exists("/runpod-volume")
        volume_loras_dir = "/runpod-volume/models/loras" if use_volume else None
        
        if use_volume:
            os.makedirs(volume_loras_dir, exist_ok=True)
            print(f"[Network Storage] Volume detected at {volume_loras_dir}. Auto-linking existing files...")
            try:
                # Recursively walk through volume_loras_dir and link files to container_loras_dir
                for root, dirs, files in os.walk(volume_loras_dir):
                    for file in files:
                        if file.endswith(('.safetensors', '.ckpt', '.pt', '.bin')):
                            # Get relative path from volume_loras_dir
                            rel_path = os.path.relpath(os.path.join(root, file), volume_loras_dir)
                            volume_file_path = os.path.join(volume_loras_dir, rel_path)
                            container_file_path = os.path.join(container_loras_dir, rel_path)
                            
                            # Create nested directories inside container_loras_dir if they exist in volume
                            os.makedirs(os.path.dirname(container_file_path), exist_ok=True)
                            
                            if not os.path.lexists(container_file_path):
                                os.symlink(volume_file_path, container_file_path)
                                print(f"[Network Storage Link] Created symlink: {container_file_path} -> {volume_file_path}")
            except Exception as link_err:
                print(f"[Network Storage Link] Warning: Failed to scan/link some volume files: {link_err}")
        
        # 2. Execute the workflow inside the ComfyUI Wrapper
        result = await wrapper.execute_workflow(input_data)
        return result
        
    except Exception as err:
        print(f"Job execution failed with error: {str(err)}")
        return {"error": str(err)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
