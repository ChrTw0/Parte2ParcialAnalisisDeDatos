document.addEventListener('DOMContentLoaded', () => {

    // --- State Management ---
    let currentPage = 1;
    const limit = 20;
    let currentSort = { by: 'Banco', order: 'asc' };
    let currentItems = [];
    let comparisonList = [];

    // --- DOM Elements ---
    const elements = {
        bancoFilter: document.getElementById('banco-filter'),
        tipoFilter: document.getElementById('tipo-filter'),
        monedaFilter: document.getElementById('moneda-filter'),
        tasaMnMin: document.getElementById('tasa-mn-min'),
        tasaMnMax: document.getElementById('tasa-mn-max'),
        tasaMeMin: document.getElementById('tasa-me-min'),
        tasaMeMax: document.getElementById('tasa-me-max'),
        productoSearch: document.getElementById('producto-search'),
        conceptoSearch: document.getElementById('concepto-search'),
        applyFiltersBtn: document.getElementById('apply-filters-btn'),
        resetFiltersBtn: document.getElementById('reset-filters-btn'),
        exportCsvBtn: document.getElementById('export-csv-btn'),
        compareBtnContainer: document.getElementById('compare-button-container'),
        compareBtn: document.getElementById('compare-btn'),
        statsCards: document.getElementById('stats-cards'),
        tableHead: document.getElementById('data-table-head'),
        tableBody: document.getElementById('data-table-body'),
        paginationControls: document.getElementById('pagination-controls'),
    };

    // --- API Calls ---
    const api = {
        async get(endpoint) {
            const response = await fetch(endpoint);
            if (!response.ok) {
                console.error(`Error fetching ${endpoint}: ${response.statusText}`);
                return null;
            }
            return response.json();
        }
    };

    // --- Rendering Functions ---
    function renderFilterOptions({ bancos, tipos, monedas }) {
        const populate = (select, options) => {
            select.innerHTML = '<option value="">Todos</option>';
            options.forEach(opt => {
                select.innerHTML += `<option value="${opt}">${opt}</option>`;
            });
        };
        populate(elements.bancoFilter, bancos);
        populate(elements.tipoFilter, tipos);
        populate(elements.monedaFilter, monedas);
    }

    function renderStats({ total_registros, bancos_count, tasa_promedio_mn, tasa_promedio_me }) {
        elements.statsCards.innerHTML = `
            <div class="col-md-3"><div class="card text-center p-3"><div class="card-body"><h5>Total Registros</h5><p class="fs-4">${total_registros}</p></div></div></div>
            <div class="col-md-3"><div class="card text-center p-3"><div class="card-body"><h5>Bancos</h5><p class="fs-4">${bancos_count}</p></div></div></div>
            <div class="col-md-3"><div class="card text-center p-3"><div class="card-body"><h5>Tasa Prom. (MN)</h5><p class="fs-4">${tasa_promedio_mn || 'N/A'}%</p></div></div></div>
            <div class="col-md-3"><div class="card text-center p-3"><div class="card-body"><h5>Tasa Prom. (ME)</h5><p class="fs-4">${tasa_promedio_me || 'N/A'}%</p></div></div></div>
        `;
    }

    function renderTable(items) {
        if (!items || items.length === 0) {
            elements.tableBody.innerHTML = '<tr><td colspan="9" class="text-center">No se encontraron datos.</td></tr>';
            return;
        }

        elements.tableBody.innerHTML = items.map((item, index) => `
            <tr>
                <td><input class="form-check-input compare-checkbox" type="checkbox" data-item-index="${index}"></td>
                <td>${item.Banco}</td>
                <td>${item.Producto_Nombre || ''}</td>
                <td>${item.Concepto || ''}</td>
                <td><span class="badge ${getTipoBadge(item.Tipo)}">${item.Tipo || ''}</span></td>
                <td><span class="badge ${getMonedaBadge(item.Moneda)}">${item.Moneda || ''}</span></td>
                <td>${formatValue(item.Tasa_Porcentaje_MN, '%') || formatValue(item.Monto_Fijo_MN, 'S/') || ''}</td>
                <td>${formatValue(item.Tasa_Porcentaje_ME, '%') || formatValue(item.Monto_Fijo_ME, '$') || ''}</td>
                <td>
                    <button class="btn btn-sm btn-info view-details-btn" data-index="${index}">Detalle</button>
                </td>
            </tr>
        `).join('');
    }

    function renderPagination(total_items, total_pages, current_page) {
        if (total_pages <= 1) {
            elements.paginationControls.innerHTML = '';
            return;
        }

        let paginationHTML = '<ul class="pagination justify-content-center">';
        paginationHTML += `<li class="page-item ${current_page === 1 ? 'disabled' : ''}"><a class="page-link" href="#" data-page="${current_page - 1}">Anterior</a></li>`;

        for (let i = 1; i <= total_pages; i++) {
            if (i === current_page) {
                paginationHTML += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else if (i <= 2 || i >= total_pages - 1 || (i >= current_page - 1 && i <= current_page + 1)) {
                paginationHTML += `<li class="page-item"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
            } else if (i === 3 || i === total_pages - 2) {
                paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        paginationHTML += `<li class="page-item ${current_page === total_pages ? 'disabled' : ''}"><a class="page-link" href="#" data-page="${current_page + 1}">Siguiente</a></li>`;
        paginationHTML += '</ul>';
        elements.paginationControls.innerHTML = paginationHTML;
    }
    
    function renderTableHeaders() {
        const headers = [
            { key: 'compare', label: '<i class="bi bi-check-square"></i>' },
            { key: 'Banco', label: 'Banco' },
            { key: 'Producto_Nombre', label: 'Producto' },
            { key: 'Concepto', label: 'Concepto' },
            { key: 'Tipo', label: 'Tipo' },
            { key: 'Moneda', label: 'Moneda' },
            { key: 'Valor (MN)', label: 'Valor (MN)' },
            { key: 'Valor (ME)', label: 'Valor (ME)' },
            { key: 'acciones', label: 'Acciones' },
        ];

        elements.tableHead.innerHTML = `<tr>${headers.map(h => `
            <th class="${h.key !== 'acciones' && h.key !== 'compare' ? 'sortable-header' : ''}" data-sort-by="${h.key}">${h.label} ${h.key !== 'acciones' && h.key !== 'compare' ? '<i class="bi bi-arrow-down-up"></i>' : ''}</th>
        `).join('')}</tr>`;
    }
    
    // --- Helper Functions ---
    function getTipoBadge(tipo) {
        const map = { 'TASA': 'bg-primary', 'COMISION': 'bg-warning text-dark', 'GASTO': 'bg-secondary', 'SEGURO': 'bg-info text-dark' };
        return map[tipo] || 'bg-light text-dark';
    }

    function getMonedaBadge(moneda) {
        const map = { 'MN': 'bg-success', 'ME': 'bg-danger', 'AMBAS': 'bg-dark' };
        return map[moneda] || 'bg-light text-dark';
    }

    function formatValue(value, unit) {
        if (value === null || value === undefined) return null;
        return unit === '%' ? `${value}%` : `${unit} ${value.toFixed(2)}`;
    }

    // --- Main Data Fetching Logic ---
    async function fetchData() {
        const skip = (currentPage - 1) * limit;
        const params = new URLSearchParams({
            skip,
            limit,
            sort_by: currentSort.by,
            sort_order: currentSort.order,
        });

        const filters = {
            banco: elements.bancoFilter.value,
            tipo: elements.tipoFilter.value,
            moneda: elements.monedaFilter.value,
            producto: elements.productoSearch.value,
            concepto: elements.conceptoSearch.value,
            tasa_mn_gte: elements.tasaMnMin.value,
            tasa_mn_lte: elements.tasaMnMax.value,
            tasa_me_gte: elements.tasaMeMin.value,
            tasa_me_lte: elements.tasaMeMax.value,
        };

        for (const [key, value] of Object.entries(filters)) {
            if (value) params.append(key, value);
        }

        const data = await api.get(`/api/v1/tarifarios?${params.toString()}`);
        if (data) {
            currentItems = data.items;
            renderTable(data.items);
            renderPagination(data.total_items, data.total_pages, data.current_page);
        }
    }

    // --- Event Listeners ---
    elements.applyFiltersBtn.addEventListener('click', () => {
        currentPage = 1; // Reset to first page on new filter
        fetchData();
    });

    elements.resetFiltersBtn.addEventListener('click', () => {
        elements.bancoFilter.value = '';
        elements.tipoFilter.value = '';
        elements.monedaFilter.value = '';
        elements.tasaMnMin.value = '';
        elements.tasaMnMax.value = '';
        elements.tasaMeMin.value = '';
        elements.tasaMeMax.value = '';
        elements.productoSearch.value = '';
        elements.conceptoSearch.value = '';
        currentPage = 1;
        fetchData();
    });

    elements.exportCsvBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const params = new URLSearchParams({
            sort_by: currentSort.by,
            sort_order: currentSort.order,
        });

        const filters = {
            banco: elements.bancoFilter.value,
            tipo: elements.tipoFilter.value,
            moneda: elements.monedaFilter.value,
            producto: elements.productoSearch.value,
            concepto: elements.conceptoSearch.value,
            tasa_mn_gte: elements.tasaMnMin.value,
            tasa_mn_lte: elements.tasaMnMax.value,
            tasa_me_gte: elements.tasaMeMin.value,
            tasa_me_lte: elements.tasaMeMax.value,
        };

        for (const [key, value] of Object.entries(filters)) {
            if (value) params.append(key, value);
        }

        window.location.href = `/api/v1/export/csv?${params.toString()}`;
    });

    elements.paginationControls.addEventListener('click', (e) => {
        if (e.target.tagName === 'A' && e.target.dataset.page) {
            e.preventDefault();
            currentPage = parseInt(e.target.dataset.page, 10);
            fetchData();
        }
    });
    
    elements.tableHead.addEventListener('click', (e) => {
        const header = e.target.closest('.sortable-header');
        if (header) {
            const sortBy = header.dataset.sortBy;
            if (currentSort.by === sortBy) {
                currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.by = sortBy;
                currentSort.order = 'asc';
            }
            fetchData();
        }
    });

    elements.tableBody.addEventListener('click', (e) => {
        // Logic for Details Button
        if (e.target.classList.contains('view-details-btn')) {
            const index = e.target.dataset.index;
            const item = currentItems[index];
            if (!item) return;

            const modal = new bootstrap.Modal(document.getElementById('details-modal'));
            const modalTitle = document.getElementById('details-modal-title');
            const modalBody = document.getElementById('details-modal-body');

            modalTitle.textContent = `Detalle: ${item.Concepto || item.Producto_Nombre}`;

            let detailsHtml = '<dl class="row">';
            for (const [key, value] of Object.entries(item)) {
                if (value !== null && value !== '') {
                    detailsHtml += `
                        <dt class="col-sm-4">${key.replace(/_/g, ' ')}</dt>
                        <dd class="col-sm-8">${value}</dd>
                    `;
                }
            }
            detailsHtml += '</dl>';
            modalBody.innerHTML = detailsHtml;
            modal.show();
        }

        // Logic for Compare Checkbox
        if (e.target.classList.contains('compare-checkbox')) {
            const index = parseInt(e.target.dataset.itemIndex, 10);
            const item = currentItems[index];
            if (!item) return;

            const isChecked = e.target.checked;
            if (isChecked) {
                // Add to list if not already there
                if (!comparisonList.some(compItem => JSON.stringify(compItem) === JSON.stringify(item))) {
                    comparisonList.push(item);
                }
            } else {
                // Remove from list
                comparisonList = comparisonList.filter(compItem => JSON.stringify(compItem) !== JSON.stringify(item));
            }
            updateCompareButton();
        }
    });

    function updateCompareButton() {
        const count = comparisonList.length;
        if (count >= 2) {
            elements.compareBtnContainer.style.display = 'block';
            elements.compareBtn.textContent = `Comparar (${count})`;
            elements.compareBtn.disabled = false;
        } else {
            elements.compareBtnContainer.style.display = 'none';
            elements.compareBtn.textContent = 'Comparar (0)';
            elements.compareBtn.disabled = true;
        }
    }

    elements.compareBtn.addEventListener('click', () => {
        if (comparisonList.length < 2) return;
        renderComparisonModal();
        const modal = new bootstrap.Modal(document.getElementById('comparison-modal'));
        modal.show();
    });

    function renderComparisonModal() {
        const modalBody = document.getElementById('comparison-modal-body');
        const attributes = Object.keys(currentItems[0] || {});
        
        let tableHtml = '<div class="table-responsive"><table class="table table-bordered table-hover">';

        // Header row
        tableHtml += '<thead><tr><th class="table-light">Atributo</th>';
        comparisonList.forEach(item => {
            tableHtml += `<th class="table-light">${item.Producto_Nombre || item.Concepto}</th>`;
        });
        tableHtml += '</tr></thead>';

        // Body rows
        tableHtml += '<tbody>';
        attributes.forEach(attr => {
            if (attr === 'Producto_Codigo') return; // Skip irrelevant fields
            tableHtml += `<tr><td class="fw-bold table-light">${attr.replace(/_/g, ' ')}</td>`;
            comparisonList.forEach(item => {
                const value = item[attr] !== null && item[attr] !== undefined ? item[attr] : '-';
                tableHtml += `<td>${value}</td>`;
            });
            tableHtml += '</tr>';
        });
        tableHtml += '</tbody></table></div>';

        modalBody.innerHTML = tableHtml;
    }

    // --- Initialization ---
    async function init() {
        renderTableHeaders();
        const [filterOptions, stats] = await Promise.all([
            api.get('/api/v1/filters'),
            api.get('/api/v1/stats')
        ]);

        if (filterOptions) renderFilterOptions(filterOptions);
        if (stats) renderStats(stats);
        
        fetchData(); // Initial data load
    }

    init();
});