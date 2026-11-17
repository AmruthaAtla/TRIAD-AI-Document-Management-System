const API_BASE_URL = "/api";

// USER REGISTRATION
async function registerUser(event) {
    event.preventDefault();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const division = document.getElementById("division").value.trim();

    const message = document.getElementById("message");

    message.textContent = "Creating your account...";
    message.className = "message";

    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                email: email,
                password: password,
                division: division
            })
        });

        const result = await response.json();

        if (!response.ok) {
            message.textContent = result.error || "Registration failed";
            message.className = "message error";
            return;
        }

        message.textContent = "Account created successfully! Redirecting to login...";
        message.className = "message success";

        document.getElementById("signupForm").reset();

        setTimeout(() => {
            window.location.href = "/";

        }, 1500);

    } catch (error) {
        console.error("Registration error:", error);

        message.textContent = "Unable to connect to the server.";
        message.className = "message error";
    }
}


// USER LOGIN
async function loginUser(event) {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    const message = document.getElementById("message");

    message.textContent = "Signing in...";
    message.className = "message";

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const result = await response.json();

        if (!response.ok) {
            message.textContent = result.error || "Login failed";
            message.className = "message error";
            return;
        }

        sessionStorage.setItem("access_token", result.access_token);
        sessionStorage.setItem("user", JSON.stringify(result.user));

        message.textContent = "Login successful!";
        message.className = "message success";

        setTimeout(() => {
            window.location.href = "/static/pages/dashboard.html";
        }, 800);

    } catch (error) {
        console.error("Login error:", error);

        message.textContent = "Unable to connect to the server.";
        message.className = "message error";
    }
}