<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

header('Content-Type: application/json');
include 'db_connect.php';

$data = json_decode(file_get_contents("php://input"), true);

$unique_id = $data['unique_id'];
$password = $data['password'];

if(empty($unique_id) || empty($password)){
    echo json_encode(["success"=>false, "message"=>"All fields are required"]);
    exit;
}

$hashed_password = password_hash($password, PASSWORD_DEFAULT);

// Update user password
$stmt = $conn->prepare("UPDATE users SET password=? WHERE username=? AND role='patient'");
$stmt->bind_param("ss", $hashed_password, $unique_id);

if($stmt->execute()){
    echo json_encode(["success"=>true, "message"=>"Password set successfully. You can now login."]);
}else{
    echo json_encode(["success"=>false, "message"=>"Error updating password."]);
}

$conn->close();
?>
