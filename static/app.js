let scanHistory = [];
let autoDetectMode = false;
let autoDetectInterval = null;
let totalCarbonSaved = 0;
let itemsRecycled = 0;
let itemsSorted = 0;

const badges = [
    { name: "Beginner", threshold: 0, icon: "🌱", color: "#6b7280" },
    { name: "Eco Warrior", threshold: 100, icon: "💚", color: "#10b981" },
    { name: "Champion", threshold: 500, icon: "♻️", color: "#3b82f6" },
    { name: "Hero", threshold: 1000, icon: "🌟", color: "#f59e0b" },
    { name: "Master", threshold: 2000, icon: "🏆", color: "#ef4444" }
];

let currentBadgeIndex = 0;

function showBadgeToast(badgeName, badgeIcon, badgeColor) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.borderLeftColor = badgeColor;
    toast.innerHTML = `
        <div class="toast-icon" style="background: ${badgeColor}15;">${badgeIcon}</div>
        <div class="toast-content">
            <div class="toast-title">New Badge Earned!</div>
            <div class="toast-message">${badgeName}</div>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function updateBadge() {
    let newBadgeIndex = 0;
    for (let i = badges.length - 1; i >= 0; i--) {
        if (totalCarbonSaved >= badges[i].threshold) {
            newBadgeIndex = i;
            break;
        }
    }
    
    if (newBadgeIndex > currentBadgeIndex) {
        const badge = badges[newBadgeIndex];
        showBadgeToast(badge.name, badge.icon, badge.color);
        currentBadgeIndex = newBadgeIndex;
    }
    
    const badge = badges[currentBadgeIndex];
    const badgeIconEl = document.getElementById('currentBadgeIcon');
    const badgeNameEl = document.getElementById('currentBadgeName');
    if (badgeIconEl) badgeIconEl.innerHTML = badge.icon;
    if (badgeNameEl) badgeNameEl.innerHTML = badge.name;
}

function updateImpactMetrics(result) {
    itemsSorted++;
    if (result.recyclable && result.carbonSaved > 0) {
        itemsRecycled++;
        totalCarbonSaved += result.carbonSaved;
    }
    
    const totalCarbonEl = document.getElementById('totalCarbon');
    const itemsRecycledEl = document.getElementById('itemsRecycled');
    const itemsSortedEl = document.getElementById('itemsSorted');
    
    if (totalCarbonEl) totalCarbonEl.innerHTML = totalCarbonSaved;
    if (itemsRecycledEl) itemsRecycledEl.innerHTML = itemsRecycled;
    if (itemsSortedEl) itemsSortedEl.innerHTML = itemsSorted;
    
    updateBadge();
}

async function analyzeImage() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');
    
    if (!video || !canvas) return;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    const imageData = canvas.toDataURL('image/jpeg');
    
    const resultDiv = document.getElementById('result');
    if (resultDiv) {
        resultDiv.innerHTML = `
            <div class="loading-state">
                <div class="loading-spinner"></div>
                <p>Analyzing...</p>
            </div>
        `;
    }
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imageData, auto: autoDetectMode })
        });
        
        const result = await response.json();
        displayResult(result);
        
        if (result.category !== 'Human' && result.category !== 'Error' && result.category !== 'Unknown') {
            addToHistory(result);
            updateImpactMetrics(result);
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        if (resultDiv) {
            resultDiv.innerHTML = `<div class="error-state"><p>Analysis failed. Please try again.</p></div>`;
        }
    }
}

function toggleAutoDetect() {
    const button = document.getElementById('autoDetectBtn');
    autoDetectMode = !autoDetectMode;
    
    if (autoDetectMode) {
        button.textContent = 'Stop';
        button.classList.add('stop');
        startAutoDetect();
    } else {
        button.textContent = 'Auto Detect';
        button.classList.remove('stop');
        stopAutoDetect();
    }
}

function startAutoDetect() {
    if (autoDetectInterval) clearInterval(autoDetectInterval);
    autoDetectInterval = setInterval(() => analyzeImage(), 3000);
}

function stopAutoDetect() {
    if (autoDetectInterval) {
        clearInterval(autoDetectInterval);
        autoDetectInterval = null;
    }
}

function displayResult(result) {
    const resultDiv = document.getElementById('result');
    if (!resultDiv) return;
    
    const confidence = result.confidence ? result.confidence.toFixed(1) : '0';
    const isRecyclable = result.recyclable || false;
    
    let resinHtml = '';
    if (result.resinCode) {
        resinHtml = `
            <div class="resin-code">
                <span class="resin-label">Resin Code</span>
                <span class="resin-value">${result.resinCode} (${result.resinType || 'Unknown'})</span>
            </div>
        `;
    }
    
    const categoryClass = result.category ? result.category.toLowerCase() : '';
    
    const html = `
        <div class="result-header">
            <div>
                <h3>${result.itemName || 'Unknown item'}</h3>
                <span class="category-tag ${categoryClass}">${result.category || 'Unknown'}</span>
            </div>
            <span class="bin-tag ${result.binColor || 'black'}">${result.bin || 'Unknown'}</span>
        </div>
        
        <div class="confidence-row">
            <span class="confidence-label">Confidence</span>
            <div class="confidence-bar-wrapper">
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${confidence}%"></div>
                </div>
                <span class="confidence-value">${confidence}%</span>
            </div>
        </div>
        
        ${resinHtml}
        
        <div class="instruction-box">
            <p>${result.instruction || 'No instructions available'}</p>
        </div>
        
        <div class="impact-row">
            <div class="impact-item">
                <span class="impact-label">Carbon Saved</span>
                <span class="impact-value">${result.carbonSaved || 0}g CO₂</span>
            </div>
            <div class="impact-item">
                <span class="impact-label">Recyclable</span>
                <span class="impact-value ${isRecyclable ? 'success' : 'danger'}">${isRecyclable ? 'Yes' : 'No'}</span>
            </div>
        </div>
    `;
    
    resultDiv.innerHTML = html;
}

function addToHistory(item) {
    scanHistory.unshift({
        name: item.itemName || 'Unknown',
        category: item.category || 'Unknown',
        bin: item.bin || 'Unknown',
        binColor: item.binColor || 'black',
        timestamp: new Date().toLocaleTimeString(),
        confidence: item.confidence || 0,
        resinCode: item.resinCode,
        carbonSaved: item.carbonSaved || 0,
        recyclable: item.recyclable || false,
        instruction: item.instruction || ''
    });
    
    if (scanHistory.length > 5) scanHistory = scanHistory.slice(0, 5);
    updateHistoryDisplay();
}

function showHistoryDetails(index) {
    const item = scanHistory[index];
    if (!item) return;
    
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Scan Details</h3>
                <button class="modal-close" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="detail-row">
                    <span class="detail-label">Item</span>
                    <span class="detail-value">${item.name}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Category</span>
                    <span class="detail-value">${item.category}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Bin</span>
                    <span class="detail-value bin-tag ${item.binColor}">${item.bin}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Confidence</span>
                    <span class="detail-value">${item.confidence ? item.confidence.toFixed(1) : '0'}%</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Carbon Saved</span>
                    <span class="detail-value">${item.carbonSaved}g CO₂</span>
                </div>
                <div class="instruction-detail">
                    <strong>Instructions</strong>
                    <p>${item.instruction || 'No instructions available'}</p>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
}

function updateHistoryDisplay() {
    const historyDiv = document.getElementById('history');
    if (!historyDiv) return;
    
    if (scanHistory.length === 0) {
        historyDiv.innerHTML = '<p class="empty-history">No scans recorded</p>';
        return;
    }
    
    let html = '<div class="history-list">';
    for (let i = 0; i < scanHistory.length; i++) {
        const item = scanHistory[i];
        const confidence = item.confidence ? item.confidence.toFixed(1) : '0';
        html += `
            <div class="history-item" onclick="showHistoryDetails(${i})">
                <div class="history-main">
                    <div class="history-name">${item.name}</div>
                    <div class="history-meta">
                        <span class="history-category">${item.category}</span>
                        <span class="history-bin ${item.binColor}">${item.bin}</span>
                    </div>
                </div>
                <div class="history-stats">
                    <span class="history-confidence">${confidence}%</span>
                    <span class="history-carbon">+${item.carbonSaved}g</span>
                    <span class="history-time">${item.timestamp}</span>
                </div>
            </div>
        `;
    }
    html += '</div>';
    historyDiv.innerHTML = html;
}

function startCamera() {
    const video = document.getElementById('video');
    if (!video) return;
    
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => { video.srcObject = stream; })
        .catch(err => {
            const resultDiv = document.getElementById('result');
            if (resultDiv) {
                resultDiv.innerHTML = `<div class="error-state"><p>Unable to access camera. Please check permissions.</p></div>`;
            }
        });
}

window.onload = startCamera;