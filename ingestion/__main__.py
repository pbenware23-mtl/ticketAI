"""
Run the ingestion API server: python -m ingestion
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "ingestion.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
