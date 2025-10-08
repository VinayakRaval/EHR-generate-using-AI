<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

header('Content-Type: application/json');
include 'db_connect.php';

$data = json_decode(file_get_contents("php://input"), true);

$doctor_id = $data['doctor_id'];
$name = $data['name'];
$age = $data['age'];
$gender = $data['gender'];
$contact = $data['contact'];

// Generate unique ID for patient
$unique_id = 'PAT' . rand(1000,9999);

// Default password = NULL, patient will set later
$password = null;

// Insert into users table
$stmt1 = $conn->prepare("INSERT INTO users (username, password, role) VALUES (?, ?, 'patient')");
$stmt1->bind_param("ss", $unique_id, $password);
$stmt1->execute();

// Get patient_id
$patient_id = $conn->insert_id;

// Insert into patients_info table
$stmt2 = $conn->prepare("INSERT INTO patients_info (unique_id, doctor_id, name, age, gender, contact) VALUES (?, ?, ?, ?, ?, ?)");
$stmt2->bind_param("sissss", $unique_id, $doctor_id, $name, $age, $gender, $contact);
$stmt2->execute();

echo json_encode(["success"=>true, "unique_id"=>$unique_id, "message"=>"Patient created successfully. Share this ID with the patient."]);

$conn->close();
?>
