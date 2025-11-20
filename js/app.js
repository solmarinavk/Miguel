/**
 * CALLE - CSV to Excel Converter
 * Modern JavaScript Application
 */

// ========================================
// State Management
// ========================================
const AppState = {
    currentFile: null,
    csvData: null,
    parsedData: null,
    delimiter: ',',
    fileName: '',
};

// ========================================
// DOM Elements
// ========================================
const elements = {
    dropZone: document.getElementById('dropZone'),
    fileInput: document.getElementById('fileInput'),
    delimiterSection: document.getElementById('delimiterSection'),
    processBtn: document.getElementById('processBtn'),
    uploadSection: document.getElementById('uploadSection'),
    previewSection: document.getElementById('previewSection'),
    dataTable: document.getElementById('dataTable'),
    tableContainer: document.getElementById('tableContainer'),
    fileInfo: document.getElementById('fileInfo'),
    tableStats: document.getElementById('tableStats'),
    downloadBtn: document.getElementById('downloadBtn'),
    uploadNewBtn: document.getElementById('uploadNewBtn'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    customDelimiter: document.getElementById('customDelimiter'),
};

// ========================================
// Utility Functions
// ========================================

/**
 * Show loading overlay
 */
function showLoading() {
    elements.loadingOverlay.style.display = 'flex';
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    elements.loadingOverlay.style.display = 'none';
}

/**
 * Format file size to human readable
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Get selected delimiter
 */
function getSelectedDelimiter() {
    const selectedRadio = document.querySelector('input[name="delimiter"]:checked');
    if (selectedRadio.value === 'custom') {
        const customValue = elements.customDelimiter.value;
        return customValue || ',';
    }
    return selectedRadio.value === '\\t' ? '\t' : selectedRadio.value;
}

/**
 * Parse CSV data
 */
function parseCSV(csvText, delimiter) {
    const lines = csvText.split(/\r?\n/).filter(line => line.trim() !== '');
    const result = [];

    for (let line of lines) {
        const row = [];
        let current = '';
        let inQuotes = false;

        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            const nextChar = line[i + 1];

            if (char === '"') {
                if (inQuotes && nextChar === '"') {
                    current += '"';
                    i++;
                } else {
                    inQuotes = !inQuotes;
                }
            } else if (char === delimiter && !inQuotes) {
                row.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }
        row.push(current.trim());
        result.push(row);
    }

    return result;
}

/**
 * Render data table
 */
function renderTable(data) {
    if (!data || data.length === 0) {
        elements.dataTable.innerHTML = '<tr><td>No hay datos para mostrar</td></tr>';
        return;
    }

    const headers = data[0];
    const rows = data.slice(1);

    // Create table header
    let tableHTML = '<thead><tr>';
    headers.forEach(header => {
        tableHTML += `<th>${escapeHtml(header)}</th>`;
    });
    tableHTML += '</tr></thead>';

    // Create table body
    tableHTML += '<tbody>';
    rows.forEach(row => {
        tableHTML += '<tr>';
        row.forEach(cell => {
            tableHTML += `<td>${escapeHtml(cell)}</td>`;
        });
        tableHTML += '</tr>';
    });
    tableHTML += '</tbody>';

    elements.dataTable.innerHTML = tableHTML;

    // Update stats
    updateTableStats(headers.length, rows.length);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Update table statistics
 */
function updateTableStats(columns, rows) {
    elements.tableStats.innerHTML = `
        <div>Total de columnas: <span>${columns}</span></div>
        <div>Total de filas: <span>${rows}</span></div>
        <div>Total de celdas: <span>${columns * rows}</span></div>
    `;
}

/**
 * Update file information display
 */
function updateFileInfo(fileName, fileSize) {
    elements.fileInfo.innerHTML = `
        <span>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
            ${escapeHtml(fileName)}
        </span>
        <span>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M14,17H7V15H14M17,13H7V11H17M17,9H7V7H17M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3Z"/>
            </svg>
            ${fileSize}
        </span>
    `;
}

// ========================================
// File Handling
// ========================================

/**
 * Handle file selection
 */
function handleFileSelect(file) {
    if (!file) return;

    // Validate file type
    const validTypes = ['text/csv', 'text/plain', 'application/vnd.ms-excel'];
    const validExtensions = ['.csv', '.txt'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

    if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
        alert('Por favor, selecciona un archivo CSV o TXT válido.');
        return;
    }

    // Store file information
    AppState.currentFile = file;
    AppState.fileName = file.name;

    // Read file content
    const reader = new FileReader();
    reader.onload = function(e) {
        AppState.csvData = e.target.result;
        elements.delimiterSection.style.display = 'block';

        // Scroll to delimiter section
        elements.delimiterSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };
    reader.onerror = function() {
        alert('Error al leer el archivo. Por favor, intenta nuevamente.');
    };
    reader.readAsText(file);
}

/**
 * Process CSV with selected delimiter
 */
function processCSV() {
    if (!AppState.csvData) {
        alert('Por favor, selecciona un archivo CSV primero.');
        return;
    }

    showLoading();

    // Use setTimeout to allow UI to update
    setTimeout(() => {
        try {
            AppState.delimiter = getSelectedDelimiter();
            AppState.parsedData = parseCSV(AppState.csvData, AppState.delimiter);

            if (AppState.parsedData.length === 0) {
                throw new Error('El archivo CSV está vacío o el delimitador es incorrecto.');
            }

            // Show preview section
            elements.uploadSection.style.display = 'none';
            elements.previewSection.style.display = 'block';

            // Render table
            renderTable(AppState.parsedData);

            // Update file info
            updateFileInfo(AppState.fileName, formatFileSize(AppState.currentFile.size));

            // Scroll to preview
            elements.previewSection.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            alert('Error al procesar el archivo: ' + error.message);
            console.error('Error:', error);
        } finally {
            hideLoading();
        }
    }, 100);
}

/**
 * Convert to Excel and download
 */
function downloadExcel() {
    if (!AppState.parsedData) {
        alert('No hay datos para descargar.');
        return;
    }

    showLoading();

    setTimeout(() => {
        try {
            // Create workbook
            const workbook = XLSX.utils.book_new();

            // Convert data to worksheet
            const worksheet = XLSX.utils.aoa_to_sheet(AppState.parsedData);

            // Add worksheet to workbook
            XLSX.utils.book_append_sheet(workbook, worksheet, 'Datos');

            // Generate Excel file
            const fileName = AppState.fileName.replace(/\.[^/.]+$/, '') + '.xlsx';
            XLSX.writeFile(workbook, fileName);

        } catch (error) {
            alert('Error al generar el archivo Excel: ' + error.message);
            console.error('Error:', error);
        } finally {
            hideLoading();
        }
    }, 100);
}

/**
 * Reset to upload new file
 */
function resetUpload() {
    // Reset state
    AppState.currentFile = null;
    AppState.csvData = null;
    AppState.parsedData = null;
    AppState.delimiter = ',';
    AppState.fileName = '';

    // Reset UI
    elements.fileInput.value = '';
    elements.delimiterSection.style.display = 'none';
    elements.uploadSection.style.display = 'block';
    elements.previewSection.style.display = 'none';

    // Reset delimiter selection
    document.querySelector('input[name="delimiter"][value=","]').checked = true;
    elements.customDelimiter.value = '';

    // Scroll to top
    elements.uploadSection.scrollIntoView({ behavior: 'smooth' });
}

// ========================================
// Event Listeners
// ========================================

// Drop zone click
elements.dropZone.addEventListener('click', () => {
    elements.fileInput.click();
});

// File input change
elements.fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    handleFileSelect(file);
});

// Drag and drop events
elements.dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.dropZone.classList.add('drag-over');
});

elements.dropZone.addEventListener('dragleave', () => {
    elements.dropZone.classList.remove('drag-over');
});

elements.dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.dropZone.classList.remove('drag-over');

    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
});

// Process button
elements.processBtn.addEventListener('click', processCSV);

// Download button
elements.downloadBtn.addEventListener('click', downloadExcel);

// Upload new button
elements.uploadNewBtn.addEventListener('click', resetUpload);

// Custom delimiter input
elements.customDelimiter.addEventListener('focus', () => {
    document.querySelector('input[name="delimiter"][value="custom"]').checked = true;
});

// Delimiter radio change - hide/show custom input
document.querySelectorAll('input[name="delimiter"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'custom') {
            elements.customDelimiter.focus();
        }
    });
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + O to open file
    if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
        e.preventDefault();
        elements.fileInput.click();
    }

    // Ctrl/Cmd + S to download (if data is available)
    if ((e.ctrlKey || e.metaKey) && e.key === 's' && AppState.parsedData) {
        e.preventDefault();
        downloadExcel();
    }
});

// ========================================
// Initialization
// ========================================
console.log('🎉 Calle - CSV to Excel Converter loaded successfully!');
console.log('💡 Keyboard shortcuts:');
console.log('   Ctrl/Cmd + O: Open file');
console.log('   Ctrl/Cmd + S: Download Excel');
