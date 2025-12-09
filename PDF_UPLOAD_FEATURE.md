## PDF Upload Feature - Meeting Agent

### Overview

The meeting agent now includes a **PDF upload feature** that allows you to add PDF documents before starting a meeting. The agent will analyze these PDFs during the meeting to provide context-aware answers to questions.

### How It Works

#### 1. **PDF Upload Before Meeting**
- Click the blue **"📄 Add PDF"** button in the Meeting Agent interface
- Select one or more PDF files from your computer
- Each PDF is processed and added to the knowledge index
- Confirmation message shows when PDF is successfully loaded

#### 2. **PDF Analysis During Questions**
When someone asks a question in the meeting:
1. The agent searches the uploaded PDF(s) for relevant content
2. Extracts the top 5 most relevant chunks matching the question
3. Combines PDF context with meeting transcript and screen text
4. Sends all context to Gemini for a comprehensive answer
5. Speaks the answer aloud using text-to-speech

#### 3. **PDF in Summary**
When you stop the meeting and generate a summary:
- PDFs are included in the Q&A pairs
- Most relevant PDF content is referenced in answers
- Summary document includes all extracted PDF context

### Usage Guide

#### Adding PDFs

**Before starting the meeting:**

1. Click **"📄 Add PDF"** button
2. Select a PDF file from the file picker
3. File is indexed and ready to use
4. You can add multiple PDFs - just click the button multiple times
5. Start the meeting when ready - click **"▶ Start"**

**Important Notes:**
- ✅ You CAN add PDFs before or during the meeting
- ❌ You CANNOT add PDFs while recording (button is disabled)
- ✅ You CAN add multiple PDFs to the same meeting
- ⏸️ Stop the meeting, then add more PDFs if needed

#### PDF Button States

| State | Button Status | Action |
|-------|---------------|--------|
| Before Meeting | Enabled (Blue) | Click to add PDFs |
| Recording | Disabled (Grayed) | Wait for Stop |
| After Stop | Enabled (Blue) | Add more PDFs or Start new meeting |

### Example Scenario

**Scenario: Company policy Q&A meeting**

1. **Preparation:**
   - Click "📄 Add PDF"
   - Upload `company-policies.pdf`
   - Upload `employee-handbook.pdf`
   - Click "▶ Start" to begin recording

2. **During Meeting:**
   - Someone asks: "What's our vacation policy?"
   - Agent searches PDFs for "vacation policy"
   - Finds relevant section from `employee-handbook.pdf`
   - Generates answer combining PDF content + transcript context
   - Answer is spoken aloud and displayed

3. **Summary:**
   - Click "⏹ Stop"
   - Summary includes all Q&A with PDF references
   - Saved to `meeting_summaries/summary_YYYYMMDD_HHMMSS.txt`

### Technical Details

#### PDF Processing

**Chunk Creation:**
- Each PDF is split into chunks of 800 characters
- Chunks overlap by 200 characters for context continuity
- Improves retrieval of relevant information

**Example:**
```
PDF: "The company policy on remote work..."
↓
Chunk 1: "The company policy on remote work states that... [200-char overlap with Chunk 2]"
Chunk 2: "[Continued from Chunk 1] ...employees can work remotely on... [200-char overlap with Chunk 3]"
Chunk 3: "[Continued from Chunk 2] ...Tuesdays and Thursdays with approval from..."
```

**Vector Search:**
- Uses FAISS (Facebook AI Similarity Search) for fast retrieval
- Embeddings based on text features
- Returns top 5 most relevant chunks per question
- Integrates with Gemini for final answer generation

#### Context Flow

```
Question Asked in Meeting
        ↓
Detect Question (pattern matching)
        ↓
Search PDFs for relevant chunks (FAISS)
        ↓
Combine with:
   - Meeting transcript (recent text)
   - Screen content (current display)
   - PDF context (from search results)
        ↓
Send to Gemini API for answer generation
        ↓
Speak answer + Display in overlay
        ↓
Save Q&A pair to transcript
```

### Supported File Formats

- **PDF (.pdf)** ✅ Fully supported
- **Other formats** (Word, Excel, etc.) - Not yet supported
  - Future enhancement: Add support for DOCX, XLSX, etc.

### Limitations & Considerations

1. **PDF Size:**
   - Smaller PDFs (< 10 MB) process faster
   - Large PDFs (> 50 MB) may take longer to index
   - Very large PDFs may consume more API tokens

2. **PDF Content:**
   - Works best with text-based PDFs
   - Scanned image-based PDFs require OCR (not yet implemented)
   - Tables and structured data may not extract perfectly

3. **API Impact:**
   - Adding PDFs doesn't use API quota
   - Searching and answering questions uses API quota
   - See `TOKEN_OPTIMIZATION.md` for cost estimates

4. **Text Extraction:**
   - PDFs with embedded fonts may have extraction issues
   - Encrypted PDFs will fail to load
   - Some special characters may not extract correctly

### Troubleshooting

#### Problem: "PDF file not found" error

**Solution:**
- Verify file path is correct
- Check file exists and is readable
- Try a different PDF file
- Check file permissions

#### Problem: PDF loads but doesn't help answer questions

**Solutions:**
- Check that PDF contains relevant content for questions asked
- Verify PDF text is extractable (not image-based/scanned)
- Try asking more specific questions matching PDF content
- Check API quota is available (not exhausted)

#### Problem: Button is grayed out

**Solution:**
- This is normal - button is disabled during recording
- Click "⏹ Stop" to re-enable it
- Add PDFs before clicking "▶ Start"

#### Problem: Memory usage grows with multiple PDFs

**Solution:**
- This is normal - FAISS index grows with more content
- Close and restart agent if using many large PDFs
- Consider splitting large PDFs into smaller files

### Code Architecture

**Main Components:**

1. **overlay.py:**
   - `pdf_selected` signal emitted when PDF is chosen
   - `on_add_pdf()` method handles file picker dialog
   - Button disabled during recording

2. **agent.py:**
   - `add_pdf_file(pdf_path)` method receives and processes PDF
   - Calls `pdf_index.add_pdf(pdf_path)` to add to knowledge base

3. **pdf_index.py:**
   - `add_pdf(pdf_path)` - dynamically adds single PDF
   - `query(question, k=5)` - searches index for relevant chunks
   - `build(folder)` - loads initial PDFs from directory

4. **llm_client.py:**
   - Uses PDF context in `ask_llm_with_context()`
   - Limits PDF context to 200 characters (optimized)

5. **main.py:**
   - Connects `pdf_selected` signal to `agent.add_pdf_file()`

### Performance Tips

1. **Optimize PDF Size:**
   - Remove unnecessary images/graphics from PDFs
   - Use text compression where possible
   - Split very large PDFs into smaller documents

2. **Improve Answer Quality:**
   - Use PDFs with clear, searchable text
   - Include relevant keywords in PDF content
   - Ask specific questions matching PDF topics

3. **Reduce API Costs:**
   - Keep PDF context under 200 characters (already optimized)
   - Use specific questions instead of broad ones
   - See `TOKEN_OPTIMIZATION.md` for more cost-saving tips

### Future Enhancements

Potential features to add:

1. **Multiple File Format Support**
   - DOCX, XLSX, TXT, Markdown
   - Web links (URL fetching)
   - Email attachments

2. **Advanced PDF Processing**
   - OCR for scanned PDFs
   - Table extraction and understanding
   - Image recognition in PDFs

3. **Better Search**
   - Semantic search using Gemini embeddings
   - Hybrid search (keyword + semantic)
   - PDF metadata extraction

4. **Knowledge Management**
   - Save/load PDF knowledge bases
   - Tag PDFs by topic
   - Automatic PDF organization

---

**Updated**: December 8, 2025
**Status**: ✅ Ready to Use
**API Requirement**: None (PDF indexing is local)
**Gemini API Used**: Only during answer generation
