
//-------return button

function goBack(){
  if(window.location.pathname.endsWith(".html")){
    // Récupérer le nom de la page courante
    var currentPage = window.location.pathname.split("/").pop();
    var dest = "./index.html";
    // Vérifier si la page courante est "index.html"
    if (currentPage === "index.html") {
      // Modifier le lien retour vers "../index.html"
      dest = "../index.html";
    }
    window.location.href = dest;
  }
  else{
    const pathname = window.location.pathname;
    var target = pathname.substring(0, pathname.lastIndexOf('/'));
    const currentPage = pathname.split("/").pop();
    if (currentPage == "" || currentPage == null ){
      window.location.href = target+"/../"
    }else {
      window.location.href = target+"/";
    }
  }
}

//--------------Markmap page------------------
//--------iframe for md


// Fonction appelée lors du clic sur le bouton
function toggleIframe(evt) {
  iframe=document.getElementById("iframe")
  // Si l'iframe existe, on la supprime
  if (iframe) {
    iframe.remove();
    iframe = null;
    document.getElementById("mdButton").innerText = "Switch to md in split screen";
    // document.getElementById("fullscreenButton").style.display = "none";
    // document.getElementById("previewButton").innerText = "md in Fullscreen";
  } else {
    // Si l'iframe n'existe pas, on la crée
    var orientation = "bottom";
    if (evt){
      orientation = evt.currentTarget.orientation; 
    }
    console.log(orientation);
    // Obtention de l'URL courante
    var currentUrl = window.location.href;

    // Modification de l'URL pour utiliser le port 1818 et le type de fichier .md
    var newUrl = getSourceTarget();

    // Création de l'élément iframe
    iframe = document.createElement("iframe");
    iframe.setAttribute('id','iframe');

    // Attribution de l'URL modifiée à l'attribut src de l'iframe
    iframe.src = newUrl;

    // Positionnement de l'iframe en bas de page
    iframe.style.position = "fixed";
    
    if (orientation == "left"){
      iframe.style.left = "0";
      iframe.style.bottom = "0";
      iframe.style.top = "85px";
      iframe.style.width = "40%";
      iframe.style.height = "100%";
      iframe.style.resize = "horizontal"; // Permet la redimension en hauteur
    }
    else if (orientation == "right"){
      iframe.style.right = "0";
      iframe.style.bottom = "0";
      iframe.style.top = "85px";
      iframe.style.width = "40%";
      iframe.style.height = "100%";
      iframe.style.resize = "horizontal"; // Permet la redimension en hauteur
    }
    else{ //iframe en bas de l'écran
      iframe.style.bottom = "0";
      iframe.style.left = "0";
      iframe.style.width = "100%";
      iframe.style.height = "50%";
      iframe.style.resize = "vertical"; // Permet la redimension en hauteur
    }

    // Ajout de l'iframe à la fin du corps de la page
    document.body.appendChild(iframe);
    document.getElementById("fullscreenButton").style.display = "inline-block";
  }
}

// Get source file from markmap view
function getSourceTarget(){
  const pathname = window.location.pathname;
  var target = pathname.substring(0, pathname.lastIndexOf('/'));
  const currentPage = pathname.split("/").pop();
  if (window.self !== window.top){ // for iframe
    window.parent.document.body.removeChild(window.frameElement);
  }
  else if (currentPage == "index.html" || currentPage == null ){
    target = target + "/";
  } else {
    source = document.getElementById("source").innerText;
    if (source == ".adoc"){
      target = pathname.replace(".html",".adoc");
    }
    else {
      target = pathname.replace(".html",".md");
    }
  }
  return target;
}

function goPreview(){
  target = getSourceTarget();
  window.location.href = target;
}

// Fonction pour passer en mode plein écran
function toggleFullscreen() {
  iframe=document.getElementById("iframe")
  if (!iframe) {
    toggleIframe();
  }
  if (iframe.requestFullscreen) {
    iframe.requestFullscreen();
  } else if (iframe.mozRequestFullScreen) {
    iframe.mozRequestFullScreen();
  } else if (iframe.webkitRequestFullscreen) {
    iframe.webkitRequestFullscreen();
  } else if (iframe.msRequestFullscreen) {
    iframe.msRequestFullscreen();
  }
}

function openInNewTab() {
  // Get the url of the file used to generate the current markmap
  var newUrl = getSourceTarget();
  console.log(newUrl)

  // Ouverture de la nouvelle page dans un nouvel onglet
  window.open(newUrl, "_blank");
}

if(window.location.pathname.endsWith(".html")){
  // Variable globale pour stocker la référence vers l'iframe
  var iframe = null;

  // Obtention de la référence vers le bouton "ntab"
  var ntabButton = document.getElementById("ntabButton");

  // Ajout d'un écouteur d'événement sur le clic du bouton "ntab"
  ntabButton.addEventListener("click", openInNewTab);

  // Obtention des références vers les boutons
  var lPannel = document.getElementById("leftPanel");
  var rPannel = document.getElementById("rightPanel");
  var bPannel = document.getElementById("bottomPanel");
  // var fullscreenButton = document.getElementById("previewButton");

  // Ajout d'écouteurs d'événements sur le clic des boutons
  lPannel.addEventListener("click", toggleIframe);
  lPannel.orientation = "left";
  rPannel.addEventListener("click", toggleIframe);
  rPannel.orientation = "right";
  bPannel.addEventListener("click", toggleIframe);
  bPannel.orientation = "bottom";
  fullscreenButton.addEventListener("click", goPreview);
}
else{   //--------------markdown preview page------------------
    // Search field
  // Récupérer la référence de l'élément de saisie
  const searchInput = document.getElementById('searchQuery');

  // Ajouter un gestionnaire d'événement pour la touche Entrée
  searchInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
      searchFiles();
    }
  });

  // Récupérer la référence de l'image SVG
  const searchIcon = document.getElementById("magnifier");

  // Ajouter un gestionnaire d'événement pour le clic sur l'image SVG
  searchIcon.addEventListener('click', function() {
    searchFiles();
  });
}

function getCurrentDirectory() {
  console.log(window.self)
   if (window.self !== window.top){ //if load in iframe
    var mapButton = document.getElementById("mapButton");
    mapButton.textContent="Quit";
  }

  const currentURL = window.location.href;
  const serverURL = window.location.origin;

  // Supprimer l'adresse du serveur de l'URL
  let directory = currentURL.replace(serverURL, '');

  // Supprimer les paramètres de fin d'URL
  const queryStringIndex = directory.indexOf('?');
  if (queryStringIndex !== -1) {
    directory = directory.substring(0, queryStringIndex);
  }

  // Supprimer le slash de début si présent
  if (directory.startsWith('/')) {
    directory = directory.substring(1);
  }

  return directory;
}

function goMindmap(){
  const pathname = window.location.pathname;
  var target = pathname.substring(0, pathname.lastIndexOf('/'));
  const currentPage = pathname.split("/").pop();
  if (window.self !== window.top){
    window.parent.document.body.removeChild(window.frameElement);
  }
  if (currentPage == "" || currentPage == null ){
    target = target + "/index.html"
  } else {
    target = pathname.replace(".md",".html");
    target = pathname.replace(".adoc",".html");
  }
  console.log(pathname)
  window.location.href = target
}

function clean_search_div(){
  const resultsContainer = document.getElementById('searchResults');
  resultsContainer.innerHTML = '';

}



// Fonction pour effectuer la recherche textuelle côté client
function searchFiles() {
  const query = document.getElementById('searchQuery').value;
  const url = `/search?query=${encodeURIComponent(query)}&directory=${encodeURIComponent(getCurrentDirectory())}`;
  fetch(url)
    .then(response => {
      if (!response.ok) {
        const resultContainer = document.createElement('div');
        const lineElement = document.createElement('p');
        if (response.status >= 400 && response.status < 500) {
          lineElement.textContent = "Erreur: la recherche est introuvable.";
          throw new Error('Erreur de requête. Statut : ' + response.status);
        } else if (response.status >= 500) {
          lineElement.textContent = "Erreur: Une erreur est survenue lors de la recherche.";
          throw new Error('Erreur du serveur. Statut : ' + response.status);
        }
        resultContainer.appendChild(lineElement);
      }
      return response.json();
    })
    .then(data => {
      const resultsContainer = document.getElementById('searchResults');
      resultsContainer.innerHTML = '';

      if (data.message) {
        resultsContainer.textContent = data.message;
        return;
      }
      
      const remove_button = document.createElement('div');
      remove_button.className = 'div_search_header';
      remove_button.innerHTML = `
      <button class="remove_button" onclick="clean_search_div()">
        <svg viewBox="0 0 448 512" class="svgIcon">
          <path d="M135.2 17.7L128 32H32C14.3 32 0 46.3 0 64S14.3 96 32 96H416c17.7 0 32-14.3 32-32s-14.3-32-32-32H320l-7.2-14.3C307.4 6.8 296.3 0 284.2 0H163.8c-12.1 0-23.2 6.8-28.6 17.7zM416 128H32L53.2 467c1.6 25.3 22.6 45 47.9 45H346.9c25.3 0 46.3-19.7 47.9-45L416 128z">
          </path>
        </svg>
      </button>
      `;
      resultsContainer.appendChild(remove_button);


      data.forEach(result => {
        const resultContainer = document.createElement('div');
        resultContainer.className = 'result, card';



        const fileLink = document.createElement('a');
        fileLink.className = "card1";
        fileLink.href = result.file;
        //fileLink.textContent = result.file;
        resultContainer.appendChild(fileLink);

        const currentTitleElement = document.createElement('p');
        currentTitleElement.textContent = `Page : ${result.currentTitle}`;
        fileLink.appendChild(currentTitleElement);

        const previousTitleElement = document.createElement('p');
        previousTitleElement.textContent = result.previousTitle;
        fileLink.appendChild(previousTitleElement);

        const lineElement = document.createElement('p');
        lineElement.textContent = `Line ${result.line}: ${result.content}`;
        lineElement.className = "small";
        fileLink.appendChild(lineElement);

        const goCornerDiv = document.createElement('div');
        goCornerDiv.className = 'go-corner';
        goCornerDiv.href = result.file;
        goCornerDiv.innerHTML = `
          <div class="go-arrow">
            →
          </div>
        `;
        fileLink.appendChild(goCornerDiv);

        resultsContainer.appendChild(resultContainer);
      });
    })
    .catch(error => console.error('Erreur lors de la recherche :', error));
}

// Open details by default
document.addEventListener('DOMContentLoaded', function () {
  const detailsElements = document.querySelectorAll('details');
  detailsElements.forEach(function (details) {
    details.setAttribute('open', true);
  });
});