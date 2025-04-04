// Initialize form validation when the document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get form elements
    const form = document.getElementById('expenseForm');
    const dateInput = document.getElementById('id_date');
    const dateError = document.getElementById('dateError');
    
    // Check if we're in edit mode
    const isEditing = form.dataset.isEditing === 'true';
    
    // Set max date to today
    const today = new Date();
    const todayFormatted = today.toISOString().split('T')[0];
    dateInput.max = todayFormatted;
    
    // Set default date to today if not editing
    if (!dateInput.value && !isEditing) {
        dateInput.value = todayFormatted;
    }
    
    // Form validation
    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        
        // Check if date is in the future
        const selectedDate = new Date(dateInput.value);
        if (selectedDate > today) {
            event.preventDefault();
            dateError.classList.remove('d-none');
            dateInput.classList.add('is-invalid');
            return false;
        } else {
            dateError.classList.add('d-none');
            dateInput.classList.remove('is-invalid');
        }
        
        form.classList.add('was-validated');
    });
    
    // Validate date on change
    dateInput.addEventListener('change', function() {
        const selectedDate = new Date(this.value);
        if (selectedDate > today) {
            dateError.classList.remove('d-none');
            this.classList.add('is-invalid');
        } else {
            dateError.classList.add('d-none');
            this.classList.remove('is-invalid');
        }
    });
}); 