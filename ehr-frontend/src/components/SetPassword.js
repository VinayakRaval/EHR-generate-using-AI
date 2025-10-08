import React, { useState } from "react";

const SetPassword = () => {
  const [uniqueId, setUniqueId] = useState("");
  const [password, setPassword] = useState("");

  const handleSetPassword = async (e) => {
    e.preventDefault();

    const res = await fetch("http://localhost/ehr-backend/set_password.php", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ unique_id: uniqueId, password }),
    });

    const data = await res.json();
    alert(data.message);
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h2>Set Your Password</h2>
      <form onSubmit={handleSetPassword}>
        <input placeholder="Your Unique ID" value={uniqueId} onChange={e => setUniqueId(e.target.value)} required />
        <input type="password" placeholder="New Password" value={password} onChange={e => setPassword(e.target.value)} required />
        <button type="submit">Set Password</button>
      </form>
    </div>
  );
};

export default SetPassword;
