import React, { useState } from "react";

const CreateDoctor = () => {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleCreateDoctor = async (e) => {
    e.preventDefault();

    const res = await fetch("http://localhost/ehr-backend/create_doctor.php", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, username, password }),
    });

    const data = await res.json();
    alert(data.message);
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h2>Create Doctor Account</h2>
      <form onSubmit={handleCreateDoctor}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit">Create Doctor</button>
      </form>
    </div>
  );
};

export default CreateDoctor;
