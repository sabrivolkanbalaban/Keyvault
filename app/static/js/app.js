// KeyVault Client-Side JavaScript

/**
 * Copy text to clipboard with visual feedback
 */
function copyToClipboard(text, btn) {
    navigator.clipboard.writeText(text).then(function () {
        const original = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check-lg text-success"></i>';
        btn.classList.add('btn-outline-success');
        btn.classList.remove('btn-outline-secondary');
        setTimeout(function () {
            btn.innerHTML = original;
            btn.classList.remove('btn-outline-success');
            btn.classList.add('btn-outline-secondary');
        }, 1500);
    });
}

/**
 * Toggle password field visibility
 */
function togglePassword(fieldId, btn) {
    const field = document.getElementById(fieldId);
    if (field.type === 'password') {
        field.type = 'text';
        btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
    } else {
        field.type = 'password';
        btn.innerHTML = '<i class="bi bi-eye"></i>';
    }
}

/**
 * Auto-dismiss alerts after 5 seconds
 */
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });
});
