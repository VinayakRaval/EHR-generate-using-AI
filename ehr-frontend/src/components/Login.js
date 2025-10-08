const handleLogin = async () => {
    const res = await fetch("http://localhost/backend/login.php", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });
    const data = await res.json();
    if(data.success){
        alert(`Login successful as ${data.role}`);
        // Redirect based on role
    } else {
        alert(data.message);
    }
};
