// DOM Elements
const navbar = document.querySelector('.navbar');
const navToggle = document.querySelector('.nav-toggle');
const navLinks = document.querySelectorAll('.nav-link');
const filterBtns = document.querySelectorAll('.filter-btn');
const portfolioItems = document.querySelectorAll('.portfolio-item');
const darkModeToggle = document.getElementById('darkModeToggle');
const contactForm = document.getElementById('contactForm');
const skillLevels = document.querySelectorAll('.skill-level');

// Mobile Navigation Toggle
navToggle.addEventListener('click', () => {
    navbar.classList.toggle('active');
    // Animate hamburger icon
    const bars = document.querySelectorAll('.bar');
    bars.forEach(bar => bar.classList.toggle('active'));
});

// Close mobile menu when clicking a link
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        navbar.classList.remove('active');
        // Reset hamburger icon
        const bars = document.querySelectorAll('.bar');
        bars.forEach(bar => bar.classList.remove('active'));
    });
});

// Smooth Scrolling for Navigation Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();

        const targetId = this.getAttribute('href');
        if (targetId === '#') return;

        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 80,
                behavior: 'smooth'
            });

            // Update active link
            navLinks.forEach(link => link.classList.remove('active'));
            this.classList.add('active');
        }
    });
});

// Portfolio Filtering
filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all buttons
        filterBtns.forEach(b => b.classList.remove('active'));
        // Add active class to clicked button
        btn.classList.add('active');

        const filterValue = btn.getAttribute('data-filter');

        portfolioItems.forEach(item => {
            if (filterValue === 'all' || item.getAttribute('data-category') === filterValue) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    });
});

// Skill Bar Animation
function animateSkillBars() {
    skillLevels.forEach(level => {
        const width = level.getAttribute('data-level');
        level.style.width = '0';
        setTimeout(() => {
            level.style.width = width + '%';
        }, 500);
    });
}

// Initialize skill bars when they come into view
const skillsSection = document.querySelector('.skills');
const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
};

const skillsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateSkillBars();
            skillsObserver.unobserve(entry.target);
        }
    });
}, observerOptions);

skillsObserver.observe(skillsSection);

// Testimonial Slider
let currentTestimonial = 0;
const testimonials = document.querySelectorAll('.testimonial');

function showTestimonial(index) {
    testimonials.forEach(testimonial => testimonial.classList.remove('active'));
    testimonials[index].classList.add('active');
}

function nextTestimonial() {
    currentTestimonial = (currentTestimonial + 1) % testimonials.length;
    showTestimonial(currentTestimonial);
}

function prevTestimonial() {
    currentTestimonial = (currentTestimonial - 1 + testimonials.length) % testimonials.length;
    showTestimonial(currentTestimonial);
}

// Initialize testimonial slider
showTestimonial(currentTestimonial);

// Auto-rotate testimonials every 5 seconds
setInterval(nextTestimonial, 5000);

// Event listeners for testimonial navigation
document.querySelector('.next').addEventListener('click', nextTestimonial);
document.querySelector('.prev').addEventListener('click', prevTestimonial);

// Contact Form Validation and Submission
contactForm.addEventListener('submit', function(e) {
    e.preventDefault();

    // Get form values
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const subject = document.getElementById('subject').value.trim();
    const message = document.getElementById('message').value.trim();

    // Simple validation
    if (!name || !email || !subject || !message) {
        alert('Please fill in all fields');
        return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert('Please enter a valid email address');
        return;
    }

    // If validation passes, show success message
    alert('Thank you for your message! I will get back to you soon.');
    contactForm.reset();
});

// Dark Mode Toggle
function toggleDarkMode() {
    const body = document.body;
    const isDarkMode = body.classList.toggle('dark-mode');

    // Save preference to localStorage
    localStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled');

    // Update icon
    const icon = darkModeToggle.querySelector('i');
    if (isDarkMode) {
        icon.className = 'fas fa-sun';
    } else {
        icon.className = 'fas fa-moon';
    }
}

// Check for saved theme preference or respect OS preference
function initDarkMode() {
    const savedTheme = localStorage.getItem('darkMode');
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

    if (savedTheme === 'enabled' ||
        (!savedTheme && prefersDarkScheme.matches)) {
        document.body.classList.add('dark-mode');
        darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    }
}

// Initialize dark mode
initDarkMode();

// Event listener for dark mode toggle
darkModeToggle.addEventListener('click', toggleDarkMode);

// Header scroll effect
window.addEventListener('scroll', () => {
    const header = document.querySelector('.header');
    if (window.scrollY > 100) {
        header.style.background = 'rgba(255, 255, 255, 0.98)';
        header.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
    } else {
        header.style.background = 'rgba(255, 255, 255, 0.95)';
        header.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
    }
});

// Animation on scroll for sections
const animateOnScroll = (entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
            observer.unobserve(entry.target);
        }
    });
};

const sectionObserver = new IntersectionObserver(animateOnScroll, {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
});

// Observe all sections that need animation
document.querySelectorAll('section').forEach(section => {
    sectionObserver.observe(section);
});

// Add animation classes to elements
document.querySelectorAll('.about-content, .skills-content, .portfolio-grid, .testimonial-slider')
    .forEach(el => {
        el.classList.add('animate-on-scroll');
    });

// Initialize scroll animations
document.addEventListener('DOMContentLoaded', () => {
    // Trigger initial animation check
    window.dispatchEvent(new Event('scroll'));
});