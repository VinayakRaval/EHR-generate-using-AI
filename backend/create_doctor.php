<?php
header('Content-Type: application/json');
include 'db_connect.php'; // Database connection

$data = json_decode(file_get_contents("php://input"), true);

$email = $data['email'];
$username = $data['username'];
$password = $data['password'];

// Validation
if(empty($email) || empty($username) || empty($password)){
    echo json_encode(["success" => false, "message" => "All fields are required"]);
    exit;
}

// Hash password
$hashed_password = password_hash($password, PASSWORD_DEFAULT);

// Insert doctor into users table
$stmt = $conn->prepare("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, 'doctor')");
$stmt->bind_param("sss", $username, $email, $hashed_password);

if($stmt->execute()){
    echo json_encode(["success" => true, "message" => "Doctor account created successfully"]);
} else {
    echo json_encode(["success" => false, "message" => "Error: " . $stmt->error]);
}

$conn->close();
?>
