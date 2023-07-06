// routes/index.js

const express = require('express');
const router = express.Router();
const mainController = require('../src/mainController');
const searchController = require('../src/search');

router.get('/search', searchController.searchFiles);
// Route principale
router.get('/*', mainController.index);

// Autres routes
// router.get('/users', mainController.getUsers);
// router.post('/users', mainController.createUser);
// ...

module.exports = router;