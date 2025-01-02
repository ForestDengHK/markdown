// Initialize marked with options
marked.setOptions({
    breaks: true,
    gfm: true,
    headerIds: true,
    sanitize: false
});

// Initialize CodeMirror
let editor;

// Default content
let defaultContent = `# Welcome to the Markdown Editor!

## Features

This editor supports:

1. **Real-time preview**
2. *Syntax highlighting*
3. Export to multiple formats:
   - PDF
   - Word
   - HTML

### Code Blocks

\`\`\`python
def hello_world():
    print("Hello, World!")
\`\`\`

### Tables

| Feature | Status |
|---------|--------|
| Editor  | 
| Preview | 
| Export  | 

> Try editing this content to see the live preview!
`;

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize CodeMirror
    editor = CodeMirror.fromTextArea(document.getElementById('markdown-input'), {
        mode: 'markdown',
        theme: 'neat',
        lineWrapping: true,
        viewportMargin: Infinity,
        lineNumbers: true,
        autofocus: true,
        extraKeys: {"Enter": "newlineAndIndentContinueMarkdownList"},
        scrollbarStyle: "native"
    });

    // Set default content
    editor.setValue(defaultContent);

    // Update preview on change
    editor.on('change', function() {
        updatePreview();
    });

    // Sync scrolling
    let isEditorScrolling = false;
    let isPreviewScrolling = false;
    const previewContent = document.getElementById('preview-content');
    
    editor.on('scroll', function() {
        if (isPreviewScrolling) return;
        isEditorScrolling = true;
        
        const editorInfo = editor.getScrollInfo();
        const editorHeight = editorInfo.height - editorInfo.clientHeight;
        const scrollRatio = editorInfo.top / editorHeight;
        
        const previewHeight = previewContent.scrollHeight - previewContent.clientHeight;
        previewContent.scrollTop = scrollRatio * previewHeight;
        
        setTimeout(() => { isEditorScrolling = false; }, 50);
    });
    
    previewContent.addEventListener('scroll', function() {
        if (isEditorScrolling) return;
        isPreviewScrolling = true;
        
        const previewHeight = this.scrollHeight - this.clientHeight;
        const scrollRatio = this.scrollTop / previewHeight;
        
        const editorInfo = editor.getScrollInfo();
        const editorHeight = editorInfo.height - editorInfo.clientHeight;
        editor.scrollTo(null, scrollRatio * editorHeight);
        
        setTimeout(() => { isPreviewScrolling = false; }, 50);
    });

    // Initial preview update
    updatePreview();

    // Start visitor tracking
    updateVisitorCount();
    setInterval(updateVisitorCount, 60000); // Update every minute
});

// Force refresh when window is resized
window.addEventListener('resize', () => {
    editor.refresh();
});

// Update preview when editor content changes
function updatePreview() {
    const markdownContent = editor.getValue();
    const htmlContent = marked.parse(markdownContent);
    document.getElementById('preview-content').innerHTML = htmlContent;
}

// Export functions
async function exportPDF() {
    const element = document.createElement('div');
    element.innerHTML = marked.parse(editor.getValue());
    element.className = 'prose max-w-none p-8';
    
    const opt = {
        margin: 1,
        filename: 'document.pdf',
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    try {
        await html2pdf().set(opt).from(element).save();
    } catch (error) {
        console.error('Error exporting PDF:', error);
        alert('Error exporting to PDF. Please try again.');
    }
}

function exportWord() {
    const htmlContent = marked.parse(editor.getValue());
    const blob = new Blob([htmlContent], { type: 'application/msword' });
    saveAs(blob, 'document.doc');
}

function exportHTML() {
    const htmlContent = marked.parse(editor.getValue());
    const blob = new Blob([htmlContent], { type: 'text/html' });
    saveAs(blob, 'document.html');
}

// Fetch and update visitor statistics
function updateVisitorCount() {
    fetch('/visitors')
        .then(response => response.json())
        .then(data => {
            document.getElementById('visitor-count').textContent = data.total_visitors;
            const recentVisitors = document.getElementById('recent-visitors');
            recentVisitors.textContent = `Current IP: ${data.current_visitor}`;
        })
        .catch(error => console.error('Error fetching visitor count:', error));
}


