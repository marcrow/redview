require('dotenv').config();

const ignoreContent = (req, res, next) => {


  const ignoredDirectories = process.env.RESTRICTED_DIRECTORIES.split(','); // Ajoutez les répertoires que vous souhaitez ignorer
  const ignoredFiles = process.env.RESTRICTED_FILES.split(","); // Ajoutez les fichiers que vous souhaitez ignorer

  // Récupérer le chemin de la requête
  const requestPath = req.path;
  
  // Vérifier si le chemin correspond à un répertoire ignoré, un fichier caché ou un fichier ignoré
  if (
    ignoredDirectories.some((dir) => requestPath.includes(dir)) ||
    requestPath.split('/').some((part) => part.startsWith('.')) || // ignore hidden files
    ignoredFiles.includes(requestPath.split('/').pop()) // Vérifier le dernier élément du chemin de la requête
  ) {
    // Répondre avec un code 404 (ou toute autre action souhaitée pour ignorer la requête)
    return res.sendStatus(404);
  }
  
  // Poursuivre le traitement de la requête pour les autres répertoires, fichiers non cachés et fichiers non ignorés
  next();
};

module.exports = ignoreContent;
