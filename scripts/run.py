import uvicorn

if __name__ == "__main__":
    print("Starting Voice-Based Minutes of Meeting Pipeline Server...")
    print("Access Web UI at: http://localhost:8000")
    print("Access API Docs at: http://localhost:8000/docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
