import React, { useState } from "react";

const DoctorDashboard = ({ doctorId }) => {
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("male");
  const [contact, setContact] = useState("");
  const [uniqueId, setUniqueId] = useState("");

  const handleCreatePatient = async (e) => {
    e.preventDefault();

    const res = await fetch("http://localhost/ehr-backend/create_patient.php", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ doctor_id: doctorId, name, age, gender, contact }),
    });

    const data = await res.json();
    if (data.success) {
      setUniqueId(data.unique_id);
      alert("Patient created! Unique ID: " + data.unique_id);
    } else {
      alert("Error creating patient.");
    }
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h2>Create Patient</h2>
      <form onSubmit={handleCreatePatient}>
        <input placeholder="Name" value={name} onChange={e => setName(e.target.value)} required />
        <input type="number" placeholder="Age" value={age} onChange={e => setAge(e.target.value)} required />
        <select value={gender} onChange={e => setGender(e.target.value)}>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
        </select>
        <input placeholder="Contact" value={contact} onChange={e => setContact(e.target.value)} required />
        <button type="submit">Create Patient</button>
      </form>

      {uniqueId && (
        <p>Patient Unique ID: <strong>{uniqueId}</strong></p>
      )}
    </div>
  );
};

export default DoctorDashboard;
