import runpod
import json
import asyncio
from comfyui_wrapper import ComfyUIWrapper

wrapper = ComfyUIWrapper()

async def handler(job):
    try:
        input_data = job.get("input", {})
        
        print(f"Received job: {json.dumps(input_data, indent=2)}")
        
        # Executa o workflow
        result = await wrapper.execute_workflow(input_data)
        
        return {
            "status": "COMPLETED",
            **result
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "status": "FAILED",
            "error": str(e)
        }

# Inicia o Serverless
runpod.serverless.start({
    "handler": handler,
    "return_aggregate_stream": True
})
