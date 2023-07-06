const { debug } = require('console');
const express = require('express');
const fs = require('fs');
const path = require('path');
const showdown = require('showdown');
const app = express();
require('dotenv').config();

const converter = new showdown.Converter();
converter.setOption("ghCompatibleHeaderId", true)
converter.setOption("simplifiedAutoLink", true)
converter.setOption("tables", true)
converter.setOption("smartIndentationFix", true)

function getCss() {
    const css_dir = process.env.CSS_DIR;
    const css_used = process.env.CSS_USED;
    const cssUsedArray = css_used.split(',');
    let result = "";
    console.log(cssUsedArray)
    cssUsedArray.forEach((value, index, array) => {
      result = result + '<link rel="stylesheet" type="text/css" href="' + css_dir + value + '">\n'
    })
    return result;
  }
  
  function encodeHTMLEntities(rawStr) {
    return rawStr.replace(/[\u00A0-\u9999<>\&]/g, ((i) => `&#${i.charCodeAt(0)};`));
  }
  
  function escapeXSS(text) {
    var specialChar = /[ !@$%^&*()+=\[\]{};':"\\|<>\/?~]/;
    lines = text.split('\n');
    text = "";
    isCode = false
    lines.forEach(function (line) {
      if (line.includes("```")) {
        isCode = !isCode
        if (specialChar.test(line)) {  // xss injection via language code bloc input
          console.log(line)
          line = "```text";
        }
      }
      if (!isCode) { // xss in text out of the code bloc
        line = encodeHTMLEntities(line);
      }
      text = text + line + "\n";
    })
    return text;
  }
  
  function escapeBadChar(text) {
    text = text.replace(/\$'/g, function () { //$' broke code block
      return "µ9";
    });
    text = escapeXSS(text)
    return text;
  }
  
  function retieveBadChar(text) {
    text = text.replace(/µ9/g, function () {
      return "$'";
    });
    return text;
  }

  function extractYamlAndMarkdown(md) {
    let isYaml = false;
    let yaml = '';
    let yamlEnd = 0;
    let markdownText = '';
    let result =[];
    const lines = md.split('\n');
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (yamlEnd > 0) {
        markdownText = lines.slice(i-2).join('\n');
        yaml = lines.slice(0, yamlEnd - 1).join('\n');
        console.log(yaml);
        break;
      }
      
      if (line === '') {
        continue;
      } else if (isYaml) {
        yaml += line;
        if (line.trim() === '---') {
          isYaml = false;
        }
      } else if (line.trim() === '---') {
        yaml += line;
        isYaml = true;
      } else {
        console.log(line);
        yamlEnd = i;
      }
    }
    if (yamlEnd == 0){
      markdownText = lines;
    }
    result[0]=yaml;
    result[1]=markdownText;
    return result;
  }

function processMarkdownFile(filePath, res) {
    console.log(filePath);
    fs.readFile(filePath, 'utf-8', (err, data) => {
      if (err) {
        console.error(err);
        return res.status(500).send('Erreur lors de la lecture du fichier Markdown.');
      }
  
      const templatePath = process.env.MD2HTML;
      fs.readFile(templatePath, 'utf-8', (err, htmldata) => {
        if (err) {
          console.error(err);
          return res.status(500).send('Erreur lors de la lecture du template html');
        }
        let content = escapeBadChar(data);
        const parsedContent = extractYamlAndMarkdown(content);
        const markdownContent = parsedContent[1];
        let htmlContent = htmldata;
        htmlContent = htmlContent.replace("$css", getCss());
        htmlContent = htmlContent.replace("$md", converter.makeHtml(markdownContent))
        htmlContent = retieveBadChar(htmlContent);
        res.header('Content-Type', 'text/html'); // Spécifier explicitement le type MIME
        res.send(htmlContent);
      })
  
    });
  }
  
function validateInput(filePath) {
doesExist = fs.existsSync(filePath);
if (doesExist) {
    if (!path.resolve(filePath).startsWith(process.env.PWD)) {
    console.error("lfi attempt via " + filePath);
    return false;
    }
    return true;
} else {
    return false;
}
}
  

const index = (req, res) => {
  const url = decodeURIComponent(req.url);
  let filePath = path.join(process.env.PWD, url);
  const is_valid = validateInput(filePath);

  if (!is_valid) {
    console.log("fichier invalide");
    return res.status(404).send('Fichier introuvable.');
  }

  const extension = path.extname(filePath);
  if (extension === "") {
    console.log("empty");
    filePath = filePath + "Readme.md";
  }

  if (path.extname(filePath) === ".md") {
    return processMarkdownFile(filePath, res);
  } else if (path.extname(filePath) === ".html") {
    return res.sendFile(filePath);
  } else {
    return res.status(404).send("La ressource demandée n'est ni du markdown ni du html");
  }
};

module.exports = {
  index,
};