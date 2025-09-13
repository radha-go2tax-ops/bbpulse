#!/usr/bin/env python3
"""
Simple script to run the BluBus Pulse backend application.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("blubuspulse.main:app", host="0.0.0.0", port=8000, reload=True)
