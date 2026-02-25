let connectedUsers = [];
let currentSuggestion = "";
let suggestionMatches = [];
let currentMatchIndex = 0;

const baseCommands = ['list', 'sessions', 'stop', 'chat:', 'file', 'accept', 'deny', 'exit'];

function toggleHelp() {
    document.getElementById('help-modal').classList.toggle('hidden');
}

async function doLogin() {
    const host = document.getElementById('host').value;
    const port = parseInt(document.getElementById('port').value);
    const nickname = document.getElementById('nickname').value;
    const status = document.getElementById('login-status');

    if (!nickname) { status.innerText = "Ingresa un nickname."; return; }

    status.innerText = "Conectando...";
    const conn = await pywebview.api.connect(host, port);
    if (conn.status === 'success') {
        const reg = await pywebview.api.set_name(nickname);
        if (reg.status === 'success') {
            document.getElementById('login-screen').classList.add('hidden');
            document.getElementById('main-ui').classList.remove('hidden');
            document.getElementById('my-name').innerText = reg.username;
            addEvent("[SISTEMA] Conectado exitosamente.");
            pywebview.api.send_command("list");
        } else {
            status.innerText = reg.message;
        }
    } else {
        status.innerText = conn.message;
    }
}

async function sendCmd() {
    const input = document.getElementById('cmd-input');
    const cmd = input.value.trim();
    if (!cmd) return;

    if (cmd === 'exit') {
        pywebview.api.close_window();
        return;
    }

    await pywebview.api.send_command(cmd);
    input.value = '';
    clearSuggestion();
}

function handleInput() {
    updateSuggestion();
}

function handleKeyDown(e) {
    const input = document.getElementById('cmd-input');

    if (e.key === 'Enter') {
        sendCmd();
    } else if (e.key === 'Tab') {
        e.preventDefault();
        if (currentSuggestion) {
            if (suggestionMatches.length > 1) {
                // Iterar si hay múltiples matches
                currentMatchIndex = (currentMatchIndex + 1) % suggestionMatches.length;
                applyMatchIndex();
            } else {
                // Aceptar sugerencia única
                input.value = currentSuggestion;
                updateSuggestion();
            }
        }
    } else if (e.key === 'ArrowRight') {
        // Aceptar sugerencia con flecha derecha si el cursor está al final
        if (input.selectionStart === input.value.length && currentSuggestion) {
            input.value = currentSuggestion;
            updateSuggestion();
        }
    }
}

function clearSuggestion() {
    currentSuggestion = "";
    suggestionMatches = [];
    currentMatchIndex = 0;
    document.getElementById('hint-layer').innerText = "";
}

function updateSuggestion() {
    const input = document.getElementById('cmd-input');
    const val = input.value;
    const hint = document.getElementById('hint-layer');

    if (!val) {
        clearSuggestion();
        return;
    }

    const lowerVal = val.toLowerCase();
    suggestionMatches = [];

    // Lógica de autocompletado multi-parte
    if (lowerVal.includes(':')) {
        const parts = val.split(':');
        const cmd = parts[0].toLowerCase();
        const prefix = parts[1].toLowerCase();

        if (cmd === 'chat' || cmd === 'stop') {
            // Autocompletar usuario tras los dos puntos
            suggestionMatches = connectedUsers
                .filter(u => u.toLowerCase().startsWith(prefix))
                .map(u => `${parts[0]}:${u}`);
        }
    } else {
        // Autocompletar comando base
        suggestionMatches = baseCommands
            .filter(c => c.startsWith(lowerVal))
            .map(c => c);
    }

    if (suggestionMatches.length > 0) {
        currentMatchIndex = 0;
        applyMatchIndex();
    } else {
        clearSuggestion();
    }
}

function applyMatchIndex() {
    const input = document.getElementById('cmd-input');
    const hint = document.getElementById('hint-layer');
    const val = input.value;

    currentSuggestion = suggestionMatches[currentMatchIndex];

    // Si el valor actual coincide con el inicio de la sugerencia (respetando mayúsculas/minúsculas original del input)
    // Mostramos el resto en el hint layer
    if (currentSuggestion.toLowerCase().startsWith(val.toLowerCase())) {
        const remaining = currentSuggestion.slice(val.length);
        // Usamos el texto exacto del usuario + el resto de la sugerencia
        hint.innerText = val + remaining;
    } else {
        hint.innerText = "";
    }
}

function addEvent(message) {
    if (message.startsWith("USERS_UPDATE:")) {
        const usersStr = message.replace("USERS_UPDATE:", "");
        connectedUsers = usersStr.split(",").filter(u => u !== "");
        return;
    }

    const log = document.getElementById('log');
    const div = document.createElement('div');
    div.className = 'msg';

    if (message.includes('[SISTEMA]') || message.includes('[SOLICITUD]')) div.classList.add('system');
    else if (message.includes('[ERROR]') || message.includes('[!]')) div.classList.add('error');
    else if (message.includes('[INFO]')) div.classList.add('info');
    else if (message.includes('] dice:')) div.classList.add('user-msg');
    else if (message.startsWith('[YO]')) {
        div.classList.add('own-msg');
        div.style.alignSelf = 'flex-end';
        div.style.textAlign = 'right';
        div.style.background = '#33415555';
        div.style.padding = '5px 10px';
        div.style.borderRadius = '10px';
    }

    div.innerText = message;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
}
