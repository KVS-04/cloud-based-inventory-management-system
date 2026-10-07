/**
 * DataTables - Client-side table search, sort, pagination
 */

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.data-table').forEach(table => initDataTable(table));
});

function initDataTable(table) {
    const wrapper = table.closest('.table-wrapper') || table.parentElement;
    const searchInput = wrapper.querySelector('.table-search') || document.querySelector(`[data-table-search="${table.id}"]`);
    const perPageSelect = wrapper.querySelector('.per-page-select');
    const paginationContainer = wrapper.querySelector('.table-pagination') || document.querySelector(`[data-table-pagination="${table.id}"]`);
    const countDisplay = wrapper.querySelector('.table-count');

    const tbody = table.querySelector('tbody');
    if (!tbody) return;

    let allRows = Array.from(tbody.querySelectorAll('tr'));
    let filteredRows = [...allRows];
    let currentPage = 1;
    let perPage = perPageSelect ? parseInt(perPageSelect.value) : 25;

    // Search
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const query = searchInput.value.toLowerCase();
            filteredRows = allRows.filter(row => row.textContent.toLowerCase().includes(query));
            currentPage = 1;
            renderTable();
        });
    }

    // Per page selector
    if (perPageSelect) {
        perPageSelect.addEventListener('change', () => {
            perPage = parseInt(perPageSelect.value);
            currentPage = 1;
            renderTable();
        });
    }

    // Column sorting
    table.querySelectorAll('th[data-sort]').forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => {
            const col = th.cellIndex;
            const isAsc = th.classList.contains('sort-asc');
            table.querySelectorAll('th').forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
            th.classList.add(isAsc ? 'sort-desc' : 'sort-asc');

            filteredRows.sort((a, b) => {
                const aVal = a.cells[col]?.textContent.trim() || '';
                const bVal = b.cells[col]?.textContent.trim() || '';
                const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return isAsc ? bNum - aNum : aNum - bNum;
                }
                return isAsc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
            });
            currentPage = 1;
            renderTable();
        });
    });

    // Bulk select
    const selectAll = table.querySelector('.select-all');
    if (selectAll) {
        selectAll.addEventListener('change', () => {
            const visible = getVisibleRows();
            visible.forEach(row => {
                const cb = row.querySelector('.row-select');
                if (cb) cb.checked = selectAll.checked;
            });
        });
    }

    function getVisibleRows() {
        const start = (currentPage - 1) * perPage;
        return filteredRows.slice(start, start + perPage);
    }

    function renderTable() {
        const totalPages = Math.ceil(filteredRows.length / perPage);
        const start = (currentPage - 1) * perPage;
        const visible = filteredRows.slice(start, start + perPage);

        // Show/hide rows
        allRows.forEach(row => row.style.display = 'none');
        visible.forEach(row => row.style.display = '');

        // Update count
        if (countDisplay) {
            const end = Math.min(start + perPage, filteredRows.length);
            countDisplay.textContent = `Showing ${filteredRows.length ? start+1 : 0}-${end} of ${filteredRows.length} entries`;
        }

        // Render pagination
        if (paginationContainer) {
            let html = '<nav><ul class="pagination pagination-sm mb-0">';
            html += `<li class="page-item ${currentPage <= 1 ? 'disabled' : ''}"><a class="page-link" href="#" data-page="${currentPage-1}">&laquo;</a></li>`;
            for (let i = 1; i <= totalPages; i++) {
                if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
                    html += `<li class="page-item ${i === currentPage ? 'active' : ''}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
                } else if (i === currentPage - 3 || i === currentPage + 3) {
                    html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
                }
            }
            html += `<li class="page-item ${currentPage >= totalPages ? 'disabled' : ''}"><a class="page-link" href="#" data-page="${currentPage+1}">&raquo;</a></li>`;
            html += '</ul></nav>';
            paginationContainer.innerHTML = html;

            paginationContainer.querySelectorAll('[data-page]').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const page = parseInt(link.dataset.page);
                    if (page >= 1 && page <= totalPages) {
                        currentPage = page;
                        renderTable();
                    }
                });
            });
        }
    }

    renderTable();
}
