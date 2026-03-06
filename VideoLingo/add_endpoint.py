with open("backend/main.py", "r") as f:
    content = f.read()

target = '    return StreamingResponse(event_generator(), media_type="text/event-stream")\n\n\n@app.post("/api/transcribe")'

replacement = '''    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/rename-file")
async def rename_file_endpoint(req: RenameRequest):
    import re, uuid
    old_path = os.path.join("static", req.old_filename)
    if not os.path.exists(old_path) or ".." in req.old_filename:
        raise HTTPException(status_code=404, detail="File not found or invalid")
    
    # Clean new filename
    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', req.new_filename.replace(' ', '_'))
    if not safe_name:
        safe_name = "audio"
    if not safe_name.endswith(".mp3"):
        safe_name += ".mp3"
        
    new_path = os.path.join("static", safe_name)
    try:
        # Avoid overwriting existing files
        if os.path.exists(new_path) and old_path != new_path:
            safe_name = f"{safe_name.replace('.mp3', '')}_{str(uuid.uuid4())[:4]}.mp3"
            new_path = os.path.join("static", safe_name)
            
        os.rename(old_path, new_path)
        return {
            "status": "success",
            "new_filename": safe_name,
            "new_url": f"/static/{safe_name}"
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transcribe")'''

if target in content:
    content = content.replace(target, replacement)
    with open("backend/main.py", "w") as f:
        f.write(content)
    print("Added endpoint successfully.")
else:
    print("Target not found.")

