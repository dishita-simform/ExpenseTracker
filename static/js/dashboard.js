document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    initializeDashboard();
    
    // Set up event listeners for forms
    setupFormListeners();
});

function initializeDashboard() {
    // Set up periodic refresh (every 30 seconds)
    setInterval(refreshDashboard, 30000);
}

function setupFormListeners() {
    // Add Transaction form
    const addTransactionForm = document.getElementById('addTransactionForm');
    if (addTransactionForm) {
        addTransactionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitTransactionForm(this);
        });
    }
    
    // Edit Transaction form
    const editTransactionForm = document.getElementById('editTransactionForm');
    if (editTransactionForm) {
        editTransactionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitTransactionForm(this);
        });
    }
}

function submitTransactionForm(form) {
    const formData = new FormData(form);
    const url = form.getAttribute('action');
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close modal if it exists
            const modal = bootstrap.Modal.getInstance(document.getElementById('addTransactionModal'));
            if (modal) modal.hide();
            
            // Refresh dashboard
            refreshDashboard();
            
            // Show success message
            showNotification('Transaction saved successfully!', 'success');
        } else {
            showNotification(data.error || 'Error saving transaction', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while saving the transaction', 'error');
    });
}

function refreshDashboard() {
    fetch('/api/dashboard-data/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        updateDashboardStats(data);
        updateRecentTransactions(data.recent_transactions);
        updateBudgetOverview(data.budget_categories);
    })
    .catch(error => {
        console.error('Error refreshing dashboard:', error);
    });
}

function updateDashboardStats(data) {
    // Update total balance
    document.getElementById('totalBalance').textContent = `₹${data.total_balance}`;
    
    // Update income
    document.getElementById('totalIncome').textContent = `₹${data.total_income}`;
    
    // Update expenses
    document.getElementById('totalExpenses').textContent = `₹${data.total_expenses}`;
    
    // Update savings
    document.getElementById('totalSavings').textContent = `₹${data.total_savings}`;
}

function updateRecentTransactions(transactions) {
    const tbody = document.querySelector('#recentTransactionsTable tbody');
    if (!tbody) return;
    
    if (transactions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4">
                    <div class="text-muted">
                        <i class="fas fa-receipt fs-2 mb-2"></i>
                        <p class="mb-0">No transactions yet</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    transactions.forEach(transaction => {
        const amountClass = transaction.amount < 0 ? 'text-danger' : 'text-success';
        const amountDisplay = transaction.amount < 0 ? 
            `₹${Math.abs(transaction.amount)}` : 
            `₹${transaction.amount}`;
            
        html += `
            <tr>
                <td class="ps-4">
                    <div class="d-flex align-items-center">
                        <div class="category-icon me-2 bg-${transaction.category.color}">
                            <i class="fas fa-${transaction.category.icon}"></i>
                        </div>
                        ${transaction.category.name}
                    </div>
                </td>
                <td>${transaction.description}</td>
                <td>${transaction.date}</td>
                <td class="text-end pe-4">
                    <span class="${amountClass}">${amountDisplay}</span>
                </td>
                <td class="text-end pe-4">
                    <button class="btn btn-sm btn-primary" onclick="editTransaction(${transaction.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteTransaction(${transaction.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

function updateBudgetOverview(categories) {
    const container = document.getElementById('budgetOverviewContainer');
    if (!container) return;
    
    if (categories.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <div class="text-muted">
                    <i class="fas fa-chart-pie fs-2 mb-2"></i>
                    <p class="mb-0">No budget categories set</p>
                    <a href="/budget-settings/" class="btn btn-sm btn-primary mt-3">
                        <i class="fas fa-plus me-2"></i>Set Budget
                    </a>
                </div>
            </div>
        `;
        return;
    }
    
    let html = '';
    categories.forEach(category => {
        html += `
            <div class="budget-item mb-4">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="d-flex align-items-center">
                        <div class="category-icon me-2 bg-gradient-${category.color}">
                            <i class="fas fa-${category.icon}"></i>
                        </div>
                        <span>${category.name}</span>
                    </div>
                    <div class="text-end">
                        <span class="fw-bold">₹${category.spent}</span>
                        <small class="text-muted">/ ₹${category.budget}</small>
                    </div>
                </div>
                <div class="progress">
                    <div class="progress-bar bg-gradient-${category.color}" 
                         role="progressbar" 
                         style="width: ${category.percentage}%"
                         aria-valuenow="${category.percentage}" 
                         aria-valuemin="0" 
                         aria-valuemax="100"></div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function editTransaction(id) {
    fetch(`/api/transaction/${id}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('editCategory').value = data.category;
            document.getElementById('editAmount').value = data.amount;
            document.getElementById('editDescription').value = data.description;
            document.getElementById('editDate').value = data.date;
            document.getElementById('editTransactionForm').action = `/transaction/${id}/edit/`;
            
            const modal = new bootstrap.Modal(document.getElementById('editTransactionModal'));
            modal.show();
        });
}

function deleteTransaction(id) {
    if (confirm('Are you sure you want to delete this transaction?')) {
        fetch(`/transaction/${id}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                refreshDashboard();
                showNotification('Transaction deleted successfully!', 'success');
            } else {
                showNotification(data.error || 'Error deleting transaction', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while deleting the transaction', 'error');
        });
    }
}

function showNotification(message, type = 'info') {
    // Check if toast container exists, if not create it
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Set toast content
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
} 