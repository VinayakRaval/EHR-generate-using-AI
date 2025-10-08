<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: POST");
header("Access-Control-Allow-Headers: Content-Type");

// Connect to database
$conn = new mysqli("localhost", "root", "", "ehr"); // change db credentials if needed
if ($conn->connect_error) {
    die(json_encode(["success"=>false,"message"=>"DB Connection failed"]));
}

// Read POST JSON
$data = json_decode(file_get_contents("php://input"), true);

if(!$data || !isset($data['username']) || !isset($data['password'])){
    echo json_encode(["success"=>false,"message"=>"Username or password not provided"]);
    exit;
}

$username = $data['username'];
$password = $data['password'];

// Check doctor table
$doctorQuery = $conn->prepare("SELECT * FROM doctors WHERE username=? AND password=?");
$doctorQuery->bind_param("ss", $username, $password);
$doctorQuery->execute();
$doctorResult = $doctorQuery->get_result();

if ($doctorResult && $doctorResult->num_rows > 0) {
    echo json_encode(["success"=>true,"message"=>"Login successful","role"=>"doctor"]);
    exit;
}

// Check patient table
$patientQuery = $conn->prepare("SELECT * FROM patients WHERE username=? AND password=?");
$patientQuery->bind_param("ss", $username, $password);
$patientQuery->execute();
$patientResult = $patientQuery->get_result();

if ($patientResult && $patientResult->num_rows > 0) {
    echo json_encode(["success"=>true,"message"=>"Login successful","role"=>"patient"]);
    exit;
}

// Invalid login
echo json_encode(["success"=>false,"message"=>"Invalid username or password"]);
?>
