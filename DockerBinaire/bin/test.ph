<?php

// Test avec des sockets TCP brutes
function testRawSocket() {
    $host = 'www.google.com';
    $port = 80;
    
    // Création de la requête HTTP brute
    $request = "GET / HTTP/1.1\r\n";
    $request .= "Host: $host\r\n";
    $request .= "Connection: close\r\n\r\n";
    
    $socket = fsockopen($host, $port, $errno, $errstr, 30);
    
    if (!$socket) {
        echo "Erreur: $errstr ($errno)\n";
        return;
    }
    
    fwrite($socket, $request);
    
    echo "Réponse :\n";
    while (!feof($socket)) {
        echo fgets($socket, 128);
    }
    
    fclose($socket);
}

testRawSocket();