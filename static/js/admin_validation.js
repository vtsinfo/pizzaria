/**
 * admin_validation.js
 * Handles input masking and Address Lookup (CEP) for Admin pages.
 */

document.addEventListener('DOMContentLoaded', () => {
    applyMasks();
    setupAddressSearch();
});

function applyMasks() {
    // CEP Mask
    document.querySelectorAll('.mask-cep').forEach(input => {
        input.addEventListener('input', (e) => {
            let v = e.target.value.replace(/\D/g, "");
            v = v.replace(/^(\d{5})(\d)/, "$1-$2");
            e.target.value = v.substring(0, 9);
        });

        // Auto-lookup on blur
        input.addEventListener('blur', (e) => {
            const cep = e.target.value.replace(/\D/g, '');
            if (cep.length === 8) {
                fetchAddress(cep, e.target);
            }
        });
    });

    // CPF Mask
    document.querySelectorAll('.mask-cpf').forEach(input => {
        input.addEventListener('input', (e) => {
            let v = e.target.value.replace(/\D/g, "");
            v = v.replace(/(\d{3})(\d)/, "$1.$2");
            v = v.replace(/(\d{3})(\d)/, "$1.$2");
            v = v.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
            e.target.value = v.substring(0, 14);
        });
    });

    // CNPJ Mask
    document.querySelectorAll('.mask-cnpj').forEach(input => {
        input.addEventListener('input', (e) => {
            let v = e.target.value.replace(/\D/g, "");
            v = v.replace(/^(\d{2})(\d)/, "$1.$2");
            v = v.replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3");
            v = v.replace(/\.(\d{3})(\d)/, ".$1/$2");
            v = v.replace(/(\d{4})(\d)/, "$1-$2");
            e.target.value = v.substring(0, 18);
        });
    });

    // Phone Mask (Landline & Cell)
    document.querySelectorAll('.mask-phone').forEach(input => {
        input.addEventListener('input', (e) => {
            let v = e.target.value.replace(/\D/g, "");
            if (v.length > 10) {
                // (11) 91234-5678
                v = v.replace(/^(\d\d)(\d{5})(\d{4}).*/, "($1) $2-$3");
            } else {
                // (11) 1234-5678
                v = v.replace(/^(\d\d)(\d{4})(\d{0,4}).*/, "($1) $2-$3");
            }
            e.target.value = v;
        });
    });
}

function fetchAddress(cep, inputElement) {
    // Find target fields based on data attributes or convention
    // Convention: If input is inside a form, look for name="endereco", name="bairro", name="cidade", name="estado"
    // OR look for specific IDs defined in data-target-* attributes on the CEP input

    const form = inputElement.closest('form') || document.body;

    // Helper to find field
    const findField = (ids, names) => {
        // 1. Try Specific IDs first (Must be inside the same form)
        if (ids && Array.isArray(ids)) {
            for (let id of ids) {
                let el = document.getElementById(id);
                // Verify if this element belongs to the active form/context
                if (el && form.contains(el)) return el;
            }
        }

        // 2. Try data attribute
        if (names && names.length > 0 && inputElement.dataset[`target${names[0]}`]) {
            return document.getElementById(inputElement.dataset[`target${names[0]}`]);
        }

        // 3. Try common names
        if (names && Array.isArray(names)) {
            for (let name of names) {
                let el = form.querySelector(`[name="${name}"]`) || form.querySelector(`[name$="${name}"]`);
                if (el) return el;
                // Try suffix with underscore
                el = form.querySelector(`[name$="_${name}"]`);
                if (el) return el;
            }
        }
        return null;
    };

    const fieldLogradouro = findField(['matriz_logradouro', 'unidade_endereco'], ['endereco_principal', 'endereco', 'logradouro', 'rua']);
    const fieldBairro = findField(['matriz_bairro', 'unidade_bairro'], ['bairro']);
    const fieldCidade = findField(['matriz_cidade', 'unidade_cidade'], ['cidade']);
    const fieldUF = findField(['matriz_estado', 'unidade_estado'], ['estado', 'uf']);
    const fieldNumero = findField(['matriz_numero', 'unidade_numero'], ['numero']);

    // Show loading?
    if (fieldLogradouro) fieldLogradouro.placeholder = "Buscando...";

    fetch(`https://viacep.com.br/ws/${cep}/json/`)
        .then(r => r.json())
        .then(data => {
            if (data.erro) {
                showCepError(inputElement, "CEP não encontrado!");
                if (fieldLogradouro) fieldLogradouro.placeholder = "";
                return;
            }

            if (fieldLogradouro) {
                fieldLogradouro.value = data.logradouro;
                fieldLogradouro.placeholder = "";
            }
            if (fieldBairro) fieldBairro.value = data.bairro;
            if (fieldCidade) fieldCidade.value = data.localidade;
            if (fieldUF) fieldUF.value = data.uf;

            // Visual feedback - Locked feeling but editable
            /*
            [fieldLogradouro, fieldBairro, fieldCidade, fieldUF].forEach(el => {
                if(el) {
                    el.classList.add('bg-secondary', 'text-white');
                    setTimeout(() => el.classList.remove('bg-secondary', 'text-white'), 1000);
                }
            });
            */

            // Focus Number
            if (fieldNumero) {
                fieldNumero.focus();
                // Ensure visibility
                // fieldNumero.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        })
        .catch(() => {
            showCepError(inputElement, "Erro ao buscar CEP.");
            if (fieldLogradouro) fieldLogradouro.placeholder = "";
        });
}

function showCepError(inputElement, msg) {
    // Find or create error message element ABOVE the input group
    const container = inputElement.closest('.col-md-3') || inputElement.closest('.col-4') || inputElement.parentNode;

    let errorEl = container.querySelector('.cep-error-msg');
    if (!errorEl) {
        errorEl = document.createElement('div');
        errorEl.className = 'cep-error-msg text-danger fw-bold small mb-1 fade-in';
        // Insert as first child of container
        container.insertBefore(errorEl, container.firstChild);
    }
    errorEl.innerText = msg;

    // Check if input is in a group, color the border
    inputElement.classList.add('is-invalid');

    // Auto hide after 5s
    setTimeout(() => {
        errorEl.innerText = '';
        inputElement.classList.remove('is-invalid');
    }, 5000);
}

// --- ADDRESS SEARCH MODAL (Advanced) ---
let currentTargetForm = null;

function setupAddressSearch() {
    // Listen for clicks on "search-cep-btn"
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('search-cep-btn') || e.target.closest('.search-cep-btn')) {
            const btn = e.target.classList.contains('search-cep-btn') ? e.target : e.target.closest('.search-cep-btn');
            currentTargetForm = btn.closest('form');

            // Open Modal
            const modalEl = document.getElementById('addressSearchModal');
            if (modalEl) {
                const modal = new bootstrap.Modal(modalEl);
                modal.show();
            }
        }
    });

    // Search Action in Modal
    const btnSearch = document.getElementById('btnSearchAddress');
    if (btnSearch) {
        btnSearch.addEventListener('click', performAddressSearch);
    }
}

function performAddressSearch() {
    const uf = document.getElementById('searchUF').value;
    const city = document.getElementById('searchCity').value;
    const street = document.getElementById('searchStreet').value;
    const resultList = document.getElementById('addressResults');

    if (street.length < 3) {
        alert("Digite pelo menos 3 letras da rua.");
        return;
    }

    resultList.innerHTML = '<div class="text-center py-3"><i class="fas fa-spinner fa-spin"></i> Buscando...</div>';

    fetch(`https://viacep.com.br/ws/${uf}/${city}/${street}/json/`)
        .then(r => r.json())
        .then(data => {
            resultList.innerHTML = '';

            if (!Array.isArray(data) || data.length === 0) {
                resultList.innerHTML = '<div class="alert alert-warning">Nenhum endereço encontrado.</div>';
                return;
            }

            const ul = document.createElement('ul');
            ul.className = 'list-group';

            data.forEach(item => {
                const li = document.createElement('li');
                li.className = 'list-group-item list-group-item-action bg-dark text-light border-secondary cursor-pointer';
                li.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${item.logradouro}</strong><br>
                            <small>${item.bairro} - ${item.localidade}/${item.uf}</small>
                        </div>
                        <span class="badge bg-warning text-dark">${item.cep}</span>
                    </div>
                `;
                li.onclick = () => selectAddress(item);
                ul.appendChild(li);
            });
            resultList.appendChild(ul);
        })
        .catch(e => {
            resultList.innerHTML = '<div class="alert alert-danger">Erro na busca. Verifique os dados.</div>';
        });
}

function selectAddress(item) {
    if (!currentTargetForm) return;

    // Helper to set value safely
    const setVal = (names, val) => {
        for (let name of names) {
            let el = currentTargetForm.querySelector(`[name="${name}"]`) || currentTargetForm.querySelector(`[name$="${name}"]`);
            if (el) {
                el.value = val;
                // Trigger change/input event if needed for frameworks like Vue
                el.dispatchEvent(new Event('input'));
                el.dispatchEvent(new Event('change'));
                return;
            }
        }
    };

    setVal(['cep', 'CEP'], item.cep);
    setVal(['endereco', 'logradouro', 'rua'], item.logradouro);
    setVal(['bairro'], item.bairro);
    setVal(['cidade'], item.localidade);
    setVal(['estado', 'uf'], item.uf);

    // Close Modal
    const modalEl = document.getElementById('addressSearchModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    modal.hide();

    // Focus Number
    setVal(['numero'], ''); // Clear number
    const numEl = currentTargetForm.querySelector('[name="numero"]');
    if (numEl) numEl.focus();
}
