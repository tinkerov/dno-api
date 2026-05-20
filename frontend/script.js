const API_URL = "http://127.0.0.1:8000";

// Глобальный массив, где будем хранить список всех товаров с бэка
let ALL_PRODUCTS = [];

document.addEventListener("DOMContentLoaded", () => {
    showSection('shop');
    loadProducts();
    updateCartCount();
    checkAuthStatus();
    setupAuthForms();
});

// ФУНКЦИЯ ПЕРЕКЛЮЧЕНИЯ ЭКРАНОВ (SPA ЛОГИКА)
function showSection(sectionName) {
    // Сначала скрываем ВСЕ секции
    document.querySelectorAll('.spa-section').forEach(section => {
        section.classList.remove('active');
    });

    // Показываем нужную секцию
    const targetSection = document.getElementById(`section-${sectionName}`);
    if (targetSection) targetSection.classList.add('active');

    // Если перешли в корзину — обновляем её содержимое
    if (sectionName === 'cart') {
        renderCart();
    }
}

// 1. ЗАГРУЗКА ВСЕХ ТОВАРОВ С БЭКЕНДА НА ВИТРИНУ (БЕЗ ФИЛЬТРОВ)
async function loadProducts() {
    const container = document.getElementById("products-container");
    if (!container) return;

    try {
        // Делаем прямой и простой запрос на получение всех товаров
        const response = await fetch(`${API_URL}/items`);
        if (!response.ok) throw new Error(`Ошибка: ${response.status}`);
        
        ALL_PRODUCTS = await response.json();
        container.innerHTML = "";

        if (ALL_PRODUCTS.length === 0) {
            container.innerHTML = "<p style='padding: 20px; font-size: 16px; color: #555;'>На складе DNO пока пусто...</p>";
            return;
        }

        ALL_PRODUCTS.forEach(product => {
            const card = document.createElement("div");
            card.className = "product-card";
            
            // Проверяем наличие картинки. Если её нет (или старая база) — ставим заглушку
            const imageSrc = product.image_url || "https://via.placeholder.com/150?text=No+Image";

            card.innerHTML = `
                <img src="${imageSrc}" alt="${product.name}">
                <div class="product-info">
                    <h2 class="product-name" style="font-size: 18px; margin: 10px 0;">${product.name}</h2>
                    <p class="product-desc" style="font-size: 14px; color: #666; flex-grow: 1;">${product.description || ""}</p>
                </div>
                <div class="buy-section">
                    <span class="product-price" style="font-weight: bold; font-size: 18px;">${product.price} ₽</span>
                    <button class="buy-btn" onclick="addToCart(${product.id})">В корзину</button>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error(error);
        container.innerHTML = "<p style='padding: 20px; color: red;'>Не удалось загрузить товары с бэкенда.</p>";
    }
}

// 2. ЛОГИКА КОРЗИНЫ (LOCALSTORAGE)
function addToCart(productId) {
    let cart = JSON.parse(localStorage.getItem("cart")) || [];
    const item = cart.find(i => i.id === productId);

    if (item) {
        item.quantity += 1;
    } else {
        cart.push({ id: productId, quantity: 1 });
    }

    localStorage.setItem("cart", JSON.stringify(cart));
    updateCartCount();
    alert("Товар добавлен в корзину!");
}

function updateCartCount() {
    const cart = JSON.parse(localStorage.getItem("cart")) || [];
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    const cartCountEl = document.getElementById("cart-count");
    if (cartCountEl) cartCountEl.innerText = count;
}

function renderCart() {
    const container = document.getElementById("cart-container");
    const totalElement = document.getElementById("cart-total");
    const cart = JSON.parse(localStorage.getItem("cart")) || [];

    if (!container || !totalElement) return;

    if (cart.length === 0) {
        container.innerHTML = "<p>Корзина пуста.</p>";
        totalElement.innerText = "0";
        return;
    }

    container.innerHTML = "";
    let totalSum = 0;

    cart.forEach(cartItem => {
        const product = ALL_PRODUCTS.find(p => p.id === cartItem.id);
        if (product) {
            totalSum += product.price * cartItem.quantity;
            const card = document.createElement("div");
            card.className = "product-card";
            const imageSrc = product.image_url || "https://via.placeholder.com/150?text=No+Image";

            card.innerHTML = `
                <img src="${imageSrc}" alt="${product.name}">
                <div class="product-info">
                    <h2 class="product-name" style="font-size: 18px; margin: 10px 0;">${product.name}</h2>
                    <p class="product-desc">Количество: ${cartItem.quantity} шт.</p>
                </div>
                <div class="buy-section">
                    <span class="product-price" style="font-weight: bold; font-size: 18px;">${product.price * cartItem.quantity} ₽</span>
                    <button class="buy-btn" style="background: #ff4d4d; color: white;" onclick="removeFromCart(${product.id})">Удалить</button>
                </div>
            `;
            container.appendChild(card);
        }
    });
    totalElement.innerText = totalSum;
}

function removeFromCart(productId) {
    let cart = JSON.parse(localStorage.getItem("cart")) || [];
    cart = cart.filter(item => item.id !== productId);
    localStorage.setItem("cart", JSON.stringify(cart));
    updateCartCount();
    renderCart();
}

function checkoutOrder() {
    const token = localStorage.getItem("token");
    if (!token) {
        alert("Для оформления заказа необходимо войти в аккаунт!");
        showSection('login');
        return;
    }
    alert("Заказ оформлен! (Тут будет POST запрос на создание заказа в бэкенд)");
}

// 3. АВТОРИЗАЦИЯ И РЕГИСТРАЦИЯ
function setupAuthForms() {
    const registerForm = document.getElementById("register-form");
    const loginForm = document.getElementById("login-form");

    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("register-email").value;
            const password = document.getElementById("register-password").value;

            const response = await fetch(`${API_URL}/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            if (response.ok) {
                alert("Успешная регистрация! Теперь войдите.");
                showSection('login');
            } else {
                const errorData = await response.json().catch(() => ({}));
                const detail = errorData.detail || `Код ошибки: ${response.status}`;
                alert(`Ошибка регистрации: ${detail}`);
            }
        });
    }

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("login-email").value;
            const password = document.getElementById("login-password").value;

            const formData = new FormData();
            formData.append("username", email);
            formData.append("password", password);

            const response = await fetch(`${API_URL}/login`, { 
                method: "POST",
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem("token", data.access_token);
                alert("Вы вошли в систему!");
                checkAuthStatus();
                showSection('shop');
            } else {
                const errorData = await response.json().catch(() => ({}));
                const detail = errorData.detail || `Код ошибки: ${response.status}`;
                alert(`Ошибка входа: ${detail}`);
            }
        });
    }
}

function checkAuthStatus() {
    const token = localStorage.getItem("token");
    const authBtn = document.getElementById("auth-nav-btn");
    if (!authBtn) return;

    if (token) {
        authBtn.innerText = "Выйти";
        authBtn.onclick = () => {
            localStorage.removeItem("token");
            checkAuthStatus();
            showSection('shop');
        };
    } else {
        authBtn.innerText = "Войти";
        authBtn.onclick = () => showSection('login');
    }
}