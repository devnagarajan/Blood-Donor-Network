/**
 * RedFusion - Main JavaScript
 * Mobile Menu & Interactive Features
 */

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const toggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (toggler && navbarCollapse) {
        toggler.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            const isClickInside = toggler.contains(event.target) || navbarCollapse.contains(event.target);
            if (!isClickInside && navbarCollapse.classList.contains('show')) {
                navbarCollapse.classList.remove('show');
            }
        });
    }
    
    // Dropdown toggle for mobile
    const dropdowns = document.querySelectorAll('.nav-item.dropdown');
    dropdowns.forEach(function(dropdown) {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (toggle && menu) {
            // For mobile: click to toggle
            if (window.innerWidth < 768) {
                toggle.addEventListener('click', function(e) {
                    e.preventDefault();
                    menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
                });
            }
        }
    });
});

// Alert close button functionality
document.addEventListener('DOMContentLoaded', function() {
    const closeButtons = document.querySelectorAll('.btn-close');
    closeButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const alert = this.closest('.alert');
            if (alert) {
                alert.style.display = 'none';
            }
        });
    });
});

// Secret Admin Access - Type "redfusion" anywhere on the page
(function() {
    let secretKey = '';
    const SECRET_CODE = 'redfusion'; // Change this to your desired secret key
    const ADMIN_URL = '/admin/';
    let typingTimeout;

    document.addEventListener('keydown', function(e) {
        // Ignore if typing in input fields
        if (e.target.tagName === 'INPUT' || 
            e.target.tagName === 'TEXTAREA' || 
            e.target.isContentEditable) {
            return;
        }

        // Clear timeout if exists
        clearTimeout(typingTimeout);

        // Add pressed key to secret key
        secretKey += e.key.toLowerCase();

        // Keep only last N characters (length of secret code)
        if (secretKey.length > SECRET_CODE.length) {
            secretKey = secretKey.slice(-SECRET_CODE.length);
        }

        // Check if secret code matches
        if (secretKey === SECRET_CODE) {
            // Visual feedback
            document.body.style.transition = 'background-color 0.3s';
            document.body.style.backgroundColor = '#dc3545';
            
            setTimeout(function() {
                document.body.style.backgroundColor = '';
                // Redirect to admin
                window.location.href = ADMIN_URL;
            }, 300);
            
            // Reset
            secretKey = '';
        }

        // Reset after 2 seconds of no typing
        typingTimeout = setTimeout(function() {
            secretKey = '';
        }, 2000);
    });
})();
