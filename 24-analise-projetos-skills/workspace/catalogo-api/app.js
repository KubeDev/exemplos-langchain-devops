const express = require("express");

const app = express();
const porta = process.env.PORT || 3000;

const produtos = [
  { id: 1, nome: "Teclado", preco: 250 },
  { id: 2, nome: "Monitor", preco: 1200 },
];

app.get("/health", (req, res) => res.json({ status: "ok" }));
app.get("/produtos", (req, res) => res.json(produtos));

app.listen(porta, () => console.log(`catalogo-api na porta ${porta}`));
