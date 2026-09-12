import os
import asyncio
import random
import base64
from abc import ABC, abstractmethod
from typing import Dict, Any
import httpx

class AIProvider(ABC):
    @abstractmethod
    async def verify_content(self, content: str, prompt: str) -> Dict[str, Any]:
        """
        Returns a dict with 'confidence' (float) and 'result' (string).
        """
        pass

    @abstractmethod
    async def moderate_content(self, content: str, prompt: str) -> Dict[str, Any]:
        pass

class MockAIProvider(AIProvider):
    async def verify_content(self, content: str, prompt: str) -> Dict[str, Any]:
        await asyncio.sleep(1)
        confidence = random.uniform(0.5, 1.0)
        result = "Verified" if confidence > 0.7 else "Could not verify"
        return {"confidence": confidence, "result": result}

    async def moderate_content(self, content: str, prompt: str) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"flagged": False, "confidence": 0.95, "reason": "mock"}

    async def moderate_image(self, image_url: str, prompt: str) -> Dict[str, Any]:
        return {"flagged": False, "confidence": 0.95, "reason": "mock"}

class VisionAIProvider(AIProvider):
    """
    Real implementation using a vision-capable LLM API (e.g., Anthropic Claude).
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"

    async def verify_content(self, content: str, prompt: str) -> Dict[str, Any]:
        # 'content' is the signed URL to the image in S3/R2
        try:
            async with httpx.AsyncClient() as client:
                # 1. Download the actual image bytes from the signed URL
                image_response = await client.get(content)
                if image_response.status_code != 200:
                    return {"confidence": 0.0, "result": "Error fetching media for verification"}

                image_bytes = image_response.content
                base64_image = base64.b64encode(image_bytes).decode('utf-8')

                # 2. Send to Vision LLM
                response = await client.post(
                    self.api_url,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-6",
                        "max_tokens": 1024,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/jpeg",
                                            "data": base64_image
                                        },
                                    },
                                    {
                                        "type": "text",
                                        "text": f"Verify if this image shows the user completing the mission: {prompt}. "
                                                f"Respond in JSON format: {{\"confidence\": float, \"result\": string}}"
                                    },
                                ],
                            },
                        ],
                    },
                )
                response.raise_for_status()
                # Simple parsing of the JSON response
                import json
                result_text = response.json()["content"][0]["text"]
                data = json.loads(result_text)
                return {
                    "confidence": float(data.get("confidence", 0.0)),
                    "result": data.get("result", "No result provided")
                }
        except Exception as e:
            print(f"AI Provider Error: {str(e)}")
            return {"confidence": 0.0, "result": f"Error during verification: {str(e)}"}


    async def moderate_content(self, content: str, prompt: str) -> Dict[str, Any]:
        """Text/image moderation using the same Anthropic provider."""
        import json
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                blocks = [{"type":"text","text":prompt + "\nContent:\n" + content}]
                response = await client.post(
                    self.api_url,
                    headers={"x-api-key": self.api_key, "anthropic-version":"2023-06-01","content-type":"application/json"},
                    json={"model":"claude-sonnet-4-6","max_tokens":256,
                          "messages":[{"role":"user","content":blocks}]})
                response.raise_for_status()
                text=response.json()["content"][0]["text"]
                data=json.loads(text)
                return {"flagged":bool(data.get("flagged",True)),
                        "confidence":float(data.get("confidence",0)),
                        "reason":data.get("reason","")}
        except Exception as exc:
            # Fail closed: moderation uncertainty goes to human review.
            return {"flagged":True,"confidence":0.0,"reason":f"moderation_error:{exc}"}


    async def moderate_image(self, image_url: str, prompt: str) -> Dict[str, Any]:
        import json
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r=await client.get(image_url); r.raise_for_status()
                b64=base64.b64encode(r.content).decode()
                response=await client.post(self.api_url,headers={"x-api-key":self.api_key,"anthropic-version":"2023-06-01","content-type":"application/json"},
                    json={"model":"claude-sonnet-4-6","max_tokens":256,"messages":[{"role":"user","content":[
                        {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":b64}},
                        {"type":"text","text":prompt+" Return JSON with keys flagged (boolean), confidence (number), and reason (string)."}]}]})
                response.raise_for_status(); data=json.loads(response.json()["content"][0]["text"])
                return {"flagged":bool(data.get("flagged",True)),"confidence":float(data.get("confidence",0)),"reason":data.get("reason","")}
        except Exception as exc:
            return {"flagged":True,"confidence":0.0,"reason":f"moderation_error:{exc}"}

# Singleton configuration
provider_type = os.getenv("AI_PROVIDER", "mock" if os.getenv("APP_ENV", "development").lower() != "production" else "vision")
if provider_type == "mock":
    ai_provider = MockAIProvider()
else:
    ai_provider = VisionAIProvider(os.getenv("AI_API_KEY", ""))
