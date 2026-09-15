// Aircraft Tracking Module
// This module adds real-time aircraft tracking to the map

(function() {
    'use strict';

    // Aircraft layer will be created when map is ready
    var aircraftLayer = null;

    // Cache for aircraft photos
    var photoCache = {};

    // Track currently open popup
    var openPopupHex = null;

    // Function to fetch aircraft photo
    function fetchAircraftPhoto(registration, callback) {
        // Check cache first
        if (photoCache.hasOwnProperty(registration)) {
            callback(photoCache[registration]);
            return;
        }

        // Don't fetch if no registration
        if (!registration || registration === 'N/A') {
            photoCache[registration] = null;
            callback(null);
            return;
        }

        // Fetch from PlaneSpotters API
        var apiUrl = 'https://api.planespotters.net/pub/photos/reg/' + registration;
        fetch(apiUrl)
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Photo API error');
                }
                return response.json();
            })
            .then(function(data) {
                var photoUrl = null;
                if (data.photos && data.photos.length > 0) {
                    photoUrl = data.photos[0].thumbnail_large ? data.photos[0].thumbnail_large.src : null;
                }
                photoCache[registration] = photoUrl;
                callback(photoUrl);
            })
            .catch(function(error) {
                photoCache[registration] = null;
                callback(null);
            });
    }

    // Function to get color based on altitude
    function getAltitudeColor(altitude) {
        if (altitude < 10000) {
            return '#00ff00'; // Green - Low altitude
        } else if (altitude < 25000) {
            return '#ffa500'; // Orange - Medium altitude
        } else if (altitude < 40000) {
            return '#0080ff'; // Blue - High altitude
        } else {
            return '#ff00ff'; // Magenta - Very high altitude
        }
    }

    // Function to convert degrees to compass direction
    function getCompassDirection(degrees) {
        var directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
        var index = Math.round(degrees / 45) % 8;
        return directions[index];
    }

    // Function to get country from registration prefix
    function getCountryFromRegistration(registration) {
        if (!registration || registration === 'N/A') return null;

        var countryMap = {
            'D-': 'Germany', 'N': 'USA', 'G-': 'UK', 'F-': 'France',
            'EC-': 'Spain', 'I-': 'Italy', 'PH-': 'Netherlands', 'OO-': 'Belgium',
            'OY-': 'Denmark', 'SE-': 'Sweden', 'LN-': 'Norway', 'OH-': 'Finland',
            'EI-': 'Ireland', 'HB-': 'Switzerland', 'OE-': 'Austria', 'SP-': 'Poland',
            'YR-': 'Romania', 'HA-': 'Hungary', 'OK-': 'Czech Republic', 'OM-': 'Slovakia',
            'LY-': 'Lithuania', 'YL-': 'Latvia', 'ES-': 'Estonia', 'UR-': 'Ukraine',
            'RA-': 'Russia', 'VQ-': 'UK (Bermuda)', 'VP-': 'UK (Various)', 'C-': 'Canada',
            'TC-': 'Turkey', 'T.': 'Turkey (Mil)', '4X-': 'Israel', 'SX-': 'Greece',
            'CS-': 'Portugal', 'CR-': 'Portugal', 'CT-': 'Portugal',
            'A6-': 'UAE', 'A7-': 'Qatar', 'HZ-': 'Saudi Arabia', 'ET-': 'Ethiopia',
            'JA': 'Japan', 'HL': 'South Korea', 'B-': 'China', 'VT-': 'India',
            '9H-': 'Malta'
        };

        // Check military patterns
        if (/^\d{2}\+\d{2}$/.test(registration)) return 'Germany (Mil)'; // German military format
        if (registration.startsWith('T.')) return 'Turkey (Mil)';
        if (registration.startsWith('MM')) return 'Italy (Mil)';
        if (registration.startsWith('ZM') || registration.startsWith('ZZ') || registration.startsWith('ZJ') || registration.startsWith('ZK')) return 'UK (Mil)';
        if (/^[0-9]{2,3}$/.test(registration)) return 'France (Mil)';
        if (/^R[A-Z][0-9]{5}$/.test(registration)) return 'Russia (Mil)';

        for (var prefix in countryMap) {
            if (registration.startsWith(prefix)) {
                return countryMap[prefix];
            }
        }
        return null;
    }

    // Function to check if aircraft is military
    function isMilitary(registration, category) {
        if (!registration || registration === 'N/A') return false;

        // Military registration patterns
        if (/^\d{2}\+\d{2}$/.test(registration)) return true; // German military
        if (registration.startsWith('T.')) return true; // Turkish military
        if (registration.startsWith('MM')) return true; // Italian military
        if (registration.startsWith('ZM') || registration.startsWith('ZZ') || registration.startsWith('ZJ') || registration.startsWith('ZK')) return true; // UK military
        if (/^[0-9]{2,3}$/.test(registration)) return true; // French military
        if (/^R[A-Z][0-9]{5}$/.test(registration)) return true; // Russian military

        return false;
    }

    // Function to get category description
    function getCategoryDescription(category) {
        var categoryMap = {
            'A0': 'No ADS-B Emitter Category',
            'A1': 'Light (< 15,500 lbs)',
            'A2': 'Small (15,500 to 75,000 lbs)',
            'A3': 'Large (75,000 to 300,000 lbs)',
            'A4': 'High Vortex Large',
            'A5': 'Heavy (> 300,000 lbs)',
            'A6': 'High Performance (> 5g)',
            'A7': 'Rotorcraft',
            'B0': 'No ADS-B Emitter Category',
            'B1': 'Glider / sailplane',
            'B2': 'Lighter-than-air',
            'B3': 'Parachutist / skydiver',
            'B4': 'Ultralight / hang-glider',
            'B5': 'Reserved',
            'B6': 'Unmanned aerial vehicle',
            'B7': 'Space / trans-atmospheric',
            'C0': 'No ADS-B Emitter Category',
            'C1': 'Surface vehicle - emergency',
            'C2': 'Surface vehicle - service',
            'C3': 'Point obstacle'
        };

        return categoryMap[category] || category;
    }

    // Function to create rotating colored plane icon
    function createPlaneIcon(heading, altitude) {
        var color = getAltitudeColor(altitude);
        var planeSvg = '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">' +
            '<path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" ' +
            'fill="' + color + '" stroke="#000" stroke-width="0.5"/>' +
            '</svg>';

        return L.divIcon({
            html: '<div style="transform: rotate(' + heading + 'deg);">' + planeSvg + '</div>',
            className: 'plane-icon',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
    }

    // Function to fetch and display aircraft
    function updateAircraft() {
        // Check if map is available
        if (typeof map === 'undefined') {
            console.error('Map object not found. Retrying...');
            return;
        }

        // Create aircraft layer if not exists
        if (!aircraftLayer) {
            console.log('Creating aircraft layer...');
            aircraftLayer = L.layerGroup().addTo(map);
        }

        console.log('Fetching aircraft data...');
        fetch('/api/aircraft/')
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                // Save which aircraft popup is currently open (if any)
                var previouslyOpenHex = openPopupHex;

                // Clear existing aircraft markers
                aircraftLayer.clearLayers();

                // Update masthead live counter
                var ribbonAir = document.getElementById('ribbonAircraft');
                if (ribbonAir) ribbonAir.textContent = (data.features ? data.features.length : 0).toLocaleString('lt-LT');

                if (data.features && data.features.length > 0) {
                    console.log('Displaying ' + data.features.length + ' aircraft over Lithuania');

                    data.features.forEach(function(feature) {
                        var props = feature.properties;
                        var coords = feature.geometry.coordinates;
                        var heading = props.heading || 0;
                        var altitude = props.altitude || 0;

                        // Create plane marker with rotation and color
                        var marker = L.marker([coords[1], coords[0]], {
                            icon: createPlaneIcon(heading, altitude)
                        });

                        // Create popup with aircraft info
                        var color = getAltitudeColor(altitude);
                        var altitudeBand = altitude < 10000 ? 'Low' :
                                          altitude < 25000 ? 'Medium' :
                                          altitude < 40000 ? 'High' : 'Very High';

                        var compassDirection = getCompassDirection(heading);
                        var registration = props.registration;
                        var photoId = 'photo-' + props.hex;

                        // Check if we already have photo in cache
                        var cachedPhoto = photoCache[registration];

                        // Build compact popup content
                        var popupContent =
                            '<div class="popup-content aircraft-popup" style="min-width: 250px; max-width: 320px; font-size: 12px;">' +
                            '<h4 style="margin: 0 0 8px 0; color:' + color + '; font-size: 14px;"><span>✈</span> ' + (props.flight || 'Unknown Flight') + '</h4>';

                        // Basic Info Section (compact)
                        var country = getCountryFromRegistration(props.registration);
                        var military = isMilitary(props.registration, props.category);
                        var categoryDesc = getCategoryDescription(props.category);

                        popupContent += '<div style="margin-bottom: 8px; font-size: 11px;">';
                        popupContent += '<strong style="color: #666; font-size: 11px;">AIRCRAFT</strong><br>';
                        popupContent += '<div style="margin-left: 8px;">';
                        popupContent += '<span style="font-size: 12px;">' + props.description + '</span> (' + props.type + ')<br>';
                        if (country) {
                            popupContent += '<small style="font-size: 10px;">' + country + '</small><br>';
                        }
                        popupContent += '<small style="font-size: 10px;">Reg: ' + props.registration + ' | Hex: ' + props.hex + ' | Squawk: ' + props.squawk + '</small>';
                        popupContent += '</div></div>';

                        // Altitude Section (compact)
                        popupContent += '<div style="margin-bottom: 6px; font-size: 11px;">';
                        popupContent += '<strong style="color: #666; font-size: 11px;">ALTITUDE</strong><br>';
                        popupContent += '<div style="margin-left: 8px;">';
                        popupContent += '<span style="color:' + color + '; font-weight:bold; font-size: 13px;">' +
                            Math.round(props.altitude).toLocaleString() + ' ft</span>';
                        if (props.baro_rate && props.baro_rate !== 0) {
                            var rateSymbol = props.baro_rate > 0 ? '↑' : '↓';
                            var rateColor = props.baro_rate > 0 ? 'green' : 'red';
                            popupContent += ' <small style="color:' + rateColor + '; font-size: 10px;">' + rateSymbol + ' ' +
                                Math.abs(Math.round(props.baro_rate)) + ' ft/min</small>';
                        }
                        popupContent += '</div></div>';

                        // Speed Section (compact)
                        popupContent += '<div style="margin-bottom: 6px; font-size: 11px;">';
                        popupContent += '<strong style="color: #666; font-size: 11px;">SPEED</strong><br>';
                        popupContent += '<div style="margin-left: 8px;">';
                        popupContent += '<span style="font-size: 12px;">' + Math.round(props.speed) + ' knots</span>';
                        if (props.mach) {
                            popupContent += ' <small style="font-size: 10px;">(Mach ' + props.mach.toFixed(2) + ')</small>';
                        }
                        popupContent += '</div></div>';

                        // Navigation Section (compact)
                        popupContent += '<div style="margin-bottom: 6px; font-size: 11px;">';
                        popupContent += '<strong style="color: #666; font-size: 11px;">NAVIGATION</strong><br>';
                        popupContent += '<div style="margin-left: 8px;">';
                        popupContent += '<span style="font-size: 12px;">' + Math.round(heading) + '° (' + compassDirection + ')</span>';
                        if (props.roll) {
                            popupContent += ' <small style="font-size: 10px;">| Roll: ' + props.roll.toFixed(1) + '°</small>';
                        }
                        if (props.nav_modes && props.nav_modes.length > 0) {
                            popupContent += '<br><small style="font-size: 10px;">AP: ' + props.nav_modes.join(', ') + '</small>';
                        }
                        popupContent += '</div></div>';

                        // Weather Section (compact, if available)
                        if (props.wind_speed || props.oat) {
                            popupContent += '<div style="margin-bottom: 6px; font-size: 11px;">';
                            popupContent += '<strong style="color: #666; font-size: 11px;">WEATHER</strong><br>';
                            popupContent += '<div style="margin-left: 8px; font-size: 10px;">';
                            if (props.wind_speed && props.wind_dir) {
                                popupContent += 'Wind: ' + Math.round(props.wind_speed) + ' kt @ ' + Math.round(props.wind_dir) + '° ';
                            }
                            if (props.oat) {
                                popupContent += '| Temp: ' + Math.round(props.oat) + '°C';
                            }
                            popupContent += '</div></div>';
                        }

                        // Database Flags Section - only show if we have actual flags
                        var flags = [];
                        if (military) flags.push('military');
                        if (categoryDesc && categoryDesc !== props.category) flags.push(categoryDesc);
                        if (props.nic) flags.push('NIC: ' + props.nic);
                        if (props.nac_p) flags.push('NAC_P: ' + props.nac_p);
                        if (props.sil) flags.push('SIL: ' + props.sil);
                        if (props.mlat && props.mlat.length > 0) flags.push('MLAT');

                        if (flags.length > 0) {
                            popupContent += '<div style="margin-bottom: 6px; font-size: 11px;">';
                            popupContent += '<strong style="color: #666; font-size: 11px;">DB FLAGS</strong><br>';
                            popupContent += '<div style="margin-left: 8px; font-size: 10px;">';
                            popupContent += flags.join(', ');
                            popupContent += '</div></div>';
                        }

                        // Emergency status (only show if there's an actual emergency)
                        if ((props.emergency && props.emergency !== 'none') || (props.alert && props.alert !== 0)) {
                            popupContent += '<div style="background: #ffebee; padding: 6px; border-left: 3px solid #f44336; margin-top: 6px; font-size: 11px;">';
                            popupContent += '<strong style="color: #d32f2f; font-size: 11px;">⚠ ALERT</strong>';
                            if (props.emergency && props.emergency !== 'none') {
                                popupContent += ' - ' + props.emergency;
                            }
                            popupContent += '</div>';
                        }

                        // Photo section at the bottom - use cached photo if available
                        popupContent += '<div id="' + photoId + '" style="margin-top: 10px; text-align: center; border-top: 1px solid #eee; padding-top: 8px;">';

                        if (cachedPhoto !== undefined) {
                            // We have cached result (either photo URL or null)
                            if (cachedPhoto) {
                                popupContent += '<img src="' + cachedPhoto + '" ' +
                                    'style="max-width: 100%; max-height: 150px; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.1);" ' +
                                    'onerror="this.style.display=\'none\';" ' +
                                    'alt="Aircraft">' +
                                    '<div style="font-size: 9px; color: #999; margin-top: 4px;">PlaneSpotters.net</div>';
                            } else {
                                popupContent += '<div style="color: #999; font-size: 10px;">No photo available</div>';
                            }
                        } else {
                            // Not cached yet, show loading message
                            popupContent += '<div style="color: #999; font-size: 10px;">Loading photo...</div>';
                        }

                        popupContent += '</div>';
                        popupContent += '</div>';

                        marker.bindPopup(popupContent, {maxWidth: 320});

                        // Track popup open/close events
                        marker.on('popupopen', function() {
                            openPopupHex = props.hex;

                            // Only fetch photo if not already cached
                            if (photoCache[registration] === undefined) {
                                fetchAircraftPhoto(registration, function(photoUrl) {
                                    var photoElement = document.getElementById(photoId);
                                    if (photoElement) {
                                        if (photoUrl) {
                                            photoElement.innerHTML =
                                                '<img src="' + photoUrl + '" ' +
                                                'style="max-width: 100%; max-height: 150px; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.1);" ' +
                                                'onerror="this.style.display=\'none\';" ' +
                                                'alt="Aircraft">' +
                                                '<div style="font-size: 9px; color: #999; margin-top: 4px;">PlaneSpotters.net</div>';
                                        } else {
                                            photoElement.innerHTML = '<div style="color: #999; font-size: 10px;">No photo available</div>';
                                        }
                                    }
                                });
                            }
                        });

                        marker.on('popupclose', function() {
                            if (openPopupHex === props.hex) {
                                openPopupHex = null;
                            }
                        });

                        // Add to aircraft layer
                        aircraftLayer.addLayer(marker);

                        // Re-open popup if this was the previously open aircraft
                        if (previouslyOpenHex && previouslyOpenHex === props.hex) {
                            marker.openPopup();
                        }
                    });
                } else {
                    console.log('No aircraft data received');
                }
            })
            .catch(function(error) {
                var ribbonAirErr = document.getElementById('ribbonAircraft');
                if (ribbonAirErr) ribbonAirErr.textContent = '—';
                console.error('Error fetching aircraft data:', error);
            });
    }

    // Initialize aircraft tracking - wait a bit for map to be fully ready
    function initAircraftTracking() {
        console.log('Initializing aircraft tracking...');

        // Retry logic: check if map exists, if not retry after delay
        if (typeof map === 'undefined') {
            console.log('Map not ready yet, retrying in 500ms...');
            setTimeout(initAircraftTracking, 500);
            return;
        }

        console.log('Map found! Starting aircraft updates...');
        updateAircraft();
        setInterval(updateAircraft, 10000);
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAircraftTracking);
    } else {
        initAircraftTracking();
    }
})();
