// Main JavaScript file for ecommerce website

// DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', function() {
    console.log('Ecommerce website loaded successfully');

    // Add any interactive functionality here
    const loginLink = document.querySelector('.nav-links a[href="login.html"]');
    if (loginLink) {
        loginLink.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = 'login.html';
        });
    }
});

// Function to handle product clicks
function viewProduct(productId) {
    console.log('Viewing product:', productId);
    // In a real application, this would navigate to the product page
}

// Function to add item to cart
function addToCart(productId) {
    console.log('Adding product to cart:', productId);
    // In a real application, this would add the product to the shopping cart
}