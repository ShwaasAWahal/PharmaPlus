// ============================================
// PHARMA PULSE - LOGIN PAGE FUNCTIONALITY
// ============================================

class LoginForm {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.nameInput = document.getElementById('name');
        this.phoneInput = document.getElementById('phone');
        this.nameError = document.getElementById('nameError');
        this.phoneError = document.getElementById('phoneError');

        this.init();
    }

    init() {
        // Form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Real-time validation
        this.nameInput.addEventListener('blur', () => this.validateName());
        this.phoneInput.addEventListener('blur', () => this.validatePhone());
        this.phoneInput.addEventListener('input', () => this.formatPhone());

        // Clear errors on focus
        this.nameInput.addEventListener('focus', () => this.clearError('name'));
        this.phoneInput.addEventListener('focus', () => this.clearError('phone'));
    }

    /**
     * Validate Name Field
     */
    validateName() {
        const value = this.nameInput.value.trim();

        // Check if empty
        if (!value) {
            this.showError('name', 'Please enter your full name');
            return false;
        }

        // Check minimum length
        if (value.length < 3) {
            this.showError('name', 'Name must be at least 3 characters');
            return false;
        }

        // Check if contains only letters and spaces
        if (!/^[a-zA-Z\s]+$/.test(value)) {
            this.showError('name', 'Name should only contain letters and spaces');
            return false;
        }

        this.clearError('name');
        return true;
    }

    /**
     * Validate Phone Number
     */
    validatePhone() {
        const value = this.phoneInput.value.trim();

        // Check if empty
        if (!value) {
            this.showError('phone', 'Please enter your phone number');
            return false;
        }

        // Check length
        if (value.length !== 10) {
            this.showError('phone', 'Phone number must be 10 digits');
            return false;
        }

        // Check if only numbers
        if (!/^[0-9]{10}$/.test(value)) {
            this.showError('phone', 'Phone number should contain only digits');
            return false;
        }

        // Check if starts with valid digit (1-9)
        if (!/^[6-9]/.test(value)) {
            this.showError('phone', 'Phone number should start with 6-9');
            return false;
        }

        this.clearError('phone');
        return true;
    }

    /**
     * Format Phone Number as User Types
     */
    formatPhone() {
        let value = this.phoneInput.value.replace(/\D/g, '');
        
        // Limit to 10 digits
        if (value.length > 10) {
            value = value.slice(0, 10);
        }

        this.phoneInput.value = value;
    }

    /**
     * Show Error Message
     */
    showError(field, message) {
        const errorElement = document.getElementById(`${field}Error`);
        const input = field === 'name' ? this.nameInput : this.phoneInput;

        errorElement.textContent = message;
        errorElement.classList.add('show');
        input.style.borderColor = '#E53E3E';
        input.style.backgroundColor = 'rgba(245, 53, 61, 0.02)';
    }

    /**
     * Clear Error Message
     */
    clearError(field) {
        const errorElement = document.getElementById(`${field}Error`);
        const input = field === 'name' ? this.nameInput : this.phoneInput;

        errorElement.textContent = '';
        errorElement.classList.remove('show');
        input.style.borderColor = '';
        input.style.backgroundColor = '';
    }

    /**
     * Handle Form Submission
     */
    handleSubmit(e) {
        e.preventDefault();

        // Validate both fields
        const isNameValid = this.validateName();
        const isPhoneValid = this.validatePhone();

        if (isNameValid && isPhoneValid) {
            this.submitForm();
        }
    }

    /**
     * Submit Form (Mock API Call)
     */
    submitForm() {
        const name = this.nameInput.value.trim();
        const phone = this.phoneInput.value.trim();

        // Show loading state
        const loginBtn = document.querySelector('.btn-login');
        const originalText = loginBtn.innerHTML;
        loginBtn.innerHTML = '<span class="btn-text">Logging in...</span>';
        loginBtn.disabled = true;

        // Simulate API call
        setTimeout(() => {
            console.log('Login successful:', {
                name: name,
                phone: '+91' + phone,
                timestamp: new Date().toISOString()
            });

            // Show success message
            this.showSuccessMessage(name);

            // Reset button
            loginBtn.innerHTML = originalText;
            loginBtn.disabled = false;
        }, 1500);
    }

    /**
     * Show Success Message
     */
    showSuccessMessage(name) {
        const formContainer = document.querySelector('.form-container');
        const successDiv = document.createElement('div');
        successDiv.className = 'success-notification';
        successDiv.innerHTML = `
            <div class="success-content">
                <span class="success-icon">✓</span>
                <h3>Welcome, ${name}!</h3>
                <p>You have been logged in successfully.</p>
            </div>
        `;

        formContainer.appendChild(successDiv);

        // Add animation
        setTimeout(() => {
            successDiv.classList.add('show');
        }, 10);

        // Remove after 3 seconds and reset form
        setTimeout(() => {
            successDiv.classList.remove('show');
            setTimeout(() => {
                successDiv.remove();
                this.resetForm();
            }, 300);
        }, 3000);
    }

    /**
     * Reset Form
     */
    resetForm() {
        this.form.reset();
        this.clearError('name');
        this.clearError('phone');
    }
}

// ============================================
// INITIALIZE APP
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    new LoginForm();

    // Handle Create Account button
    const createAccountBtn = document.querySelector('.btn-signup');
    createAccountBtn.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Redirect to signup page');
        // Redirect to signup page
        // window.location.href = '/signup';
        alert('Redirecting to Sign Up Page...');
    });

    // Handle Forgot Details link
    const forgotLink = document.querySelector('.footer-link:first-of-type');
    forgotLink.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Redirect to forgot details page');
        alert('Redirecting to Account Recovery...');
    });

    // Handle Need Help link
    const helpLink = document.querySelector('.footer-link:last-of-type');
    helpLink.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Redirect to help page');
        alert('Opening Help Center...');
    });

    // Add subtle parallax effect on mouse move (optional)
    document.addEventListener('mousemove', (e) => {
        const leftSection = document.querySelector('.left-section');
        if (leftSection) {
            const x = (e.clientX / window.innerWidth) * 10;
            const y = (e.clientY / window.innerHeight) * 10;
            leftSection.style.backgroundPosition = `${x}px ${y}px`;
        }
    });
});

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Validate Indian Phone Number
 */
function isValidIndianPhone(phone) {
    const pattern = /^[6-9][0-9]{9}$/;
    return pattern.test(phone);
}

/**
 * Format phone number with country code
 */
function formatPhoneWithCode(phone) {
    return '+91' + phone;
}

/**
 * Check if all form fields are valid
 */
function isFormValid() {
    const name = document.getElementById('name').value.trim();
    const phone = document.getElementById('phone').value.trim();

    return name.length >= 3 && isValidIndianPhone(phone);
}