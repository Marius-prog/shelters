// At the top of your file
var map = L.map('map', {
    zoomControl: false,
    center: [55.1694, 23.8813],
    zoom: window.innerWidth <= 768 ? 5 : 7,
    minZoom: window.innerWidth <= 768 ? 5 : 7,
    maxZoom: 16
});

// Add tile layer once
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© Morelo'
}).addTo(map);


// Remove fitBounds to use the initial zoom level from map initialization

// Generate QR Code
function generateQRCode() {
    const websiteUrl = "https://www.slepk.lt";
    const qr = qrcode(0, 'M');
    qr.addData(websiteUrl);
    qr.make();

    const qrContainer = document.getElementById('qrCode');
    const qrImage = qrContainer.querySelector('.qr-code-image');
    qrImage.innerHTML = qr.createImgTag(4);
}

// Update QR code title with current language
function updateQRCodeTitle(lang) {
    const qrTitle = document.querySelector('.qr-code-title');
    qrTitle.textContent = translations[lang].qrCodeText;
}

// Update the switchLanguage function to include QR code title
function switchLanguage(lang) {
    // ... existing language switch code ...

    // Update QR code title
    updateQRCodeTitle(lang);

    // Save preference
    localStorage.setItem('preferredLanguage', lang);
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Generate QR code
    generateQRCode();

    // Set initial language for QR code title
    const savedLang = localStorage.getItem('preferredLanguage') || 'lt';
    updateQRCodeTitle(savedLang);

    // ... rest of your existing initialization code ...
});


// Initialize the map with mobile detection
var isMobile = window.innerWidth <= 768;


// Function to adjust map for mobile with exact same smooth transition
function adjustMapForMobile() {
    const newZoom = window.innerWidth <= 768 ? 6 : 8;

    map.flyTo([55.1694, 23.8813], 8, {
        duration: 1.5,
        easeLinearity: 0.25
    });
}

// Simple debounced resize handler
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(adjustMapForMobile, 150); // Same 150ms delay as filter title
});


// Try using a simpler GeoJSON source
fetch('https://nominatim.openstreetmap.org/search?country=lithuania&format=geojson&polygon_geojson=1')
    .then(response => response.json())
    .then(data => {
        if (data && data.features && data.features.length > 0) {
            var lithuaniaBorder = L.geoJSON(data.features[0].geometry, {
                style: function() {
                    return {
                        color: 'rgb(100, 149, 237)', // Pure green in RGB
                        weight: 5,
                        opacity: 1,
                        fill: false
                    };
                }
            }).addTo(map);

            // map.fitBounds(lithuaniaBorder.getBounds(), {
            //     padding: [20, 20]
            // });
        }
    })
    .catch(error => console.error('Error:', error));

var markers = L.markerClusterGroup();


// Get the sheltersData from the window object (already parsed in the template)
var shelters = window.sheltersData;

// Verify shelter data is loaded
if (shelters && shelters.features && shelters.features.length > 0) {
    console.log('Processing', shelters.features.length, 'shelter features');
} else {
    console.error('No shelter features found or invalid data format');
    shelters = {
        "type": "FeatureCollection",
        "features": []
    };
}

function updateStatistics(features) {
    var visibleShelters = features.length;
    var totalCapacity = features.reduce(function(sum, feature) {
        var capacity = parseFloat(feature.properties.capacity);
        return sum + (isNaN(capacity) ? 0 : capacity);
    }, 0);

    document.getElementById('shelterCount').textContent =
        visibleShelters.toLocaleString('lt-LT');
    document.getElementById('capacityCount').textContent =
        Math.round(totalCapacity).toLocaleString('lt-LT');
}

function createMarkers(geojsonData) {
    var geoJsonLayer = L.geoJSON(geojsonData, {
        onEachFeature: function(feature, layer) {
            var props = feature.properties;
            var coordinates = feature.geometry.coordinates;
            var capacity = props.capacity ? parseFloat(props.capacity) : 0;

            var popupContent = `
                <div class="popup-content">
                    <h4>${props.purpose || 'Shelter'}</h4>
                    <p><strong>adresas:</strong> ${props.address}</p>
                    <p><strong>savivaldybė:</strong> ${props.municipality}</p>
                    <p><strong>plotas m²:</strong> ${capacity ? capacity.toLocaleString('lt-LT') : 'N/A'}</p>
                    <p><strong>stovis:</strong> ${props.condition || 'N/A'}</p>
                    <button 
                        class="view-street-btn" 
                        onclick="showStreetView(${coordinates[1]}, ${coordinates[0]})">
                        Gatvės vaizdas
                    </button>
                </div>
            `;
            layer.bindPopup(popupContent);
        }
    });

    markers.addLayer(geoJsonLayer);
    map.addLayer(markers);
}

function filterMarkers() {
    var selectedMunicipality = document.getElementById('municipalityFilter').value;

    var filteredFeatures = shelters.features.filter(function(feature) {
        return !selectedMunicipality ||
            feature.properties.municipality === selectedMunicipality;
    });

    
    markers.clearLayers();

    var filteredGeoJson = {
        type: "FeatureCollection",
        features: filteredFeatures
    };

    createMarkers(filteredGeoJson);
    updateStatistics(filteredFeatures);
}

// Add event listeners for map interactions
markers.on('clusterclick', function(e) {
    var clusterFeatures = [];
    e.layer.getAllChildMarkers().forEach(function(marker) {
        if (marker.feature) {
            clusterFeatures.push(marker.feature);
        }
    });
    updateStatistics(clusterFeatures);
});

map.on('moveend', function() {
    var visibleFeatures = [];
    markers.eachLayer(function(layer) {
        if (map.getBounds().contains(layer.getLatLng()) && layer.feature) {
            visibleFeatures.push(layer.feature);
        }
    });
    updateStatistics(visibleFeatures);
});

// Add event listener for municipality filter
document.getElementById('municipalityFilter').addEventListener('change', filterMarkers);

// Initialize with all data
createMarkers(shelters);
updateStatistics(shelters.features);

// Update statistics when clicking on individual markers
markers.on('click', function(e) {
    if (e.layer.feature) {
        // If clicking on a single marker
        updateStatistics([e.layer.feature]);
    }
});

// Update statistics when closing a popup
map.on('popupclose', function() {
    // Revert to showing statistics for all visible markers
    var visibleFeatures = [];
    markers.eachLayer(function(layer) {
        if (map.getBounds().contains(layer.getLatLng()) && layer.feature) {
            visibleFeatures.push(layer.feature);
        }
    });
    updateStatistics(visibleFeatures);
});

// Update statistics when zooming
map.on('zoomend', function() {
    var visibleFeatures = [];
    markers.eachLayer(function(layer) {
        if (map.getBounds().contains(layer.getLatLng()) && layer.feature) {
            visibleFeatures.push(layer.feature);
        }
    });
    updateStatistics(visibleFeatures);
});

// Theme toggle functionality
const themeToggle = document.getElementById('themeToggle');
const sunPath = themeToggle.querySelector('.sun');
const moonPath = themeToggle.querySelector('.moon');

// Check for saved theme preference
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);
updateThemeIcon(savedTheme);

themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
});

function updateThemeIcon(theme) {
    if (theme === 'dark') {
        sunPath.style.display = 'none';
        moonPath.style.display = 'block';
    } else {
        sunPath.style.display = 'block';
        moonPath.style.display = 'none';
    }
}

// Update translations object
const translations = {
    lt: {
        title: "Lietuvos priedangų žemėlapis",
        shelterCount: "Priedangų skaičius",
        totalArea: "Bendras plotas m²",
        filterHeader: "Pasirink savivaldybę",
        allMunicipalities: "Visos savivaldybės",
        infoHeader: "Priedangų informacija",
        qrCodeText: "Skanuok ir atidaryk telefone",
        shelterButton: "Priedanga",
        shelterModalTitle: "Kas yra priedanga?",
        shelterModalDesc: "Priedanga - tai specialiai įrengta arba tam pritaikyta statinio patalpa, kurioje gyventojai gali laikinai slėptis nuo karo grėsmių.",
        shelterTypes: "Priedangos gali būti:",
        shelterType1: "Rūsiai",
        shelterType2: "Požeminės automobilių stovėjimo aikštelės",
        shelterType3: "Požeminės pėsčiųjų perėjos",
        shelterType4: "Kitos požeminės erdvės"
    },
    en: {
        title: "Lithuania Shelter Map",
        shelterCount: "Number of Shelters",
        totalArea: "Total Area m²",
        filterHeader: "Select Municipality",
        allMunicipalities: "All Municipalities",
        infoHeader: "Shelter Information",
        qrCodeText: "Scan to open on phone",
        shelterButton: "Shelter",
        shelterModalTitle: "What is a shelter?",
        shelterModalDesc: "A shelter is a specially equipped or adapted building space where residents can temporarily take refuge from war threats.",
        shelterTypes: "Shelters can be:",
        shelterType1: "Basements",
        shelterType2: "Underground parking lots",
        shelterType3: "Underground pedestrian crossings",
        shelterType4: "Other underground spaces"
    },
    ru: {
        title: "Ката убежищ Литвы",
        shelterCount: "Количество убежищ",
        totalArea: "Общая площадь м²",
        filterHeader: "Выберите муниципалитет",
        allMunicipalities: "Все муниципалитеты",
        infoHeader: "Информация об убежищах",
        qrCodeText: "Сканируйте для открытия на телефоне",
        shelterButton: "Убежище",
        shelterModalTitle: "Что такое убежище?",
        shelterModalDesc: "Убежище - это специально оборудованное или приспособленное помещение здания, где жители могут временно укрыться от военных угроз.",
        shelterTypes: "Убежища могут быть:",
        shelterType1: "Подвалы",
        shelterType2: "Подземные парковки",
        shelterType3: "Подземные пешеходные переходы",
        shelterType4: "Другие подземные помещения"
    },
    pl: {
        title: "Mapa schronów Litwy",
        shelterCount: "Liczba schronów",
        totalArea: "Całkowita powierzchnia m²",
        filterHeader: "Wybierz gminę",
        allMunicipalities: "Wszystkie gminy",
        infoHeader: "Informacja o schronach",
        qrCodeText: "Zeskanuj, aby otworzyć w telefonie",
        shelterButton: "Schron",
        shelterModalTitle: "Co to jest schron?",
        shelterModalDesc: "Schron to specjalnie wyposażone lub zaadaptowane pomieszczenie budynku, w którym mieszkańcy mogą tymczasowo schronić się przed zagrożeniami wojennymi.",
        shelterTypes: "Schrony mogą być:",
        shelterType1: "Piwnice",
        shelterType2: "Podziemne parkingi",
        shelterType3: "Podziemne przejścia dla pieszych",
        shelterType4: "Inne przestrzenie podziemne"
    }
};

// Function to update all translations
function switchLanguage(lang) {
    // Update text content
    document.getElementById('mapTitle').textContent = translations[lang].title;
    document.querySelector('.filter-control h3').textContent = translations[lang].filterHeader;

    // Update QR code title
    document.querySelector('.qr-code-title').textContent = translations[lang].qrCodeText;

    // Update statistics
    const stats = document.querySelector('.info-panel');
    stats.querySelector('p:nth-child(2)').innerHTML =
        `${translations[lang].shelterCount}: <span id="shelterCount">${document.getElementById('shelterCount').textContent}</span>`;
    stats.querySelector('p:nth-child(3)').innerHTML =
        `${translations[lang].totalArea}: <span id="capacityCount">${document.getElementById('capacityCount').textContent}</span>`;

    // Update municipality dropdown
    const select = document.getElementById('municipalityFilter');
    const currentValue = select.value;

    // Update "All municipalities" option
    select.options[0].text = translations[lang].allMunicipalities;

    // Get all municipalities
    const municipalities = [...new Set(shelters.features.map(f => f.properties.municipality))].sort();

    // Clear existing options except first one
    while (select.options.length > 1) {
        select.remove(1);
    }

    // Add municipality options
    municipalities.forEach(municipality => {
        const option = document.createElement('option');
        option.value = municipality;
        option.textContent = municipality;
        select.appendChild(option);
    });

    // Restore selected value
    select.value = currentValue;

    // Save preference
    localStorage.setItem('preferredLanguage', lang);

    // Update info panel header
    document.querySelector('.info-panel h3').textContent = translations[lang].infoHeader;

    // Update shelter button and modal content
    document.getElementById('shelterInfoBtn').textContent = translations[lang].shelterButton;
    document.querySelector('#shelterInfoModal h2').textContent = translations[lang].shelterModalTitle;

    // Update modal body content
    const modalBody = document.querySelector('.modal-body');
    modalBody.innerHTML = `
        <p>${translations[lang].shelterModalDesc}</p>
        <p>${translations[lang].shelterTypes}</p>
        <ul>
            <li>${translations[lang].shelterType1}</li>
            <li>${translations[lang].shelterType2}</li>
            <li>${translations[lang].shelterType3}</li>
            <li>${translations[lang].shelterType4}</li>
        </ul>
    `;
}

// Add this after your existing municipality filter code
const municipalitySettings = {
    'Vilniaus m.': { coords: [54.687157, 25.279652], zoom: 12 },
    'Kauno m.': { coords: [54.8985, 23.9036], zoom: 12 },
    'Klaipėdos m.': { coords: [55.7033, 21.1443], zoom: 12 },
    'Šiaulių m.': { coords: [55.9349, 23.3137], zoom: 13 },
    'Panevėžio m.': { coords: [55.7333, 24.3500], zoom: 13 },
    'Alytaus m.': { coords: [54.3963, 24.0459], zoom: 13 },
    'Marijampolės': { coords: [54.5599, 23.3501], zoom: 13 },
    'Utenos r.': { coords: [55.4675, 25.5989], zoom: 11 },
    'Telšių r.': { coords: [55.9814, 22.2489], zoom: 11 },
    'Tauragės r.': { coords: [55.2522, 22.2897], zoom: 11 },
    // Add more municipalities with custom zoom levels
};

document.getElementById('municipalityFilter').addEventListener('change', function(e) {
    const selectedMunicipality = e.target.value;

    if (selectedMunicipality && municipalitySettings[selectedMunicipality]) {
        const settings = municipalitySettings[selectedMunicipality];

        // Fly to the selected municipality with custom zoom
        map.flyTo(settings.coords, settings.zoom, {
            duration: 1.5,
            easeLinearity: 0.25
        });
    } else {
        // Reset to default view of Lithuania
        map.flyTo([55.1694, 23.8813], 8, {
            duration: 1.5,
            easeLinearity: 0.25
        });
    }
});

// Initialize language on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedLang = localStorage.getItem('preferredLanguage') || 'lt';
    switchLanguage(savedLang);

    // Language selector event listener
    document.getElementById('languageSelect').addEventListener('change', function(e) {
        switchLanguage(e.target.value);
    });
});

function resetFilter() {
    const municipalityFilter = document.getElementById('municipalityFilter');
    municipalityFilter.value = ''; // Reset to default option

    // Trigger the change event to update the map
    const event = new Event('change');
    municipalityFilter.dispatchEvent(event);
}


// Add this right after map initialization
map.createPane('municipalitiesPane');
map.getPane('municipalitiesPane').style.zIndex = 200; // Below markers
// map.getPane('municipalitiesPane').style.pointerEvents = 'none';


// Add this right after your map initialization
let panorama;
let streetViewService;

// Initialize Google Maps services
function initializeGoogleMaps() {
    try {
        if (typeof google !== 'undefined' && google.maps) {
            streetViewService = new google.maps.StreetViewService();
            console.log('Google Maps initialized successfully');
        } else {
            console.warn('Google Maps API not loaded, Street View will use fallback');
        }
    } catch (error) {
        console.error('Error initializing Google Maps:', error);
    }
}

// Make sure this function is available globally
window.initializeGoogleMaps = initializeGoogleMaps;

// Update your createMarkers function
function createMarkers(geojsonData) {
    var geoJsonLayer = L.geoJSON(geojsonData, {
        onEachFeature: function(feature, layer) {
            var props = feature.properties;
            var coordinates = feature.geometry.coordinates;
            var capacity = props.capacity ? parseFloat(props.capacity) : 0;

            var popupContent = `
                <div class="popup-content">
                    <h4>${props.purpose || 'Shelter'}</h4>
                    <p><strong>adresas:</strong> ${props.address}</p>
                    <p><strong>savivaldybė:</strong> ${props.municipality}</p>
                    <p><strong>plotas m²:</strong> ${capacity ? capacity.toLocaleString('lt-LT') : 'N/A'}</p>
                    <p><strong>stovis:</strong> ${props.condition || 'N/A'}</p>
                    <button 
                        class="view-street-btn" 
                        onclick="showStreetView(${coordinates[1]}, ${coordinates[0]})">
                        Gatvės vaizdas
                    </button>
                </div>
            `;
            layer.bindPopup(popupContent);
        }
    });
    markers.addLayer(geoJsonLayer);
    map.addLayer(markers);
}

// Street View function - make it globally available
window.showStreetView = function(lat, lng) {
    console.log('Opening street view for:', lat, lng);

    // Make sure the coordinates are in a valid range
    // If they appear to be swapped, fix them
    if (Math.abs(lat) > 90) {
        // Coordinates are swapped
        const temp = lat;
        lat = lng;
        lng = temp;
        console.log('Coordinates were swapped, now using:', lat, lng);
    }

    const modal = document.getElementById('streetViewModal');
    const container = document.getElementById('street-view-container');

    // Clear previous content
    container.innerHTML = '';

    // Check if Google Maps API is loaded
    if (typeof google !== 'undefined' && google.maps && google.maps.StreetViewPanorama) {
        // Use Google Maps JavaScript API (better experience)
        const position = { lat: lat, lng: lng };

        panorama = new google.maps.StreetViewPanorama(container, {
            position: position,
            pov: { heading: 34, pitch: 10 },
            zoom: 1,
            addressControl: true,
            linksControl: true,
            panControl: true,
            enableCloseButton: false,
            fullscreenControl: true
        });

        console.log('Using Google Maps JavaScript API for Street View');
    } else {
        // Fallback to iframe embed
        const iframe = document.createElement('iframe');
        iframe.style.width = '100%';
        iframe.style.height = '100%';
        iframe.style.border = 'none';

        // Use the direct Street View URL format with correct coordinates
        const streetViewUrl = `https://www.google.com/maps/embed?pb=!4v1709221839755!6m8!1m7!1s!2m2!1d${lat}!2d${lng}!3f0!4f0!5f0.8`;

        iframe.src = streetViewUrl;
        container.appendChild(iframe);

        console.log('Using iframe fallback for Street View');
    }

    modal.style.display = 'block';
}

// Add modal close handlers
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('streetViewModal');
    const closeBtn = document.querySelector('.street-view-close');

    function closeModal() {
        modal.style.display = 'none';
        document.getElementById('street-view-container').innerHTML = '';
    }

    closeBtn.onclick = closeModal;

    window.onclick = function(event) {
        if (event.target === modal) {
            closeModal();
        }
    };

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modal.style.display === 'block') {
            closeModal();
        }
    });
});



// Get modal elements
var modal = document.getElementById("shelterInfoModal");
var btn = document.getElementById("shelterInfoBtn");
var span = document.getElementsByClassName("close")[0];

// Open modal
btn.onclick = function() {
    modal.style.display = "block";
}

// Close modal with X
span.onclick = function() {
    modal.style.display = "none";
}



// Get modal elements
var streetViewModal = document.getElementById("streetViewModal");
var streetViewClose = document.querySelector('.street-view-close');

// Close modal with X
streetViewClose.onclick = function() {
    streetViewModal.style.display = "none";
}


document.addEventListener('DOMContentLoaded', function() {
    // Logo click handler
    document.querySelector('.logo').addEventListener('click', function() {
        this.classList.add('clicked');
        setTimeout(() => {
            map.flyTo([55.1694, 23.8813], 8, {
                duration: 1.5,
                easeLinearity: 0.25
            });
            // Remove the extra setTimeout and use map's moveend event instead
            // map.once('moveend', () => {
            //     window.location.reload();
            // });
        }, 150);
    });

    // Header title click handler
    document.querySelector('.header-title').addEventListener('click', function() {
        this.classList.add('clicked');
        setTimeout(() => {
            map.flyTo([55.1694, 23.8813], 8, {
                duration: 1.5,
                easeLinearity: 0.25
            });
            // Remove the extra setTimeout and use map's moveend event instead
            // map.once('moveend', () => {
            //     window.location.reload();
            // });
        }, 150);
    });

    // Filter header click handler (unchanged)
    document.querySelector('.filter-header').addEventListener('click', function() {
        this.classList.add('clicked');
        setTimeout(() => {
            const municipalityFilter = document.getElementById('municipalityFilter');
            municipalityFilter.value = '';
            map.flyTo([55.1694, 23.8813], 8, {
                duration: 1.5,
                easeLinearity: 0.25
            });
            municipalityFilter.dispatchEvent(new Event('change'));
        }, 150);
    });
});