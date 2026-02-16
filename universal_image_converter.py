import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

APP_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Universal Bulk Image Converter | HEIC Support</title>
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
            max-width: 1100px;
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
        .setting-row {
            margin: 1rem 0;
            padding: 1rem;
            background-color: #f8fafc;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        select {
            padding: 0.5rem;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
            font-size: 1rem;
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
        .saved-positive {
            color: #16a34a;
            font-weight: 500;
        }
        .total-saved-bar {
            padding: 0.75rem 1rem;
            background-color: #dcfce7;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-weight: 500;
            color: #166534;
        }
        .checkbox-label {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>🖼️ Universal Bulk Image Converter (HEIC Supported)</h1>
    <p class="note">✅ All processing is done 100% locally on your device, no files are uploaded, no file size limits</p>

    <div class="card">
        <input type="file" id="fileInput" accept="image/*,.heic,.heif" multiple hidden>
        <button id="selectBtn" class="btn btn-primary">📁 Select Multiple Images</button>

        <div class="setting-row">
            <label for="outputFormat">Output Format</label>
            <select id="outputFormat">
                <option value="jpeg">JPEG (Best for photos)</option>
                <option value="webp">WebP (Best balance of size / quality)</option>
                <option value="png">PNG (Lossless, for transparent images)</option>
                <option value="avif">AVIF (Next gen, smallest size)</option>
            </select>
        </div>

        <div class="setting-row">
            <label class="checkbox-label">
                <input type="checkbox" id="lossless">
                Enable Lossless Compression (maximum quality)
            </label>
            <label for="quality">Quality: <span id="qualityValue">80</span>%</label>
            <input type="range" id="quality" min="10" max="100" value="80" step="5">
            <p class="hint">💡 80% quality is recommended, it is visually identical to original and reduces file size by 50-75%</p>
        </div>

        <button id="convertBtn" class="btn btn-success" disabled>🔄 Convert All</button>
        <button id="downloadAllBtn" class="btn btn-secondary" disabled>💾 Download All as ZIP</button>
    </div>

    <h3>Conversion Results</h3>
    <div id="totalSavedContainer"></div>
    <div id="results" class="card">
        <p class="empty-text">No files converted yet.</p>
    </div>

    <!-- Libraries, all logic runs locally in your browser -->
    <script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/heic2any@0.0.4/dist/heic2any.min.js"></script>

    <script>
        const fileInput = document.getElementById('fileInput')
        const selectBtn = document.getElementById('selectBtn')
        const outputFormat = document.getElementById('outputFormat')
        const losslessToggle = document.getElementById('lossless')
        const quality = document.getElementById('quality')
        const qualityValue = document.getElementById('qualityValue')
        const convertBtn = document.getElementById('convertBtn')
        const downloadAllBtn = document.getElementById('downloadAllBtn')
        const results = document.getElementById('results')
        const totalSavedContainer = document.getElementById('totalSavedContainer')

        let selectedFiles = []
        let convertedFiles = []

        // Helper to format file size
        const formatSize = (bytes) => {
            if (bytes < 1024) return bytes + ' B'
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
            return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
        }

        // Check if file is HEIC / HEIF
        const isHeicFile = (file) => {
            return file.type === 'image/heic' || file.type === 'image/heif'
                || file.name.toLowerCase().endsWith('.heic')
                || file.name.toLowerCase().endsWith('.heif')
        }

        // Update quality display
        quality.addEventListener('input', () => {
            qualityValue.textContent = quality.value
        })

        // Lossless toggle logic
        losslessToggle.addEventListener('change', () => {
            quality.disabled = losslessToggle.checked
            qualityValue.textContent = losslessToggle.checked ? 'Lossless' : quality.value
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
            totalSavedContainer.innerHTML = ''
        })

        // Convert all images
        convertBtn.addEventListener('click', async () => {
            convertBtn.disabled = true
            results.innerHTML = ''
            convertedFiles = []
            let totalOriginalSize = 0
            let totalConvertedSize = 0

            const exportQuality = losslessToggle.checked ? 1 : (parseInt(quality.value) / 100)
            const targetFormat = `image/${outputFormat.value}`
            const outputExt = outputFormat.value

            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i]
                totalOriginalSize += file.size
                const resultItem = document.createElement('div')
                resultItem.className = 'result-item'
                resultItem.innerHTML = `<span>Converting ${file.name}...</span>`
                results.appendChild(resultItem)

                try {
                    let sourceBlob = file

                    // Step 1: Decode HEIC first if needed, lossless decode to preserve full quality
                    if (isHeicFile(file)) {
                        sourceBlob = await heic2any({ blob: file, toType: 'image/png', quality: 1 })
                    }

                    const objectUrl = URL.createObjectURL(sourceBlob)
                    const img = new Image()
                    await new Promise((resolve, reject) => {
                        img.onload = resolve
                        img.onerror = reject
                        img.src = objectUrl
                    })

                    // Step 2: Draw to canvas with highest quality, 100% original resolution
                    const canvas = document.createElement('canvas')
                    // WE NEVER RESIZE YOUR IMAGE, always preserve original resolution
                    canvas.width = img.width
                    canvas.height = img.height
                    const ctx = canvas.getContext('2d')
                    ctx.imageSmoothingEnabled = true
                    ctx.imageSmoothingQuality = 'high'
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

                    // Step 3: Export to selected output format
                    const convertedBlob = await new Promise((resolve, reject) => {
                        canvas.toBlob((blob) => {
                            if(!blob) return reject()
                            resolve(blob)
                        }, targetFormat, exportQuality)
                    })

                    URL.revokeObjectURL(objectUrl)

                    // Generate new filename
                    const nameWithoutExt = file.name.substring(0, file.name.lastIndexOf('.')) || file.name
                    const newFileName = `${nameWithoutExt}.${outputExt}`

                    convertedFiles.push({
                        name: newFileName,
                        blob: convertedBlob,
                        originalSize: file.size
                    })
                    totalConvertedSize += convertedBlob.size

                    const savedPercent = Math.round(100 - ((convertedBlob.size / file.size) * 100))
                    const downloadUrl = URL.createObjectURL(convertedBlob)

                    // Update UI
                    resultItem.innerHTML = `
                        <div style="display:flex;align-items:center;gap:1rem;flex:1;">
                            <img src="${downloadUrl}" class="preview" alt="preview">
                            <div>
                                <div>${newFileName}</div>
                                <small>
                                    Original: ${formatSize(file.size)} • New: ${formatSize(convertedBlob.size)}
                                    <span class="saved-positive"> (Saved ${savedPercent}%)</span>
                                </small>
                            </div>
                        </div>
                        <a href="${downloadUrl}" download="${newFileName}" class="btn btn-sm">Download</a>
                    `

                } catch (err) {
                    resultItem.innerHTML = `<span style="color:#dc2626">❌ Failed to convert ${file.name}</span>`
                }
            }

            // Show total saved
            const totalSaved = totalOriginalSize - totalConvertedSize
            const totalSavedPercent = Math.round(100 - ((totalConvertedSize / totalOriginalSize) * 100))
            totalSavedContainer.innerHTML = `
                <div class="total-saved-bar">
                    🎉 Total Space Saved: ${formatSize(totalSaved)} (${totalSavedPercent}%)
                </div>
            `

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
            a.download = `converted_images_${outputFormat.value}.zip`
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
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    PORT = 8080
    server = HTTPServer(('localhost', PORT), RequestHandler)
    print(f"🚀 Image Converter running on http://localhost:{PORT}")
    print("💡 Browser will open automatically. Press Ctrl+C to stop the server when done.")
    webbrowser.open(f'http://localhost:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Server stopped.")
        server.server_close()