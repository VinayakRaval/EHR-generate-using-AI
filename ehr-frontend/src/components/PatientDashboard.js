import React, { useState, useEffect } from "react";
import "../styles/PatientDashboard.css";


const PatientDashboard = () => {
  const [records, setRecords] = useState([]);

  useEffect(() => {
    fetchRecords();
  }, []);

  const fetchRecords = async () => {
    const res = await fetch("http://localhost/ehr-backend/get_patient_records.php");
    const data = await res.json();
    if(data.success){
      setRecords(data.records);
    }
  };

  const downloadFile = (url) => {
    window.open(url, "_blank");
  };

  return (
    <div className="patient-dashboard">
      <h1>Patient Dashboard</h1>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Prescription / Report</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {records.map((rec, index) => (
            <tr key={index}>
              <td>{rec.date}</td>
              <td>{rec.title}</td>
              <td>
                <button onClick={() => downloadFile(rec.file_url)}>Download</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PatientDashboard;
