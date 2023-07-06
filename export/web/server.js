// server.js

const app = require('./node/app');
const port = process.env.PORT || 3000;

// Démarrage du serveur
app.listen(port, () => {
  console.log(`Serveur démarré sur le port ${port}`);
});