// app.js

const express = require('express');
const app = express();
const routes = require('./routes');
const ignoreContent = require('./src/ignoreContent');
const process = require('process');

// Configuration et middleware
// Ignore hidden files and specific directories and files set in .env
app.use(ignoreContent);

// Middleware pour le parsing des requêtes JSON
app.use(express.json());

// Middleware pour le parsing des requêtes URL encodées
app.use(express.urlencoded({ extended: true }));


app.use('/ressources', express.static('ressources'));



const DATA_PATH = process.env.DATA_PATH || '';
// Change working directory (used by docker)
if(DATA_PATH!=""){
    process.chdir(DATA_PATH);
}

app.use('/img', express.static('data/img'));


// Routes
app.use('/', routes);

module.exports = app;