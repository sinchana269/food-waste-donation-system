// Set this to your production backend URL once deployed (e.g., https://your-backend.onrender.com)
const PROD_API_URL = "https://kind-areas-tan.loca.lt"; 
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? "http://localhost:8000" 
    : PROD_API_URL;


// API Handlers
async function api_request(endpoint, method = 'GET', data = null, use_token = true) {
    const loader = document.getElementById('loader');
    if (loader) loader.style.display = 'flex';

    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (use_token) {
        const token = localStorage.getItem('token');
        if (token) headers['Authorization'] = `Bearer ${token}`;
    }

    const options = { method, headers };
    if (data) options.body = JSON.stringify(data);

    try {
        const response = await fetch(`${API_URL}${endpoint}`, options);
        if (response.status === 401) {
            localStorage.removeItem('token');
            if (window.location.pathname !== '/login.html' && window.location.pathname !== '/index.html') {
                window.location.href = 'login.html';
            }
        }
        return await response.json();
    } catch (error) {
        console.error("API Request Failed:", error);
        return { error: "Network Error" };
    } finally {
        if (loader) loader.style.display = 'none';
    }
}

// Global Auth State
function checkAuth() {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user'));
    
    if (token && user) {
        // Update UI based on auth
        const authButtons = document.querySelectorAll('.auth-btn');
        authButtons.forEach(btn => btn.style.display = 'none');
        
        const logoutBtn = document.createElement('button');
        logoutBtn.className = 'btn btn-outline-danger ms-2';
        logoutBtn.innerText = 'Logout';
        logoutBtn.onclick = () => {
            localStorage.clear();
            window.location.href = 'index.html';
        };
        document.querySelector('.navbar-nav').appendChild(logoutBtn);
    }
}

document.addEventListener('DOMContentLoaded', checkAuth);
