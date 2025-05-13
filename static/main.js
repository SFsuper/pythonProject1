const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const urlInput = document.getElementById('urlInput');
const resultDiv = document.getElementById('result');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');

function initEventListeners() {
    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) processImage(e.target.files[0]);
    });

    // Drag and drop
    ['dragover', 'dragenter'].forEach(event => {
        dropZone.addEventListener(event, highlightDropZone);
    });

    ['dragleave', 'dragend', 'drop'].forEach(event => {
        dropZone.addEventListener(event, unhighlightDropZone);
    });

    dropZone.addEventListener('drop', handleDrop);

    // Load from URL
    urlInput.addEventListener('change', () => loadFromUrl());
}

function highlightDropZone(e) {
    e.preventDefault();
    dropZone.classList.add('border-primary', 'bg-light');
}

function unhighlightDropZone(e) {
    e.preventDefault();
    dropZone.classList.remove('border-primary', 'bg-light');
}

function handleDrop(e) {
    e.preventDefault();
    if (e.dataTransfer.files.length) {
        processImage(e.dataTransfer.files[0]);
    }
}

function updateProgress(percent) {
    progressBar.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
}

async function processImage(file) {
    if (!file.type.match('image.*')) {
        showError('Только изображения (JPG/PNG)');
        return;
    }

    try {
        progressContainer.classList.remove('d-none');
        updateProgress(0);

        const formData = new FormData();
        formData.append('file', file);

        const API_URL = window.location.origin;
        const response = await fetch(`${API_URL}/detect`, {
            method: 'POST',
            body: formData,
        });

        updateProgress(100);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || 'Ошибка сервера');
        }

        const data = await response.json();
        showResult(data, file);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
    } finally {
        setTimeout(() => {
            progressContainer.classList.add('d-none');
        }, 1000);
    }
}

function showResult(data, file) {
    if (data.error) {
        showError(data.error);
        return;
    }

    let html = '<div class="alert alert-success">';
    html += `
        <h5><i class="bi bi-check-circle"></i> Результат:</h5>
        <p><strong>Порода:</strong> ${data.breed}</p>
        <p><strong>Уверенность:</strong> ${data.confidence.toFixed(2)}%</p>
        <hr>
    `;
    html += '</div>';

    if (file) {
        html += `
            <div class="position-relative">
                <img src="${URL.createObjectURL(file)}"
                     class="img-fluid rounded mt-3"
                     style="max-height: 300px;">
            </div>
        `;
    }

    resultDiv.innerHTML = html;
}

function showError(message) {
    resultDiv.innerHTML = `
        <div class="alert alert-danger">
            <i class="bi bi-exclamation-triangle"></i> ${message}
        </div>
    `;
}

async function loadFromUrl() {
    const url = urlInput.value.trim();
    if (!url) {
        showError('Введите URL изображения');
        return;
    }

    try {
        progressContainer.classList.remove('d-none');
        updateProgress(0);

        // Отправляем URL на сервер для обработки
        const API_URL = window.location.origin;
        const response = await fetch(`${API_URL}/detect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image_url: url }),
        });

        updateProgress(100);

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Ошибка сервера');
        }

        const data = await response.json();
        showResult(data);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
    } finally {
        setTimeout(() => {
            progressContainer.classList.add('d-none');
        }, 1000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
});
