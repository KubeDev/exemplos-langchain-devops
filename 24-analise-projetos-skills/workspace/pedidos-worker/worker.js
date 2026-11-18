const express = require("express");

const app = express();
const porta = process.env.PORT || 8080;
let processados = 0;

// Simula o consumo da fila: um pedido a cada 2 segundos.
setInterval(() => {
  processados += 1;
  console.log(`pedido ${processados} processado`);
}, 2000);

app.get("/healthz", (req, res) => res.json({ status: "ok", processados }));

app.listen(porta, () => console.log(`pedidos-worker na porta ${porta}`));
