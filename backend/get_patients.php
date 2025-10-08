<?php
header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");

require 'db.php';

$sql = "SELECT id, name, email, role, created_at FROM users WHERE role='patient'";
$result = $conn->query($sql);

$patients = [];
if ($result->num_rows > 0) {
    while($row = $result->fetch_assoc()) {
        $patients[] = $row;
    }
}
echo json_encode($patients);
$conn->close();
?>
