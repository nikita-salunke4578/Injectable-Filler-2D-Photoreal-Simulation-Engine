from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.common.image_io import decode_image_base64
from app.simulations.lips.analysis import analyze_facial_proportions
from app.simulations.cheeks.analysis import analyze_cheek_proportions

router = APIRouter(prefix="/api", tags=["analysis"])

class AnalyzeRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded image data string")
    zone: str = Field(..., description="The zone to analyze (e.g. 'lips', 'cheeks')")

@router.post("/analyze-face")
async def analyze_face(request: AnalyzeRequest) -> dict:
    """
    Scans the uploaded face image and returns mathematical analysis and surgical recommendations.
    """
    try:
        image = decode_image_base64(request.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image data") from e

    if request.zone == "lips":
        result = analyze_facial_proportions(image)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    elif request.zone == "cheeks":
        result = analyze_cheek_proportions(image)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    
    raise HTTPException(status_code=400, detail=f"Analysis for zone {request.zone} not implemented yet.")
