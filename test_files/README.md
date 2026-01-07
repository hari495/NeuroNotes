# Test Files for File Upload Feature

This directory contains sample files for testing the file upload functionality.

## Sample Files

1. **sample_machine_learning.txt** - Text file about machine learning fundamentals
2. **sample_python_tips.md** - Markdown file with Python best practices

## How to Use

### Via Streamlit UI
1. Start the FastAPI server: `uvicorn app.main:app --reload`
2. Start Streamlit: `streamlit run app/frontend.py`
3. In the sidebar, click "Upload notes from files"
4. Select one or more files from this directory
5. Click "Upload All Files"

### Via Test Script
Run the automated test script:
```bash
python test_file_upload.py
```

The test script will:
- Create test files in memory
- Test single file upload
- Test batch upload
- Test error handling for unsupported files
- Verify uploaded files are searchable via chat

### Via API Directly (curl)

**Single File Upload:**
```bash
curl -X POST "http://localhost:8000/api/notes/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_files/sample_machine_learning.txt"
```

**Batch Upload:**
```bash
curl -X POST "http://localhost:8000/api/notes/upload/batch" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@test_files/sample_machine_learning.txt" \
  -F "files=@test_files/sample_python_tips.md"
```

**Check Supported Types:**
```bash
curl "http://localhost:8000/api/notes/upload/supported-types"
```

## Supported File Types

- `.txt` - Plain text files
- `.md` - Markdown files
- `.pdf` - PDF documents

## Testing Queries

After uploading these files, try these chat queries:
- "What is machine learning?"
- "What are Python best practices?"
- "Tell me about supervised learning"
- "How do I optimize Python code?"
- "What testing framework should I use?"

## Adding Your Own Test Files

Feel free to add more test files to this directory:
- Keep files reasonably sized (< 1MB recommended)
- Use descriptive filenames
- Include diverse content to test different scenarios
