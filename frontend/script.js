/**
 * Configurações e Constantes
 */
const API_BASE_URL = 'http://localhost:5050';

/**
 * Gerenciamento de Estado
 * Armazena informações vitais sobre o usuário, sessão e estado da interface.
 */
const state = {
    userId: localStorage.getItem('if_agent_user_id'),
    sessionId: localStorage.getItem('if_agent_current_session_id'),
    isSidebarOpen: false,
    isLoading: false, // Pode ser usado para travar interface se necessário
    isAnonymous: false
};

/**
 * Elementos da Interface do Usuário (UI)
 * Mapeamento centralizado dos elementos do DOM para acesso rápido.
 */
const elements = {
    sidebar: document.getElementById('sidebar'),
    openSidebarBtn: document.getElementById('openSidebarBtn'),
    closeSidebarBtn: document.getElementById('closeSidebarBtn'),
    newChatBtn: document.getElementById('newChatBtn'),
    historyList: document.getElementById('historyList'),
    anonymousChatBtn: document.getElementById('anonymousChatBtn'),
    chatArea: document.getElementById('chatArea'),
    messagesContainer: document.getElementById('messagesContainer'),
    welcomeScreen: document.getElementById('welcomeScreen'),
    userPrompt: document.getElementById('userPrompt'),
    sendBtn: document.getElementById('sendBtn'),
    toastContainer: document.getElementById('toastContainer'),
    anonymousBadge: document.getElementById('anonymousBadge'),
    welcomeIcon: document.querySelector('.welcome_icon')
};

/**
 * Inicialização da Aplicação
 * Configura ouvintes de eventos, verifica ID do usuário e carrega o histórico inicial.
 */
async function init() {
    setupEventListeners();
    setupTextAreaAutoResize();
    setupModalListeners();

    // Verificação ou Geração de ID de Usuário
    if (!state.userId) {
        try {
            await generateUserId();
        } catch (error) {
            showToast('Erro ao criar identificação de usuário.', 'error');
            return; // Impede prosseguimento se não houver ID
        }
    }

    // Carrega o histórico de sessões anteriores do localStorage
    loadHistory();

    // Tenta restaurar a última sessão ativa
    if (state.sessionId) {
        loadSession(state.sessionId);
    } else {
        showWelcomeScreen();
    }
}

/**
 * =================================================================================
 * Interações com a API (Backend)
 * =================================================================================
 */

/**
 * Gera um novo User ID através do backend.
 * @throws {Error} Se a requisição falhar.
 */
async function generateUserId() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/generate`);
        if (!response.ok) throw new Error('Falha na requisição de autenticação');
        const data = await response.json();
        state.userId = data.user_id;
        localStorage.setItem('if_agent_user_id', state.userId);
    } catch (error) {
        console.error('Erro ao gerar ID de usuário:', error);
        throw error;
    }
}

/**
 * Cria uma nova sessão no backend.
 * @param {string} [userIdOverride] - ID de usuário opcional (usado para modo anônimo).
 * @returns {Promise<string|null>} O ID da sessão criada ou null em caso de erro.
 */
async function apiCreateSessionId(userIdOverride) {
    try {
        const uid = userIdOverride || state.userId;
        const response = await fetch(`${API_BASE_URL}/sessions/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: uid })
        });

        if (!response.ok) throw new Error('Falha ao criar sessão no backend');

        const data = await response.json();
        return data.session_id;
    } catch (error) {
        console.error('Erro ao criar ID de sessão:', error);
        return null;
    }
}

/**
 * Carrega e renderiza uma sessão específica.
 * @param {string} sessionId - O ID da sessão a ser carregada.
 */
async function loadSession(sessionId) {
    state.sessionId = sessionId;
    localStorage.setItem('if_agent_current_session_id', sessionId);

    // Atualiza estado ativo na interface (barra lateral)
    updateHistoryActiveState(sessionId);

    // Reseta estado anônimo ao carregar um item do histórico (assumimos que histórico = usuário normal)
    state.isAnonymous = false;
    elements.anonymousBadge.style.display = 'none';
    if (elements.welcomeIcon) elements.welcomeIcon.classList.remove('anonymous');

    showWelcomeScreen(false);
    elements.messagesContainer.innerHTML = '<div class="history_empty_state"><span class="loader_spinner"></span></div>';

    try {
        const response = await fetch(`${API_BASE_URL}/sessions/get`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, user_id: state.userId })
        });

        if (!response.ok) {
            throw new Error('Erro ao carregar sessão do servidor');
        }

        const data = await response.json();

        // Atualiza título local se o backend retornou um resumo atualizado
        if (data.summary) {
            updateLocalSessionTitle(sessionId, data.summary);
        }

        // Renderiza as mensagens (campo 'messages' ou 'chat' para compatibilidade)
        const messages = data.messages || data.chat || [];
        renderChat(messages);
    } catch (error) {
        console.warn('Falha ao carregar sessão:', error);
        if (state.sessionId === sessionId) {
            showToast('Não foi possível carregar a conversa.', 'error');
            // Exibe estado vazio em caso de erro
            elements.messagesContainer.innerHTML = '<div class="history_empty_state"><p>Erro ao carregar mensagens.</p></div>';
        }
    }
}

/**
 * Envia uma mensagem do usuário para o agente.
 */
async function sendMessage() {
    const text = elements.userPrompt.value.trim();
    if (!text) return;

    // Atualização imediata da interface (Optimistic UI)
    elements.userPrompt.value = '';
    resizeTextArea(elements.userPrompt);
    elements.sendBtn.disabled = true;
    showWelcomeScreen(false);

    // Se não houver sessão, cria uma (Lazy Creation)
    if (!state.sessionId) {
        // Usa 'anonymous' se a flag estiver ativa, senão usa ID do usuário real
        const uid = state.isAnonymous ? 'anonymous' : state.userId;
        const newId = await apiCreateSessionId(uid);

        if (!newId) {
            showToast('Erro ao iniciar sessão.', 'error');
            elements.sendBtn.disabled = false;
            return;
        }
        state.sessionId = newId;

        // Persiste o ID da sessão atual
        localStorage.setItem('if_agent_current_session_id', newId);

        // Só salva no histórico se NÃO for anônimo
        if (!state.isAnonymous) {
            let title = text.substring(0, 30);
            if (text.length > 30) title += '...';
            addToLocalHistory(newId, title);
            loadHistory();
        }
    }

    // Adiciona mensagem do usuário na interface
    addMessageToUI('user', text);

    // Exibe indicador de digitação
    const loadingId = addLoadingIndicator();

    try {
        // Envia requisição para o backend
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: text,
                user_id: state.isAnonymous ? 'anonymous' : state.userId,
                session_id: state.sessionId
            })
        });

        if (!response.ok) throw new Error('Erro na comunicação com o agente');

        const data = await response.json();

        // Remove indicador de carregamento
        removeMessageFromUI(loadingId);

        // Adiciona resposta do agente
        addMessageToUI('model', data.response);

    } catch (error) {
        removeMessageFromUI(loadingId);
        showToast('Ocorreu um erro ao processar sua mensagem.', 'error');
        addMessageToUI('model', '**Erro:** Não foi possível obter uma resposta agora. Tente novamente.', false);
    } finally {
        elements.sendBtn.disabled = false;
        elements.userPrompt.focus();
    }
}

/**
 * =================================================================================
 * Gerenciamento de Sessão (Frontend Logic)
 * =================================================================================
 */

/**
 * Inicia o processo de uma nova conversa (Reset de UI).
 * Apenas limpa o estado, a sessão real será criada ao enviar a primeira mensagem.
 */
function startNewChat() {
    state.sessionId = null;
    state.isAnonymous = false;
    localStorage.removeItem('if_agent_current_session_id');

    // Remove sinalizadores de modo anônimo
    elements.anonymousBadge.style.display = 'none';
    if (elements.welcomeIcon) elements.welcomeIcon.classList.remove('anonymous');

    clearChat();
    showWelcomeScreen(true);
    updateHistoryActiveState(null);
}

/**
 * Inicia o modo anônimo.
 * Semelhante ao novo chat, mas seta a flag isAnonymous.
 */
function startAnonymousChat() {
    state.sessionId = null;
    state.isAnonymous = true;
    localStorage.removeItem('if_agent_current_session_id');

    // Ativa sinalizadores visuais
    elements.anonymousBadge.style.display = 'flex';
    if (elements.welcomeIcon) elements.welcomeIcon.classList.add('anonymous');

    clearChat();
    showWelcomeScreen(true);
    updateHistoryActiveState(null);

    // Fecha sidebar no mobile para melhor UX
    if (window.innerWidth <= 768) elements.sidebar.classList.remove('open');

    showToast('Modo Anônimo ativado. Suas conversas não serão salvas no histórico.', 'info');
}

/**
 * =================================================================================
 * Gerenciamento de Histórico Local (localStorage)
 * =================================================================================
 */

/**
 * Obtém o histórico salvo localmente.
 */
function getLocalHistory() {
    try {
        const item = localStorage.getItem('if_agent_history_v1');
        return item ? JSON.parse(item) : [];
    } catch {
        return [];
    }
}

/**
 * Adiciona um item ao topo do histórico local.
 */
function addToLocalHistory(id, title) {
    const history = getLocalHistory();
    // Previne duplicados
    if (history.find(h => h.id === id)) return;

    history.unshift({
        id: id,
        title: title,
        timestamp: Date.now()
    });

    localStorage.setItem('if_agent_history_v1', JSON.stringify(history));
}

/**
 * Atualiza o título de uma sessão no histórico local.
 * Útil quando o backend retorna um resumo mais preciso.
 */
function updateLocalSessionTitle(id, newTitle) {
    // Se for anônimo, ignoramos o histórico local
    if (state.isAnonymous) return;

    const history = getLocalHistory();
    const index = history.findIndex(h => h.id === id);
    if (index !== -1) {
        if (history[index].title !== newTitle) {
            history[index].title = newTitle;
            localStorage.setItem('if_agent_history_v1', JSON.stringify(history));

            // Atualiza a lista visualmente
            const localHistory = getLocalHistory();
            renderHistoryList(localHistory);
        }
    }
}

/**
 * Lógica de Exclusão de Sessão
 */
let sessionToDeleteId = null;

function setupModalListeners() {
    const deleteModal = document.getElementById('deleteModal');
    const cancelBtn = document.getElementById('cancelDeleteBtn');
    const confirmBtn = document.getElementById('confirmDeleteBtn');

    cancelBtn.addEventListener('click', closeDeleteModal);

    confirmBtn.addEventListener('click', () => {
        if (sessionToDeleteId) {
            deleteSession(sessionToDeleteId);
        }
        closeDeleteModal();
    });

    // Fechar ao clicar fora do modal
    deleteModal.addEventListener('click', (e) => {
        if (e.target === deleteModal) {
            closeDeleteModal();
        }
    });
}

window.openDeleteModal = function (id, title) {
    sessionToDeleteId = id;
    document.getElementById('deleteModalTitle').textContent = title;
    document.getElementById('deleteModal').classList.add('open');
}

function closeDeleteModal() {
    sessionToDeleteId = null;
    document.getElementById('deleteModal').classList.remove('open');
}

function deleteSession(id) {
    let history = getLocalHistory();
    history = history.filter(h => h.id !== id);
    localStorage.setItem('if_agent_history_v1', JSON.stringify(history));

    // Se a sessão apagada era a atual, reseta a interface
    if (state.sessionId === id) {
        startNewChat();
    } else {
        // Apenas recarrega a sidebar se não resetamos tudo
        loadHistory();
    }
}

/**
 * Carrega a lista de histórico na interface (wrapper para renderHistoryList)
 */
function loadHistory() {
    const localHistory = getLocalHistory();
    renderHistoryList(localHistory);
}

/**
 * =================================================================================
 * Renderização e Helpers de UI
 * =================================================================================
 */

/**
 * Renderiza a lista de histórico na barra lateral.
 */
function renderHistoryList(historyItems) {
    if (!historyItems || historyItems.length === 0) {
        elements.historyList.innerHTML = '<div class="history_empty_state"><p>Nenhuma conversa.</p></div>';
        return;
    }

    elements.historyList.innerHTML = '';

    historyItems.forEach(item => {
        const div = document.createElement('div');
        div.className = 'history_item';
        if (item.id === state.sessionId) div.classList.add('active');

        // Área do link (clicável para abrir)
        const linkArea = document.createElement('div');
        linkArea.className = 'history_link_area';
        linkArea.innerHTML = `<i class="ph ph-chat-circle"></i> <span>${escapeHtml(item.title)}</span>`;
        linkArea.onclick = () => {
            if (item.id !== state.sessionId) {
                loadSession(item.id);
            }
            if (window.innerWidth <= 768) elements.sidebar.classList.remove('open');
        };

        // Botão de Excluir (visível no hover desktop ou sempre mobile)
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete_chat_btn';
        deleteBtn.innerHTML = '<i class="ph ph-trash"></i>';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            window.openDeleteModal(item.id, item.title);
        };

        div.appendChild(linkArea);
        div.appendChild(deleteBtn);

        elements.historyList.appendChild(div);
    });
}

/**
 * Atualiza visualmente qual item do histórico está ativo.
 */
function updateHistoryActiveState(activeId) {
    // Re-renderização total garante consistência de dados
    renderHistoryList(getLocalHistory());
}

/**
 * Renderiza uma lista completa de mensagens de chat.
 */
function renderChat(messages) {
    elements.messagesContainer.innerHTML = '';
    messages.forEach(msg => {
        addMessageToUI(msg.role, msg.content, false);
    });
    scrollToBottom();
}

/**
 * Adiciona uma única mensagem à interface.
 * @param {string} role - 'user' ou 'model'.
 * @param {string} content - O texto da mensagem.
 * @param {boolean} animate - Se deve animar a entrada (fade-in).
 */
function addMessageToUI(role, content, animate = true) {
    const isUser = role === 'user';
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message';
    if (!animate) msgDiv.style.animation = 'none';
    if (!animate) msgDiv.style.opacity = '1';

    const avatarIcon = isUser ? 'ph-user' : 'ph-robot';
    const avatarClass = isUser ? 'message_avatar user' : 'message_avatar';

    // Sanitização e Markdown:
    // Usuário: Apenas escape HTML simples para segurança.
    // Modelo: Markdown parseado e depois higienizado com DOMPurify.
    const parsedContent = isUser ? escapeHtml(content) : DOMPurify.sanitize(marked.parse(content));

    msgDiv.innerHTML = `
        <div class="${avatarClass}">
            <i class="ph ${avatarIcon}"></i>
        </div>
        <div class="message_content">
            ${isUser ? `<p>${parsedContent}</p>` : parsedContent}
        </div>
    `;

    elements.messagesContainer.appendChild(msgDiv);
    scrollToBottom();
}

/**
 * Adiciona o indicador de "digitando..."
 * @returns {string} O ID do elemento criado, para remoção posterior.
 */
function addLoadingIndicator() {
    const id = 'loading-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message';
    msgDiv.id = id;
    msgDiv.innerHTML = `
        <div class="message_avatar">
            <i class="ph ph-robot"></i>
        </div>
        <div class="message_content">
            <div class="typing_indicator">
                <div class="typing_dot"></div>
                <div class="typing_dot"></div>
                <div class="typing_dot"></div>
            </div>
        </div>
    `;
    elements.messagesContainer.appendChild(msgDiv);
    scrollToBottom();
    return id;
}

/**
 * Remove uma mensagem específica (usado para remover loading).
 */
function removeMessageFromUI(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

/**
 * Limpa a área de chat visualmente.
 */
function clearChat() {
    elements.messagesContainer.innerHTML = '';
    elements.userPrompt.value = '';
    resizeTextArea(elements.userPrompt);
}

/**
 * Alterna entre Tela de Boas-vindas e Container de Mensagens.
 */
function showWelcomeScreen(show = true) {
    if (show) {
        elements.welcomeScreen.style.display = 'flex';
        elements.messagesContainer.style.display = 'none';
    } else {
        elements.welcomeScreen.style.display = 'none';
        elements.messagesContainer.style.display = 'flex';
    }
}

/**
 * Rola a área de chat para o final.
 */
function scrollToBottom() {
    elements.chatArea.scrollTop = elements.chatArea.scrollHeight;
}

/**
 * =================================================================================
 * Utilitários
 * =================================================================================
 */

/**
 * Exibe uma notificação toast temporária.
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    elements.toastContainer.appendChild(toast);

    // Animação de saída e remoção
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)'; // Sai por cima
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Escapa caracteres HTML para prevenir XSS simples.
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Redimensiona a altura da textarea baseada no conteúdo.
 */
function resizeTextArea(el) {
    el.style.height = 'auto'; // Reset para calcular corretamente
    el.style.height = el.scrollHeight + 'px';

    // Habilita/Desabilita botão de enviar
    elements.sendBtn.disabled = el.value.trim().length === 0;
}

/**
 * Configura ouvintes para redimensionamento automático.
 */
function setupTextAreaAutoResize() {
    elements.userPrompt.addEventListener('input', function () {
        resizeTextArea(this);
    });
}

/**
 * Configura todos os ouvintes de eventos da aplicação.
 */
function setupEventListeners() {
    // Alternar Barra Lateral (Sidebar)
    elements.openSidebarBtn.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
            elements.sidebar.classList.toggle('open');
        } else {
            elements.sidebar.classList.toggle('closed');
        }
    });

    elements.closeSidebarBtn.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
            elements.sidebar.classList.remove('open');
        } else {
            elements.sidebar.classList.add('closed');
        }
    });

    // Fechar sidebar no mobile ao clicar fora
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && elements.sidebar.classList.contains('open')) {
            // Verifica se o clique foi fora da sidebar e NÃO no botão de abrir
            if (!elements.sidebar.contains(e.target) && !elements.openSidebarBtn.contains(e.target)) {
                elements.sidebar.classList.remove('open');
            }
        }
    });

    // Botão Nova Conversa
    elements.newChatBtn.addEventListener('click', () => {
        // Previne criar nova sessão se a atual já estiver vazia
        const isEmpty = elements.messagesContainer.querySelectorAll('.message').length === 0;
        if (state.sessionId && isEmpty) {
            showToast('Você já está em uma nova conversa.', 'info');
            if (window.innerWidth <= 768) elements.sidebar.classList.remove('open');
            return;
        }

        startNewChat();
        if (window.innerWidth <= 768) {
            elements.sidebar.classList.remove('open');
        }
    });

    // Enviar Mensagem
    elements.sendBtn.addEventListener('click', sendMessage);

    elements.userPrompt.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Botão Modo Anônimo
    elements.anonymousChatBtn.addEventListener('click', () => {
        startAnonymousChat();
    });
}

// Inicia a aplicação quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', init);
