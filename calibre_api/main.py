import subprocess
import json
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List

app = FastAPI()

@app.get("/books")
async def list_books(
    search: Optional[str] = Query(None, description="Search query for filtering books."),
    limit: Optional[int] = Query(None, description="Maximum number of results to return."),
    sort_by: Optional[str] = Query(None, description="Field to sort results by.")
):
    cmd = ["calibredb", "list", "--for-machine"]
    if search:
        cmd.extend(["--search", search])
    if limit:
        cmd.extend(["--limit", str(limit)])
    if sort_by:
        cmd.extend(["--sort-by", sort_by])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        books = json.loads(result.stdout)
        return books
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"calibredb command failed: {e.stderr}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse calibredb output.")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="calibredb command not found. Make sure Calibre is installed and in your PATH.")

@app.get("/")
async def root():
    return {"message": "Welcome to the Calibre API"}
