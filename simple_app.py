#!/usr/bin/env python3
"""
Simple FastAPI application for testing operator creation.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
import uvicorn

# Create FastAPI instance
app = FastAPI(
    title="BluBus Plus Test API",
    description="Simple test API for operator creation",
    version="1.0.0"
)

# Pydantic model for operator creation
class OperatorCreate(BaseModel):
    company_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    business_license: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

class OperatorResponse(OperatorCreate):
    id: int
    status: str = "PENDING"

# In-memory storage for testing
operators_db = []
next_id = 1

@app.get("/")
async def root():
    return {"message": "BluBus Plus Test API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/operators/", response_model=OperatorResponse)
async def create_operator(operator_data: OperatorCreate):
    """Create a new operator account."""
    global next_id
    
    # Check if operator with same email already exists
    for op in operators_db:
        if op["contact_email"] == operator_data.contact_email:
            raise HTTPException(
                status_code=400,
                detail="Operator with this email already exists"
            )
    
    # Create operator
    operator = {
        "id": next_id,
        "status": "PENDING",
        **operator_data.dict()
    }
    
    operators_db.append(operator)
    next_id += 1
    
    print(f"✅ Created operator: {operator}")
    return operator

@app.get("/operators/", response_model=list[OperatorResponse])
async def list_operators():
    """List all operators."""
    return operators_db

if __name__ == "__main__":
    print("Starting BluBus Plus Test API on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

