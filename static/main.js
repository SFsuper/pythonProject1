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

        const response = await fetch('/detect', {
            method: 'POST',
            body: formData,
        });

        updateProgress(100);

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error + "11111" || 'Ошибка сервера');
        }

        const data = await response.json();
        showResult(data, file);

    } catch (error) {
        showError(error.message + "1111");
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

        const response = await fetch(url);
        updateProgress(50);

        if (!response.ok) throw new Error('Ошибка загрузки изображения');

        const blob = await response.blob();
        updateProgress(80);

        await processImage(blob);

    } catch (error) {
        showError(error.message + "222");
    } finally {
        setTimeout(() => {
            progressContainer.classList.add('d-none');
        }, 1000)
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();

    window.loadFromUrl = loadFromUrl;
});
