// Login JavaScript file for ecommerce website

// DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', function() {
    console.log('Login page loaded successfully');

    // Get the login form
    const loginForm = document.getElementById('loginForm');

    // Add event listener to the form
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Get form data
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            // Simple validation
            if (username.trim() === '' || password.trim() === '') {
                alert('Please fill in all fields');
                return;
            }

            // In a real application, this would send data to a server
            console.log('Login attempt with:', { username, password });

            // For demo purposes, just show a success message
            alert('Login functionality would be implemented here. Redirecting to home page...');

            // Redirect to home page after login
            window.location.href = 'index.html';
        });
    }
});

// Function to handle registration link click
function goToRegister() {
    window.location.href = 'register.html';
}