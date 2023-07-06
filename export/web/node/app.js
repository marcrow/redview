// app.js

const express = require('express');
const app = express();
const routes = require('./routes');
const ignoreContent = require('./src/ignoreContent');

// Configuration et middleware
// Ignore les fichiers caché et des listes de répertoires et de fichiers
app.use(ignoreContent);

// Configuration des vues (si vous utilisez des templates)
// app.set('view engine', 'ejs');
// app.set('views', path.join(__dirname, 'views'));


// Middleware pour le parsing des requêtes JSON
app.use(express.json());

// Middleware pour le parsing des requêtes URL encodées
app.use(express.urlencoded({ extended: true }));

// Middleware pour servir les fichiers statiques
app.use('/ressources', express.static('ressources'));
app.use('/img', express.static('img'));

// Routes
app.use('/', routes);

module.exports = app;