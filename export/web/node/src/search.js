const fs = require('fs');
const path = require('path');


exports.searchFiles = (req, res) => {
  let searchQuery = req.query.query;
  let currentDirectory = req.query.directory;
  let searchFromCurrentDir = false;
  let searchInTitles = false;
  let unique = false;

  if (!searchQuery) {
    res.status(400).json({ error: 'La requête de recherche est invalide.' });
    return;
  }

  if (searchQuery.includes('>title')) {
    searchInTitles = true;
    searchQuery = searchQuery.replace('>titles', '').trim();
    searchQuery = searchQuery.replace('>title', '').trim();
  }

  if (searchQuery.includes('>unique')) {
    unique = true;
    searchQuery = searchQuery.replace('>unique', '').trim();
  }

  if (searchQuery.includes('>here')) {
    searchFromCurrentDir = true;
    searchQuery = searchQuery.replace('>here', '').trim();
    if (currentDirectory.endsWith('.html') || currentDirectory.endsWith('.md')) {
      let currentDirectory = path.dirname(currentDirectory);
    }
    if (!currentDirectory || !/^[\w/.]+$/.test(currentDirectory) || currentDirectory.includes("..")) {
      res.status(400).json({ error: 'Le répertoire courant est invalide.' });
      return;
    }
  }

  const folderPath = searchFromCurrentDir ? process.env.PWD + "/data/" + currentDirectory : process.env.PWD;
  if (!path.resolve(folderPath).startsWith(process.env.PWD)) {
    console.error("lfi attempt via " + folderPath);
    res.status(400).json({ error: 'La requête de recherche est invalide.' });
    return false;
  }

  // const folderPath = process.env.PWD;

  searchInDirectory(folderPath, searchQuery, searchInTitles, unique)
    .then(matchingFiles => {
      if (matchingFiles.length === 0) {
        res.json({ message: 'Aucun résultat trouvé.' });
      } else {
        res.json(matchingFiles);
      }
    })
    .catch(error => {
      console.error('Erreur lors de la recherche de fichiers :', error);
      res.status(500).json({ error: 'Une erreur est survenue lors de la recherche.' });
    });
};





function searchInDirectory(directoryPath, searchQuery, searchInTitles, unique) {
  return new Promise((resolve, reject) => {
    fs.readdir(directoryPath, (err, files) => {
      if (err) {
        reject(err);
        return;
      }

      const matchingFiles = [];

      const promises = files.map(file => {
        const filePath = path.join(directoryPath, file);

        return new Promise((resolve, reject) => {
          fs.stat(filePath, (err, stats) => {
            if (err) {
              reject(err);
              return;
            }

            if (stats.isDirectory()) {
              searchInDirectory(filePath, searchQuery, searchInTitles, unique)
                .then(results => {
                  matchingFiles.push(...results);
                  resolve();
                })
                .catch(error => reject(error));
            } else if (stats.isFile() && path.extname(file).toLowerCase() === '.md' && path.basename(file).toLocaleLowerCase() != "readme.md") {
              searchInMd(filePath, searchQuery, searchInTitles, unique)
                .then(results => {
                  matchingFiles.push(...results);
                  resolve();
                })
                .catch(error => reject(error));
              } else if (stats.isFile() && path.extname(file).toLowerCase() === '.adoc' && path.basename(file).toLocaleLowerCase() != "readme.adoc") {
                searchInAsciidoc(filePath, searchQuery, searchInTitles, unique)
                  .then(results => {
                    matchingFiles.push(...results);
                    resolve();
                  })
                  .catch(error => reject(error));
            } else {
              resolve();
            }
          });
        });
      });

      Promise.all(promises)
        .then(() => resolve(matchingFiles))
        .catch(error => reject(error));
    });
  });
}

function searchInMd(filePath, searchQuery, searchInTitles, unique) {
  return new Promise((resolve, reject) => {
    fs.readFile(filePath, 'utf8', (err, content) => {
      if (err) {
        reject(err);
        return;
      }

      const lines = content.split('\n');
      let nearTitle = '';
      let currentTitle = '';
      let only_title = searchInTitles;
      let ignore = false; // used to ignore lines
      let isYaml = false;
      let isSummary = false;
      const matchingLines = [];

      lines.forEach((line, index) => {
        line = line.toLowerCase();
        if (isYaml) { // used in the future to search by tag
          if (line == "---") { // end of yaml
            isYaml = false;
            ignore = false;
          }
        }
        if (index < 3 && line == "---" && !isYaml) { // detect start of yaml
          isYaml = true;
          ignore = true;
        }

        if (line.includes("__Summary :__ ")) { // ignore content in summary
          isSummary = true;
          ignore = true;
        }
        if (line.startsWith('#') && !line.toLowerCase().startsWith('#phase')) { // other title level
          nearTitle = line.substring(2).trim();
          if (line.startsWith('# ')) { // Title level 1
            if (isSummary) { // end of summary
              ignore = false;
              isSummary = false;
            }
            currentTitle = nearTitle;
          }
          if (only_title) {
            ignore = false;
          }
        } else if (only_title) {
          ignore = true;
        }
        if (!ignore) {
          if (line.includes(searchQuery.toLowerCase())) {
            if (!line.includes("[") && !line.includes(")")) {
              if (unique) {
                ignore = true;
              }
              matchingLines.push({
                file: filePath.replace( process.env.PWD + "/data", ""),
                line: index + 1,
                content: line.trim().slice(0, 130) + "...",
                nearTitle,
                currentTitle,
              });
            }
          }
        }
      });
      resolve(matchingLines);
    });
  });
}

function searchInAsciidoc(filePath, searchQuery, searchInTitles, unique) {
  return new Promise((resolve, reject) => {
    fs.readFile(filePath, 'utf8', (err, content) => {
      if (err) {
        reject(err);
        return;
      }

      const lines = content.split('\n');
      let nearTitle = '';
      let currentTitle = '';
      let only_title = searchInTitles;
      let ignore = false; // used to ignore lines
      let isYaml = false;
      let isSummary = false;
      const matchingLines = [];

      lines.forEach((line, index) => {
        line = line.toLowerCase();
        //no yaml in asciidoc

        if (line.includes("__Summary :__ ")) { // ignore content in summary
          isSummary = true;
          ignore = true;
        }
        if (line.startsWith('=') && !line.toLowerCase().startsWith('#phase')) { // other title level
          nearTitle = line.substring(2).trim();
          if (line.startsWith('= ')) { // Title level 1
            if (isSummary) { // end of summary
              ignore = false;
              isSummary = false;
            }
            currentTitle = nearTitle;
          }
          if (only_title) {
            ignore = false;
          }
        } else if (only_title) {
          ignore = true;
        }
        if (!ignore) {
          if (line.includes(searchQuery.toLowerCase())) {
            if (!line.includes("[") && !line.includes(")")) {
              if (unique) {
                ignore = true;
              }

              matchingLines.push({
                file: filePath.replace( process.env.PWD + "/data", ""),
                line: index + 1,
                content: line.trim().slice(0, 130) + "...",
                nearTitle,
                currentTitle,
              });
            }
          }
        }
      });
      resolve(matchingLines);
    });
  });
}
