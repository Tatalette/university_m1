<?php

function sendBinaryRequest($host, $port, $data) {
    $socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
    
    if ($socket === false) {
        throw new Exception("Erreur création socket: " . socket_strerror(socket_last_error()));
    }
    
    // Connexion
    $result = socket_connect($socket, $host, $port);
    if ($result === false) {
        throw new Exception("Erreur connexion: " . socket_strerror(socket_last_error($socket)));
    }
    
    // Envoi des données binaires
    socket_write($socket, $data, strlen($data));
    
    // Réception de la réponse
    $response = '';
    while ($buf = socket_read($socket, 2048)) {
        $response .= $buf;
        if (strlen($buf) < 2048) break;
    }
    
    socket_close($socket);
    return $response;
}

// Exemple d'utilisation
try {
    // Données binaires exemple
    $binaryData = hex2bin("48656c6c6f20576f726c64"); // "Hello World" en hex
    
    $response = sendBinaryRequest('example.com', 80, $binaryData);
    
    echo "Réponse reçue (" . strlen($response) . " bytes):\n";
    echo bin2hex($response) . "\n";
    
} catch (Exception $e) {
    echo "Erreur: " . $e->getMessage() . "\n";
}