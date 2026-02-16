import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

# Entire UI and conversion logic, all runs 100% on frontend / browser
APP_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bulk WebP Converter</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', Roboto, sans-serif;
            background-color: #f0f4f8;
            min-height: 100vh;
            padding: 2rem;
            max-width: 1000px;
            margin: 0 auto;
        }
        h1 {
            color: #1e293b;
            margin-bottom: 0.75rem;
        }
        .card {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
        }
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: 0.2s;
            margin: 0.5rem 0.5rem 0.5rem 0;
        }
        .btn:hover {
            transform: translateY(-1px);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .btn-primary {
            background-color: #2563eb;
            color: white;
        }
        .btn-primary:hover {
            background-color: #1d4ed8;
        }
        .btn-success {
            background-color: #16a34a;
            color: white;
        }
        .btn-success:hover {
            background-color: #15803d;
        }
        .btn-secondary {
            background-color: #7c3aed;
            color: white;
        }
        .btn-secondary:hover {
            background-color: #6d28d9;
        }
        .btn-sm {
            padding: 0.4rem 0.8rem;
            font-size: 0.875rem;
            text-decoration: none;
            background-color: #2563eb;
            color: white;
        }
        .preview {
            width: 48px;
            height: 48px;
            object-fit: cover;
            border-radius: 6px;
        }
        .result-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem;
            border-bottom: 1px solid #e2e8f0;
        }
        .result-item:last-child {
            border-bottom: none;
        }
        .note {
            color: #16a34a;
            font-weight: 500;
            margin-bottom: 1.5rem;
        }
        .quality-container {
            margin: 1.5rem 0;
            padding: 1rem;
            background-color: #f8fafc;
            border-radius: 8px;
        }
        #quality {
            width: 100%;
            margin-top: 0.5rem;
        }
        .hint {
            font-size: 0.875rem;
            color: #64748b;
            margin: 0.5rem 0 0 0;
        }
        .empty-text {
            color: #94a3b8;
            text-align: center;
            padding: 2rem;
        }
        h3 {
            color: #1e293b;
            margin-bottom: 0.75rem;
        }
    </style>
</head>
<body>
    <h1>🖼️ Bulk Image to WebP Converter</h1>
    <p class="note">✅ All processing is done locally on your device, no files are uploaded, no file size limits</p>

    <div class="card">
        <input type="file" id="fileInput" accept="image/*" multiple hidden>
        <button id="selectBtn" class="btn btn-primary">📁 Select Multiple Images</button>

        <div class="quality-container">
            <label for="quality">WebP Quality: <span id="qualityValue">80</span>%</label>
            <input type="range" id="quality" min="10" max="100" value="80" step="5">
            <p class="hint">80% quality is recommended for perfect balance of file size and image quality</p>
        </div>

        <button id="convertBtn" class="btn btn-success" disabled>🔄 Convert All to WebP</button>
        <button id="downloadAllBtn" class="btn btn-secondary" disabled>💾 Download All as ZIP</button>
    </div>

    <h3>Conversion Results</h3>
    <div id="results" class="card">
        <p class="empty-text">No files converted yet.</p>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>
    <script>
        const fileInput = document.getElementById('fileInput')
        const selectBtn = document.getElementById('selectBtn')
        const quality = document.getElementById('quality')
        const qualityValue = document.getElementById('qualityValue')
        const convertBtn = document.getElementById('convertBtn')
        const downloadAllBtn = document.getElementById('downloadAllBtn')
        const results = document.getElementById('results')

        let selectedFiles = []
        let convertedFiles = []

        // Update quality display
        quality.addEventListener('input', () => {
            qualityValue.textContent = quality.value
        })

        // Trigger file select window
        selectBtn.addEventListener('click', () => fileInput.click())

        // Handle file selection
        fileInput.addEventListener('change', (e) => {
            selectedFiles = Array.from(e.target.files)
            convertBtn.disabled = selectedFiles.length === 0
            results.innerHTML = `<p>${selectedFiles.length} image(s) selected, click Convert button to start.</p>`
            convertedFiles = []
            downloadAllBtn.disabled = true
        })

        // Convert all images to WebP
        convertBtn.addEventListener('click', async () => {
            convertBtn.disabled = true
            results.innerHTML = ''
            convertedFiles = []
            const qualityLevel = parseInt(quality.value) / 100

            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i]
                const resultItem = document.createElement('div')
                resultItem.className = 'result-item'
                resultItem.innerHTML = `<span>Converting ${file.name}...</span>`
                results.appendChild(resultItem)

                try {
                    const img = new Image()
                    const objectUrl = URL.createObjectURL(file)
                    
                    await new Promise((resolve, reject) => {
                        img.onload = resolve
                        img.onerror = reject
                        img.src = objectUrl
                    })

                    // Draw image to canvas
                    const canvas = document.createElement('canvas')
                    canvas.width = img.width
                    canvas.height = img.height
                    const ctx = canvas.getContext('2d')
                    ctx.drawImage(img, 0, 0)

                    // Export canvas as WebP
                    const webpBlob = await new Promise((resolve) => {
                        canvas.toBlob(resolve, 'image/webp', qualityLevel)
                    })

                    URL.revokeObjectURL(objectUrl)

                    // Generate new filename
                    const nameWithoutExt = file.name.substring(0, file.name.lastIndexOf('.')) || file.name
                    const webpFileName = `${nameWithoutExt}.webp`

                    convertedFiles.push({
                        name: webpFileName,
                        blob: webpBlob
                    })

                    // Update UI with result
                    const downloadUrl = URL.createObjectURL(webpBlob)
                    resultItem.innerHTML = `
                        <div style="display:flex;align-items:center;gap:1rem;">
                            <img src="${downloadUrl}" class="preview" alt="preview">
                            <span>${webpFileName} <small>(${(webpBlob.size / 1024).toFixed(1)} KB)</small></span>
                        </div>
                        <a href="${downloadUrl}" download="${webpFileName}" class="btn btn-sm">Download</a>
                    `

                } catch (err) {
                    resultItem.innerHTML = `<span style="color:#dc2626">❌ Failed to convert ${file.name}</span>`
                }
            }

            downloadAllBtn.disabled = convertedFiles.length === 0
            convertBtn.disabled = false
        })

        // Download all files as ZIP
        downloadAllBtn.addEventListener('click', async () => {
            downloadAllBtn.disabled = true
            downloadAllBtn.textContent = '⏳ Generating ZIP...'

            const zip = new JSZip()
            convertedFiles.forEach(file => {
                zip.file(file.name, file.blob)
            })

            const zipBlob = await zip.generateAsync({type: 'blob'})
            const downloadUrl = URL.createObjectURL(zipBlob)

            const a = document.createElement('a')
            a.href = downloadUrl
            a.download = 'converted_webp_images.zip'
            a.click()

            URL.revokeObjectURL(downloadUrl)
            downloadAllBtn.textContent = '💾 Download All as ZIP'
            downloadAllBtn.disabled = false
        })
    </script>
</body>
</html>
"""

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(APP_HTML.encode('utf-8'))
    # Disable access logs
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    PORT = 8080
    server = HTTPServer(('localhost', PORT), RequestHandler)
    print(f"🚀 WebP Converter running on http://localhost:{PORT}")
    print("💡 Browser will open automatically. Press Ctrl+C to stop the server when done.")
    webbrowser.open(f'http://localhost:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Server stopped.")
        server.server_close()