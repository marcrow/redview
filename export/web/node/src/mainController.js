const { debug } = require('console');
const express = require('express');
const fs = require('fs');
const path = require('path');
const showdown = require('showdown');
// import asciidoctor from 'asciidoctor';
const asciidoctor = require('asciidoctor')
const Asciidoctor = asciidoctor()
const app = express();
require('dotenv').config();
const downdoc = require('downdoc')
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
    text = text.replace(/#\!/g, function () { //$' broke code block
      return "µ8";
    });
    text = escapeXSS(text)
    return text;
  }
  
  function retieveBadChar(text) {
    text = text.replace(/µ9/g, function () {
      return "$'";
    });
    text = text.replace(/µ8/g, function () {
      return "#!";
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
        yamlEnd = i;
        break;
      }
    }
    if (yamlEnd == 0){
      markdownText = lines;
    }
    result[0]=yaml;
    result[1]=markdownText.join("\n");
    return result;
  }

function processAsciidocFile(filePath, res) {
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
      let asciidocContent = escapeBadChar(data);
      //const asciidocContent = extractYamlAndMarkdown(data);
      // const asciidocContent = data;
      let htmlContent = htmldata;
      htmlContent = htmlContent.replace("$css", getCss());
      htmlContent = htmlContent.replace("$md", Asciidoctor.convert(asciidocContent, {'standalone':true}))
      htmlContent = retieveBadChar(htmlContent);
      res.header('Content-Type', 'text/html'); // Spécifier explicitement le type MIME
      res.send(htmlContent);
    })

  });
}

function generateSummary(markdownText) {
  const lines = markdownText.split('\n');
  const sommaire = [];
  let insideCodeBlock = false; // Pour détecter si nous sommes à l'intérieur d'un bloc de code

  lines.forEach(line => {
      // Vérifier les blocs de code
      if (line.trim() === "```") {
          insideCodeBlock = !insideCodeBlock;
          return;
      }
      
      if (insideCodeBlock) return;

      // Détecter les titres en ne prenant en compte que ceux qui ont un espace après le '#'
      const result = /^(\#{1,6})\s+(.*)$/.exec(line);
      if (result) {
          const level = result[1].length;
          const title = result[2];
          sommaire.push({ level, title });
      }
  });

  let output = '## Summary\n';
  sommaire.forEach(item => {
      const indent = '  '.repeat(item.level - 1);
      const link = item.title
          .toLowerCase()
          .replace(/\s+/g, '-')
          .replace(/[^\w\-]/g, '');
      output += `${indent}- [${item.title}](#${link})\n`;
  });

  return output;
}

function generateMarkdownWithSummary(filepath) {
  return new Promise((resolve, reject) => {
      fs.readFile(filepath, 'utf-8', (err, data) => {
          if (err) {
              reject(err);
              return;
          }
          let content = escapeBadChar(data);
          const parsedContent = extractYamlAndMarkdown(content);
          let markdownContent = parsedContent[1];
          if (path.basename(filepath) === "Readme.md"){
            resolve(markdownContent);
          }
          else{
            const summary = generateSummary(markdownContent);
            resolve(summary + "\n\n" + markdownContent);
          }
          
      });
  });
}

function convertMarkdownToHtml(filepath) {
  return generateMarkdownWithSummary(filepath)
      .then(markdownWithSummary => {
          return new Promise((resolve, reject) => {
              const templatePath = process.env.MD2HTML;
              fs.readFile(templatePath, 'utf-8', (err, htmldata) => {
                  if (err) {
                      reject(err);
                      return;
                  }

                  let htmlContent = htmldata;
                  htmlContent = htmlContent.replace("$css", getCss());
                  htmlContent = htmlContent.replace("$md", converter.makeHtml(markdownWithSummary));
                  htmlContent = retieveBadChar(htmlContent);
                  resolve(htmlContent);
              });
          });
      });
}

function processMarkdownFile(filepath, res){
  convertMarkdownToHtml(filepath)
        .then(htmlContent => {
            res.header('Content-Type', 'text/html');
            res.send(htmlContent);
        })
        .catch(err => {
            console.error(err);
            res.status(500).send(err.message);
        });
}




function mdToMarkmap(filePath, res){

  fs.readFile(filePath, 'utf-8', (err, data) => {
    if (err) {
      console.error(err);
      return res.status(500).send('File not found');
    }
    const parsedContent = extractYamlAndMarkdown(data);
    const markdownContent = parsedContent[1];
    let response = ""
    fs.readFile("ressources/template.html", 'utf-8', (err, template) => {
      if (err){
        console.error(err);
        return res.status(500).send('markmap html template not found');
      }
      response = template;
      response = response +  markdownContent;
      response = response + "</script></div><span id='source' hidden='hidden'>.md</span></body></html>";
      res.send(response);

    })

  });
};


function asciiToMarkmap(filePath, res){
  let response = ""
  fs.readFile(filePath, 'utf-8', (err, data) => {
    if (err){
      console.error(err);
      return res.status(500).send('File not found.');
    }
    fs.readFile("ressources/template.html", 'utf-8', (err, template) => {
    if (err){
      console.error(err);
      return res.status(500).send('markmap html template not found');
    }
    response = template;
    response = response +  downdoc(data);
    response = response + "</script></div><span id='source' hidden='hidden'>.adoc</span></body></html>";
    res.send(response);
    })
  })
  
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


function isFileTypeSupported(fileType) {
  if(process.env.SUPPORTED_TYPES){
    const SUPPORTED_TYPES = JSON.parse(process.env.SUPPORTED_TYPES);
    return Object.keys(SUPPORTED_TYPES).includes(fileType.toLowerCase());
  }
  else{
    return {}
  }

}

function isFileTypeIsAuthorized(fileType){
  const AUTHORIZED_TYPES = process.env.AUTHORIZED_TYPES;
  if (AUTHORIZED_TYPES) {
      const typesList = AUTHORIZED_TYPES.split(',');
      return typesList.includes(fileType.toLowerCase());
  }
  return false;
}

function generateSupportedContent(type, filePath, req, res){
  const prismLanguages = JSON.parse(process.env.SUPPORTED_TYPES);
  const prismLanguageKey = type.toLowerCase();
  const prismLanguageValue = prismLanguages[prismLanguageKey];
  const fileContent = ""
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
          data = '```'+ prismLanguageValue + "\n"+data + '\n```\n'

          let content = escapeBadChar(data);
          let htmlContent = htmldata;
          htmlContent = htmlContent.replace("$css", getCss());
          htmlContent = htmlContent.replace("$md", converter.makeHtml(content))
          htmlContent = retieveBadChar(htmlContent);
          res.header('Content-Type', 'text/html'); // Spécifier explicitement le type MIME
          res.send(htmlContent);
      })
  })
}



function return404(res,text = "Not supported type"){
  return res.status(404).send(text);
}

function extractFileType(filename) {
  const fileExtension = filename.split('.').pop();
  return fileExtension.toLowerCase();
}

function otherFilesResponder(req, res){
    const url = decodeURIComponent(req.url);
    let filePath = path.join(process.env.PWD, url);
    const type = extractFileType(filePath);
    if(isFileTypeSupported(type)){
        return generateSupportedContent(type, filePath,req, res)
    }
    else if(isFileTypeIsAuthorized(type)){
        return res.sendFile(filePath);
    }
    else{
      return return404(res);
    }
}

const resources = (req,res) => {
  const url = decodeURIComponent(req.url);
  let filePath = path.join(process.env.PWD, url);
  const is_valid = validateInput(filePath);
  if (!is_valid && extension != ".html") { //except html because markmap from adoc is generate in real-time
      return res.status(404).send('File not found.'+extension);
  }
  return res.sendFile(filePath);

};

const index = (req, res) => {
  const url = decodeURIComponent(req.url);
  let filePath = path.join(process.env.PWD, "/data");
  filePath = path.join(filePath, url);

  // if (!is_valid) {
  //   const alternateFilePath = filePath.replace('.html', '.adoc'); 
  //   if (!validateInput(alternateFilePath)){
  //     console.log("fichier invalide :(");
  //     return res.status(404).send('File not found.');
  //   }
  // }

  const extension = path.extname(filePath);
  if (extension === "") {
    console.log("empty");
    filePath = filePath + "Readme.md";
  }

  const is_valid = validateInput(filePath);
  if (!is_valid && extension != ".html") { //except html because markmap from adoc is generate in real-time
      return res.status(404).send('File not found.'+extension);
  }

  if (path.extname(filePath) === ".md") {
    return processMarkdownFile(filePath, res);
  } else if (path.extname(filePath) === ".html") {
    // if the file exists deliver it, else test if adoc exists then if md exists else return 404. If md or adoc file exist, then return markmap file
    fs.access(filePath, fs.constants.F_OK, (err) => {
      if (err){
        const alternateFilePath = filePath.replace('.html', '.adoc');
        fs.access(alternateFilePath, fs.constants.F_OK, (err) => {
          if (err) {
            const alternateFilePath = filePath.replace('.html', '.md');
            fs.access(alternateFilePath, fs.constants.F_OK, (err) => {
              if (err) {
                return res.status(404).send('File not found.');
              }else{
                mdToMarkmap(alternateFilePath, res);
              }})
          }else{
              asciiToMarkmap(alternateFilePath, res);
          }})
      } else{
          return res.sendFile(filePath);
      }  
    })

  } else if (path.extname(filePath) == ".adoc") {
    return processAsciidocFile(filePath,res);
  }
  else {
    return otherFilesResponder(req, res);
    //return res.status(404).send("La ressource demandée n'est ni du markdown ni du html");
  }
};

module.exports = {
  index,resources
};