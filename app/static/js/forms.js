/**
 * Form handling - Validation, image upload, dynamic line items
 */

document.addEventListener('DOMContentLoaded', () => {
    initImageUpload();
    initDynamicLineItems();
    initFormValidation();
});

function initImageUpload() {
    document.querySelectorAll('.upload-area').forEach(area => {
        const input = area.querySelector('input[type="file"]') || document.getElementById(area.dataset.input);
        const preview = area.querySelector('.upload-preview') || document.getElementById(area.dataset.preview);

        if (!input) return;

        area.addEventListener('click', () => input.click());

        area.addEventListener('dragover', (e) => { e.preventDefault(); area.classList.add('dragover'); });
        area.addEventListener('dragleave', () => area.classList.remove('dragover'));
        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                showPreview(input.files[0], preview, area);
            }
        });

        input.addEventListener('change', () => {
            if (input.files.length) showPreview(input.files[0], preview, area);
        });
    });
}

function showPreview(file, preview, area) {
    if (!file || !file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        if (preview) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        }
        if (area) {
            area.style.backgroundImage = `url(${e.target.result})`;
            area.style.backgroundSize = 'cover';
            area.style.backgroundPosition = 'center';
            const text = area.querySelector('.upload-text');
            if (text) text.style.display = 'none';
        }
    };
    reader.readAsDataURL(file);
}

function initDynamicLineItems() {
    const addBtn = document.getElementById('addLineItem');
    const container = document.getElementById('lineItemsContainer');
    if (!addBtn || !container) return;

    addBtn.addEventListener('click', () => {
        const index = container.querySelectorAll('.line-item').length;
        const row = document.createElement('div');
        row.className = 'line-item row g-2 mb-2 align-items-end';
        row.innerHTML = `
            <div class="col-md-4">
                <input type="text" class="form-control form-control-sm" name="items[${index}][product_name]" placeholder="Product" required>
            </div>
            <div class="col-md-2">
                <input type="number" class="form-control form-control-sm item-qty" name="items[${index}][quantity]" placeholder="Qty" min="1" required>
            </div>
            <div class="col-md-2">
                <input type="number" class="form-control form-control-sm item-price" name="items[${index}][unit_price]" placeholder="Price" step="0.01" min="0" required>
            </div>
            <div class="col-md-2">
                <input type="text" class="form-control form-control-sm item-total" name="items[${index}][total]" placeholder="Total" readonly>
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-outline-danger btn-sm remove-line-item"><i class="bi bi-trash"></i></button>
            </div>`;
        container.appendChild(row);
        bindLineItemEvents(row);
    });

    // Bind existing rows
    container.querySelectorAll('.line-item').forEach(row => bindLineItemEvents(row));
}

function bindLineItemEvents(row) {
    const qty = row.querySelector('.item-qty');
    const price = row.querySelector('.item-price');
    const total = row.querySelector('.item-total');
    const remove = row.querySelector('.remove-line-item');

    const calc = () => {
        if (qty && price && total) {
            total.value = (parseFloat(qty.value || 0) * parseFloat(price.value || 0)).toFixed(2);
        }
        updateOrderTotals();
    };

    if (qty) qty.addEventListener('input', calc);
    if (price) price.addEventListener('input', calc);
    if (remove) remove.addEventListener('click', () => { row.remove(); updateOrderTotals(); });
}

function updateOrderTotals() {
    const totals = document.querySelectorAll('.item-total');
    let subtotal = 0;
    totals.forEach(t => subtotal += parseFloat(t.value || 0));

    const subtotalEl = document.getElementById('subtotal');
    const taxEl = document.getElementById('taxAmount');
    const grandTotalEl = document.getElementById('grandTotal');

    if (subtotalEl) subtotalEl.textContent = subtotal.toFixed(2);
    const tax = parseFloat(document.getElementById('tax')?.value || 0);
    const shipping = parseFloat(document.getElementById('shipping')?.value || 0);
    if (taxEl) taxEl.textContent = tax.toFixed(2);
    if (grandTotalEl) grandTotalEl.textContent = (subtotal + tax + shipping).toFixed(2);
}

function initFormValidation() {
    document.querySelectorAll('form[data-validate]').forEach(form => {
        form.addEventListener('submit', (e) => {
            let valid = true;
            form.querySelectorAll('[required]').forEach(input => {
                if (!input.value.trim()) {
                    input.classList.add('is-invalid');
                    valid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            if (!valid) { e.preventDefault(); showToast('Please fill in all required fields.', 'warning'); }
        });
    });
}
