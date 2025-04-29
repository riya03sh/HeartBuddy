document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });

    // Numeric input validation
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('input', function() {
            const min = parseInt(this.min) || 0;
            const max = parseInt(this.max) || Infinity;
            let value = parseFloat(this.value);
            
            if (isNaN(value)) {
                this.value = '';
                return;
            }
            
            if (value < min) this.value = min;
            if (value > max) this.value = max;
        });
    });

    // Special handling for ST Depression (allows decimals)
    const stDepressionInput = document.getElementById('st_depression');
    if (stDepressionInput) {
        stDepressionInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9.]/g, '');
            if ((this.value.match(/\./g) || []).length > 1) {
                this.value = this.value.substring(0, this.value.lastIndexOf('.'));
            }
        });
    }
});