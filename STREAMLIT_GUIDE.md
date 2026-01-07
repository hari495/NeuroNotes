# Streamlit Interface Guide

Complete guide to using the RAG Notes App web interface built with Streamlit.

## Quick Start

### 1. Start the FastAPI Backend

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### 2. Launch the Streamlit Interface

```bash
# Option 1: Using the launch script
./run_streamlit.sh

# Option 2: Direct command
streamlit run app/frontend.py
```

The web interface will open automatically at `http://localhost:8501`

## Interface Overview

The Streamlit app has two main sections:

### Sidebar (Left)
- **Create New Note** - Add notes to your knowledge base
- **Your Notes** - View all saved notes
- **Chat Settings** - Configure search parameters

### Main Area (Right)
- **Chat Interface** - Ask questions and view answers
- **Conversation History** - See past messages
- **Sources** - View which notes were used for each answer

## Features

### 1. Creating Notes

**Location:** Sidebar → "Create New Note"

**Steps:**
1. Enter a **Title** for your note
2. Add your **Content** in the text area
3. Click **💾 Save Note**

**Example:**
```
Title: Python Basics
Content: Python is a high-level programming language known for its
simplicity and readability. It supports multiple programming paradigms...
```

**After Saving:**
- See success message with chunk statistics
- Note appears in "Your Notes" section
- Can immediately query it via chat

**Tips:**
- Use descriptive titles for better organization
- Longer notes (>500 chars) will be chunked automatically
- Each note is assigned a unique ID

### 2. Chatting with Notes

**Location:** Main Area → Chat Input

**Steps:**
1. Type your question in the chat input box
2. Press Enter or click Send
3. Wait for the AI to search and respond
4. View the answer with optional sources

**Example Queries:**
```
❓ "What are the key features of Python?"
❓ "Explain the types of machine learning"
❓ "How does FastAPI handle async requests?"
```

**Response Includes:**
- **Answer** - Generated from your notes
- **Sources** - Which notes were used (expandable)
- **Similarity Score** - How relevant each source is

### 3. Viewing Sources

**Location:** Below each AI response → "📚 Sources" expander

**Information Shown:**
- **Source Number** - Order of relevance
- **Note Title** - Which note the chunk is from
- **Similarity** - How closely it matches your query (higher = better)
- **Preview** - First 200 characters of the source text

**Example:**
```
Source 1 - Python Basics (similarity: 85%)
"Python is a high-level programming language known for its
simplicity and readability. It supports..."
```

### 4. Adjusting Settings

**Location:** Sidebar → "⚙️ Chat Settings"

**Settings:**

#### Context Chunks (k)
- **Range:** 1-10 chunks
- **Default:** 3
- **Use Cases:**
  - **k=1-2:** Quick, focused answers
  - **k=3-5:** Balanced (recommended)
  - **k=6-10:** Comprehensive, detailed answers

#### Show Sources
- **Default:** ON
- **When ON:** Shows which notes were used
- **When OFF:** Only shows the answer

### 5. Managing Notes

**Location:** Sidebar → "📚 Your Notes"

**Features:**
- **View All Notes** - See titles and metadata
- **Refresh** - Update the list
- **Note Details** - Click to expand:
  - Note ID
  - Number of chunks
  - Custom metadata

**Note Statistics:**
- **Total Chunks** - Total pieces of text indexed
- **Embedding Dim** - Vector dimension (768 for nomic-embed-text)

### 6. Conversation History

**Location:** Main chat area

**Features:**
- **Auto-scroll** - New messages appear at bottom
- **Persistent** - History maintained during session
- **Clear Button** - Reset conversation (🗑️ Clear Chat History)

**Message Types:**
- 👤 **User** - Your questions (right-aligned)
- 🤖 **Assistant** - AI responses (left-aligned)

## User Interface Elements

### Sidebar Components

```
┌─────────────────────────────┐
│ 📝 Create New Note          │
│  ┌─────────────────────┐    │
│  │ Title               │    │
│  ├─────────────────────┤    │
│  │ Content (text area) │    │
│  │                     │    │
│  └─────────────────────┘    │
│  [💾 Save Note]             │
├─────────────────────────────┤
│ 📊 Stats                    │
│  Total Chunks: 42           │
│  Embedding Dim: 768         │
├─────────────────────────────┤
│ 📚 Your Notes               │
│  [🔄 Refresh Notes]         │
│  ▼ Python Basics            │
│  ▼ Machine Learning         │
├─────────────────────────────┤
│ ⚙️ Chat Settings            │
│  Context Chunks: [===] 3    │
│  ☑ Show Sources             │
└─────────────────────────────┘
```

### Main Chat Area

```
┌─────────────────────────────────────┐
│ 💬 Chat with Your Notes             │
│                                     │
│ 👤 What is Python?                  │
│                                     │
│ 🤖 Python is a high-level...        │
│    📚 Sources (3 chunks used)       │
│       ▼ Source 1 - Python Basics    │
│                                     │
│ 👤 Explain machine learning         │
│                                     │
│ 🤖 Machine learning is...           │
│    📚 Sources (2 chunks used)       │
│                                     │
│ [Type your question here...]        │
│                                     │
│      [🗑️ Clear Chat History]       │
└─────────────────────────────────────┘
```

## Workflow Examples

### Example 1: Study Session

**Scenario:** Preparing for a Python exam

1. **Add Study Notes:**
   ```
   Sidebar → Create New Note
   Title: "Python Data Types"
   Content: "Python has several built-in data types..."
   Save Note ✓
   ```

2. **Add More Notes:**
   ```
   Title: "Python Functions"
   Content: "Functions in Python are defined using..."
   Save Note ✓
   ```

3. **Ask Questions:**
   ```
   Chat: "What are Python's data types?"
   Response: Lists built-in types with examples
   Sources: Shows "Python Data Types" note
   ```

4. **Follow-up:**
   ```
   Chat: "How do I define a function?"
   Response: Explains function syntax
   Sources: Shows "Python Functions" note
   ```

### Example 2: Research Organization

**Scenario:** Organizing research papers

1. **Ingest Papers:**
   ```
   Title: "Neural Networks - Smith 2024"
   Content: [Copy paper abstract/summary]

   Title: "Deep Learning - Jones 2024"
   Content: [Copy key findings]
   ```

2. **Query Research:**
   ```
   Chat: "What did Smith say about neural networks?"
   Settings: k=5 (more context)
   Response: Summarizes Smith's findings
   ```

3. **Compare Sources:**
   ```
   Chat: "Compare approaches from Smith and Jones"
   Response: Analyzes both papers
   Sources: Shows chunks from both papers
   ```

### Example 3: Personal Knowledge Base

**Scenario:** Building a second brain

1. **Add Various Topics:**
   ```
   - Cooking recipes
   - Book summaries
   - Learning notes
   - Meeting notes
   ```

2. **Quick Lookup:**
   ```
   Chat: "What was the recipe for pasta?"
   Settings: k=2, Show Sources ON
   Response: Recipe details with source citation
   ```

## Tips & Best Practices

### Writing Good Notes

✅ **DO:**
- Use descriptive, searchable titles
- Include key terms and concepts
- Structure content logically
- Add context and explanations

❌ **DON'T:**
- Use vague titles like "Note 1"
- Include only keywords without context
- Mix unrelated topics in one note
- Make notes too short (< 50 chars)

### Asking Good Questions

✅ **DO:**
- Be specific: "What are Python's data types?"
- Ask one thing at a time
- Use terms from your notes
- Rephrase if answer is unclear

❌ **DON'T:**
- Be too vague: "Tell me about Python"
- Ask multiple questions at once
- Use jargon not in your notes
- Expect knowledge outside your notes

### Optimizing Search

**For Precise Answers:**
- Set k=1-2
- Use specific queries
- Look for exact matches in sources

**For Comprehensive Answers:**
- Set k=5-10
- Use broader queries
- Review all sources

### Managing Your Knowledge Base

1. **Regular Updates:**
   - Add new notes frequently
   - Update existing information
   - Remove outdated content

2. **Organization:**
   - Use consistent naming
   - Group related topics
   - Add metadata when ingesting

3. **Quality over Quantity:**
   - Prefer well-written notes
   - Include context, not just facts
   - Review and refine content

## Troubleshooting

### "No relevant context found"

**Problem:** AI can't find information to answer

**Solutions:**
- Add notes about the topic
- Rephrase your question
- Check if terminology matches your notes
- Increase k (context chunks)

### Slow Responses

**Problem:** Answers take too long

**Solutions:**
- Reduce k (fewer chunks)
- Check FastAPI backend status
- Ensure Ollama is running
- Restart services

### Sources Don't Match Question

**Problem:** Retrieved sources seem irrelevant

**Solutions:**
- Increase k to get more options
- Rephrase query with different words
- Check similarity scores
- Add more relevant notes

### Chat History Too Long

**Problem:** Chat becomes cluttered

**Solutions:**
- Click "Clear Chat History"
- Refresh page (session resets)
- Start new conversation

### Cannot Create Note

**Problem:** Save button doesn't work

**Solutions:**
- Check both title AND content are filled
- Ensure FastAPI backend is running
- Check browser console for errors
- Verify API endpoint (localhost:8000)

## Keyboard Shortcuts

- **Enter** - Send message
- **Shift+Enter** - New line in chat input
- **Ctrl+R** / **Cmd+R** - Refresh page

## Advanced Features

### URL Parameters

You can customize the app via URL:

```
http://localhost:8501/?k=5&sources=false
```

(Note: Currently requires code modification to support)

### Metadata Filtering

Future feature: Filter by note categories, dates, or tags

### Export Conversations

Future feature: Save chat history as markdown or PDF

## System Requirements

### Browser Compatibility
- ✅ Chrome (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

### Network
- FastAPI backend must be running
- Both services on localhost (or configure URLs)

### Performance
- Handles 100s of notes efficiently
- Chat responses: 2-10 seconds typical
- Note creation: < 2 seconds

## Security Notes

⚠️ **Important:**
- Currently configured for localhost only
- No authentication implemented
- All data stored locally
- Suitable for personal use

For production deployment:
- Add authentication
- Use HTTPS
- Configure CORS properly
- Add rate limiting

## Next Steps

Now that you have the Streamlit interface:

1. **Try it out:**
   - Create a few test notes
   - Ask various questions
   - Experiment with settings

2. **Build your knowledge base:**
   - Add your study materials
   - Import research notes
   - Organize documentation

3. **Advanced usage:**
   - Explore API endpoints directly
   - Customize the interface
   - Integrate with other tools

## Getting Help

- Check logs in terminal for errors
- Visit `http://localhost:8000/docs` for API docs
- Review `CHAT_API_GUIDE.md` for API details
- See `RAG_GUIDE.md` for RAG system info

Happy chatting with your notes! 📚💬
