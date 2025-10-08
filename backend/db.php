<?php
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "ehr_db";

$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error) {
    die(json_encode(["success"=>false,"message"=>"DB Connection Failed"]));
}
?>
