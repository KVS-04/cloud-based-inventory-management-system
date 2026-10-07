/**
 * Barcode Scanner - Uses QuaggaJS for camera-based scanning
 */

function initBarcodeScanner() {
    const scannerDiv = document.getElementById('barcode-scanner');
    if (!scannerDiv) return;

    const startBtn = document.getElementById('startScanner');
    const stopBtn = document.getElementById('stopScanner');
    const manualInput = document.getElementById('manualBarcode');
    const lookupBtn = document.getElementById('lookupBarcode');
    const resultCard = document.getElementById('scanResult');

    let scanning = false;

    // Load QuaggaJS dynamically
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/@ericblade/quagga2@1.8.4/dist/quagga.min.js';
    script.onload = () => { console.log('QuaggaJS loaded'); };
    document.head.appendChild(script);

    if (startBtn) {
        startBtn.addEventListener('click', startScanning);
    }
    if (stopBtn) {
        stopBtn.addEventListener('click', stopScanning);
    }
    if (lookupBtn) {
        lookupBtn.addEventListener('click', () => {
            const code = manualInput.value.trim();
            if (code) lookupBarcode(code);
        });
    }
    if (manualInput) {
        manualInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const code = manualInput.value.trim();
                if (code) lookupBarcode(code);
            }
        });
    }

    function startScanning() {
        if (typeof Quagga === 'undefined') {
            showToast('Barcode scanner library not loaded yet. Please wait.', 'warning');
            return;
        }
        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: scannerDiv,
                constraints: {
                    width: { ideal: 640 }, height: { ideal: 480 },
                    facingMode: "environment"
                }
            },
            decoder: {
                readers: ["ean_reader", "ean_8_reader", "upc_reader", "upc_e_reader", "code_128_reader", "code_39_reader"]
            },
            locate: true
        }, (err) => {
            if (err) {
                console.error('Scanner error:', err);
                showToast('Unable to access camera. Please check permissions.', 'danger');
                return;
            }
            Quagga.start();
            scanning = true;
            if (startBtn) startBtn.style.display = 'none';
            if (stopBtn) stopBtn.style.display = 'inline-block';
            scannerDiv.classList.add('scanning');
        });

        Quagga.onDetected((result) => {
            const code = result.codeResult.code;
            playBeep();
            stopScanning();
            if (manualInput) manualInput.value = code;
            lookupBarcode(code);
        });
    }

    function stopScanning() {
        if (typeof Quagga !== 'undefined' && scanning) {
            Quagga.stop();
            scanning = false;
        }
        if (startBtn) startBtn.style.display = 'inline-block';
        if (stopBtn) stopBtn.style.display = 'none';
        scannerDiv.classList.remove('scanning');
        scannerDiv.innerHTML = '<div class="text-center text-muted py-5"><i class="bi bi-upc-scan" style="font-size:3rem;opacity:0.3;"></i><p class="mt-2">Click "Start Scanner" to begin</p></div>';
    }

    async function lookupBarcode(code) {
        try {
            const response = await fetch('/api/barcode/lookup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                body: JSON.stringify({ barcode: code })
            });
            const data = await response.json();
            if (data.success && data.data) {
                displayProduct(data.data);
            } else {
                showToast('Product not found for barcode: ' + code, 'warning');
                if (resultCard) resultCard.style.display = 'none';
            }
        } catch (err) {
            showToast('Error looking up barcode', 'danger');
        }
    }

    function displayProduct(product) {
        if (!resultCard) return;
        resultCard.style.display = 'block';
        resultCard.innerHTML = `
            <div class="card animate-slide-in">
                <div class="card-body">
                    <div class="d-flex align-items-center gap-3 mb-3">
                        <img src="${product.image_url || '/static/img/default-product.png'}" class="product-thumb" style="width:60px;height:60px;" alt="">
                        <div>
                            <h5 class="mb-1">${product.name}</h5>
                            <span class="text-muted">SKU: ${product.sku}</span> &bull;
                            <span class="text-muted">Barcode: ${product.barcode}</span>
                        </div>
                    </div>
                    <div class="row g-2 mb-3">
                        <div class="col-4"><small class="text-muted">Price</small><div class="fw-bold">${formatCurrency(product.price)}</div></div>
                        <div class="col-4"><small class="text-muted">Category</small><div class="fw-bold">${product.category}</div></div>
                        <div class="col-4"><small class="text-muted">Unit</small><div class="fw-bold">${product.unit}</div></div>
                    </div>
                    <hr>
                    <h6>Quick Stock Adjustment</h6>
                    <form id="quickAdjustForm" class="row g-2">
                        <input type="hidden" name="product_id" value="${product.id}">
                        <div class="col-12 mb-2">
                            <select class="form-select form-select-sm" name="warehouse_id" required>
                                <option value="WH-MAIN">Main Warehouse</option>
                                <option value="WH-STORE">Retail Store</option>
                            </select>
                        </div>
                        <div class="col-4">
                            <select class="form-select form-select-sm" name="movement_type">
                                <option value="stock_in">Stock In</option>
                                <option value="stock_out">Stock Out</option>
                                <option value="adjustment">Adjustment</option>
                            </select>
                        </div>
                        <div class="col-4">
                            <input type="number" class="form-control form-control-sm" name="quantity" placeholder="Qty" min="1" required>
                        </div>
                        <div class="col-4">
                            <button type="submit" class="btn btn-primary btn-sm w-100">Adjust</button>
                        </div>
                    </form>
                </div>
            </div>`;

        // Handle quick adjust form
        const form = document.getElementById('quickAdjustForm');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                try {
                    await apiCall('/api/inventory/adjust', 'POST', Object.fromEntries(formData));
                    showToast('Stock adjusted successfully!', 'success');
                } catch(err) {}
            });
        }
    }

    function playBeep() {
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();
            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            oscillator.frequency.value = 1000;
            oscillator.type = 'sine';
            gainNode.gain.value = 0.3;
            oscillator.start();
            setTimeout(() => oscillator.stop(), 150);
        } catch(e) {}
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBarcodeScanner);
} else {
    initBarcodeScanner();
}
